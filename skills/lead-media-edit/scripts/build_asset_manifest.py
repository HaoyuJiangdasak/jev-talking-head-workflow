# -*- coding: utf-8 -*-
"""盘点 motion 工程 public/ 中的图片、视频、透明素材和字体。"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}


def probe(path: Path) -> dict:
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,pix_fmt:format=duration", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        data = json.loads(p.stdout or "{}")
        stream = (data.get("streams") or [{}])[0]
        duration = (data.get("format") or {}).get("duration")
        return {
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": round(float(duration), 3) if duration else None,
            "pix_fmt": stream.get("pix_fmt"),
        }
    except Exception:
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("public")
    ap.add_argument("out")
    args = ap.parse_args()
    root = Path(args.public).resolve()
    items = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        ext = path.suffix.lower()
        if ext in IMAGE_EXT:
            kind = "image"
        elif ext in VIDEO_EXT:
            kind = "video"
        elif ext in FONT_EXT:
            kind = "font"
        else:
            continue
        info = probe(path) if kind in {"image", "video"} else {}
        pix_fmt = info.get("pix_fmt") or ""
        items.append({
            "path": rel,
            "kind": kind,
            "bytes": path.stat().st_size,
            "width": info.get("width"),
            "height": info.get("height"),
            "duration": info.get("duration"),
            "has_alpha": ext in {".png", ".webp", ".svg", ".webm"} or "a" in pix_fmt,
        })
    out = {"root": "public", "assets": items}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"asset manifest: {len(items)} files -> {args.out}")


if __name__ == "__main__":
    main()
