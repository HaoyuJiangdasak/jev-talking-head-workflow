---
name: center-stage-talking-head
description: 将真人口播人物保留在画面中央，并让标题、卡片、数字、截图、步骤、UI 和指向动画按口播时间线围绕人物同步出现；适合参考片式的“人物与动画合二为一”视频，也可和现有口播粗剪、字幕、HyperFrames、Remotion、ChatCut 工作流一起使用。
metadata:
  display-name: Center Stage Talking Head
  short-description: 居中人物与语义动画同步口播
---

# Center Stage Talking Head

这个 Skill 是现有口播能力的编排层。它保留用户已有的粗剪、字幕、人声、音效和 QA 能力，在需要“人物居中、周围弹出解释画面”时加入 `stage` 舞台；复杂 UI 或大面积图解时切换 `pip`。

它安装在用户级共享 Skill 目录中，可以和 `lead-media-edit`、`full-video-motion-workflow`、`hyperframes`、`general-video`、`talking-head-recut`、`embedded-captions` 以及 Claude Code 的其他 Skill 一起调用。不要创建项目级隔离副本，也不要为了它关闭其他 Skill。

## 何时使用

- 用户要求人物在中央讲话，周围出现卡片、文字、数字、截图、流程、手机、UI 或指向线；
- 用户给出参考片，要求人物动作和动画按照语义节点同步；
- 用户已有 `lead-media-edit` 粗剪链路，希望把固定角落人物改成中央主讲舞台；
- 用户要求把同一套能力接到 Codex 和 Claude Code 的共享环境。

普通字幕任务继续路由到 `embedded-captions`；已有口播的图形包装可以配合 `talking-head-recut`；需要完整粗剪和成片交付时使用 `lead-media-edit`；需要整片分镜、透明素材和 ChatCut/HyperFrames 组装时使用 `full-video-motion-workflow`。

## 固定数据流

1. `lead-media-edit` 完成粗剪，生成粗剪后的 `rough.mp4` 和 `transcript_rough.json`。
2. 读取字级时间轴，生成候选 `motion-cues.json`；候选必须人工复核，删除没有解释作用的卡片，补充真实截图和可核实数字。
3. 生成 `asset-manifest.json`，确认 UI、手机、Logo、透明 WebM 和字体都存在。
4. 人物位置稳定时使用固定 `FACE`；人物会移动时维护 `FACE` 关键帧和 `face-boxes.json`。
5. 用 `full`、`stage`、`pip` 三种状态编排：
   - `full`：人物全屏，保持自然口播；
   - `stage`：人物保持中央，透明卡片和动画在左右安全区出现；
   - `pip`：人物缩成圆环，让复杂 UI 或大面积 B-roll 让位。
6. 运行 cue、素材和避脸校验，再用 Remotion/HyperFrames 生成动效，最后回到 `lead-media-edit` 的音频、字幕和 QA 链路。

## 必须执行的校验

```bash
python <lead-media-edit>/scripts/build_motion_cues.py \
  工作素材/transcript_rough.json \
  .code/<项目名>/motion/src/data/motion-cues.json

python <lead-media-edit>/scripts/build_asset_manifest.py \
  .code/<项目名>/motion/public \
  .code/<项目名>/motion/asset-manifest.json

python <lead-media-edit>/scripts/validate_motion_cues.py \
  .code/<项目名>/motion/src/data/motion-cues.json \
  --duration <粗剪时长> \
  --public .code/<项目名>/motion/public \
  --face-boxes face-boxes.json
```

校验器会检查时间范围、实际持续时间重叠、必填字段、素材引用和扩展脸部安全区。失败时停止渲染；warning 需要人工确认是否有意叠加。

## 视觉规则

- 人物脸、嘴、手势和字幕带属于禁区；卡片优先放左右两侧和顶部。
- 一个 cue 只表达一个新信息；入场、稳定和退出都要有时间段。
- 数字、年份、产品名和 Logo 只使用口播、分镜或来源明确的资产；示意画面标注“示意”。
- `callout` 可以用虚线和落点指向人物手势、手机或屏幕位置。
- 透明叠加层使用 WebM VP9/ProRes 4444；H.264 黑底不当作透明素材。
- 保留用户已有字幕和人声轨道，避免重复生成或把音效烙进每个动效素材。

详细 cue schema、FACE 关键帧、素材清单和跨客户端安装说明见 [references/workflow.md](references/workflow.md)。

## 直接调用

```text
使用 center-stage-talking-head + lead-media-edit。
人物保持在中央，按 transcript_rough.json 的语义节点让卡片、数字、截图、步骤和 callout 围绕人物同步出现；复杂 UI 段落切 pip。保留现有字幕和人声，渲染前执行 cue、asset-manifest 和 face-boxes 校验。
```
