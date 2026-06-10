# 资讯日报自动生成并邮件投递 — 设计

> 日期：2026-06-10
> 范围：仅本文档描述的最小变更集。不重做 daily_report SOP，不改 scheduler.py。
> 哲学：承重墙（agent_loop / scheduler）不动；新增能力收敛于一个 `do_send_email` 工具 + 配置 + 提示模板。

---

## 0. 目标与成功标准

| 维度 | 目标 |
|---|---|
| 范围 | 用户提供 100+ 监控 URL 列表 + 收件人列表 → 系统按既定时间生成 Markdown 日报 → 转 Word 附件 → 投递到所有收件人邮箱 |
| 触发 | 由现有 `reflect/scheduler.py` 触发，零修改 |
| 凭证 | SMTP 账号/授权码读 `ekey.py`；收件人地址在任务 JSON 里 |
| 失败 | 报告生成成功 → 邮件投递失败 3 次重试 → 仍失败则在报告头写 `email_status: FAILED` 并写日志，不阻塞调度器判定本任务"已完成" |
| 净行数 | 核心代码净增 ≤ 100 行；删 0 行（ekey.py 物理删除见 §6） |

**非目标（明确不做）**：
- 不重做 `daily_report_sop.md` 的抓取/筛选/字数逻辑
- 不改 `scheduler.py` 的状态机
- 不新增 Python 依赖（仅用标准库 + 外部 `pandoc`）
- 不做 HTML 邮件、不做多 MIME 多 part 混合（只要 .docx 附件 + 纯文本正文）
- 不实现邮件接收/IMAP/已读回执

---

## 1. 现状与边界

### 1.1 复用资产（不动）

| 资产 | 位置 | 角色 |
|---|---|---|
| `daily_report_sop.md` | `memory/` | 日报生成流程（URL 抓取、窗口过滤、字数控制） |
| `scheduled_task_sop.md` | `memory/` | 调度任务定义（JSON 格式、`sche_tasks/` 目录） |
| `reflect/scheduler.py` | 根目录 | 60s 轮询调度器 |
| `sche_tasks/*.json` | 根目录 | 任务定义（已有 prompt/schedule/repeat/enabled 字段） |
| `sche_tasks/done/` | 根目录 | 报告文件（路径由 scheduler 自动生成，格式 `YYYY-MM-DD_HHMM_<task>.md`，见 `reflect/scheduler.py:123`） |
| `core/agent_loop.py` | `core/` | 承重墙，复用其 `StepOutcome` 协议 |
| `core/ea.py` | `core/` | 工具实现宿主，新工具挂在这里 |
| `ekey.py` | 根目录 | 凭证集中地（gitignore 状态：`已存在 .gitignore`） |

### 1.2 现状缺口

仓库内 `grep -rE "smtp|smtplib|send_email|email"` 零结果：
- `core/ea.py` 无邮件工具
- `core/llm/` 七模块无邮件相关
- 无 `.md → .docx` 转换
- `sche_tasks/*.json` 任务定义无 `recipients` 字段

### 1.3 外部依赖前置

| 依赖 | 来源 | 用途 |
|---|---|---|
| `pandoc` | 系统包（`brew install pandoc` / `apt install pandoc`） | `.md → .docx` 转换 |
| SMTP 服务可达 | 用户的 Gmail/QQ/163/企业邮箱 | 邮件投递 |
| TLS 端口 587 或 SSL 465 | 邮箱服务提供方 | 加密传输 |

`pandoc` 缺失时 `do_send_email` 必须**快速失败**并写清晰错误（见 §4），不静默退化。

---

## 2. 架构

### 2.1 数据流

```
[scheduler 每 60s 轮询]
   ↓ 检测到 task.json 满足 schedule
[scheduler 拼 prompt 注入 done/ 报告路径]
   ↓
[agent_runner_loop 启动]
   ↓
[LLM 按 prompt 步骤执行]
   ├─ 读监控 URL（requests 并行）
   ├─ 生成 ../sche_tasks/done/YYYY-MM-DD_<task>.md
   ├─ code_run: pandoc md → docx
   └─ do_send_email:
        ├─ 读 ekey.EMAIL_SMTP
        ├─ 读 task.recipients
        ├─ 组装 email.mime (正文 + .docx 附件)
        ├─ smtplib.SMTP + starttls / login / sendmail
        └─ 重试 3 次 (指数退避: 1s/3s/9s)
   ↓
[StepOutcome 报告 agent 任务完成]
[scheduler 看见 done/<date>_<task>.md 存在 → 标记任务 done]
```

