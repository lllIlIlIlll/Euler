# 本地PC能力盘点 v1.0 (2026-06-05)

> 探测时间: 2026-06-05 00:10
> 探测者: GenericAgent R03
> 主机: Apple M4, 32GB RAM, 195GB可用, macOS 26.6

## 标签说明
- 🟢 **实测可用** — 探测已通过
- 🟡 **未测** — 探测条件不满足但有潜在能力
- 🔴 **不可用** — 探测确认缺失
- 🟠 **已落地复用案例** — 已在pipeline中实际使用或即将集成

---

## 1. OCR / Vision 能力

| 方案 | 标签 | 路径/版本 | 备注 |
|---|---|---|---|
| Swift Vision (VNRecognizeTextRequest) | 🟢实测可用 | /usr/bin/swift | macOS原生,中英文双语,精确模式,支持横竖排 |
| Tesseract | 🟢实测可用 | /opt/homebrew/bin/tesseract 5.5.2 | 开源OCR,支持100+语言,CLI可批量处理 |
| Apple Vision via Shortcuts | 🟡未测 | /usr/bin/shortcuts (16个指令) | 含DeepSeek/抠图等指令,可做轻量OCR |
| pytesseract | 🔴不可用 | — | Python wrapper,需pip install |
| pyobjc | 🔴不可用 | — | Python<->Cocoa桥,需pip install |
| easyocr / paddleocr | 🔴不可用 | — | 深度学习OCR,包体大需联网下载模型 |
| OpenCV cv2 | 🔴不可用 | — | 图像处理,需pip install |

### 🟠 已落地复用案例
1. **R02 Pipeline Monitor (img fallback)**: fetch_bing_news抓取失败时,可对失败页面截图后用Swift Vision提取关键文字,作为schema校验的fallback
2. **历史报告截图OCR**: 用户提供的报告图片/PDF扫描件,可用Tesseract批量提取文字后喂给validate.py做E.4检查
3. **Bing News卡片快照**: Playwright抓取失败时,截图后Swift Vision回退解析(可识别b'1\xa0...'类UTF-8边界问题)

---

## 2. LLM 后端

| 方案 | 标签 | 备注 |
|---|---|---|
| Ollama | 🔴不可用 | 不在PATH,需brew install ollama + ollama pull model |
| LM Studio | 🔴不可用 | 不在PATH,需手动下载app |
| llama.cpp / llamafile | 🔴不可用 | 不在PATH,需brew install或下载binary |
| Anthropic SDK (pip) | 🔴不可用 | 不在Python site-packages |
| OpenAI SDK (pip) | 🔴不可用 | 不在Python site-packages |
| 本地core/agentmain.py | 🟢实测可用 | Claude API经核心代理调用,本仓库内置 |

### 🟠 已落地复用案例
1. **核心调度**: 所有Agent/Subagent运行均通过`python3 ../core/agentmain.py --task ... --nobg`调度
2. **批量文本处理**: TODO 3双源核验的"语义相似度判断"将调用subagent(LLM后端不可本地跑,只能远程)

### 建议
- 本机无本地LLM,所有LLM调用都需走Claude API,需注意token成本
- 如未来需要本地LLM,优先安装Ollama(`brew install ollama`)+ 7B/13B模型

---

## 3. 可直连免费数据源 (排除SOP Appendix B已列)

> 探测方法: 直接urllib.request.Request,8秒超时,UA='capability-inventory/1.0'
> 已排除: Bing News/Reuters/AP/Bloomberg/WHO/IAEA/Carbon Brief/WMO/FAO/WFP/War on the Rocks/Foreign Affairs/Geopolitical Monitor/Washington Examiner/The Hill/Saudi Gazette/Gulf Today/Daily Times/Euromaidan Press/Tech Times/Seeking Alpha/American Bazaar/IEA/Global Energy Monitor/Our World in Data

### 学术/科研 (🟢 全可用)

| API | URL | 格式 | 用途 | 限速 |
|---|---|---|---|---|
| **arXiv** | http://export.arxiv.org/api/query | XML/Atom | AI/物理/数学预印本 | 无明确限制,礼貌使用 |
| **arXiv RSS** | http://export.arxiv.org/rss/cs.AI | XML/RSS | 订阅式获取新论文 | 同上 |
| **PubMed E-utilities** | https://eutils.ncbi.nlm.nih.gov/entrez/eutils/ | XML | 生物医学文献 | 3 req/s (无key) |
| **Crossref** | https://api.crossref.org/works | JSON | DOI元数据反查 | 礼貌使用,有polite pool |
| **OpenAlex** | https://api.openalex.org/works | JSON | 学术作品全索引(2.4亿+) | 100k req/day (免费) |

### 经济/统计 (🟢 2/3可用)

| API | URL | 格式 | 用途 | 限速 |
|---|---|---|---|---|
| **WorldBank** | https://api.worldbank.org/v2/ | JSON | 200+国家经济指标 | 无明确限制 |
| Worldometer | https://www.worldometers.info/ | HTML(需解析) | 实时人口/COVID数据 | 无API,需爬 |
| UNData | https://data.un.org/ | HTTP 500 ❌ | UN成员国数据 | 暂时不可用 |

