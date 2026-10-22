# Workflow contract

## Take review

`jev_take_candidates.json` 只能包含已经通过 `speech_islands.py ... listen` 人工听过的候选。Jev 可以判断完整度、重说风险和语义切点风险，但不能听音频，因此 `candidate_keep` 仍然是候选而不是自动切片命令。

## Motion review

`jev_motion_candidates.json` 使用粗剪后的 `transcript_rough.json` 时间。每段建议 5–15 秒，硬上限 20 秒。Jev 只能从输入候选中选择重点词和视觉状态，不能生成新的数字、Logo、截图或素材文件名。

## Deterministic gates

Jev 结果之后仍必须运行：

- `build_motion_cues.py`
- `build_asset_manifest.py`
- `validate_motion_cues.py`
- face-boxes 检查
- 字幕断句检查
- `qa_check.py`
- 实际 viewer 的首帧、稳定态、转场和退出检查

`disabled`、`partial`、低 confidence 或概率接近的结果都走人工复核。Jev 不可用不应阻断普通剪辑流程。
