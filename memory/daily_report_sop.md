# 非传统安全领域动态日报 SOP v3.1

> 触发生成日报时先读此文件。整合 v1.5/v1.6/v1.8 全部执行踩坑经验。
> **v3.1 核心变更**: 适配 v1.8 指令 — 5板块结构 + E.4(14项) + E.5(12项排版) 自检。
>
> **三件套渲染器**: `daily_report_render.py` — MD/DOCX/HTML 全量硬编码(F.1-F.5)
> **交付自检**: `daily_report_validate.py` — E.4 内容14项 + E.5 排版12项 | CLI: `validate.py <report_data.json> [--docx docx路径] [--strict]` (**首参是 json 非.md**, 误传.md→JSONDecodeError)
> **用户指令存档**: `daily_report_instruction.md` — v1.8 原文(9大监控领域/5板块/约束标签体系)
>
> 相关脚本: `fetch_bing_news.py`(爬虫) / `daily_report_build_today.py`(旧版,保留兼容)
> HTML主题: `claude_html_theme.md`

---

## 新流程概览 (v3.1)

```
Phase 1 采集 → Phase 2 整编(输出 report_data.json) → render.py(三件套) → validate.py(自检) → 交付
```

**关键**: LLM 只输出 `report_data.json` (纯数据), 所有格式/颜色/间距由 `render.py` 硬编码渲染。
`report_data.json` 结构见下方 Phase 2 输出规范。

---

## Phase 0 · 硬约束（执行前必读，违反即返工）

### H1. 24小时窗口 — 第一硬约束
- 仅纳入 **D-1日 00:00 ~ D日 18:00（北京时间）** 内发布的条目
- D = 报告日期（如6月4日报 → 仅6月3日~4日）
- **严禁**：为凑条目数而放宽窗口。宁可某板块条目不足，也不纳入超窗条目
- 验收命令：`grep -oP '\d+月\d+日' report.md | sort | uniq -c`，超窗日期出现则 FAIL

### H2. 板块内倒序排列
- 每个板块内条目必须 **按发布日期严格倒序**（D日在前，D-1日在后）
- 同一天内按重要性排序
- 验收：逐板块提取日期序列，检查是否单调非递增

### H3. 条目数约束
| 板块 | 下限 | 上限 | 说明 |
|------|------|------|------|
| S1 涉华要闻 | 3 | 5 | 不足3条时用D-1日补充，但不可超窗 |
| S2 各国动向 | 5 | 10 | 覆盖多领域优先 |
| S3 热点+苗头 | 2 | 5 | 含社会热点与苗头预警 |
| S4 趋势观察 | 2 | 4 | 跨事件关联分析 |
| S5 情报价值 | 3 | 5 | 含情报缺口标注 |

### H4. 内容质量红线
- 每条目必须有：**来源媒体名 + 原文URL**
- 涉华政策类条目需 **≥2源交叉核验**（或标注"单源待确认"）
- 禁止主观评价词（"令人震惊""不幸的是"）
- 中文字数：正文 2000~3500 字

---

## Phase 1 · 数据采集

### 1.1 爬虫策略（已验证）
| 来源 | 结果 | 替代方案 |
|------|------|----------|
| **Google News** | ❌ CAPTCHA封锁（46次全0） | → **Bing News** 无反爬 |
| 联邦站点 .gov (FDA/USGS/IEA/BGS) | ❌ Cloudflare 403 | → Bing聚合绕路 |
| WHO/ECDC/PAHO | ✅ Playwright+Chrome可爬 | 直接爬取 |
| Bing News | ✅ 无反爬，15查询批量 | **首选** |

### 1.2 Bing News 批量抓取
- 使用 `fetch_bing_news.py`，15个查询分3批执行（每批5个）
- Playwright 需显式指定 Chrome 路径：
  ```python
  p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
  ```
- 每个查询URL格式：`https://www.bing.com/news/search?q=...&qft=interval%3d"7"`
- DOM抓取JS：提取 `div.algo` / `li.b_algo` 卡片的 title/url/snippet/source/rel_time

### 1.3 关键查询词清单
```
S1: China rare earth export controls / DeepSeek funding / China AI chips
S2: country-specific security dynamics / nuclear / IAEA
S3: food crisis / water security / energy transition
S4: rare earth supply chain / hydro-hegemony / nuclear proliferation
S5: climate extreme weather / El Nino WMO / cybersecurity CISA
```

### 1.4 采集后处理
- 输出 `{query_key: [{title,url,snippet,source,rel_time},...]}` JSON
- 解析 rel_time 为绝对日期（"2d ago" → D-2）
- **立即标记超窗条目**，后续流程中不再使用


