# Center Stage Talking Head 工作流说明

## 状态和文件

`motion-template/src/engine/Presenter.tsx` 支持 `full`、`stage`、`pip`。`stage` 保持 A-roll 全屏，`StageOverlay` 负责标题、指标卡、步骤卡、设备卡、引用卡、标签卡和 `callout`。

`project.ts` 中的核心字段：

```ts
export const FACE = [
  { t: 0, x: 960, y: 470, r: 300 },
  { t: 12.4, x: 1010, y: 455, r: 286 },
];

export const MODES: Mode[] = [
  { t: 0, mode: "full" },
  { t: 2.8, mode: "stage", dur: 0.42 },
  { t: 9.4, mode: "pip", dur: 0.62 },
  { t: 14.2, mode: "full", dur: 0.62 },
];
```

`motion-cues.json` 的常用类型：`title`、`metric`、`feature-card`、`steps`、`device`、`quote`、`tags`、`callout`。cue 的 `asset` 指向 `public/` 下的实际文件；`callout` 额外使用 `target: {x, y}`。

## 分工

- `lead-media-edit`：粗剪、Whisper、字幕、音频标准化、音效混音、最终合成和 QA；
- `full-video-motion-workflow`：整片视觉段落、scene-plan、透明素材和 ChatCut 组装；
- `center-stage-talking-head`：人物状态、语义 cue、素材清单、避脸安全区和可复用舞台组件；
- HyperFrames：网页、流程、UI 互动、透明 HTML 动效；
- Remotion：人物状态、卡片、数字、callout、跨段落时间编排。

这些 Skill 是协作关系。调用本 Skill 不会替代、隔离或关闭其他 Skill。

## 跨客户端安装

Codex 共享目录：

```text
%USERPROFILE%\.codex\skills\center-stage-talking-head
```

Claude Code 共享目录：

```text
%USERPROFILE%\.claude\skills\center-stage-talking-head
```

两处使用同一份 SKILL.md 和同一套调用名 `center-stage-talking-head`。Claude Code 的 HyperFrames 插件由用户级插件配置启用；已有 `lead-media-edit` 保留并补充 stage 适配。

## 还原度边界

人物居中、语义卡点、卡片/数字/步骤、指向线、PIP 切换和安全区可以复现参考片的视觉结构。原视频中的 UI 截图、Logo、手机录屏和事实数字需要对应素材，不能用模板凭空补出。
