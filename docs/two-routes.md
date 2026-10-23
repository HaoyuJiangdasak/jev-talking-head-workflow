# 两条口播视频制作路线

本仓库把同一条真人口播拆成两个执行后端。前半段的数据契约相同，后半段根据用户是否要桌面时间线选择 ChatCut 或本地渲染。

## 共用数据契约

两条路线都使用以下文件：

```text
work/
├── transcript_raw.json
├── edl.json
├── rough.mp4
├── transcript_rough.json
└── analysis/
    ├── scene-plan.json
    ├── motion-cues.json
    ├── asset-manifest.json
    ├── face-boxes.json
    ├── claims.md
    └── QA.md
```

`transcript_rough.json` 是唯一的口播时间基准。`motion-cues.json` 记录人物状态、卡片、截图、数字、步骤和 callout 的起止时间；`face-boxes.json` 只提供脸部安全区候选，手势和文字碰撞仍需要看帧确认。

## ChatCut 组装路线

选择条件：需要在桌面软件里继续拖动素材、试听音频、修改轨道或交付可编辑项目。

1. `lead-media-edit` 完成真人口播粗剪、字幕和人声处理。
2. `full-video-motion-workflow` 读取完整 transcript，建立 `scene-plan.json` 和 `STORYBOARD.md`。
3. HyperFrames 负责网页/UI/交互演示，Remotion 负责人物状态、卡片、进度条和跨段落编排。
4. 动效按独立素材导出，透明层验证 Alpha 后导入 ChatCut。
5. ChatCut 负责导入、排列、混音、字幕保护、预览和导出。

ChatCut MCP 必须在当前 Claude/Codex 会话真正显示 Connected 后才可调用 `read_project`、`manage_timelines`、`preview_timeline` 或 `export`。如果 MCP 没有连接，继续走本地路线；不要停在“等待 ChatCut”。

## 本地 Skill + Remotion/FFmpeg 路线

选择条件：希望由代理直接完成批处理、稳定渲染、字幕文件和 QA，或 ChatCut MCP 当前不可用。

1. `center-stage-talking-head` 选择 `full`、`stage`、`pip` 并编排 cue。
2. `lead-media-edit` 运行转写、粗剪、字幕、人声、音效和 QA 脚本。
3. Remotion 输出人物与动效合成画面；HyperFrames 仅在需要 HTML/UI 动画时加入。
4. FFmpeg 用 `libx264` 完成最终合成，生成 MP4、SRT/ASS 和 QA 报告。

本路线不会创建 ChatCut 项目，所有源文件和中间文件都留在当前视频项目目录，方便后续切换到 ChatCut。

## 统一验收

- 口播语义和切点经过人工复听。
- 人物脸、嘴、手势和字幕没有被卡片覆盖。
- 重要 cue 与实际词时间一致，退出后没有残影。
- 科学数字、产品名和研究结论有来源或明确标记为示意。
- 最终 MP4 解码完整，音视频时长一致，完成黑帧、爆音、字幕和响度检查。

