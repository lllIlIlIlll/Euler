# DrissionPage 使用 SOP (2026-06-01 立)

## 1. 选型决策
- **首选 `SessionPage`**（同包,基于 requests,无浏览器依赖,稳定)
- **仅在需要 JS 渲染时**才用 `ChromiumPage`
- 决策顺序:SessionPage → 失败/反爬严 → ChromiumPage 渲染层 → 仍失败 → 标记反爬跳过

## 2. 安装与版本
```
pip install DrissionPage      # 截至 2026-06 已验证 4.1.1.4
python -c "from DrissionPage import __version__; print(__version__)"
```

## 3. SessionPage API 关键陷阱(踩过)
| 误用 | 正确 |
|---|---|
| `r = page.get(url); r.status_code` | `ok = page.get(url)`  ← 返回 **bool(url可用性)**,不是 Response |
| `r.text` / `r.html` | `page.html`  ← HTML 在 page 对象本身 |
| `r.headers['content-type']` | `page.response.headers` (drission 4.x) |
| `print(r)` 期望看到 200 | 用 `page.response.status_code` (有页面) 或靠 `page.get` 的 bool |
| 状态码 = None | 调用 `get` 后 `page.response.status_code` 才有效 |

## 4. 公共请求配置(放循环外一次设) — **必须 p.set.* 链式 API (4.x)**
```python
p = SessionPage()
p.set.timeout(20)              # 不是 p.timeout=20 (无attr setter)
p.set.retry_times(1)
p.set.retry_interval(2)
p.set.user_agent("Mozilla/5.0 ... Chrome/124 Safari/537.36")  # 必设
# 探测: [a for a in dir(p.set) if not a.startswith('_')]
```

## 5. 批量抓取模板
```python
for url in URLS:
    try:
        if not p.get(url):       # bool 判定
            errors.append({...})
            continue
        html = p.html
        title = p.title
        # 元数据在首页里:meta[property=og:title], time, h1, h2...
        # 列表页用 p.eles('css selector') 拿结构化时间戳
    except Exception as e:
        errors.append({'url': url, 'error': str(e)[:120]})
```

## 6. 元数据正则常见坑
- `re.findall(r'<h1[^>]*>(.*?)</h1>', html)` 拿到的 **是已剥离标签的纯文本**
  - **不要**再对结果 `re.search(r'<h1...>')` → 返回 None → `.group()` 崩溃
  - 直接对 findall 结果 `.strip()` 即可
- 日期格式多:`2026-05-31` / `May 31, 2026` / `2026/05/31` / `31 May 2026` / `2026-05-31T08:00:00+08:00` → 用多 pattern 兜底:
  ```python
  PATS = [r'20\d{2}-\d{2}-\d{2}', r'[A-Z][a-z]{2,8} \d{1,2},? 20\d{2}', r'20\d{2}/\d{2}/\d{2}']
  ```

## 7. 反爬失败 5 家(V4 实测,2026-06-01)
- `industry.gov.au` (Cloudflare严格)
- `fao.org` / `fews.net` / `ipcinfo.org` / `pris.iaea.org`
- 建议 V5 周期:换 `ChromiumPage` + 配置 `cookies` + 调低 headless 探测风险

## 8. 实用产物
- 抓取脚本:`temp/fetch_sp2.py`(V4 实跑,18/23 成功)
- 原始 JSON:`temp/dp_v3.json`
