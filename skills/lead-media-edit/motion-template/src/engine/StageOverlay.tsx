import React from "react";
import { staticFile } from "remotion";
import { E, clamp, env, ramp } from "./ease";
import { C } from "./theme";
import { NUM, SANS, SERIF } from "./fonts";

export type CueKind = "title" | "metric" | "feature-card" | "steps" | "device" | "quote" | "tags" | "callout";
export type CueSide = "left" | "right" | "top-left" | "top-right" | "auto";

export type MotionCue = {
  id: string;
  start: number;
  duration: number;
  kind: CueKind;
  side?: CueSide;
  title?: string;
  body?: string;
  value?: string;
  items?: string[];
  tags?: string[];
  accent?: "amber" | "teal" | "coral";
  asset?: string;
  target?: { x: number; y: number };
};

const accentColor = (cue: MotionCue) => {
  if (cue.accent === "teal") return C.teal;
  if (cue.accent === "coral") return C.coral;
  return C.amber;
};

const sideFor = (cue: MotionCue) => cue.side && cue.side !== "auto" ? cue.side : cue.id.length % 2 ? "left" : "right";

const boxFor = (cue: MotionCue) => {
  const side = sideFor(cue);
  if (side === "right") return { left: 1320, top: 220, width: 480, align: "left" as const };
  if (side === "top-right") return { left: 1260, top: 90, width: 560, align: "left" as const };
  if (side === "top-left") return { left: 90, top: 90, width: 620, align: "left" as const };
  return { left: 90, top: 220, width: 560, align: "left" as const };
};

const wrapStyle: React.CSSProperties = {
  position: "absolute",
  pointerEvents: "none",
  transformOrigin: "center center",
};

const AssetPreview: React.FC<{ cue: MotionCue }> = ({ cue }) => {
  if (!cue.asset) return null;
  return (
    <img
      src={staticFile(cue.asset)}
      alt=""
      style={{ width: "100%", maxHeight: 230, objectFit: "contain", objectPosition: "left center", display: "block", marginBottom: 14, borderRadius: 12, border: `1px solid ${C.grid}` }}
    />
  );
};

const Panel: React.FC<{ cue: MotionCue; t: number; children: React.ReactNode; compact?: boolean }> = ({ cue, t, children, compact }) => {
  const inA = cue.start;
  const inB = cue.start + Math.min(0.42, cue.duration * 0.22);
  const outA = cue.start + cue.duration - Math.min(0.38, cue.duration * 0.18);
  const outB = cue.start + cue.duration;
  const opacity = env(t, inA, inB, outA, outB, E.outCubic);
  if (opacity <= 0) return null;
  const k = ramp(t, inA, inB, E.outExpo);
  const out = ramp(t, outA, outB, E.inCubic);
  const box = boxFor(cue);
  const accent = accentColor(cue);
  const x = (1 - k) * (sideFor(cue) === "right" || sideFor(cue) === "top-right" ? 44 : -44);
  const y = (1 - k) * 18;
  const scale = 0.96 + 0.04 * E.outBack(k);
  return (
    <div
      style={{
        ...wrapStyle,
        left: box.left,
        top: box.top,
        width: box.width,
        opacity: opacity * (1 - 0.14 * out),
        transform: `translate(${x}px, ${y}px) scale(${scale})`,
        color: C.paper,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: compact ? 16 : 22,
          background: "rgba(5, 16, 27, 0.88)",
          border: `1px solid ${accent}88`,
          boxShadow: `0 18px 48px rgba(0,0,0,0.28), 0 0 0 1px rgba(255,255,255,0.04) inset`,
          backdropFilter: "blur(8px)",
        }}
      />
      <div style={{ position: "relative", padding: compact ? "18px 20px" : "22px 24px" }}>{children}</div>
    </div>
  );
};

