import type { CSSProperties, ReactNode } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import scriptJson from "../topics/current/script.json";
import styleJson from "../topics/current/style.json";
import timelineJson from "../topics/current/timeline.json";
import topicJson from "../topics/current/topic.json";

export const style = styleJson;
export const timeline = timelineJson;
export const script = scriptJson;
export const topic = topicJson;
export const colors: Record<string, string> = style.colors;

type Moment = string | number;

const beatById = Object.fromEntries(timeline.beats.map((beat) => [beat.id, beat]));

export const seconds = (moment: Moment) => (typeof moment === "number" ? moment : beatById[moment].start);
export const beatEnd = (id: string) => beatById[id].end;
export const beatLength = (id: string) => beatById[id].end - beatById[id].start;

export const useTime = () => useCurrentFrame() / style.fps;

export const ramp = (time: number, start: number, duration = 0.5) =>
  interpolate(time, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

export const useRamp = (at: Moment, delay = 0, duration = 0.5) => ramp(useTime(), seconds(at) + delay, duration);

export const Screen = ({ children }: { children: ReactNode }) => (
  <AbsoluteFill style={{ backgroundColor: colors.bg, color: colors.text, fontFamily: style.font }}>
    {children}
  </AbsoluteFill>
);

type AppearProps = {
  at: Moment;
  delay?: number;
  duration?: number;
  until?: Moment;
  shift?: number;
  style?: CSSProperties;
  children: ReactNode;
};

export const Appear = ({ at, delay = 0, duration = 0.5, until, shift = 24, style: extra, children }: AppearProps) => {
  const time = useTime();
  const shown = ramp(time, seconds(at) + delay, duration);
  const hidden = until === undefined ? 0 : ramp(time, seconds(until) - 0.4, 0.4);
  if (shown === 0 || hidden === 1) {
    return null;
  }
  return (
    <div style={{ opacity: shown * (1 - hidden), transform: `translateY(${(1 - shown) * shift}px)`, ...extra }}>
      {children}
    </div>
  );
};

type BoxProps = { x: number; y: number; w?: number; h?: number; style?: CSSProperties; children: ReactNode };

export const Box = ({ x, y, w, h, style: extra, children }: BoxProps) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, height: h, ...extra }}>{children}</div>
);

type TxtProps = { px?: number; color?: string; weight?: number; style?: CSSProperties; children: ReactNode };

export const Txt = ({ px = 44, color = "text", weight = 400, style: extra, children }: TxtProps) => (
  <div style={{ fontSize: px, lineHeight: 1.25, fontWeight: weight, color: colors[color] ?? color, whiteSpace: "pre-line", ...extra }}>
    {children}
  </div>
);
