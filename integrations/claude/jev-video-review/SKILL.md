---
name: jev-video-review
description: 用 TypeSafe Jev System One 对口播脚本、粗剪候选和分镜做结构化语义评审。它只输出带概率和置信度的建议，不直接修改 EDL、字幕、时间轴或渲染结果。用于提升口播内容取舍、重说判断、分镜角色和重点信息的一致性。
license: MIT
metadata:
  version: "1.0.0"
  display-name: "Jev-口播语义评审"
---

# Jev-口播语义评审

这个 skill 是一个可选的语义判断层，服务于口播视频的三个位置：

1. **粗剪候选评审**：在 `transcript_raw.json`、`probe_windows` 和 `speech_islands` 完成后、写 `edl.json` 之前，比较同一句话的多个 take，标记重说、半句、漏掉否定词/数字和衔接风险。
2. **分镜评审**：在 `transcript_rough.json` 生成后、写 `分镜.md` 或 `motion-cues.json` 之前，判断语义段落的观众任务、视觉状态和重点短语。
3. **文案评审**：在 `lead-media-script` 的三个开头候选和最终自检阶段，比较开头清晰度、承诺兑现和事实风险。

Jev 的结论是建议，不是事实。脚本永远保留原文、时间戳、原始候选和 raw answers；低置信度结果必须回到人工复听或人工看帧。Jev 不能代替 Whisper、`speech_islands`、字幕断句、`visual-analysis`、`qa_check.py` 或最终 viewer 检查。

## 路由规则

- 用户提供真人口播视频并要成片：先走 `lead-media-edit`。Jev 的第一优先接入点是粗剪决策前，第二优先是粗剪后的分镜决策。
- 用户只有选题或文案：先走 `lead-media-script`，Jev 只做开头和稿件评审，不代写全文。
- 使用 ChatCut 的完整分镜和组装：在 `full-video-motion-workflow` 的 `scene-plan.json` 生成前调用 motion 阶段。
- 需要字幕或视觉 QA 时，继续使用原有 `transcription`、`embedded-captions` 和 `visual-analysis`；不要让 Jev 代替这些确定性工具。

## 固定顺序

```text
A-roll / 文案定稿
  → 生成候选 JSON
  → Jev 批量判断
  → 读取 raw answers 与置信度
  → 高置信度只标记为推荐
  → 人工复核低置信度和高风险项
  → 写入 edl / 分镜 / motion-cues
  → 原有验证器和渲染链路
```

Jev 不直接执行切片、改字幕或生成事实画面。任何 `best_take`、`visual_mode` 或 `best_hook` 都必须先写进 review 文件，再由上游 skill 的规则和人工确认应用。

## 输入与输出

脚本入口：

```powershell
$jevPy = 'python'
$env:PYTHONIOENCODING = 'utf-8'
& $jevPy scripts/jev_video_review.py `
  --stage take `
  --input 工作素材/jev_take_candidates.json `
  --output 工作素材/jev_take_review.json `
  --provider typesafe `
  --model jev-1.14.0 `
  --cache-dir 工作素材/.jev-cache `
  --redact
