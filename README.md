# Jev Talking Head Workflow

这是一套面向中文真人口播视频的可复用制作工作流，覆盖：口播文案、真人 A-roll 粗剪、Jev 语义评审、B-roll / Motion Graphics、居中人物舞台、字幕、混音和最终 QA。

Jev 在这里承担“结构化判断层”职责：它可以比较多个 take、标记语义残句和重复风险、判断语义段落的观众任务、建议 `full / stage / pip`，以及比较开头候选。它不会直接修改 EDL、时间轴、字幕或渲染结果；低置信度结果必须回到人工复听、看帧或 QA。

## 工作流

```text
lead-media-script（可选）
  → Jev script 评审：开头、承诺、受众、事实风险、重复度
  → 真人录制

lead-media-edit
  → Whisper / probe_windows / speech_islands
  → 人工复听候选 take
  → Jev take 评审
  → 人工确认 edl.json
  → rough_cut
  → transcript_rough.json
  → Jev motion 评审
  → 分镜 / build_motion_cues / validate_motion_cues
  → Remotion / HyperFrames
  → 字幕 / 混音 / final_compose / qa_check
```

核心 skill 位于 [`skills/`](skills/)：

- [`lead-media-script`](skills/lead-media-script/)：从选题生成可直接录制的逐字稿。
- [`lead-media-edit`](skills/lead-media-edit/)：从真人口播视频交付可发布成片，包含粗剪、B-roll、字幕和 QA。
- [`jev-video-review`](skills/jev-video-review/)：Jev `take`、`motion`、`script` 三阶段结构化评审。
- [`full-video-motion-workflow`](skills/full-video-motion-workflow/)：完整分镜、透明动效、转场、ChatCut 组装流程。
- [`center-stage-talking-head`](skills/center-stage-talking-head/)：人物居中、卡片和动画围绕人物同步出现的舞台编排。

没有明确再分发许可的 ChatCut 内部 skills 没有被整套复制到这个仓库。它们通过 [`docs/optional-chatcut.md`](docs/optional-chatcut.md) 说明如何作为外部依赖接入。

## 安装到 Codex

将 `skills/` 下的目录复制到：

```text
%USERPROFILE%\.codex\skills\
```

至少需要安装：

```text
skills/lead-media-script
skills/lead-media-edit
skills/jev-video-review
skills/full-video-motion-workflow
```

如果要使用人物居中舞台，再安装 `skills/center-stage-talking-head`。

本机的 `lead-media-edit` 运行环境需要单独配置 Python、FFmpeg、Whisper、Node 和字体。不要把这些本机路径、缓存或 API key 提交到仓库。当前 Windows 环境的 Python 路径由本机 `AGENTS.md` 约束；其他机器请使用自己的解释器。

## 安装到 Claude Code

Claude Code 的 skill 发现目录是：

```text
%USERPROFILE%\.claude\skills\
```

将 `integrations/claude/` 下的对应目录复制到该目录：

```text
integrations/claude/jev-video-review
integrations/claude/lead-media-edit-bridge
integrations/claude/lead-media-script-bridge
integrations/claude/full-video-motion-workflow-bridge
```

Claude 侧优先复用已有 `/jev` MCP skill 和 `jev-1.14.0`。这个仓库不包含 MCP server 配置、API key、Claude settings 或 provider token。`jev_decide` 适合 take 选择，`jev_classify` 适合批量判断语义段角色，`jev_compare` 和 `jev_noul` 适合脚本与事实风险检查。

## JEV 运行方式

`skills/jev-video-review/scripts/jev_video_review.py` 是本地文件链路的可审计适配器：

```powershell
python skills/jev-video-review/scripts/jev_video_review.py `
  --stage take `
  --input 工作素材/jev_take_candidates.json `
  --output 工作素材/jev_take_review.json `
  --provider typesafe `
  --model jev-1.14.0 `
  --cache-dir 工作素材/.jev-cache `
  --redact
```

适配器默认脱敏手机号、邮箱、身份证号和 URL 查询串；姓名和地址仍需要调用方预处理。它支持 `--offline`、`--required`、`--cache-dir` 和 `--no-redact`，并在客户端不可用时输出 `disabled` / `partial`，继续原有剪辑链路。

Jev key 只能通过环境变量提供。不要把 key 写入 JSON、日志、截图、skill 文件或 Git history。

## 公开发布边界

- 仓库不包含 API key、token、`.env`、Claude settings、用户视频、字幕成品、音频、工作素材或缓存。
- `lead-media-edit/assets/fonts/` 中的字体继续保留各自的 SIL Open Font License 文件；不要把字体许可误认为项目 MIT 许可。
- Remotion、FFmpeg、Python、npm 和 ChatCut 依赖仍然受各自上游许可约束。
- 发布前运行 `python scripts/validate_public_release.py`，检查密钥模式、绝对用户路径、缓存和临时媒体。

## 许可证

本仓库原创工作流和适配层使用 MIT 许可。子目录中的原有 LICENSE 和 `THIRD_PARTY_NOTICES.md` 优先适用；第三方字体和地图数据按随附许可再分发。