const CueView: React.FC<{ cue: MotionCue; t: number }> = ({ cue, t }) => {
  const accent = accentColor(cue);
  const title = cue.title ?? "";
  if (cue.kind === "metric") {
    return (
      <Panel cue={cue} t={t}>
        <div style={{ fontFamily: SANS, fontSize: 24, color: C.muted, marginBottom: 6 }}>{title}</div>
        <div style={{ fontFamily: NUM, fontSize: 76, lineHeight: 0.98, fontWeight: 600, color: accent, letterSpacing: -2 }}>{cue.value}</div>
        {cue.body && <div style={{ fontFamily: SANS, fontSize: 26, marginTop: 12, color: C.paper }}>{cue.body}</div>}
      </Panel>
    );
  }
  if (cue.kind === "title") {
    return (
      <Panel cue={cue} t={t} compact>
        <div style={{ fontFamily: SERIF, fontWeight: 900, fontSize: 64, lineHeight: 1.08 }}>{title}</div>
        {cue.body && <div style={{ fontFamily: SANS, fontSize: 25, color: C.muted, marginTop: 12 }}>{cue.body}</div>}
      </Panel>
    );
  }
  if (cue.kind === "steps") {
    const items = cue.items ?? [];
    const progress = ramp(t, cue.start, cue.start + cue.duration * 0.72, E.outCubic);
    return (
      <Panel cue={cue} t={t}>
        <div style={{ fontFamily: SANS, fontSize: 25, fontWeight: 600, marginBottom: 14 }}>{title}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {items.map((item, i) => {
            const p = clamp(progress * items.length - i);
            return (
              <div key={`${cue.id}-${i}`} style={{ display: "flex", alignItems: "center", gap: 12, opacity: 0.35 + 0.65 * p, transform: `translateX(${(1 - p) * 18}px)` }}>
                <span style={{ display: "inline-flex", width: 30, height: 30, alignItems: "center", justifyContent: "center", borderRadius: "50%", background: `${accent}22`, border: `1px solid ${accent}aa`, color: accent, fontFamily: NUM, fontWeight: 600 }}>{i + 1}</span>
                <span style={{ fontFamily: SANS, fontSize: 26 }}>{item}</span>
              </div>
            );
          })}
        </div>
      </Panel>
    );
  }
  if (cue.kind === "tags") {
    return (
      <Panel cue={cue} t={t} compact>
        <div style={{ fontFamily: SANS, fontSize: 24, fontWeight: 600, marginBottom: 12 }}>{title}</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {(cue.tags ?? cue.items ?? []).map((tag, i) => <span key={`${cue.id}-${i}`} style={{ fontFamily: SANS, fontSize: 23, color: C.paper, border: `1px solid ${accent}88`, background: `${accent}18`, borderRadius: 999, padding: "7px 13px" }}>{tag}</span>)}
        </div>
      </Panel>
    );
  }
  if (cue.kind === "device") {
    return (
      <Panel cue={cue} t={t}>
        <AssetPreview cue={cue} />
        <div style={{ display: "flex", gap: 18, alignItems: "center" }}>
          <div style={{ width: 86, height: 138, borderRadius: 18, border: `2px solid ${accent}`, background: "linear-gradient(150deg, #19334a, #07131f)", boxShadow: `0 0 0 5px ${accent}16` }}>
            <div style={{ height: 7, width: 28, borderRadius: 8, background: `${accent}88`, margin: "9px auto" }} />
            <div style={{ margin: "26px 12px 0", height: 7, background: `${accent}aa`, borderRadius: 4 }} />
            <div style={{ margin: "12px 12px 0", height: 7, background: "rgba(236,227,207,0.4)", borderRadius: 4 }} />
          </div>
          <div>
            <div style={{ fontFamily: SANS, fontSize: 28, fontWeight: 600 }}>{title}</div>
            {cue.body && <div style={{ fontFamily: SANS, fontSize: 24, color: C.muted, marginTop: 8, lineHeight: 1.4 }}>{cue.body}</div>}
          </div>
        </div>
      </Panel>
    );
  }
  if (cue.kind === "quote") {
    return (
      <Panel cue={cue} t={t} compact>
        <div style={{ fontFamily: SERIF, fontSize: 42, lineHeight: 1.22, fontWeight: 700 }}>&ldquo;{title}&rdquo;</div>
        {cue.body && <div style={{ fontFamily: SANS, fontSize: 22, color: C.muted, marginTop: 12 }}>{cue.body}</div>}
      </Panel>
    );
  }
  if (cue.kind === "callout") {
    const box = boxFor(cue);
    const right = sideFor(cue) === "right" || sideFor(cue) === "top-right";
    const x1 = right ? box.left : box.left + box.width;
    const y1 = box.top + 84;
    const target = cue.target ?? { x: 960, y: 470 };
    return (
      <>
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible" }}>
          <line x1={x1} y1={y1} x2={target.x} y2={target.y} stroke={accent} strokeOpacity={0.72} strokeWidth={2} strokeDasharray="8 8" />
          <circle cx={target.x} cy={target.y} r={7} fill={accent} fillOpacity={0.9} />
        </svg>
        <Panel cue={cue} t={t} compact>
          <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 600 }}>{title}</div>
          {cue.body && <div style={{ fontFamily: SANS, fontSize: 23, color: C.muted, marginTop: 8 }}>{cue.body}</div>}
        </Panel>
      </>
    );
  }
  return (
    <Panel cue={cue} t={t}>
      <AssetPreview cue={cue} />
      <div style={{ fontFamily: SANS, fontSize: 27, fontWeight: 600 }}>{title}</div>
      {cue.body && <div style={{ fontFamily: SANS, fontSize: 24, color: C.muted, lineHeight: 1.45, marginTop: 10 }}>{cue.body}</div>}
    </Panel>
  );
};

/**
 * 以 cue 为唯一时间契约的居中人物舞台叠加层。
 * 所有内容都位于左右安全区，中心人物区域和底部字幕带保持空白。
 */
export const StageOverlay: React.FC<{ t: number; cues: MotionCue[]; opacity?: number }> = ({ t, cues, opacity = 1 }) => (
  <div style={{ position: "absolute", inset: 0, opacity, pointerEvents: "none" }}>
    {cues.map((cue) => <CueView key={cue.id} cue={cue} t={t} />)}
  </div>
);
