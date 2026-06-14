# Claude HTML Theme — Design System Reference

## 触发规则
用户要求输出报告、文档、设计、方案时 → 自动在 `docs/` 目录生成 Claude 风格 HTML。

## 颜色体系
| Token | 值 | 用途 |
|---|---|---|
| Primary | `#1A1A1A` | 正文/标题，近黑但更柔和 |
| Secondary | `#C9B99A` | 边框/分割线/装饰 |
| Tertiary | `#D97757` | Claude Orange，**仅**用于可交互元素(CTA/链接/聚焦环) |
| Neutral | `#FAF9F7` | 页面底色，暖奶油色 |
| Surface | `#FFFFFF` | 卡片/消息气泡底色 |
| Border | `#E0DDD8` | 默认边框 |
| On-tertiary | `#FFFFFF` | 主按钮文字色 |
| Tertiary-container | `#E8896A` | 主按钮 hover |
| User-bubble | `#F0EDE8` | 用户消息气泡 |

**红线**：Tertiary 禁用于装饰；禁纯黑 `#000` / 纯白 `#FFF` 作背景；禁用超过一个强调色。

## 字体
- **Inter**: 所有 UI 文字 (标题/正文/标签)
- **Space Mono**: 仅 `label-caps` — 时间戳/元数据/代码注释/系统标签

| Token | Family | Size | Weight | Line-height | 特殊 |
|---|---|---|---|---|---|
| h1 | Inter | 2.5rem | 600 | 1.2 | letter-spacing: -0.02em |
| h2 | Inter | 1.75rem | 600 | 1.3 | — |
| body-md | Inter | 1rem | 400 | 1.6 | — |
| body-sm | Inter | 0.875rem | 400 | 1.5 | — |
| label-caps | Space Mono | 0.75rem | 400 | — | letter-spacing: 0.05em |

## 圆角
| Token | 值 | 场景 |
|---|---|---|
| sm | 6px | Button, tag, badge |
| md | 12px | Input, card, modal |
| lg | 20px | 消息气泡, floating panel |
| full | 9999px | **仅** avatar / 圆形 icon button |

## 间距
xs:4 / sm:8 / md:16 / lg:24 / xl:32 / 2xl:48

- 组件内 padding 基准: `md`(16px)
- 面板内 section gap: `lg`(24px)
- 布局大分割: `xl`(32px) 或 `2xl`(48px)
- 最大内容宽: 720px(文章) / 960px(仪表盘)

## 组件速查
### Button Primary
`bg=tertiary, color=on-tertiary, radius=sm, padding=10px 20px`
hover: `bg=tertiary-container`。每视图仅一个。

### Button Secondary
`bg=transparent, color=primary, radius=sm, padding=10px 20px, border=border`

### Input
`bg=neutral, color=primary, radius=md, padding=12px 16px, border=border`
focus: 2px tertiary ring; placeholder: secondary color

### Message Bubbles
- User: `bg=#F0EDE8, color=primary, radius=lg, padding=md`, 右对齐
- Assistant: `bg=surface(#FFF), color=primary, radius=lg, padding=md`, 左对齐, 无气泡边框感

### Card
`bg=surface, radius=md, padding=lg`

## Do / Don't
- ✅ Tertiary 仅用于可交互元素
- ✅ 保持充裕留白，不填满空间
- ✅ Space Mono 仅用于元数据/系统标签
- ❌ 不用纯黑/纯白背景
- ❌ 只用单一强调色
- ❌ 不给矩形元素用 `rounded.full`
