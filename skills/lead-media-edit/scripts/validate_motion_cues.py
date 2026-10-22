# -*- coding: utf-8 -*-
"""校验 motion-cues.json 的时间、安全区和素材引用。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


KINDS = {"title", "metric", "feature-card", "steps", "device", "quote", "tags", "callout"}
SIDES = {"left", "right", "top-left", "top-right", "auto"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cues")
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--public", type=Path, default=None)
    ap.add_argument("--face-boxes", type=Path, default=None, help="可选 JSON：{boxes:[{start,end,x,y,w,h}]}，用于检查卡片是否压脸")
    ap.add_argument("--min-gap", type=float, default=0.35)
    args = ap.parse_args()
    cues = json.loads(Path(args.cues).read_text(encoding="utf-8"))
    if not isinstance(cues, list):
        raise SystemExit("motion cues must be a JSON array")
    errors, warnings = [], []
    face_boxes = []
    if args.face_boxes:
        face_data = json.loads(args.face_boxes.read_text(encoding="utf-8"))
        face_boxes = face_data.get("boxes", [])

    def cue_rect(cue: dict) -> tuple[float, float, float, float]:
        side = cue.get("side", "auto")
        if side == "right" or (side == "auto" and len(cue.get("id", "")) % 2 == 0):
            return (1320, 220, 480, 360)
        if side == "top-right":
            return (1260, 90, 560, 260)
        if side == "top-left":
            return (90, 90, 620, 260)
        return (90, 220, 560, 360)

    def overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
        iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
        return ix * iy / max(1.0, aw * ah)
    last = -1e9
    active_end = -1e9
    for i, c in sorted(enumerate(cues), key=lambda item: float(item[1].get("start", 0)) if isinstance(item[1].get("start"), (int, float)) else 0):
        label = c.get("id", f"#{i}")
        s, d = c.get("start"), c.get("duration")
        if not isinstance(s, (int, float)) or not isinstance(d, (int, float)):
            errors.append(f"{label}: start/duration must be numbers")
            continue
        if s < 0 or d <= 0 or s + d > args.duration + 0.05:
            errors.append(f"{label}: range {s:.3f}-{s+d:.3f} outside duration {args.duration:.3f}")
        if c.get("kind") not in KINDS:
            errors.append(f"{label}: unknown kind {c.get('kind')!r}")
        if c.get("side", "auto") not in SIDES:
            errors.append(f"{label}: side must be one of {sorted(SIDES)}")
        if not c.get("title") and c.get("kind") not in {"metric"}:
            errors.append(f"{label}: title is required")
        if c.get("kind") == "metric" and not c.get("value"):
            errors.append(f"{label}: metric requires value")
        if c.get("kind") in {"steps", "tags"} and not (c.get("items") or c.get("tags")):
            errors.append(f"{label}: {c.get('kind')} requires items/tags")
        if s - last < args.min_gap:
            warnings.append(f"{label}: starts {s-last:.2f}s after previous cue; check clutter")
        if s < active_end:
            warnings.append(f"{label}: overlaps a previous cue for {active_end-s:.2f}s; confirm this is intentional")
        last = s
        active_end = max(active_end, s + d)
        if args.public and c.get("asset") and not (args.public / c["asset"]).exists():
            errors.append(f"{label}: asset not found in public/: {c['asset']}")
        if face_boxes:
            cx, cy, cw, ch = cue_rect(c)
            for fb in face_boxes:
                if float(fb.get("end", 0)) < s or float(fb.get("start", 0)) > s + d:
                    continue
                fx = float(fb.get("x", 0)) - float(fb.get("w", 0)) * 0.2
                fy = float(fb.get("y", 0)) - float(fb.get("h", 0)) * 0.2
                fw = float(fb.get("w", 0)) * 1.4
                fh = float(fb.get("h", 0)) * 1.4
                ratio = overlap((cx, cy, cw, ch), (fx, fy, fw, fh))
                if ratio > 0.15:
                    errors.append(f"{label}: cue overlaps expanded face box by {ratio:.0%}")
                elif ratio > 0:
                    warnings.append(f"{label}: cue touches expanded face box by {ratio:.0%}; check the frame")
    if errors:
        print("motion cues: FAIL")
        for e in errors:
            print("  - " + e)
        return 1
    print(f"motion cues: PASS ({len(cues)} cues)")
    for w in warnings:
        print("  warning: " + w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