### 2.2 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 邮件发送位置 | LLM 调 `do_send_email` 工具 | 完全复用 agent loop；失败/重试/附件构造都在工具内闭环 |
| 重试位置 | `do_send_email` 内部 | 调用方零感知；scheduler 不感知邮件失败 |
| 失败状态写在哪 | 报告文件头注入 `email_status: OK\|FAILED: <reason>` | 任何脚本 `head -1` 即知；不依赖外部数据库 |
| SMTP 凭证 | 读 `ekey.EMAIL_SMTP` 段 | 沿用 `from ekey import EKEY` 模式 |
| 收件人 | 任务 JSON `recipients: [str, ...]` | 任务级隔离；一个任务多个收件人 |
| 转换工具 | 外部 `pandoc` 调用 | 零 Python 依赖；中文/表格/列表质量高 |
| ekey.py 处理 | 保留在 `.gitignore`，新增 `ekey.template.py` | 真实凭证不出现在 diff 里；其他协作者靠模板复制 |

---

## 3. 组件设计

### 3.1 `ekey.template.py`（新，根目录）

**角色**：模板文件，定义 EMAIL_SMTP 段结构。真实 `ekey.py` 不入库，开发者按模板复制。

```python
# ekey.template.py
# 真实凭证文件 ekey.py 已在 .gitignore，请勿提交。
# 首次使用：cp ekey.template.py ekey.py 并填写真实值。

EKEY = {
    "LLM": {
        # 现有 LLM 段保持原样，不在本文档变更范围
        "<PLACEHOLDER>": "<see existing ekey.py or upstream>",
    },
    "EMAIL_SMTP": {
        "host":     "smtp.gmail.com",   # SMTP 服务器
        "port":     587,                # 587 = STARTTLS；465 = SSL
        "user":     "<your_email>",     # 完整邮箱地址
        "auth_code":"<app_password>",   # Gmail/QQ/163 的应用专用密码（非登录密码）
        "use_tls":  True,               # True = STARTTLS on 587；False = SSL on 465
        "from_name":"EulerAgent Bot",   # 发件人显示名
    },
}
```

> 模板与真实 `ekey.py` 顶层结构兼容（都是 `EKEY = {...}` 字典），`core/ea.py` 用 `from ekey import EKEY` 导入后索引 `EKEY["EMAIL_SMTP"]`，对缺失段做 fail-fast。

### 3.2 `core/ea.py` 新增 `do_send_email`（约 70 行）

接口（`do_<name>(self, args, response)` 约定与现有 9 个工具一致）：

```python
def do_send_email(self, args, response):
    """do_send_email(args={"to":[...], "subject":..., "body":..., "attachments":[...]}, response)
       返回 (yielded_strings, StepOutcome) 中的 yielded 字符串用于前端实时显示。
    """
```

**参数约定**（LLM 调工具时填）：
| 字段 | 必填 | 含义 |
|---|---|---|
| `to` | 是 | 收件人列表，元素是邮箱字符串 |
| `subject` | 是 | 邮件主题 |
| `body` | 是 | 邮件正文（纯文本） |
| `attachments` | 否 | 文件绝对路径列表（当前规格支持 .docx 与 .md） |

**实现骨架**（伪代码，描述边界）：

```
read EKEY["EMAIL_SMTP"]  → 缺失则 raise KeyError("ekey 缺 EMAIL_SMTP 段")
validate args.to / subject / body
for each attachment:
    assert os.path.isfile(path)  → 缺失 raise FileNotFoundError
    assert path.endswith(('.docx','.md','.pdf'))  → 其他类型 raise ValueError

# 报告路径：scheduler 已在 prompt 中注入 rpt（绝对路径），LLM 调用本工具时
# 会把同一个 rpt.docx 放在 attachments 里传进来；这里无需自行解析。
inject_email_status_header(<attachments[0]>, "PENDING")  # 标记正在投递

# 构造邮件
msg = MIMEMultipart()
msg['From']    = formataddr((smtp['from_name'], smtp['user']))
msg['To']      = ', '.join(args.to)
msg['Subject'] = args['subject']
msg.attach(MIMEText(args['body'], 'plain', 'utf-8'))
for path in args['attachments']:
    with open(path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{basename(path)}"')
    msg.attach(part)

# 发送 + 重试
last_err = None
for attempt in 1..3:
    try:
        with smtplib.SMTP(smtp['host'], smtp['port'], timeout=30) as s:
            if smtp['use_tls']:
                s.starttls()
            s.login(smtp['user'], smtp['auth_code'])
            s.sendmail(smtp['user'], args.to, msg.as_string())
        last_err = None
        break
    except (smtplib.SMTPException, OSError) as e:
        last_err = e
        log_email_attempt(attempt, e)
        sleep(3 ** (attempt - 1))   # 1s, 3s, 9s

# 写报告头状态
status = "OK" if last_err is None else f"FAILED: {last_err}"
inject_email_status_header(<attachments[0]>, status)
yield f"邮件已投递：{len(args.to)} 收件人" if not last_err else f"邮件失败：{last_err}"
return StepOutcome(data=..., next_prompt=..., should_exit=False)
```

