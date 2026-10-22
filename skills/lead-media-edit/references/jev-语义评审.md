# Jev 语义评审适配

`jev-video-review` 是 `lead-media-edit` 的旁路判断层。它的目标是减少真人录音中“多段都能用但取舍不自然”的情况，并让 B-roll 与语义段落对齐。

## 接入位置

```text
transcribe + probe_windows + speech_islands
→ 人工听候选 take
→ jev-video-review --stage take
→ 人工确定 edl.json
→ rough_cut
→ rough.mp4 重新转录 transcript_rough.json
→ jev-video-review --stage motion
→ 分镜 / build_motion_cues / validate_motion_cues
```

不要让 Jev 直接写 EDL。Jev 看得到转写、上下文和区间统计，但不能听出语气、呼吸、爆音或真正的切点自然度。

## Take 输入

`工作素材/jev_take_candidates.json` 应只包含已经用 `speech_islands.py ... listen` 听过的候选：

```json
{
  "schema_version": "1.0",
  "stage": "take",
  "video": {"platform": "douyin", "script_mode": "technique"},
  "segments": [
    {
      "id": "s04",
      "canonical_text": "需要保留的完整意思",
      "previous_text": "上一句",
      "next_text": "下一句",
      "must_keep": ["不是", "50%"],
      "alternatives": [
        {"id": "a", "start": 12.4, "end": 16.2, "text": "候选 A", "asr_confidence": 0.91},
        {"id": "b", "start": 18.0, "end": 22.1, "text": "候选 B", "asr_confidence": 0.88}
      ],
      "evidence": {"pause_before_ms": 120, "pause_after_ms": 210}
    }
  ]
}
```

输出中的 `candidate_keep` 只是候选。`human_review`、概率接近、confidence 偏低、语义切点风险大于 2 的段落，都必须回到音频复听。

## Motion 输入

`工作素材/jev_motion_candidates.json` 取自粗剪后的 `transcript_rough.json`，保持真实起止时间：

```json
{
  "schema_version": "1.0",
  "stage": "motion",
  "video": {"platform": "douyin", "mode": "stage"},
  "segments": [
    {
      "id": "s04",
      "start": 18.42,
      "end": 24.80,
      "text": "很多人以为……",
      "candidate_emphasis": ["亏了 50%", "再涨 50%", "上涨 100%"]
    }
  ]
}
```

Jev 可以选择视觉任务和状态，但不能生成新的数字、Logo、截图、文件名或 asset 引用。现有 `build_motion_cues.py` 继续负责确定性的规则候选，`build_asset_manifest.py` 和 `validate_motion_cues.py` 继续负责素材与避脸校验。

## 降级与记录

- 找不到 Jev 客户端、key 未配置、超时或限流时，review 写 `disabled` 或 `partial`，原有剪辑链继续执行。
- 不得把 disabled 当成“无风险”。所有段落按人工复核处理。
- `jev_take_review.json` 和 `jev_motion_review.json` 应保留在 `工作素材/`，并在 `剪辑说明.md` 中记录模型、provider、输入 hash、人工改动和未解决风险。
- 不上传整段视频；只发送必要的文字、时间、候选和统计。姓名、电话、地址、客户资料先脱敏。
