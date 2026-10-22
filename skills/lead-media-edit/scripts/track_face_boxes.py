# -*- coding: utf-8 -*-
"""用本地 OpenCV Haar 检测器生成 face-boxes.json 与 FACE 关键帧。

它只负责给 cue 校验和 Presenter 提供候选安全区，不判断人物身份，也不上传视频。
检测不到脸时返回失败，调用方应抽帧人工标注，而不是假装生成了安全区。
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2


def choose_face(faces, previous):
    if len(faces) == 0:
        return None
    if previous is None:
        return max(faces, key=lambda b: int(b[2]) * int(b[3]))
    px, py, pw, ph = previous
    pcx, pcy = px + pw / 2, py + ph / 2
    return min(faces, key=lambda b: math.hypot((b[0] + b[2] / 2) - pcx, (b[1] + b[3] / 2) - pcy))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--sample-fps", type=float, default=5.0)
    ap.add_argument("--max-width", type=int, default=960)
    ap.add_argument("--min-size", type=int, default=36)
    ap.add_argument("--scale-x", type=float, default=1920 / 1.0, help="设计画布宽度；默认配合 1920x1080")
    ap.add_argument("--scale-y", type=float, default=1080 / 1.0, help="设计画布高度；默认配合 1920x1080")
    args = ap.parse_args()

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"无法打开视频：{args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = total / fps if total else 0
    step = max(1, round(fps / max(0.1, args.sample_fps)))
    detector = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    if detector.empty():
        raise SystemExit("OpenCV Haar 人脸检测器加载失败")

    boxes, keyframes = [], []
    previous = None
    frame_no = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_no % step:
            frame_no += 1
            continue
        scale = min(1.0, args.max_width / max(1, frame.shape[1]))
        sample = cv2.resize(frame, None, fx=scale, fy=scale) if scale < 1 else frame
        gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(args.min_size, args.min_size))
        if len(faces):
            # 转回原始视频坐标，避免缩放影响时间段安全区。
            faces = [(round(x / scale), round(y / scale), round(w / scale), round(h / scale)) for x, y, w, h in faces]
            selected = choose_face(faces, previous)
            previous = selected
            t = frame_no / fps
            x, y, w, h = selected
            boxes.append({"start": round(t, 3), "end": round(min(duration, t + step / fps), 3), "x": x, "y": y, "w": w, "h": h})
            sx, sy = 1920 / max(1, width), 1080 / max(1, height)
            keyframes.append({"t": round(t, 3), "x": round((x + w / 2) * sx, 2), "y": round((y + h / 2) * sy, 2), "r": round(max(w, h) * 0.78 * max(sx, sy), 2)})
        frame_no += 1
    cap.release()
    if not boxes:
        raise SystemExit("没有检测到人脸；请抽帧人工建立 face-boxes.json")

    result = {"video": str(args.video), "width": width, "height": height, "fps": fps, "boxes": boxes, "face_keyframes": keyframes}
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"face boxes: {len(boxes)} samples; duration={duration:.3f}s; output={args.out}")


if __name__ == "__main__":
    main()
