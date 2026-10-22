// 每条视频改这里：素材、时长、人物位置、人物状态切换、音效表（时间为粗剪成片秒数）
import type { Mode } from "./engine/Presenter";
import type { Cue } from "./engine/Sfx";
import type { MotionCue } from "./engine/StageOverlay";
import sfx from "./sfx.json";
import motionCues from "./data/motion-cues.json";

export const FPS = 60000 / 1001; // 与 rough.mp4 一致
export const DURATION = 10; // rough.mp4 时长（秒）
export const VIDEO = "rough.mp4"; // public/rough.mp4
// 原画面中人物头肩中心与半径（1920×1080 设计坐标）：抽帧确认
export const FACE = { x: 960, y: 470, r: 300 };

export const MODES: Mode[] = [
  { t: 0, mode: "full" },
  { t: 0.25, mode: "stage", dur: 0.42 },
  { t: 6.5, mode: "pip", dur: 0.62 },
  { t: 9.2, mode: "full", dur: 0.62 },
];

export const SFX = sfx as Cue[];
export const CUES = motionCues as MotionCue[];
