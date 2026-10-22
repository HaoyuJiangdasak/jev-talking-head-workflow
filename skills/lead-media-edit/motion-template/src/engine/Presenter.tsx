import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { E, clamp, invLerp, lerp } from "./ease";
import { C, PIP } from "./theme";

export type Mode = { t: number; mode: "full" | "pip" | "stage"; dur?: number };
export type Face = { x: number; y: number; r: number };
export type FaceKeyframe = Face & { t: number };
export type FaceSpec = Face | FaceKeyframe[];

export const faceAt = (t: number, spec: FaceSpec): Face => {
  if (!Array.isArray(spec) || spec.length === 0) return spec as Face;
  if (t <= spec[0].t) return spec[0];
  for (let i = 0; i < spec.length - 1; i++) {
    const a = spec[i];
    const b = spec[i + 1];
    if (t <= b.t) {
      const k = clamp((t - a.t) / Math.max(0.001, b.t - a.t));
      return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), r: lerp(a.r, b.r, k) };
    }
  }
  return spec[spec.length - 1];
};

/**
 * 人物本身的状态：full/stage 都保持原始全屏人物，只有 pip 才缩成圆环。
 * stage 用来承载“人物在中央、动效在人物周围”的口播编排。
 */
export const presenterProgress = (t: number, modes: Mode[]) => {
  let v = modes[0].mode === "pip" ? 1 : 0;
  for (let i = 1; i < modes.length; i++) {
    const m = modes[i];
    const target = m.mode === "pip" ? 1 : 0;
    const d = m.dur ?? 0.62;
    if (t < m.t) break;
    const k = E.inOutQuint(clamp((t - m.t) / d));
    v = lerp(v, target, k);
  }
  return v;
};

/** 动效舞台状态：pip/stage 都允许周围的图形和卡片出现。 */
export const overlayProgress = (t: number, modes: Mode[]) => {
  let v = modes[0].mode === "pip" || modes[0].mode === "stage" ? 1 : 0;
  for (let i = 1; i < modes.length; i++) {
    const m = modes[i];
    const target = m.mode === "pip" || m.mode === "stage" ? 1 : 0;
    const d = m.dur ?? 0.62;
    if (t < m.t) break;
    const k = E.inOutQuint(clamp((t - m.t) / d));
    v = lerp(v, target, k);
  }
  return v;
};

/** 旧接口别名，保持现有场景代码兼容。 */
export const pipProgress = presenterProgress;

/** 全屏段落的缓慢推近，避免长时间静止画面 */
const fullPush = (t: number, modes: Mode[]) => {
  for (let i = 0; i < modes.length; i++) {
    const a = modes[i];
    const b = modes[i + 1];
    const end = b ? b.t : a.t + 30;
    if (a.mode === "full" && t >= a.t && t < end + 0.7) return 1 + 0.045 * E.inOutCubic(invLerp(a.t, end + 0.7, t));
  }
  return 1;
};

export const Presenter: React.FC<{
  t: number;
  modes: Mode[];
  src: string;
  face: FaceSpec;
}> = ({ t, modes, src, face }) => {
  const e = presenterProgress(t, modes);
  const currentFace = faceAt(t, face);
  const sFull = fullPush(t, modes);
  const sPip = PIP.r / currentFace.r;
  const s = Math.exp(lerp(Math.log(sFull), Math.log(sPip), e));
  const ax = lerp(currentFace.x, PIP.x, e);
  const ay = lerp(currentFace.y, PIP.y, e);
  const tx = ax - currentFace.x * s;
  const ty = ay - currentFace.y * s;
  const r = Math.exp(lerp(Math.log(1400), Math.log(PIP.r), e));
  const ringA = clamp((e - 0.55) / 0.45);
  const spin = t * 22;

  return (
    <AbsoluteFill>
      {/* 落影 */}
      <div
        style={{
          position: "absolute",
          left: ax - r,
          top: ay - r,
          width: r * 2,
          height: r * 2,
          borderRadius: "50%",
          boxShadow: `0 ${18 * ringA}px ${60 * ringA}px rgba(0,0,0,${0.55 * ringA})`,
        }}
      />
      <AbsoluteFill style={{ clipPath: `circle(${r}px at ${ax}px ${ay}px)` }}>
        <OffthreadVideo
          src={staticFile(src)}
          muted
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: 1920,
            height: 1080,
            transform: `translate(${tx}px, ${ty}px) scale(${s})`,
            transformOrigin: "0 0",
          }}
        />
        {/* 缩小后轻微压暗边缘，让人物融入深色 B-roll */}
        <div
          style={{
            position: "absolute",
            left: ax - r,
            top: ay - r,
            width: r * 2,
            height: r * 2,
            borderRadius: "50%",
            background: `radial-gradient(circle, rgba(0,0,0,0) 62%, rgba(5,13,22,${0.45 * ringA}) 100%)`,
          }}
        />
      </AbsoluteFill>
      {ringA > 0 && (
        <svg
          width={r * 2 + 40}
          height={r * 2 + 40}
          style={{ position: "absolute", left: ax - r - 20, top: ay - r - 20, opacity: ringA, overflow: "visible" }}
        >
          <circle cx={r + 20} cy={r + 20} r={r} fill="none" stroke={C.paper} strokeOpacity={0.92} strokeWidth={3} />
          <g transform={`rotate(${spin} ${r + 20} ${r + 20})`}>
            <circle
              cx={r + 20}
              cy={r + 20}
              r={r + 11}
              fill="none"
              stroke={C.amber}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeDasharray={`${(r + 11) * 0.9} ${(r + 11) * 5.4}`}
            />
            <circle
              cx={r + 20}
              cy={r + 20}
              r={r + 11}
              fill="none"
              stroke={C.paper}
              strokeOpacity={0.35}
              strokeWidth={1.2}
              strokeDasharray="2 9"
            />
          </g>
        </svg>
      )}
    </AbsoluteFill>
  );
};
