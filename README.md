# Jev Talking Head Workflow

一套面向中文真人口播的可复用制作工作流，支持 Codex 和 Claude Code。它把真人 A-roll、Jev 语义评审、人物居中舞台、同步卡片与 UI、字幕、音频、Remotion 动效、FFmpeg 合成和 QA 组织成一条可回放的数据流。

仓库提供两条等价的制作路线。你可以先用 ChatCut 完成可编辑的时间线，也可以直接使用本地 Skill 工具流生成最终 MP4；两条路线共用同一份转写、分镜、cue、素材清单和验收规则。

## 两条路线

| 路线 | 适合场景 | 主要组件 | 输出 |
| --- | --- | --- | --- |
| ChatCut 组装 | 希望在桌面软件里继续拖动、试听和调整时间线 | `full-video-motion-workflow`、ChatCut Desktop、HyperFrames/Remotion、`talking-head-guide` | 可编辑 ChatCut 时间线，可选 MP4 |
| 本地 Skill 渲染 | 希望由 Codex/Claude Code 直接完成批处理和稳定导出 | `center-stage-talking-head`、`lead-media-edit`、Jev、Remotion、FFmpeg | MP4、SRT/ASS、QA 报告和可编辑源文件 |

人物居中、卡片、数字、步骤、截图和 callout 由 `center-stage-talking-head` 统一编排。人物需要让出大面积 UI 或 B-roll 时切换 `pip`；普通解释段落使用 `stage`；自然口播使用 `full`。两条路线都保留真人原声和实际手势，不把真人口播改成 TTS 或数字人。

## 快速安装

### Codex

把 `skills/` 下需要的目录复制到用户级 Skill 目录：

```text
%USERPROFILE%\.codex\skills\center-stage-talking-head
%USERPROFILE%\.codex\skills\connect-chatcut-desktop
%USERPROFILE%\.codex\skills\full-video-motion-workflow
%USERPROFILE%\.codex\skills\jev-video-review
%USERPROFILE%\.codex\skills\lead-media-edit
%USERPROFILE%\.codex\skills\lead-media-script
```

### Claude Code

把 `skills/` 下的同名目录复制到 `%USERPROFILE%\.claude\skills\`。`integrations/claude/` 里的 bridge 是需要轻量入口时使用的兼容层；如果直接复制完整 Skill，优先使用 `/center-stage-talking-head` 和 `/lead-media-edit`。

这个仓库不包含 API key、Claude settings、MCP token、用户视频或本机缓存。ChatCut 连接需要用户在桌面程序中登录，连接说明见 [`docs/chatcut-route.md`](docs/chatcut-route.md)。

## 本地渲染路线

```text
原片 → large-v3-turbo 转写 → 语音岛/候选 take → 人工复听与 EDL
     → rough_cut → transcript_rough.json
     → Jev 语义评审（可选）
     → motion-cues + asset-manifest + face-boxes 校验
     → Remotion/HyperFrames 动效
     → 字幕、音频、FFmpeg 合成
     → qa_check
```

完整命令和 Windows 环境约束见 [`docs/local-skill-route.md`](docs/local-skill-route.md)。

## ChatCut 路线

```text
原片/配音 → lead-media-edit 定稿
         → full-video-motion-workflow 分镜
         → HyperFrames/Remotion 独立动态素材
         → ChatCut 导入、排列、混音、预览、导出
```

ChatCut MCP 不可用时，工作流自动回退到本地 Remotion + FFmpeg；不要把未连接的 ChatCut 工具名称当成当前会话能力。具体职责和回退条件见 [`docs/two-routes.md`](docs/two-routes.md)。

## 公开发布边界

- 原创工作流和适配层使用 MIT 许可。
- 字体、Remotion、FFmpeg、Python 包、ChatCut 和 HyperFrames 依照各自上游许可使用。
- 不提交 API key、token、`.env`、用户视频、音频、字幕成品、工作缓存或账号配置。
- 发布前运行 `python scripts/validate_public_release.py`。

## 详细文档

- [`docs/two-routes.md`](docs/two-routes.md)：两条路线的职责、数据契约和选择规则。
- [`docs/local-skill-route.md`](docs/local-skill-route.md)：本地 Skill + Remotion/FFmpeg 全流程。
- [`docs/chatcut-route.md`](docs/chatcut-route.md)：ChatCut Desktop、MCP、HyperFrames 和回退策略。
- [`docs/claude-code.md`](docs/claude-code.md)：Claude Code 调用入口和 Skill 路由。
- [`docs/workflow.md`](docs/workflow.md)：Jev 与口播主链路的技术契约。
