# -*- coding: utf-8 -*-
"""Jev semantic review adapter for talking-head video workflows.

This script never edits an EDL, transcript, timeline, or render.  It reads a
review input JSON, asks a Jev client for typed judgments, and writes an
auditable review JSON.  When the client is unavailable it degrades to a
disabled/partial report so the normal editing workflow can continue.

Supported stages: take, motion, script.
The Jev client must expose ask(state, questions, timeout=..., provider=...,
model=...).  Configure JEV_CLIENT_PATH when the module is not importable.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
ADAPTER_VERSION = "1.0.0"
DEFAULT_MODEL = {"typesafe": "jev-1.14.0", "openrouter": "typesafe/jev-1.14"}
PII_PATTERNS = (
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[PHONE]"),
    (re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?![\w.-])"), "[EMAIL]"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[ID_NUMBER]"),
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("输入 JSON 必须是对象")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def redact_text(value: str) -> str:
    result = value
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    # Query strings often contain tokens, phone numbers or contact identifiers.
    result = re.sub(r"(?i)(https?://[^\s?]+)\?[^\s]+", r"\1?[QUERY_REDACTED]", result)
    return result


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_payload(item) for key, item in value.items()}
    return value


def validate_payload(stage: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    declared = payload.get("stage")
    if declared and declared != stage:
        raise ValueError(f"输入 stage={declared!r} 与命令行 --stage={stage!r} 不一致")
    segments = payload.get("segments")
    if stage == "script":
        hooks = payload.get("hooks") or []
        if not isinstance(hooks, list) or not 2 <= len(hooks) <= 3:
            raise ValueError("script 阶段需要 2–3 个 hooks")
        if not segments:
            return [{"id": "script"}]
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments 必须是非空数组")
    for index, item in enumerate(segments):
        if not isinstance(item, dict) or not item.get("id"):
            if stage == "motion" and isinstance(item, dict):
                item.setdefault("id", f"seg-{index + 1:03d}")
            else:
                raise ValueError("每个 segment 必须是带 id 的对象")
        if stage == "take":
            alternatives = item.get("alternatives") or []
            if not isinstance(alternatives, list) or len(alternatives) < 2:
                raise ValueError(f"take 段落 {item.get('id')} 至少需要 2 个已复听候选")
            for alternative in alternatives:
                if not isinstance(alternative, dict) or not alternative.get("id"):
                    raise ValueError(f"take 段落 {item.get('id')} 的候选必须带 id")
        elif stage == "motion":
            item.setdefault("start", item.get("s"))
            item.setdefault("end", item.get("e"))
            item.setdefault("text", item.get("text", ""))
            item.setdefault("candidate_emphasis", [])
            emphasis = item.get("candidate_emphasis") or []
            if not isinstance(emphasis, list) or len(emphasis) > 3:
                raise ValueError(f"motion 段落 {item.get('id')} 的 candidate_emphasis 最多 3 个")
            try:
                start = float(item.get("start"))
                end = float(item.get("end"))
            except (TypeError, ValueError):
                raise ValueError(f"motion 段落 {item.get('id')} 缺少有效 start/end") from None
            if end <= start or not _text(item.get("text")):
                raise ValueError(f"motion 段落 {item.get('id')} 的 start/end/text 无效")
    return segments


def load_jev_client(path_arg: str | None):
    """Load a Jev client module without assuming one project layout."""
    path_text = path_arg or os.environ.get("JEV_CLIENT_PATH", "").strip()
    if path_text:
        path = Path(path_text).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"JEV_CLIENT_PATH 不存在: {path}")
        # The known Jev projects keep jev_client.py under a package named core.
        # Add the package parent first so relative imports such as .providers work.
        if path.parent.name == "core":
            package_parent = path.parent.parent
            sys.path.insert(0, str(package_parent))
            return importlib.import_module(f"core.{path.stem}")
        spec = importlib.util.spec_from_file_location("jev_client_external", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 Jev 客户端: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    try:
        return importlib.import_module("jev_client")
    except Exception as exc:
        raise ImportError(
            "找不到 Jev 客户端。请设置 JEV_CLIENT_PATH，或把 jev_client.py 放入 Python import path。"
        ) from exc


def _text(value: Any) -> str:
    return str(value or "").strip()


def _prob(answer: dict[str, Any], choice: str) -> float:
    probs = answer.get("probabilities") or {}
    try:
        return float(probs.get(choice, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _confidence(answer: dict[str, Any]) -> float:
    try:
        return float(answer.get("confidence", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _answer(result: dict[str, Any], name: str) -> dict[str, Any]:
    answers = result.get("answers") or {}
    value = answers.get(name)
    return value if isinstance(value, dict) else {}


def _choice_question(instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "满足问题描述，并且证据在输入状态中可见。",
            "false": "不满足问题描述，或输入状态不足以支持肯定判断。",
        },
    }


def _score_question(instructions: str, criteria: list[str]) -> dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


def take_questions(alternatives: list[dict[str, Any]]) -> dict[str, Any]:
    criteria = {
        str(item.get("id", f"candidate_{i}")): (
            f"候选 {item.get('id', i)}：{_text(item.get('text'))}。"
            "完整保留目标意思，保留必要的否定词、条件词、数字和连接关系；"
            "切点自然，不能用多个半句拼出不存在的句子。"
        )
        for i, item in enumerate(alternatives)
    }
    criteria["human_review"] = "候选之间无法可靠区分，或需要人工复听后再决定。"
    return {
        "best_take": _choice_question(
            "从候选 take 中选择最完整、最正确、最自然衔接的一条。不要因为某个候选转写更短就偏好它；遇到证据不足请选择 human_review。",
            criteria,
        ),
        "is_retake_or_filler": _noul_question(
            "该候选组是否包含重复起句、明显重说、无意义口头禅或没有完成的残留片段？"
        ),
        "sentence_complete": _score_question(
            "目标句在语义、语法和听感上是否完整，0 表示明显残句，9 表示完整且可自然接上下文。",
            [
                "明显残句、缺主语/谓语/结论，不能独立理解。",
                "需要上下文才能勉强理解，衔接风险很高。",
                "部分完整，但有明显缺词或突然截断。",
                "基本完整，但需要人工复听确认切点。",
                "完整可懂，仍有轻微衔接风险。",
                "完整、正确、自然，适合进入粗剪候选。",
                "完整且表达清楚，衔接顺畅。",
                "表达非常稳定，适合作为最终 take。",
                "完整、自然并保留了必要的语气和连接词。",
                "完整度和衔接都很高，几乎没有可见风险。",
            ],
        ),
        "semantic_cut_risk": _score_question(
            "如果在当前候选的边界切出这一段，漏掉否定词、条件词、数字、主语、宾语或连接关系的风险有多高？",
            [
                "0：边界安全，语义没有明显风险。",
                "1：风险很低，仍建议听一遍切点。",
                "2：低风险，可作为候选但保留复核记录。",
                "3：需要人工复听，可能影响衔接。",
                "4：可能漏掉局部限定词或数字。",
                "5：中等风险，不能自动采用。",
                "6：可能改变句意或上下文关系。",
                "7：高风险，疑似半句或错误 take。",
                "8：很高风险，可能反转或破坏观点。",
                "9：不可安全切取，应人工重做 EDL。",
            ],
        ),
    }


def motion_questions(emphasis: list[str]) -> dict[str, Any]:
    return {
        "viewer_job": _choice_question(
            "这段口播对观众承担的主要理解任务是什么？只选一个最主要的任务。",
            {
                "hook": "提出核心问题、结果或冲突，负责让目标观众继续看。",
                "claim": "给出可复述的观点或结论。",
                "step": "解释一个可以跟做的步骤或流程。",
                "evidence": "给出数字、事实、对比或可核实的依据。",
                "example": "用具体例子帮助观众理解抽象观点。",
                "contrast": "推翻直觉、比较两种情况或处理异议。",
                "cta": "只负责一个明确的结尾行动。",
                "transition": "连接上下文，不承担新的主要信息。",
            },
        ),
        "visual_mode": _choice_question(
            "这段最适合使用哪种人物状态？只按信息密度和观众理解任务选择，不为了有动效而选择复杂状态。",
            {
                "full": "人物全屏，适合态度、过渡、情绪、CTA 或不需要额外解释的句子。",
                "stage": "人物保持中央，卡片、数字、步骤或 callout 在周围同步出现。",
                "pip": "人物缩成圆环，让位给大面积 UI、截图、流程或全屏 B-roll。",
            },
        ),
        "cue_priority": _score_question(
            "这段是否值得消耗一个主要视觉 cue？0 表示让人物自然说完，5 表示画面是理解这段的关键。",
            [
                "0：过渡或态度句，不需要独立画面。",
                "1：有轻微信息变化，人物全屏即可。",
                "2：可用一个简短关键词或轻量叠加。",
                "3：视觉能明显帮助理解。",
                "4：数字、流程或例子值得明确展示。",
                "5：没有视觉解释就很难理解，应设计主要 cue。",
            ],
        ),
        "emphasis_target": _choice_question(
            "从候选短语中选出最值得强调的一个。只能选择输入中已有的短语，不得改写数字或生成新事实。",
            {f"emphasis_{i}": value for i, value in enumerate(emphasis[:3])} | {
                "none": "没有一个短语值得单独放大，保持普通字幕。"
            },
        ),
    }


def script_questions(hooks: list[str]) -> dict[str, Any]:
    return {
        "best_hook": _choice_question(
            "从候选开头中选择最容易让目标观众识别问题、且正文最容易兑现的一条。不要因为夸张而偏好它。",
            {f"hook_{i}": value for i, value in enumerate(hooks[:3])} | {
                "human_review": "候选开头需要人工比较或事实核实。"
            },
        ),
        "promise_fulfilled": _noul_question(
            "正文是否真正回答了开头提出的问题，并给出至少一个具体例子、边界或可执行动作？"
        ),
        "audience_fit": _score_question(
            "目标受众是否具体，且前两句就能识别这是在解决他们的问题？",
            [
                "受众完全不清楚，像对所有人说。",
                "受众很宽，只能大致猜到。",
                "主题清楚，但使用场景不够具体。",
                "受众和问题基本清楚。",
                "受众、场景和阻碍都明确。",
                "受众非常具体，开头就能识别自己的问题。",
            ],
        ),
        "fact_risk": _noul_question(
            "稿件是否包含需要用户提供来源、真实经历、截图、数据或发布前核实的事实？"
        ),
        "redundancy_risk": _score_question(
            "稿件中是否多次用不同说法重复同一个观点，导致中段没有新的信息？",
            [
                "没有明显重复，每段都推进新信息。",
                "有轻微重复，不影响观看。",
                "有一处重复，建议压缩。",
                "多处重复，中段节奏会变慢。",
                "大量重复，需要重新组织结构。",
                "几乎没有增量信息，必须重写。",
            ],
        ),
    }


def build_state(stage: str, payload: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    video = payload.get("video") or {}
    if stage == "take":
        return {
            "task": "口播粗剪候选 take 语义评审",
            "video": video,
            "segment": {
                "id": item.get("id"),
                "canonical_text": item.get("canonical_text"),
                "previous_text": item.get("previous_text"),
                "next_text": item.get("next_text"),
                "must_keep": item.get("must_keep") or [],
                "alternatives": item.get("alternatives") or [],
                "evidence": item.get("evidence") or {},
            },
            "constraints": {
                "do_not_stitch_unfinished_fragments": True,
                "preserve_negations_numbers_conditions": True,
                "model_only_recommends": True,
            },
        }
    if stage == "script":
        return {
            "task": "口播文案结构化评审",
            "video": video,
            "script": {
                "title_candidates": payload.get("titles") or [],
                "hooks": payload.get("hooks") or [],
                "promise": payload.get("promise") or payload.get("one_sentence_promise"),
                "body": payload.get("script_text") or payload.get("body"),
                "known_facts": payload.get("known_facts") or [],
                "needs_verification": payload.get("needs_verification") or [],
            },
            "constraints": {
                "do_not_invent_facts": True,
                "do_not_change_author_position": True,
                "model_only_recommends": True,
            },
        }
    return {
        "task": "口播视频语义段落评审",
        "video": video,
        "segment": item,
        "constraints": {
            "use_only_input_facts": True,
            "do_not_invent_assets_or_numbers": True,
            "model_only_recommends": True,
        },
    }


def review_item(client, stage: str, payload: dict[str, Any], item: dict[str, Any],
                provider: str, model: str, timeout: float) -> dict[str, Any]:
    if stage == "take":
        alternatives = item.get("alternatives") or []
        questions = take_questions(alternatives)
    elif stage == "motion":
        questions = motion_questions(item.get("candidate_emphasis") or [])
    else:
        questions = script_questions(payload.get("hooks") or [])
    result = client.ask(build_state(stage, payload, item), questions,
                         timeout=timeout, provider=provider, model=model)
    answers = result.get("answers") or {}
    recommendation: dict[str, Any] = {
        "segment_id": item.get("id"),
        "answers": answers,
        "model": result.get("model") or model,
        "usage": result.get("usage") or {},
        "review_required": True,
        "decision": "human_review",
        "reasons": [],
    }
    if stage == "take":
        best = _answer(result, "best_take")
        choice = _text(best.get("choice"))
        probability = _prob(best, choice)
        confidence = _confidence(best)
        risk = _answer(result, "semantic_cut_risk").get("score")
        try:
            risk_value = float(risk)
        except (TypeError, ValueError):
            risk_value = 9.0
        recommendation.update({
            "decision": choice or "human_review",
            "choice_probability": probability,
            "confidence": confidence,
            "semantic_cut_risk": risk_value,
        })
        valid_choices = {str(option.get("id")) for option in item.get("alternatives", [])}
        valid_choices.add("human_review")
        if choice not in valid_choices:
            recommendation["reasons"].append("模型返回了不在候选集中的 choice")
            choice = "human_review"
            recommendation["decision"] = choice
        if not choice or choice == "human_review":
            recommendation["reasons"].append("模型没有可靠选择候选 take")
        if probability < 0.80:
            recommendation["reasons"].append("选择概率低于 0.80")
        if confidence < 0.75:
            recommendation["reasons"].append("confidence 低于 0.75")
        if risk_value > 2:
            recommendation["reasons"].append("语义切点风险高于 2")
        completeness = _answer(result, "sentence_complete").get("score")
        try:
            completeness_value = float(completeness)
        except (TypeError, ValueError):
            completeness_value = 0.0
        filler_value = _answer(result, "is_retake_or_filler").get("noul")
        try:
            filler_probability = float(filler_value)
        except (TypeError, ValueError):
            filler_probability = 1.0
        recommendation["sentence_complete"] = completeness_value
        recommendation["is_retake_or_filler_probability"] = filler_probability
        if completeness_value < 6:
            recommendation["reasons"].append("句子完整度低于 6")
        if filler_probability >= 0.35:
            recommendation["reasons"].append("疑似重说、口头禅或残留片段")
        recommendation["review_required"] = bool(recommendation["reasons"])
        if not recommendation["review_required"]:
            recommendation["decision"] = "candidate_keep"
    elif stage == "motion":
        for name in ("viewer_job", "visual_mode", "emphasis_target"):
            answer = _answer(result, name)
            if answer.get("choice"):
                choice = _text(answer.get("choice"))
                recommendation[name] = choice
                recommendation[f"{name}_probability"] = _prob(answer, choice)
                recommendation[f"{name}_confidence"] = _confidence(answer)
                if name == "emphasis_target":
                    recommendation["emphasis_target_key"] = choice
                    if choice.startswith("emphasis_"):
                        try:
                            index = int(choice.split("_", 1)[1])
                            options = item.get("candidate_emphasis") or []
                            recommendation[name] = options[index] if 0 <= index < len(options) else None
                        except (TypeError, ValueError):
                            recommendation[name] = None
                    elif choice == "none":
                        recommendation[name] = None
        score = _answer(result, "cue_priority").get("score")
        recommendation["cue_priority"] = score
        recommendation["review_required"] = True
        recommendation["reasons"].append("分镜建议必须结合实际画面、face-boxes 和透明素材复核")
    else:
        best = _answer(result, "best_hook")
        best_key = _text(best.get("choice"))
        best_hook = None
        if best_key.startswith("hook_"):
            try:
                index = int(best_key.split("_", 1)[1])
                hooks = payload.get("hooks") or []
                best_hook = hooks[index] if index < len(hooks) else None
            except (TypeError, ValueError):
                best_hook = None
        recommendation.update({
            "decision": best_hook or "human_review",
            "best_hook_key": best_key,
            "best_hook": best_hook,
            "choice_probability": _prob(best, best_key),
            "confidence": _confidence(best),
        })
        recommendation["review_required"] = True
        recommendation["reasons"].append("文案规则和事实底稿仍然优先于模型排序")
    return recommendation


def disabled_report(stage: str, payload: dict[str, Any], input_sha: str, reason: str,
                    ids: list[str], status: str = "disabled") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "status": status,
        "adapter_version": ADAPTER_VERSION,
        "model": None,
        "input_sha256": input_sha,
        "recommendations": [
            {"segment_id": segment_id, "decision": "human_review", "review_required": True,
             "reasons": [reason]}
            for segment_id in ids
        ],
        "raw_answers": [],
        "review_required": len(ids),
        "notes": [reason, "原有工作流继续执行；不要把 disabled 当作通过。"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Jev 口播视频语义评审")
    parser.add_argument("--stage", choices=("take", "motion", "script"), required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--client-path")
    parser.add_argument("--provider", choices=("typesafe", "openrouter"), default="typesafe")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--cache-dir", type=Path, help="可选的 review JSON 缓存目录")
    parser.add_argument("--redact", action=argparse.BooleanOptionalAction, default=True,
                        help="发送给远程 Jev 前自动替换手机号、邮箱、身份证号和 URL 查询串")
    parser.add_argument("--required", action="store_true", help="Jev 不可用时返回失败码")
    parser.add_argument("--offline", action="store_true", help="只验证输入并写 disabled 报告，不联网")
    args = parser.parse_args()

    payload = load_json(args.input)
    stage = args.stage
    input_sha = sha256_file(args.input)
    model = args.model or DEFAULT_MODEL[args.provider]
    try:
        items = validate_payload(stage, payload)
    except ValueError as exc:
        ids = [str(item.get("id", i)) for i, item in enumerate(payload.get("segments") or [])
               if isinstance(item, dict)] or (["script"] if stage == "script" else [])
        report = disabled_report(stage, payload, input_sha, f"输入无效：{exc}", ids, status="invalid")
        write_json(args.output, report)
        print(f"Jev review: invalid；{exc}")
        return 2 if args.required else 0

    payload_for_jev = redact_payload(payload) if args.redact else payload
    cache_key = hashlib.sha256(
        f"{input_sha}|{stage}|{args.provider}|{model}|{SCHEMA_VERSION}|{ADAPTER_VERSION}|redact={args.redact}".encode("utf-8")
    ).hexdigest()
    cache_path = args.cache_dir / f"{cache_key}.json" if args.cache_dir else None
    if cache_path and cache_path.is_file():
        cached = load_json(cache_path)
        cached["cache_hit"] = True
        write_json(args.output, cached)
        print(f"Jev review: cache hit；已写入 {args.output}")
        return 0

    if args.offline:
        report = disabled_report(stage, payload, input_sha, "offline 模式未调用 Jev",
                                 [str(item.get("id")) for item in items])
        report["cache_key"] = cache_key
        write_json(args.output, report)
        print(f"Jev review: offline；需人工复核 {len(items)} 项；已写入 {args.output}")
        return 0

    try:
        client = load_jev_client(args.client_path)
    except Exception as exc:
        reason = f"Jev 客户端不可用：{exc}"
        report = disabled_report(stage, payload, input_sha, reason,
                                 [str(item.get("id")) for item in items])
        report["cache_key"] = cache_key
        write_json(args.output, report)
        print(f"Jev review: disabled；{reason}")
        return 2 if args.required else 0

    recommendations: list[dict[str, Any]] = []
    errors: list[str] = []
    items_for_jev = payload_for_jev.get("segments") or items
    for item, jev_item in zip(items, items_for_jev):
        if not isinstance(item, dict):
            errors.append("存在不是对象的 segment")
            continue
        try:
            recommendations.append(review_item(client, stage, payload_for_jev, jev_item,
                                               args.provider, model, args.timeout))
        except Exception as exc:
            recommendations.append({
                "segment_id": item.get("id"), "decision": "human_review",
                "review_required": True,
                "reasons": [f"Jev 请求失败：{type(exc).__name__}"],
            })
            errors.append(f"{item.get('id')}: {type(exc).__name__}")

    required_count = sum(1 for item in recommendations if item.get("review_required"))
    status = "ok" if not errors else ("partial" if recommendations else "error")
    report = {
        "schema_version": SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "stage": stage,
        "status": status,
        "model": model,
        "provider": args.provider,
        "input_sha256": input_sha,
        "cache_key": cache_key,
        "cache_hit": False,
        "redacted_before_request": bool(args.redact),
        "recommendations": recommendations,
        "raw_answers": [
            {"segment_id": item.get("segment_id"), "answers": item.get("answers", {})}
            for item in recommendations
        ],
        "review_required": required_count,
        "notes": errors + ["Jev 输出是建议；应用前必须结合原始音频、时间轴和画面复核。"],
    }
    write_json(args.output, report)
    if cache_path and status in {"ok", "partial"}:
        write_json(cache_path, copy.deepcopy(report))
    print(f"Jev review: {status}；需人工复核 {required_count}/{len(items)}；已写入 {args.output}")
    return 2 if args.required and errors else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Jev review failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