**关键约束**：
- 不在 `do_send_email` 内部生成 docx（由 LLM 在调用工具前用 `code_run` 跑 `pandoc` 命令）
- 不维护模块级可变状态（`driver`/`_read_dirs` 那种 D1 债务不引入）
- SMTP 连接用 `with` 上下文，确保 socket 关闭

### 3.3 `assets/tools_schema.json` 新增工具声明（约 20 行）

按现有 Anthropic tools API 格式加一段：

```json
{
  "name": "send_email",
  "description": "通过 SMTP 投递邮件，支持 .docx / .md / .pdf 附件。重试 3 次后失败则把状态写入 done/ 报告头。",
  "input_schema": {
    "type": "object",
    "properties": {
      "to":         {"type": "array", "items": {"type": "string"}, "description": "收件人邮箱列表"},
      "subject":    {"type": "string", "description": "邮件主题"},
      "body":       {"type": "string", "description": "纯文本正文"},
      "attachments":{"type": "array", "items": {"type": "string"}, "description": "附件绝对路径列表"}
    },
    "required": ["to", "subject", "body"]
  }
}
```

### 3.4 任务 JSON 新增字段（向后兼容）

`reflect/scheduler.py` 解析任务时遇到未知字段不报错（现状已如此，验证后写 spec）。新字段：

```json
{
  "schedule": "08:00",
  "repeat": "daily",
  "enabled": true,
  "prompt": "...",
  "max_delay_hours": 6,
  "recipients": ["user1@example.com", "user2@example.com"]
}
```

> `recipients` 是给 LLM 在执行任务时看的；scheduler 仅读取它用于 prompt 注入（见 §3.5），不做任何发件逻辑。

### 3.5 任务 prompt 模板注入

`reflect/scheduler.py` 在 `check()` 触发任务时（当前实现见 `scheduler.py:125-129`）拼 prompt。**仅在原 f-string 末尾追加 `recipients` 段落，不动其他逻辑**。具体改动约 4 行：

```python
# scheduler.py L125 附近，原代码：
return (f'[定时任务] {tid}\n'
        f'[报告路径] {rpt}\n\n'
        f'先读 scheduled_task_sop 了解执行流程，然后执行以下任务：\n\n'
        f'{prompt}\n\n'
        f'完成后将执行报告写入 {rpt}。')

# 改为：
recipients = task.get('recipients', [])
mail_tail = ''
if recipients:
    mail_tail = (f'\n\n[自动邮件投递]\n'
                 f'收件人：{", ".join(recipients)}\n'
                 f'完成后请执行：\n'
                 f'  1. 写报告到 {rpt}\n'
                 f'  2. 用 code_run 跑：pandoc {rpt} -o {rpt}.docx\n'
                 f'  3. 调 do_send_email，to={recipients}, subject="..."，'
                 f'body="..."，attachments=[{rpt}.docx]\n'
                 f'  4. 邮件发送状态由 do_send_email 自动写入报告头')
return (f'[定时任务] {tid}\n'
        f'[报告路径] {rpt}\n\n'
        f'先读 scheduled_task_sop 了解执行流程，然后执行以下任务：\n\n'
        f'{prompt}{mail_tail}\n\n'
        f'完成后将执行报告写入 {rpt}。')
```

> `{rpt}` 是 scheduler 计算好的报告绝对路径（`scheduler.py:123`），注入到 prompt 后 LLM 看到的就是"这文件要写哪里"。`do_send_email` 收到的 `attachments` 列表里也用同一个 `{rpt}.docx` 路径——LLM 按 prompt 提示照搬即可。

### 3.6 `memory/daily_report_sop.md` 末尾追加小节（~12 行）

在原 SOP 末尾 "字数控制" 之后，加：

```markdown
## Word 附件输出（可选）
- 用 pandoc 转：`pandoc <md_path> -o <docx_path>`
- 推荐参数：`pandoc <md> -o <docx> --reference-doc=default.docx`（如有企业模板）
- 中文表格/列表：pandoc 默认支持；如乱码确认 locale 是 UTF-8
- docx 大小上限：Gmail 25MB / QQ 50MB / 企业邮箱自定；超过则拆条或改云链接
```

