# lead-media-edit 适配

当项目由 `lead-media-edit` 驱动时，保留它的粗剪、Whisper 字级时间、字幕、音效混音和 QA；本 Skill 只接管视觉段落与透明动效。

## 人物状态

`lead-media-edit/motion-template` 已支持三种状态：

- `full`：人物全屏，暂不显示大面积动效。
- `stage`：人物保持中央全屏，透明标题、卡片、标签和图形在人物周围同步弹出。
- `pip`：人物收进圆环，为完整 B-roll 让位。

在 `src/project.ts` 的 `MODES` 中按成片秒数切换：

```ts
export const MODES: Mode[] = [
  { t: 0, mode: "full" },
  { t: 2.8, mode: "stage", dur: 0.42 },
  { t: 9.4, mode: "pip", dur: 0.62 },
  { t: 14.2, mode: "full", dur: 0.62 },
];
```

`stage` 的动效应该导出为真实透明的 WebM VP9 或 ProRes 4444；H.264 黑底不能作为透明层。人物和字幕安全区以 `lead-media-edit/references/居中人物动态舞台.md` 为准。

cue 先由 `lead-media-edit/scripts/build_motion_cues.py` 根据 `transcript_rough.json` 生成候选，再由人工删改；如果启用 `jev-video-review`，先将 5–15 秒语义段送入 Jev，读取 `jev_motion_review.json` 中的 `viewer_job`、`visual_mode`、`cue_priority` 和 `emphasis_target`，把它们作为 `scene-plan.json` 的提示字段。Jev 不生成资产、不补数字，也不替代人工删改。渲染前运行 `validate_motion_cues.py` 检查时长、密度和素材引用。这样语义卡点、素材来源和安全区都能在渲染前被审计。

素材较多时先用 `build_asset_manifest.py` 生成 `asset-manifest.json`；人物有明显移动时维护 `face-boxes.json`，并将它传给 cue 校验器，避免卡片在某个镜头突然压住脸或手势。

## 轨道边界

- A-roll、人声、字幕和最终响度：`lead-media-edit`。
- 场景分组、进入/稳定/退出、透明卡片与转场：本 Skill。
- HyperFrames 负责网页/流程/UI 互动；Remotion 负责人物状态、标题、卡片、数字和跨段落时间编排。

先按 `transcript_rough.json` 建立 `scene-plan.json`，再把每个 cue 写入 motion 工程，避免把动效卡在原片重说或被粗剪删除的时间点上。
