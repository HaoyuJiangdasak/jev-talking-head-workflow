# -*- coding: utf-8 -*-
"""从 Whisper 字级转写生成可人工复核的 motion-cues.json。

这是候选生成器，不会替用户决定最终画面。它把“第一步/下一步/问题/数字/产品名”等
语义信号映射成稳定、低密度的 cue，供 Remotion 的 StageOverlay 使用。

用法：
  python build_motion_cues.py transcript_rough.json motion-cues.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NUMBER_RE = re.compile(r"(?:\d+(?:\.\d+)?\s*(?:万|亿|倍|%|分钟|秒|个|条|步))")
STEP_RE = re.compile(r"(?:第[一二三四五六七八九十\d]+步|首先|下一步|第二个问题|第三个问题|第一点|第二点|第三点)")
TOOL_RE = re.compile(r"(?:ChatGPT|Claude|GPT|飞书妙记|飞书|Notion|MCP|GEO|Figma|AI|Agent|抖音|手机)", re.I)
WARNING_RE = re.compile(r"(?:问题|关键|注意|最重要|核查|事实|错误|不能|不要|重中之重)")


def clean(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def first_word(words: list[dict], start: float, end: float) -> dict | None:
    for w in words:
        if float(w.get("e", 0)) >= start and float(w.get("s", 0)) <= end:
            return w
    return None


def cue_for(segment: dict, words: list[dict], match: re.Match[str], kind: str) -> dict:
    text = clean(segment.get("text", ""))
    s = float(segment.get("s", 0))
    e = float(segment.get("e", s + 3))
    hit = match.group(0)
    hit_index = max(0, text.find(hit))
    # 字级时间近似：按字符位置从 segment 起止时间内插，再用相邻 word 修正。
    ratio = hit_index / max(1, len(text))
    target = s + (e - s) * ratio
    w = first_word(words, target - 0.35, target + 0.35)
    start = max(0.0, (float(w.get("s", target)) if w else target) - 0.08)
    duration = min(5.2, max(2.2, e - start + 0.55))
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", hit).strip("-") or "cue"
    cue = {
        "id": f"auto-{kind}-{slug}-{int(start * 1000)}",
        "start": round(start, 3),
        "duration": round(duration, 3),
        "kind": kind,
        "side": "auto",
        "title": hit,
        "body": text[:48],
        "accent": "coral" if kind == "steps" else "teal" if kind == "metric" else "amber",
        "source": {"segment_start": round(s, 3), "segment_end": round(e, 3), "trigger": hit},
    }
    if kind == "metric":
        cue["value"] = hit
    if kind == "steps":
        cue["items"] = [hit]
    if kind == "device":
        cue["body"] = f"围绕“{hit}”展开画面"
    return cue


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("out")
    ap.add_argument("--min-gap", type=float, default=2.2)
    ap.add_argument("--repeat-cooldown", type=float, default=10.0, help="同一触发词再次出现前至少间隔秒数")
    args = ap.parse_args()
    data = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    words = data.get("words", [])
    candidates: list[dict] = []
    for segment in data.get("segments", []):
        text = clean(segment.get("text", ""))
        patterns = [(NUMBER_RE, "metric"), (STEP_RE, "steps"), (TOOL_RE, "device"), (WARNING_RE, "feature-card")]
        found = []
        for pattern, kind in patterns:
            m = pattern.search(text)
            if m:
                found.append((m.start(), m, kind))
        if found:
            _, match, kind = sorted(found, key=lambda item: item[0])[0]
            candidates.append(cue_for(segment, words, match, kind))

    candidates.sort(key=lambda c: c["start"])
    cues: list[dict] = []
    last_by_key: dict[tuple[str, str], float] = {}
    for cue in candidates:
        key = (cue["kind"], cue.get("title", ""))
        if cue["start"] - last_by_key.get(key, -1e9) < args.repeat_cooldown:
            continue
        if cues and cue["start"] - cues[-1]["start"] < args.min_gap:
            # 保留更具体的数字/步骤 cue，丢弃同一语义窗口内的泛化卡片。
            priority = {"metric": 4, "steps": 3, "device": 2, "feature-card": 1}
            if priority.get(cue["kind"], 0) > priority.get(cues[-1]["kind"], 0):
                cues[-1] = cue
                last_by_key[key] = cue["start"]
            continue
        cues.append(cue)
        last_by_key[key] = cue["start"]

    Path(args.out).write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"候选 cue: {len(cues)}，已写入 {args.out}")
    if not cues:
        print("未找到语义触发词；请手写 motion-cues.json，或补充专有名词后重跑。")


if __name__ == "__main__":
    main()
