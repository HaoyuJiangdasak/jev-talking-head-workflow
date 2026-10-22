import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { ensureFonts } from "./engine/fonts";
import { Presenter, overlayProgress, presenterProgress } from "./engine/Presenter";
import { StageOverlay } from "./engine/StageOverlay";
import { Grain } from "./engine/Grain";
import { C } from "./engine/theme";
import { clamp, invLerp } from "./engine/ease";
import { Example } from "./scenes/Example";
import { CUES, DURATION, FACE, MODES, VIDEO } from "./project";

ensureFonts();

// 画面合成；音频不在这里（渲染加 --muted，用 scripts/mix_audio.py 混人声+音效，final_compose.py 合成）
export const Story: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const overlay = overlayProgress(t, MODES);
  const presenter = presenterProgress(t, MODES);
  const stage = Math.max(0, overlay - presenter);
  const fadeOut = 1 - clamp(invLerp(DURATION - 0.18, DURATION, t));
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      {overlay > 0.001 && (
        <AbsoluteFill>
          <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 70% at 30% 20%, #12304a 0%, ${C.ink} 58%, ${C.deep} 100%)` }} />
          {stage <= 0.001 && <Example t={t} />}
          <Grain frame={frame} />
        </AbsoluteFill>
      )}
      <Presenter t={t} modes={MODES} src={VIDEO} face={FACE} />
      {/* stage 模式把动效放到人物上层，人物保持中央全屏，形成“人和动画合二为一”。 */}
      {overlay > 0.001 && <AbsoluteFill style={{ zIndex: 10, pointerEvents: "none" }}><StageOverlay t={t} cues={CUES} opacity={1} /></AbsoluteFill>}
      <AbsoluteFill style={{ background: "#000", opacity: 1 - fadeOut }} />
    </AbsoluteFill>
  );
};