### 科技/开源 (🟢 全可用)

| API | URL | 格式 | 用途 | 限速 |
|---|---|---|---|---|
| **GitHub REST** | https://api.github.com/ | JSON | 仓库/issue/release | 60 req/h(未认证)/5000(认证) |
| **HackerNews** | https://hacker-news.firebaseio.com/v0/ | JSON | 科技新闻热度 | 无明确限制 |
| **HackerNews-Algolia** | https://hn.algolia.com/api/ | JSON | 全文搜索+元数据 | 无明确限制 |

### 知识图谱 (🟢 1/2可用)

| API | URL | 格式 | 用途 |
|---|---|---|---|
| **Wikidata** | https://www.wikidata.org/w/api.php | JSON | 结构化事实反查(适合交叉核验) |
| IRENA (国际可再生能源) | https://www.irena.org/Data | HTTP 403 ❌ | 需绕过Cloudflare |

### 生物/环境 (🟢 1/3可用)

| API | URL | 格式 | 用途 |
|---|---|---|---|
| **GBIF** | https://api.gbif.org/v1/ | JSON | 全球生物多样性数据(物种/出现记录) |
| NASA APOD | https://api.nasa.gov/ | 超时 ❌ | 每日天文图,网络不稳定 |
| WHO COVID | https://covid19.who.int/ | SSL超时 ❌ | SSL握手超时,可能需代理 |

### 🟠 已落地复用案例
1. **TODO 3 双源交叉核验工具** (解H4硬约束):
   - arXiv/OpenAlex/Crossref: 核验Bing News抓到的"某机构发布报告"是否有学术原始出处
   - Wikidata: 核验公司/机构/人名等结构化事实
   - GitHub: 核验"开源项目事件"
2. **TODO 5 非传统安全数据源调研**:
   - PubMed: 生物安全/疫苗/流行病学
   - WorldBank: 经济背景数据(可与日报"地缘经济"板块交叉)
   - GBIF: 疫病源头/生物入侵
   - HackerNews/Algolia: 科技板块实时热点
3. **历史报告归档**: OpenAlex/Crossref反查DOI,补充报告中"原始研究"链接

---

## 4. 浏览器/Web自动化

| 工具 | 标签 | 备注 |
|---|---|---|
| Safari | 🟢实测可用 | /Applications/Safari.app,本机默认浏览器 |
| Chromium/Chrome | 🔴不可用 | 不在PATH(SOP v1.5曾用本地Chrome,可能需重新指定) |
| Firefox | 🔴不可用 | 不在PATH |
| Playwright | 🟢实测可用 | pip已装,fetch_bing_news.py用之 |
| DrissionPage | 🔴不可用 | pip未装(per SOP, WebSocket 404 issue,已改SessionPage) |
| requests | 🟢实测可用 | 2.34.2 |
| lxml | 🟢实测可用 | 6.1.1 |
| PIL | 🟢实测可用 | 12.2.0 |
| beautifulsoup4 | 🔴不可用 | pip未装(可用lxml替代) |

### 🟠 已落地复用案例
1. **fetch_bing_news.py**: Playwright + Chromium抓取,本仓库核心抓取手段
2. **dp_fetcher.py (旧)**: DrissionPage批量抓取(per SOP已降级)
3. **Pipeline Monitor**: requests+urllib检测fetch结果,无需浏览器

---

## 5. 调度/系统

| 工具 | 标签 | 备注 |
|---|---|---|
| crontab | 🟢实测可用 | /usr/bin/crontab,适合每日8点定时跑日报 |
| launchctl | 🟢实测可用 | /bin/launchctl,适合长期后台(launchd plist) |
| at | 🟢实测可用 | /usr/bin/at,适合一次性定时任务 |
| git | 🟢实测可用 | 2.50.1,GenericAgent核心代码管理 |

### 🟠 已落地复用案例
1. **R02 Pipeline Monitor集成**: `0 8 * * * cd /path && python pipeline_monitor.py` (待接入)
2. **subagent后台调度**: `cd {cwd} && python3 ../core/agentmain.py --task "..." --nobg &`

---

## 6. 已知缺陷与未来采购建议

| 类别 | 当前缺失 | 优先级 | 建议 |
|---|---|---|---|
| 本地LLM | Ollama/LM Studio | 中 | 装Ollama + qwen2.5:7b,跑语义聚类节省API成本 |
| 浏览器 | Chrome/Chromium | 低 | Playwright已能跑(用本地浏览器) |
| 图像处理 | OpenCV/Pillow高级功能 | 低 | PIL已够用 |
| 学术核验 | 付费数据库(Web of Science) | 低 | 暂用OpenAlex+Crossref覆盖大部分 |
| 时事核验 | 主流新闻API(Reuters/Bloomberg付费) | 中 | 暂用Bing News聚合 |
| WHO/NASA | 直接API访问 | 中 | WHO: 需curl测试不同endpoint / NASA: 注册免费API key |

---

## 7. 维护说明
- 本清单每季度复核一次(2026-09-05)
- 新增能力需写明"落地复用案例"才视为正式登记
- TODO 5/6/7将基于本清单的"可直连源"部分展开