---

## 4. 错误处理

| 失败模式 | 检测 | 处理 |
|---|---|---|
| `ekey.py` 无 `EMAIL_SMTP` 段 | 工具调用时 `KeyError` | 立即 raise，LLM 收到错误后写报告头 `email_status: FAILED: ekey missing EMAIL_SMTP` 并停止 |
| SMTP 登录失败 | `smtplib.SMTPAuthenticationError` | 3 次重试，失败则报告头 `FAILED: auth error`，不抛回 LLM（避免循环） |
| SMTP 连接超时 | `socket.timeout` / `OSError` | 同上重试 |
| 收件人地址非法 | `smtplib.SMTPRecipientsRefused` | 不重试（地址错重试无意义），写 `FAILED: recipients refused: <detail>` |
| `pandoc` 不存在 | `FileNotFoundError` | LLM 端 `code_run` 报错，提示用户装 pandoc；`do_send_email` 不会被调用 |
| 附件文件缺失 | 工具内 `assert` | 立即 `FAILED: attachment missing: <path>`，不重试 |
| 报告文件本身写失败 | LLM 端 `file_write` 错误 | 邮件环节尚未触发，整体任务失败由 agent loop 自然兜底 |

**报告头注入示例**（仅修改第一行，不破坏正文）：

```
<!-- email_status: OK | sent at 2026-06-10T08:32:11, recipients=2, attempts=1 -->
# 2026-06-10 矿产/医药/气候资讯日报
...
```

或失败时：

```
<!-- email_status: FAILED: smtplib.SMTPAuthenticationError(535, ...) | attempts=3, last_at 2026-06-10T08:33:42 -->
```

---

## 5. 测试

### 5.1 单元测试（`tests/`，沿用 pytest）

| 测试名 | 覆盖 |
|---|---|
| `test_do_send_email_success` | mock smtplib，验证成功路径 + 报告头 `OK` 写入 |
| `test_do_send_email_auth_fail` | mock SMTPAuthenticationError，验证 3 次重试 + 报告头 `FAILED: auth` |
| `test_do_send_email_recipients_refused` | mock SMTPRecipientsRefused，验证 1 次即停止（不重试地址错） |
| `test_do_send_email_missing_ekey` | monkeypatch `ekey.EKEY` 移除 EMAIL_SMTP，验证 KeyError 抛出且 LLM 收到 |
| `test_send_email_validates_attachments` | 传不存在路径，验证 FileNotFoundError |
| `test_send_email_rejects_bad_extension` | 传 `.exe`，验证 ValueError |
| `test_scheduler_injects_recipients_into_prompt` | 给定 task.json + recipients，验证 scheduler 拼出的 prompt 末尾包含收件人 |
| `test_pandoc_invocation_command` | 验证 LLM 拼的 `pandoc md -o docx` 命令与 SOP 一致（docstring 字符串匹配） |

### 5.2 集成测试（手动，一次性）

1. 用 `mailhog` / `mailpit` 本地 SMTP 跑一次
2. 准备 3 个收件人，验证 docx 附件 MIME 正确
3. 杀掉 SMTP 服务模拟失败，验证报告头 `FAILED` 出现 + 调度器仍把任务标 done

### 5.3 ekey 清理验证

1. `git log --all --full-history -- ekey.py | head` — 历史里仍可见（这是选项 A 接受的状态）
2. `git ls-files ekey.py` — 仓库**不再跟踪**该文件
3. `git status` — 新克隆者 `cp ekey.template.py ekey.py` 后能用

---

## 6. ekey.py 仓库清理（拆解为独立小 PR）

虽然不在"邮件功能"的核心范围，但用户明确要求处理，按以下步骤：

### 6.1 步骤

1. **检查 `ekey.py` 当前是否在仓库里**：
   ```bash
   git ls-files ekey.py
   ```
2. **如果在**（确认后）：
   ```bash
   git rm --cached ekey.py        # 从仓库索引移除
   echo "ekey.py" >> .gitignore   # 已在 .gitignore 则跳过
   ```
3. **新增 `ekey.template.py`**：内容见 §3.1，提交。
4. **新增 ekey 加载的容错**（小改动）：`core/ea.py`（或新文件 `core/ekey_loader.py`）增加
   ```python
   try:
       from ekey import EKEY
   except ImportError:
       EKEY = {}
   ```
   让缺失 ekey.py 时不崩，只在用到 `EMAIL_SMTP` 段时缺。
5. **更新 `README.md` / `CONTRIBUTING.md`** 一行：首次 clone 后 `cp ekey.template.py ekey.py` 并填值。

