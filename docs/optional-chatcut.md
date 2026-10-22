# Optional ChatCut integrations

这个仓库不复制没有明确再分发许可的 ChatCut 内部 skill。使用 ChatCut 时，按下面的职责接入现有环境：

| 需求 | 外部 skill | 接入位置 |
| --- | --- | --- |
| 口播 A-roll、去重说、停顿和重排 | `talking-head-guide` | 先完成最终 speech timeline |
| 普通字幕、ASR 修正和字幕布局 | `transcription` | A-roll 定稿后 |
| 单主体设计字幕 | `embedded-captions` | 需要字幕视觉身份时 |
| 标题、数据卡、引语、侧栏和 PiP | `talking-head-recut` | 以最终 transcript 为时间基准 |
| Motion Graphics | `create-motion-graphics` | JEV motion 评审和分镜之后 |
| 视觉逐帧检查 | `visual-analysis` | 每个生成层和最终 viewer |
| 人声隔离、TTS 或补录 | `voice` / `voice-isolation` | 按用户明确要求调用 |

Jev 只负责结构化语义建议：take 选择、段落角色、视觉状态和重点短语。它不能代替音频复听、字幕时间轴、Alpha 检查、遮脸检查、黑帧检查或最终 viewer QA。
