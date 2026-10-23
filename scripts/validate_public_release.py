from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2", ".png", ".jpg", ".jpeg", ".mp4", ".mov", ".mkv", ".wav", ".mp3", ".m4a", ".pyc"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"gho_[A-Za-z0-9_]{10,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{10,}"),
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY"),
    re.compile(r"(?:JEV|TYPESAFE|OPENROUTER|ANTHROPIC)_API_KEY\s*[:=]\s*[A-Za-z0-9_\"']{12,}", re.I),
]
PRIVATE_PATH_MARKERS = ["C:\\Users\\", "D:\\UserFiles\\Documents\\Codex\\", ".claude\\settings.json"]
FORBIDDEN_PARTS = {"__pycache__", ".jev-cache", "node_modules", ".git"}


def main() -> int:
    errors: list[str] = []
    files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]
    for path in files:
        rel = path.relative_to(ROOT)
        if any(part in FORBIDDEN_PARTS for part in rel.parts):
            errors.append(f"forbidden directory: {rel}")
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"secret pattern in {rel}: {pattern.pattern}")
        for marker in PRIVATE_PATH_MARKERS:
            if marker in text:
                errors.append(f"private path marker in {rel}: {marker}")
    if errors:
        print("PUBLIC RELEASE CHECK: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PUBLIC RELEASE CHECK: PASS ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