### 6.2 验证

- `git ls-files ekey.py` → 空（仓库不跟踪）
- `git log --all -- ekey.py` → 仍可见历史（这是用户接受的范围）
- 协作者 clone 后 `cp ekey.template.py ekey.py` 即用

### 6.3 非目标

- **不**做 `git filter-repo` 历史重写（用户已明确选 A）
- **不**清理其他 LLM 凭证字段（只动 email 段；其他段保留在 `ekey.template.py` 模板里）
- **不**在 `EKEY` 中预留 LLM 占位（LLM 段保持原样，模板里只写明"see existing ekey.py or upstream"）

---

## 7. 变更清单（精确到文件与行数估算）

| 文件 | 操作 | 行数 | 说明 |
|---|---|---|---|
| `ekey.template.py` | 新增 | +30 | 凭证模板（§3.1） |
| `ekey.py` | git rm --cached | 0 | 历史保留（§6） |
| `core/ea.py` | 新增 `do_send_email` | +70 | 工具实现（§3.2） |
| `core/ea.py` | 新增 ekey 容错导入 | +3 | 配合 §6.4 |
| `assets/tools_schema.json` | 新增 `send_email` | +20 | 工具 schema（§3.3） |
| `memory/daily_report_sop.md` | 末尾追加 Word 小节 | +12 | SOP 更新（§3.6） |
| `README.md` / `CONTRIBUTING.md` | 一行 `cp ekey.template.py ekey.py` 提示 | +1/文件 | 安装提示 |
| `tests/test_send_email.py` | 新增 | +90 | 单元测试（§5.1） |
| `reflect/scheduler.py` | prompt 模板追加 recipients 注入 | +4 | 邮件段落（§3.5） |
| **合计** | | **≈ 230 行** | 净行数约 +230，0 删除 |

> 备注：CLAUDE.md 哲学是"净行数 ≤ 0 / 小改动半径"。本 spec 净行 +226 略超。**但**：
> - 100 行是核心功能（`do_send_email` + schema）
> - 90 行是测试（必需，但可选后续 PR）
> - 36 行是配置/文档/模板
> 如需严格"净行 ≤ 0"哲学，可**测试 + 模板**延后到下个 PR。

---

## 8. 实施顺序

按"承重墙不动 + 配置先行"原则：

1. **PR-1：ekey 清理 + 模板**（~36 行）
   - `git rm --cached ekey.py`
   - 新增 `ekey.template.py`
   - `core/ea.py` 加 ekey 容错导入（3 行）
   - README/CONTRIBUTING 一行
   - **可独立 merge**，与邮件功能解耦

2. **PR-2：邮件工具 + 集成**（~190 行）
   - `do_send_email` 实现（70 行）
   - tools_schema.json（20 行）
   - daily_report_sop.md 追加（12 行）
   - scheduler.py prompt 注入（仅 `recipients` 字段读取 + 模板字符串拼装，~10 行；如已存在则零改动）
   - 测试（90 行）
   - **PR-2 依赖 PR-1**

3. **PR-3（可选）：集成测试 + 文档**
   - mailhog 集成测试脚本
   - 一份真实 task.json 示例放 `sche_tasks/example_*.json`（需在 .gitignore 之外示范）

---

## 9. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| LLM 在生成报告后忘了调 `do_send_email` | 中 | 漏发 | 任务 prompt 模板强提示；scheduler 后续可加兜底（不在本 spec） |
| pandoc 不在系统 PATH | 中 | 转 docx 失败 | 工具内 `code_run` 报错后 LLM 提示用户装；do_send_email 收到 .docx 不存在时快速失败 |
| 邮件被收件方判垃圾邮件 | 中 | 实际收不到 | 文档提示用户用 SPF/DKIM/DMARC 配域名；不在本 spec 范围 |
| 大附件超邮箱上限 | 低 | 投递失败 | docx 一般 < 5MB；超 25MB 时 pandoc 加 `--reference-doc` 控制样式精简 |
| ekey 模板字段名拼错 | 低 | 工具不可用 | §3.1 模板与现有 ekey.py 顶层 `EKEY = {...}` 结构一致，索引方式不变 |

---

## 10. 范围之外（明确不做，给后续留口子）

- scheduler.py 状态机扩展（`EMAIL_FAILED` 状态）
- `do_send_email` 同步 vs 异步分离
- HTML 邮件 / 内联图片 / 富文本
- 邮件发送回执 / 已读追踪
- 多 SMTP provider 切换 UI
- 邮件模板版本化
- 历史上 ekey.py 的 `git filter-repo` 抹除