## Phase 2 · 条目整编

### 2.1 精选流程
1. 从采集JSON中按板块关键词分组
2. 按 **时效性(D日优先) → 重要性(涉华/战略级优先) → 多样性(避免同源集中)** 排序
3. 每条目提取：发布日期、来源媒体、原文URL、核心事实(100-200字中文)
4. **剔除超窗条目**（此步骤不可跳过）

### 2.2 条目模板（中文撰写）
```
**{D日/D-1日}，{来源媒体}报道：** {一句话核心事实}。{2-3句展开细节}。{分析性总结句，如有}。
▸ 来源: {原文URL}
```

### 2.3 五板块定义
| 编号 | 板块名 | 条目数 | 内容范围 |
|------|--------|--------|----------|
| S1 | 涉华要闻 | 3-5 | 稀土管制/AI芯片/涉华外交/海外利益 |
| S2 | 各国动向 | 5-10 | 核能/粮食/水资源/气候/地缘博弈 |
| S3 | 热点追踪与苗头预警 | 2-5 | 含3.1社会热点 + 3.2苗头预警 |
| S4 | 趋势观察 | 2-4 | 跨事件关联分析，每条一个趋势线 |
| S5 | 情报价值研判 | 3-5 | 含情报缺口标注 (情报缺口：...) |

### 2.3b report_data.json 输出规范 (v3.1 新增)

LLM 整编完成后输出 `report_data.json`，结构如下：
```json
{
  "date": "2026-06-04",
  "monitoring_window": "2026-06-03 00:00 至 2026-06-04 18:00（北京时间）",
  "s1_items": [
    {"pub_date": "6月4日", "source": "Tech Times", "body": "正文约200字...", "url": "https://..."}
  ],
  "s2_items": [
    {"pub_date": "6月3日", "source": "Reuters", "body": "正文...", "url": "https://..."}
  ],
  "s3_hot": [...],
  "s3_clues": [...],
  "trends": "趋势分析正文(300-500字)",
  "signals": [
    {"label": "信号1：XXX", "text": "1-2句研判(含情报缺口)"}
  ]
}
```

**渲染**: `python daily_report_render.py report_data.json --fmt all --output-dir output/daily_yyyymmdd`  # DOCX用系统py3.10运行
**自检**: `python daily_report_validate.py report_data.json --strict`

### 2.4 趋势观察写法
- 每条以 **加粗趋势标题** 开头（如"关键矿物博弈进入制度竞争阶段。"）
- 后跟 2-3 句跨事件关联分析
- 必须引用本期 ≥2 个条目作为论据

### 2.5 情报价值研判写法
- 每条编号，简洁（1-2句）
- 必须包含 **情报缺口标注**：`(情报缺口：xxx尚不透明/待确认)`
- 优先级：涉华 > 战略级 > 预警级

---

## Phase 3 · MD/DOCX/HTML 三件套渲染 (v3.1 → render.py)

> **格式控制权已转移**: Phase 3/4/5 的所有排版规范现已硬编码在 `daily_report_render.py` 中。
> 以下保留结构说明供参考,实际渲染由 `render.py` 保证一致性。
> 命令: `python daily_report_render.py report_data.json --fmt all --output-dir output/daily_yyyymmdd`
> **⚠️输出目录(硬约束)**: 三件套+report_data.json 必须输出到 `./temp/output/daily_yyyymmdd/`,不可放temp根目录。DOCX用系统py3.10渲染。

### 3.1 MD 文件结构 (参考)
```markdown
## 非传统安全领域动态日报（{D日}）

> 监测窗口：{D-1日} 00:00 至 {D日} 18:00（北京时间）

## 一、非传统安全领域涉华要闻
{条目们，D日在前，D-1日在后}

## 二、各国非传统安全动向
{条目们，倒序}

## 三、热点追踪与苗头预警
### 3.1 社会热点
### 3.2 苗头预警

## 四、趋势观察
{趋势条目}

## 五、情报价值研判
{研判条目}
```

### 3.2 文件命名
`非传统安全领域动态日报_YYYYMMDD.md`



## Phase 4 · DOCX 排版规范 (v3.1 → 由 render.py 保证)
> 所有样式参数已内嵌于 `daily_report_render.py` 的 `render_docx()` 函数。
> 以下保留参考实现,修改样式时直接改 render.py 中对应常量。

