# 本地 Skill + Remotion/FFmpeg 路线

这条路线直接使用 Codex 或 Claude Code 的 Skill 工具流，不要求 ChatCut MCP。它适合真人口播、脑机接口科普、知识讲解和需要可重复渲染的短视频。

## 调用入口

```text
/center-stage-talking-head
/lead-media-edit
/full-video-motion-workflow
/jev-video-review
```

推荐调用顺序：

```text
center-stage-talking-head + lead-media-edit
→ full-video-motion-workflow（复杂分镜时）
→ jev-video-review（候选 take/语义段评审时）
```

原片已经录好时不调用 `lead-media-script`，除非用户明确需要补录稿件。

## Windows 环境

使用独立 Python 环境运行仓库脚本：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$Python = '<path-to-lead-media-python>'
$Browser = '<path-to-chrome-headless-shell.exe>'
$env:PATH = '<path-to-ffmpeg-bin>;' + $env:PATH
```

本机已验证的约束是：Whisper 使用 `large-v3-turbo`；FFmpeg 显式使用 `--encoder libx264`；Remotion bundle 之前运行 `subset_fonts.py`；渲染时传入稳定的 Chromium 可执行文件。

## 最小执行序列

```powershell
ffprobe -v error -show_streams -show_format -of json $Source
ffmpeg -y -i $Source -vn -ac 1 -ar 16000 $Audio16k
& $Python transcribe.py $Audio16k $Transcript --model large-v3-turbo
& $Python rough_cut.py $Source $Edl $Work --words $Transcript --encoder libx264
& $Python transcribe.py $Rough $TranscriptRough --model large-v3-turbo
& $Python track_face_boxes.py $Rough $FaceBoxes --sample-fps 5
& $Python build_motion_cues.py $TranscriptRough $CueCandidates
& $Python build_asset_manifest.py $Public $AssetManifest
& $Python validate_motion_cues.py $Cues --duration $Duration --public $Public --face-boxes $FaceBoxes
```

编辑 `scene-plan.json` 和 `motion-cues.json` 后，再执行字幕、音频、Remotion bundle、最终合成和 `qa_check.py`。不能把候选 cue 直接当成最终分镜。

## 人物与动画关系

- `full`：人物保持自然全屏口播。
- `stage`：人物在中央，标题、卡片、数字、步骤、截图和 callout 位于安全区。
- `pip`：人物缩小，让复杂 UI、流程图或证据画面获得空间。

`stage` 不会凭空把侧身人物抠到中央。人物原始构图、前景遮罩和手势空间必须先看帧确认；没有可靠抠像时使用侧边安全区或调整画面裁切。