```

如果 JEV 客户端不在 Python 的 import path 中，设置客户端文件路径：

```powershell
$env:JEV_CLIENT_PATH = 'D:\path\to\jev_client.py'
```

脚本也支持 `--client-path`。它会优先使用显式路径，其次尝试 `import jev_client`。找不到客户端、没有 key 或请求失败时，默认写入 `status: "disabled"` 或 `status: "partial"`，并把所有未判断项目标为 `review_required`，不会伪造通过结果。只有传入 `--required` 时，失败才阻断流水线。

输入的共同字段：

```json
{
  "schema_version": "1.0",
  "stage": "take|motion|script",
  "video": {
    "platform": "竖屏短视频",
    "audience": "具体受众",
    "script_mode": "script|technique"
  },
  "segments": []
}
```

`take` 阶段的每个段落必须包含已由人工或上游复听得到的候选，不允许仅凭长转写自动创造 take：

```json
{
  "id": "s04",
  "canonical_text": "这句需要保留的完整意思",
  "previous_text": "上一句",
  "next_text": "下一句",
  "must_keep": ["不是", "50%"],
  "alternatives": [
    {"id": "a", "start": 12.4, "end": 16.2, "text": "候选 A", "asr_confidence": 0.91},
    {"id": "b", "start": 18.0, "end": 22.1, "text": "候选 B", "asr_confidence": 0.88}
  ],
  "evidence": {
    "speech_islands": [{"start": 12.3, "end": 16.3}, {"start": 17.9, "end": 22.2}],
    "pause_before_ms": 120,
    "pause_after_ms": 210
  }
}
```

`motion` 阶段使用粗剪后的真实字级时间：

```json
{
  "id": "s04",
  "start": 18.42,
  "end": 24.80,
  "text": "很多人以为……",
  "candidate_emphasis": ["亏了 50%", "再涨 50%", "上涨 100%"]
}
```

输出至少包含：

```json
{
  "schema_version": "1.0",
  "stage": "take",
  "status": "ok|partial|disabled|error",
  "model": "jev-1.14.0",
  "input_sha256": "...",
  "recommendations": [],
  "raw_answers": [],
  "review_required": 0,
  "notes": []
}
```

每条 recommendation 都保留 `segment_id`、推荐项、概率、confidence、风险分数、是否可作为候选和人工复核原因。原始答案不能被清理掉，否则无法追溯模型为什么做出判断。

提供 `--cache-dir` 时，缓存键由输入文件 hash、stage、provider、model、schema 和 adapter 版本组成；改动转写或问题集后会自动失效。缓存只保存 review JSON，不保存 API key 或异常原文。

## 三套问题集

### Take 阶段

- `best_take`：从候选 take 和 `human_review` 中选一个。
- `is_retake_or_filler`：是否是重说、无意义起句或残留片段。
- `sentence_complete`：句子是否完整、语义是否可独立听懂。
- `semantic_cut_risk`：0–9 分，越高表示切掉后越可能漏否定词、条件词、数字、主语或衔接。

建议门槛：`best_take` 概率至少 0.80、confidence 至少 0.75、`semantic_cut_risk` 不高于 2，才标记为“可进入候选”。否则只标记“需人工复听”。这些是初始策略，发布前应使用真人录音样本校准。

### Motion 阶段

- `viewer_job`：问题、观点、步骤、证据、例子、对比、CTA 或过渡。
- `visual_mode`：`full`、`stage`、`pip`。
- `cue_priority`：0–5 分，判断这一段是否值得消耗一个主要视觉 cue。
- `emphasis_target`：从候选短语中选一个，不允许模型凭空生成数字、Logo 或截图。

低优先级或过渡段默认保留人物全屏，避免为了“有动效”而一句话配一个卡片。`stage` 和 `pip` 仍需通过 `validate_motion_cues.py`、face-boxes 和实际静帧检查。

### Script 阶段

- `best_hook`：从三个开头中选择最清楚、最容易兑现的一个。
- `promise_fulfilled`：正文是否真的兑现标题和开头承诺。
- `audience_fit`：受众是否具体，还是泛化到“所有人”。
- `fact_risk`：是否存在需要来源、用户事实或发布前核实的数据。
- `redundancy_risk`：是否有重复铺垫或一个观点多次改写。

它只辅助 `lead-media-script` 的结构和审稿，不推翻“不编造、不夸大、事实先于文风”的四条铁律。

## 自动化边界

- Jev 无法听出音色、口气、爆音、房间回声、自然度或口型同步。
- Jev 无法确认字幕是否遮脸、画面是否黑帧、透明素材是否真的有 Alpha、动效是否裁切或抖动。
- Jev 不负责事实查证；`fact_risk` 只能提醒“需要核实”，不能证明内容正确。
- 不把当前聊天关系分析里的 `true_intent`、`danger_level` 等问题直接用于视频编辑。
- 不向模型发送整段视频。默认发送必要的转写、候选文字、时间和少量统计；姓名、电话、地址、客户信息等先脱敏。
- 适配器默认替换手机号、邮箱、身份证号和 URL 查询串；`--no-redact` 只在确认输入没有敏感信息时使用。姓名和地址无法可靠用正则识别，仍需调用方在输入前处理。
- 请求按 2–3 个候选 take 或 5–15 秒语义段批量进行，不逐帧、逐词调用。
- 低置信度、概率接近或模型不可用时，保留原有工作流并进入人工复核，不阻断普通成片流程。

## 密钥和客户端

Jev key 只能通过环境变量提供，例如 `JEV_API_KEY`。不同旧项目还出现过 `TYPESAFE_API_KEY` 和 `OPENROUTER_API_KEY`，接入时由适配器显式映射，不把命名差异传播到视频 skill。绝不把 key 写入 review JSON、日志、截图或交付文件。

当前适配器只依赖 Jev 客户端的 `ask(state, questions, timeout, provider, model)` 形状。TypeSafe 直连建议使用 `provider=typesafe`、`model=jev-1.14.0`；OpenRouter 建议使用该来源的 `typesafe/jev-1.14` 默认模型。

TypeSafe 直连需要运行环境中可导入官方 `typesafe_sdk`，并且 `JEV_CLIENT_PATH` 指向包含 `jev_client.py` 的 Jev 客户端；没有 SDK 时可以改用客户端自带的 OpenRouter 路径。两种方式都不是本地离线模型，缺少客户端、key 或网络时会按 `disabled/partial` 降级，不把安装依赖设为成片前置条件。

## Claude Code 入口

Claude Code 从 `%USERPROFILE%\.claude\skills\jev-video-review\` 发现本 skill。Claude 侧优先复用现有 `/jev` MCP skill 和 `jev-1.14.0`：

- `take`：用 `jev_decide` 在 2–6 个已经人工复听的 take 中做有边界的选择。
- `motion`：用 `jev_classify` 批量判断语义段角色，再用 `jev_decide` 选择 `full`、`stage` 或 `pip`。
- `script`：用 `jev_compare`、`jev_noul` 或 `jev_rerank` 检查开头、承诺兑现、事实风险和重复度。

不要在这个 skill 中新增 `mcpServers`、API key 或 provider 配置；现有 `/jev` skill 已经提供 MCP server。Claude 的 MCP 结果仍然只作为建议，必须保留概率、confidence 和人工复核门槛。若用户明确使用本机 `lead-media-edit` 文件链路，再调用 `scripts/jev_video_review.py`；否则不重复运行本地客户端。