### 4.1 色板
| Token | 值 | 用途 |
|-------|-----|------|
| 主色 PRIMARY | `#1A1A1A` | 正文/标题 |
| 次色 SECONDARY | `#C9B99A` | 英文副标题/分隔线/装饰 |
| 强调色 ACCENT | `#D97757` | 板块标题/标识行/序号/来源符号 |
| 灰色 GRAY | `#666666` | 来源标签/页脚 |
| 底纹 | `#FBEEE6` | 板块标题底纹 |

### 4.2 F.2 文档顶部样式（强制，逐层精确）
文档顶部由 **四层** 构成，从上至下依次排列，**居中对齐**：

| 层级 | 内容 | 字号 | 颜色 | 字重 | 特殊 |
|------|------|------|------|------|------|
| 第一层·标识行 | `■ 国际非传统安全领域 · 每日情报整编 ■` | 9pt | ACCENT #D97757 | 加粗 | 行高14pt |
| 第二层·主标题 | `非传统安全领域动态日报` | 32pt | PRIMARY #1A1A1A | 加粗 | 字体:微软雅黑, 行高38pt, 上空6pt |
| 第三层·英文副标题 | `INTERNATIONAL NON-TRADITIONAL SECURITY BRIEFING` | 9pt | SECONDARY #C9B99A | 常规 | 字距加宽60 |
| 第四层·日期行 | `YYYY年M月D日（星期X）` | 13pt | PRIMARY #1A1A1A | 加粗 | 上空8pt |

**顶部区域整体要求**：
- 四层之间 **不插入分隔线**，依靠字号与颜色层次自然区分
- 顶部区域与正文第一个板块之间加一条 **次色细横线(1pt)** 作为分隔
- 分隔线实现：`<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="C9B99A"/></w:pBdr>`

### 4.3 python-docx 实现参考（顶部四层）
```python
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from docx.enum.text import WD_ALIGN_PARAGRAPH

C_MAIN = RGBColor(0x1A, 0x1A, 0x1A)
C_ACCENT = RGBColor(0xD9, 0x77, 0x57)
C_SUB = RGBColor(0xC9, 0xB9, 0x9A)
C_GRAY = RGBColor(0x66, 0x66, 0x66)

# Layer 1: 标识行
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = Pt(14)
r = p.add_run('■ 国际非传统安全领域 · 每日情报整编 ■')
r.font.size = Pt(9); r.font.color.rgb = C_ACCENT; r.bold = True
r.font.name = 'Inter'
r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# Layer 2: 主标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = Pt(38)
r = p.add_run('非传统安全领域动态日报')
r.font.size = Pt(32); r.font.color.rgb = C_MAIN; r.bold = True
r.font.name = 'Inter'
r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# Layer 3: 英文副标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = Pt(14)
r = p.add_run('INTERNATIONAL NON-TRADITIONAL SECURITY BRIEFING')
r.font.size = Pt(9); r.font.color.rgb = C_SUB; r.bold = False
r.font.name = 'Inter'
r._element.get_or_add_rPr().append(
    parse_xml('<w:spacing {} w:val="60"/>'.format(nsdecls('w'))))

# Layer 4: 日期行
wk = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(8)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = Pt(20)
r = p.add_run(f'2026年6月4日（{wk[date(2026,6,4).weekday()]}）')
r.font.size = Pt(13); r.font.color.rgb = C_MAIN; r.bold = True
r.font.name = 'Inter'
r._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# Separator line
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(12)
p._element.get_or_add_pPr().append(parse_xml(
    '<w:pBdr {}><w:bottom w:val="single" w:sz="4" w:space="1" w:color="C9B99A"/></w:pBdr>'.format(nsdecls('w'))))
```

### 4.4 板块标题样式
```python
# 板块标题: 左侧橙色粗线 + 淡橙底纹
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16)
p.paragraph_format.space_after = Pt(8)
p.paragraph_format.left_indent = Cm(0.5)
pPr = p._element.get_or_add_pPr()
pPr.append(parse_xml('<w:shd {} w:fill="FBEEE6" w:val="clear"/>'.format(nsdecls('w'))))
pPr.append(parse_xml(
    '<w:pBdr {}><w:left w:val="single" w:sz="32" w:space="8" w:color="D97757"/></w:pBdr>'.format(nsdecls('w'))))
r = p.add_run('一、非传统安全领域涉华要闻')
r.font.size = Pt(13); r.font.color.rgb = C_ACCENT; r.bold = True
```

### 4.5 条目正文样式
- 前缀加粗: `6月4日，Tech Times报道：` → 10.5pt PRIMARY 加粗
- 正文常规: 10.5pt PRIMARY
- 来源行: `▸ `(ACCENT) + `来源: `(GRAY) + URL(SUB)，9pt

