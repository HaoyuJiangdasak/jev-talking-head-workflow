# ChatCut 组装路线

ChatCut 是桌面时间线后端。它适合需要继续拖动、试听、微调轨道和交付可编辑项目的场景。

## 安装和登录

使用 ChatCut 官方桌面下载入口，并在桌面程序内完成登录。仓库不处理账号、密码、token 或支付信息，也不提供第三方安装包。

打开 ChatCut 后，重新启动 Claude Code/Codex 会话，让客户端重新发现 MCP。用下面的命令确认状态：

```text
claude mcp list
claude mcp get chatcut_desktop
```

只有状态显示 `Connected` 后，才把 ChatCut 工具写入实际执行计划。

## 工具职责

| 阶段 | 工具或 Skill | 作用 |
| --- | --- | --- |
| 语义和粗剪 | `lead-media-edit`、`jev-video-review` | 确定真人 A-roll、文字和时间基准 |
| 分镜和动效 | `full-video-motion-workflow`、HyperFrames、Remotion | 生成独立透明动效和全屏 B-roll |
| 时间线 | ChatCut MCP | 导入、排列、裁剪、轨道、字幕保护、混音、预览和导出 |
| 视觉 QA | `visual-analysis` 或人工 viewer | 检查首帧、稳定态、转场、退出和遮脸 |

## 轨道约定

- 主视频轨：真人 A-roll。
- 替换画面轨：全屏 B-roll 或 UI。
- 上层轨：透明标题、卡片、数字、步骤和 callout。
- 全局包装轨：只保留一条顶部进度条。
- 音频轨：人声、BGM、音效分轨。

## 回退策略

如果 `chatcut_desktop` 缺失、连接关闭、项目不可访问或桌面端未登录，继续使用 [`docs/local-skill-route.md`](local-skill-route.md)。本地路线生成的 `scene-plan.json`、`motion-cues.json`、素材清单和字幕可以在 ChatCut 恢复连接后继续导入。

