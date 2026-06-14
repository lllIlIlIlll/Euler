# Mac原生自动化能力SOP (Apple M4 / macOS 26.6)
> 本机实测 2026-06-05. 所有命令已在终端验证.

## 硬件概要
- **芯片**: Apple M4 (ARM64E)
- **macOS**: 26.6 (25G5028f), Darwin 25.6.0
- **Python**: 3.14 (managed, externally-managed)
- **brew**: 已装, leaves见下方

## 一、文件搜索: mdfind (Spotlight引擎)
> **替代es**: 本机未装es, mdfind是唯一系统级搜索.

```bash
# 按文件名搜
mdfind -name "TODO.txt" -onlyin /Users/x404

# 按类型+日期
mdfind "kind:pdf date:today"

# 元数据查询 (极快 ~26ms)
mdfind "kMDItemDisplayName == '*.md'" -onlyin /Users/x404/agents
# → 2641个.md文件

# 查看文件元数据
mdls /path/to/file
```

**性能**: 简单查询 26ms, 全盘扫描 364ms(首次,含locale加载).

## 二、进程与应用控制: osascript (AppleScript)
> 可探测和控制17个GUI应用.

### 可控应用列表
| App | 路径 | 潜在自动化 |
|-----|------|-----------|
| Finder | System | 文件操作, 窗口管理 |
| Lark (飞书) | /Applications/ | 企业协作 |
| 企业微信 | /Applications/ | 消息通知 |
| WeChat (微信) | /Applications/ | 消息 |
| Typora | /Applications/ | Markdown编辑 |
| Obsidian | /Applications/ | 知识库 |
| TickTick | /Applications/ | 任务管理 |
| Claude | /Applications/ | ⚠️ AppleScript受限(-1728) |
| Comet | /Applications/ | 当前前台App |
| Kimi | /Applications/ | AI助手 |
| Ghostty | /Applications/ | 终端 |
| ForkLift | /Applications/ | 文件管理 |

### 常用命令
```bash
# 获取前台应用
osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'

# 列出所有GUI进程
osascript -e 'tell application "System Events" to get name of every process whose background only is false'

# 获取窗口标题 (部分App支持)
osascript -e 'tell application "Typora" to get name of front window'
```

⚠️ **限制**: Claude.app AppleScript返回 -1728 (不支持window name查询).

## 三、快捷指令: shortcuts
> 本机已配置自定义快捷指令.

```bash
# 列出所有快捷指令
shortcuts list

# 运行快捷指令
shortcuts run "DeepSeek"
shortcuts run "帮我记个东西"
```

**已发现指令**: DeepSeek, 合成模糊背景, 一键抠图保存, 抠图换背景, 3D图片, 九宫格切图, 快速存储链接, 隔空投送屏幕快照.

## 四、图像处理: sips
```bash
# 调整尺寸
sips --resampleWidth 800 image.png

# 格式转换
sips -s format jpeg image.png --out image.jpg

# 获取信息
sips -g all image.png
```

## 五、文档转换: textutil
```bash
# txt → html
textutil -convert html input.txt -output output.html

# docx → txt
textutil -convert txt input.docx -output output.txt

# 支持格式: txt, html, rtf, rtfd, doc, docx, wordml, odt, webarchive
```

## 六、系统管理

### caffeinate (防休眠)
```bash
# 阻止休眠(直到Ctrl+C)
caffeinate -i

# 阻止休眠1小时
caffeinate -t 3600 &

# 进程运行期间阻止休眠
caffeinate -w $PID
```

### pmset (电源管理)
```bash
pmset -g          # 当前设置
pmset -g log      # 电源事件日志
```
**当前**: sleep=1 (被useractivityd/powerd/Comet/bluetoothd/sharingd阻止).

### screencapture
```bash
screencapture -x /tmp/screenshot.png        # 静默截屏
screencapture -R x,y,w,h /tmp/capture.png   # 区域截屏
screencapture -l $WINDOWID /tmp/win.png      # 窗口截屏
```

### say (语音合成)
```bash
say "Hello World"
say -v "Albert" "Task completed"
say -o output.aiff "Recording"  # 输出音频文件
```

### defaults (偏好设置读写)
```bash
defaults read com.apple.dock          # 读Dock设置
defaults write com.apple.dock autohide -bool true  # 修改设置
```

### plutil (Property List)
```bash
plutil -p /path/to/plist              # 读plist
plutil -convert json -o - file.plist  # plist→json
```

### system_profiler
```bash
system_profiler SPSoftwareDataType     # 系统信息
system_profiler SPHardwareDataType     # 硬件信息
system_profiler SPNetworkDataType      # 网络信息
```

### launchctl
```bash
launchctl list                         # 列出服务
launchctl load ~/Library/LaunchAgents/com.x.plist  # 加载
launchctl unload ...                   # 卸载
```

## 七、已装brew工具 (高价值)
| 工具 | 用途 |
|------|------|
| fd | 快速文件查找 (比find快) |
| ripgrep (rg) | 内容搜索 (比grep快) |
| fzf | 模糊搜索 |
| jq | JSON处理 |
| nvim | 编辑器 |
| pandoc | 文档转换 (比textutil更强大) |
| poppler | PDF工具集 (pdftotext等) |
| imagemagick | 图像处理 (比sips更强大) |
| ffmpeg | 音视频处理 |
| gh | GitHub CLI |
| lazygit | Git TUI |
| git-delta | Diff美化 |
| tmux | 终端复用 |
| starship | Prompt美化 |
| go/node | 开发运行时 |
| postgresql@17 | 数据库 |

## 八、组合技 (实际场景)

### 场景1: 查找+处理文档
```bash
mdfind "kind:pdf date:today" | xargs -I{} pdftotext {} - | head -50
```

### 场景2: 防休眠执行长任务
```bash
caffeinate -i && python3 long_task.py
```

### 场景3: 快速截图+OCR
```bash
screencapture -x /tmp/ocr_input.png && sips -s format tiff /tmp/ocr_input.png --out /tmp/ocr.tiff
```

### 场景4: 批量转换格式
```bash
fd -e docx -x textutil -convert txt {} -output {.}.txt
```