### 4.6 页面设置
```python
section = doc.sections[0]
section.page_width = Cm(21)    # A4
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2)
```

### 4.7 页脚
```python
fp = section.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run('非传统安全领域动态日报 · {DATE} · 内部资料')
r.font.size = Pt(7); r.font.color.rgb = C_GRAY
```


## Phase 5 · HTML 生成 (v3.1 → 由 render.py 保证)
> HTML渲染已内嵌于 `daily_report_render.py` 的 `render_html()` 函数。

### 5.1 Claude HTML 主题
- 按 `claude_html_theme.md` 规范
- Primary `#1A1A1A` / Secondary `#C9B99A` / Tertiary `#D97757` / Neutral `#FAF9F7`
- 卡片用 `news-item` 列表 + 橙色圆形序号
- 字体: 正文系统无衬线, 代码/标签用 Space Mono

### 5.2 HTML 结构
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8">
<style>/* Claude theme CSS */</style>
</head>
<body>
  <header>顶部四层 banner (同DOCX视觉一致)</header>
  <main>
    <section id="s1">板块一</section>
    <section id="s2">板块二</section>
    ...
  </main>
  <footer>内部资料</footer>
</body>
</html>
```

---

## Phase 6 · 交付前自检 (v3.1 → validate.py)

> **自动化自检**: `python daily_report_validate.py report_data.json --docx output.docx --strict`
> **E.4 内容自检 (14项)**: URL覆盖/字段完整/条目数/涉外因素/准入条件/时效窗口/倒序/缩写括注/命名等
> **E.5 排版自检 (12项, 需--docx)**: 顶部四层/板块标题底纹边框/来源行三色/页边距/页脚等

### 6.1 E.4 内容自检 (14项, 已编码于 validate.py)
> 以下为参考清单, 实际执行由 `daily_report_validate.py` 自动完成。

| # | 检查项 | PASS条件 |
|---|--------|----------|
| E.4-01 | URL覆盖 | 每条目有来源URL |
| E.4-02 | 字段完整性 | 必填字段无缺失 |
| E.4-03 | 板块一条数+涉外因素 | 3-5条, 含涉外因素标签 |
| E.4-04 | 板块二条数 | ≤10条 |
| E.4-05 | 3.1准入条件 | 标注准入条件标签 |
| E.4-06 | 中方主动发起 | 7日内+明文提及 |
| E.4-07 | 时效窗口 | 7天窗口(D-6~D日) |
| E.4-08 | 段首加粗格式 | 日期+来源标加粗 |
| E.4-09 | 英文缩写括注 | 首次出现已括注中文全称 |
| E.4-10 | 来源行间距 | (由render保证) |
| E.4-11 | 倒序排列 | 各板块内按日期倒序 |
| E.4-12 | 板块四五无新材/无重叠 | 无新URL/无重叠文本 |
| E.4-13 | 加粗仅三处 | (由render保证) |
| E.4-14 | 文件命名 | 含YYYYMMDD |

### 6.2 E.5 排版自检 (12项, 需 --docx, 已编码于 validate.py)

| # | 检查项 | PASS条件 |
|---|--------|----------|
| E5-01 | 顶部标识行 | 含"每日情报整编" |
| E5-02 | 主标题 | "非传统安全领域动态日报" |
| E5-03 | 英文副标题 | 全大写, 含"NON-TRADITIONAL SECURITY" |
| E5-04 | 日期行 | 含YYYY年M月D日 |
| E5-05 | 分隔线 | 顶部与正文间有次色1pt底线 |
| E5-06 | 板块标题 | 底纹+左边框 |
| E5-07 | 段首来源标 | 加粗 |
| E5-08 | 条目正文 | 样式合规 |
| E5-09 | 来源行三色 | ▸(橙)+来源:(灰)+URL(次色) |
| E5-10 | 来源行间距 | 与正文间距合规 |
| E5-11 | 页边距 | 2.5cm |
| E5-12 | 页脚 | 含分隔线+页码 |

---

## Phase 7 · 产物归档

### 7.1 三件套
归档到 `./temp/output/daily_yyyymmdd/`（渲染时 `--output-dir` 已自动归位，此处仅说明最终路径）：
```
非传统安全领域动态日报_YYYYMMDD.md
非传统安全领域动态日报_YYYYMMDD.docx
非传统安全领域动态日报_YYYYMMDD.html
```

---

## Appendix A · 历史踩坑记录

| # | 坑 | 表现 | 解决 | 首现版本 |
|---|-----|------|------|----------|
| 1 | Google News CAPTCHA | 46次请求全0结果 | 改用Bing News | v1.0 |
| 2 | .gov 站点 Cloudflare 403 | FDA/USGS/IEA等全403 | Bing聚合绕路 | v1.0 |
| 3 | DOCX顶部样式不合规 | 缺少四层精确spec | Phase 4.2 逐层参数化 | v1.6 |
| 4 | 24h窗口违规 | 为凑条目数纳入D-2及更早 | Phase 0 H1前置为第一硬约束 | v1.6 |
| 5 | 板块内未倒序 | 6月4日与6月3日混排 | Phase 0 H2强制+自检脚本 | v1.6 |
| 6 | Playwright chromium启动失败 | 网络问题拉不下来 | 显式指定本地Chrome路径 | v1.5 |
| 7 | file_write大内容截断 | ≥10KB易流截断 | 改用 code_run + Python分块追加 | SOP编写 |
| 8 | 9板块→5板块结构变更 | v1.5用9板块,v1.6改5板块 | 以v1.6用户指令为准 | v1.6 |
| 9 | **E.4-08段首动词硬约束** | body必须以 `X月X日` + 1-40字 + (报道/表示/声明/发布) + 冒号 起首。写"推演监测/综合报道"等生造词全12条FAIL | 全局替换为"报道"或四选一, 加粗前缀由render自动加 | v3.1 |
| 10 | **E.4-09缩写括注** | 2-6字母大写缩写(IRA/WHO/LNG/FT/GDACS/SCMP等)首次出现必须括中文全称(美国《通胀削减法》(IRA)) | 首次出现用"中文全称(abbr)"形式, render时缩进加粗 | v3.1 |
| 11 | **schema版本分歧** | SOP说扁平{s1_items/...}, 旧报告用sections[].items[]; validator/render只认**扁平版** | LLM输出以validator认的schema为准, 遇分歧先读validator源码确认 | v3.1 |
| 12 | **B路手工构造(数据稀薄时)** | 周日/节假日fetch.py+RSS仍无满足H3条数时, 手工构造极简report_data.json(3+5+2+2+2+3) + 标"周日数据稀薄"免责声明 + signals里加"(情报缺口:6/X数据回归后核实)" | 优先级: A路(自动)→ B路(手工)→ C路(报告失败) | v3.1 |

## Appendix C · report_data.json 字段速查 (v3.1 扁平schema)

```python
{
  "date": "2026-06-07",                          # 报告日期
  "window": "2026-06-06 00:00 至 2026-06-07 18:00 (北京时间)",  # 监测窗口
  "s1_items":   [{"pub_date": "X月X日", "source": "...", "body": "X月X日，源报道：...", "url": "..."}],  # S1 涉华要闻, 3-5条
  "s2_items":   [同S1结构],                     # S2 各国动向, 5-10条
  "s3_hot":     [同S1结构],                     # S3.1 社会热点, 与clues合计2-5
  "s3_clues":   [同S1结构],                     # S3.2 苗头性线索
  "trends": {                                   # S4 趋势观察, dict结构(非list)
    "core_situation": "...",                    # 核心态势
    "actor_dynamics": "...",                    # 行为体动态
    "china_impact": "..."                       # 对华影响
  },
  "signals": [{"label": "信号1", "text": "..."}]  # S5 重点信号, 3-5条, label无冒号
}
```

**红线复述**:
- body段首动词: 报道/表示/声明/发布 (四选一)
- 英文缩写首次出现: 中文全称(abbr)
- 倒序: 每板块D日在前,D-1日在后
- 文件名: `非传统安全领域动态日报_YYYYMMDD.{md,docx,html}`

## Appendix B · 监控网站清单

### 核心源
- Bing News (首选聚合)
- Reuters / AP / Bloomberg
- WHO / ECDC / CIDRAP (公共卫生)
- IAEA官网 (核安全)
- Carbon Brief / WMO (气候)
- FAO / WFP (粮食安全)

### 地缘与战略
- War on the Rocks / Foreign Affairs / Geopolitical Monitor
- Washington Examiner / The Hill
- Saudi Gazette / Gulf Today (中东)
- Daily Times / Euromaidan Press (区域)

### 技术与产业
- Tech Times / Seeking Alpha
- American Bazaar

### 数据源
- IEA https://www.iea.org/
- 全球能源监测 https://globalenergymonitor.org/
- Our World in Data https://ourworldindata.org/
