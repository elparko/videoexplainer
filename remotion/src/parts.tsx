import type { ReactNode } from "react";
import { AbsoluteFill } from "remotion";
import { Appear, Box, Txt, beatLength, colors, ramp, script, seconds, useRamp, useTime } from "./kit";

type Moment = string | number;

type Beat = { id: string; say: string; caption: string; facts: number[]; visual: string };
type SceneInfo = { id: string; title: string; kind?: string; tag?: string; color?: string; beats: Beat[] };

export const scenes = script.scenes as SceneInfo[];
const beats = scenes.flatMap((scene) => scene.beats);

export const cap = (id: string) => beats.find((beat) => beat.id === id)!.caption.split("\n");
export const part = (id: string, fraction: number) => beatLength(id) * fraction;

const kindColor: Record<string, string> = { benign: "green", malignant: "red", metastasis: "purple" };
const kindTag: Record<string, string> = { benign: "BENIGN", malignant: "MALIGNANT", metastasis: "METASTASES" };

export const edgeShift = (px: number, bold = false) => -(bold ? 0.04 : 0.07) * px;

export const sceneColor = (index: number) => scenes[index].color ?? kindColor[scenes[index].kind ?? ""] ?? "blue";

export const Scene = ({ index, children }: { index: number; children: ReactNode }) => {
  const time = useTime();
  const scene = scenes[index];
  const first = scene.beats[0].id;
  const start = seconds(first);
  const last = index + 1 >= scenes.length;
  const end = last ? Infinity : seconds(scenes[index + 1].beats[0].id);
  if (time < start || time >= end) {
    return null;
  }
  const tag = scene.tag ?? kindTag[scene.kind ?? ""];
  return (
    <AbsoluteFill style={{ opacity: last ? 1 : 1 - ramp(time, end - 0.4, 0.4) }}>
      {scene.kind === "overview" ? null : (
        <Box x={96} y={96}>
          <Appear at={first}>
            <Txt px={64} weight={700} style={{ marginLeft: edgeShift(64, true) }}>{scene.title}</Txt>
          </Appear>
        </Box>
      )}
      {tag ? (
        <Box x={96} y={184}>
          <Appear at={first} delay={0.2}>
            <div
              style={{
                display: "inline-block",
                padding: "8px 20px",
                borderRadius: 14,
                backgroundColor: colors[sceneColor(index)],
                color: colors.bg,
                fontSize: 32,
                lineHeight: 1.25,
                fontWeight: 700,
                letterSpacing: 2,
              }}
            >
              {tag}
            </div>
          </Appear>
        </Box>
      ) : null}
      {children}
    </AbsoluteFill>
  );
};

export const COLUMN_X = 840;
export const COLUMN_W = 984;
export const ROW_TEXT_INDENT = 40;
export const ROW_PX = 44;
export const ROW_GAP = 40;
export const CHIP_GAP = 16;
const LINE = 1.25;
const DOT = 18;
const CAP_HEIGHT = 0.714;
const ASCENT = 0.952;
const CONTENT = 1.165;
export const firstLineCapCenter = (px: number) => (px * LINE - px * CONTENT) / 2 + px * ASCENT - (px * CAP_HEIGHT) / 2;

type RowsProps = { x?: number; y?: number; w?: number; children: ReactNode };

export const Rows = ({ x = COLUMN_X, y = 280, w = COLUMN_W, children }: RowsProps) => (
  <Box x={x} y={y} w={w} style={{ display: "flex", flexDirection: "column", gap: ROW_GAP }}>
    {children}
  </Box>
);

type RowProps = { at: Moment; delay?: number; until?: Moment; color: string; px?: number; children: ReactNode };

export const Row = ({ at, delay, until, color, px = ROW_PX, children }: RowProps) => (
  <Appear at={at} delay={delay} until={until} style={{ position: "relative" }}>
    <div
      style={{
        position: "absolute",
        left: 0,
        top: firstLineCapCenter(px) - DOT / 2,
        width: DOT,
        height: DOT,
        borderRadius: DOT / 2,
        backgroundColor: colors[color],
      }}
    />
    <Txt px={px} style={{ marginLeft: ROW_TEXT_INDENT }}>{children}</Txt>
  </Appear>
);

type CaptionRowsProps = { beat: string; color: string; until?: Moment; px?: number };

export const CaptionRows = ({ beat, color, until, px }: CaptionRowsProps) => (
  <>
    {cap(beat).map((line, i) => (
      <Row key={i} at={beat} delay={i * 0.3} until={until} color={color} px={px}>
        {line}
      </Row>
    ))}
  </>
);

export const Heading = ({ at, until, children }: { at: Moment; until?: Moment; children: ReactNode }) => (
  <Box x={COLUMN_X} y={280}>
    <Appear at={at} until={until}>
      <Txt px={ROW_PX} weight={700} color="muted">{children}</Txt>
    </Appear>
  </Box>
);

export const Chip = ({ color, children }: { color: string; children: ReactNode }) => (
  <div
    style={{
      display: "inline-block",
      padding: 20,
      border: `3px solid ${colors[color]}`,
      borderRadius: 16,
      backgroundColor: colors.panel,
      fontSize: 40,
      lineHeight: 1.2,
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </div>
);

export type Point = [number, number];
export type Curve = [Point, Point, Point, Point];

export const cubic = (p: Curve, t: number): Point => {
  const u = 1 - t;
  const k = [u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t];
  return [0, 1].map((axis) => k.reduce((sum, weight, i) => sum + weight * p[i][axis], 0)) as Point;
};

export const pointAtY = (curve: Curve, y: number): Point => {
  let low = 0;
  let high = 1;
  const rising = curve[3][1] > curve[0][1];
  for (let i = 0; i < 30; i++) {
    const middle = (low + high) / 2;
    if (cubic(curve, middle)[1] < y === rising) {
      low = middle;
    } else {
      high = middle;
    }
  }
  return cubic(curve, (low + high) / 2);
};

export const curveD = (curve: Curve) => `M ${curve[0].join(" ")} C ${curve.slice(1).map((point) => point.join(" ")).join(" ")}`;

export const liverCurves: Curve[] = [
  [[50, 260], [50, 140], [190, 90], [340, 100]],
  [[340, 100], [470, 108], [590, 140], [640, 200]],
  [[640, 200], [665, 235], [630, 275], [570, 295]],
  [[570, 295], [470, 330], [390, 380], [310, 440]],
  [[310, 440], [230, 495], [110, 490], [75, 410]],
  [[75, 410], [55, 360], [50, 310], [50, 260]],
];

export const liverPath = `M ${liverCurves[0][0].join(" ")} ${liverCurves
  .map((curve) => `C ${curve.slice(1).map((point) => point.join(" ")).join(" ")}`)
  .join(" ")} Z`;

export const LABEL_PX = 36;

type LabelProps = { x: number; y: number; color: string; anchor?: "start" | "middle" | "end"; opacity?: number; children: ReactNode };

export const Label = ({ x, y, color, anchor = "start", opacity = 1, children }: LabelProps) =>
  opacity === 0 ? null : (
    <text x={x} y={y} fontSize={LABEL_PX} fill={colors[color]} textAnchor={anchor} opacity={opacity}>
      {children}
    </text>
  );

export const Liver = ({ tint = 0, label = true }: { tint?: number; label?: boolean }) => (
  <>
    <path d={liverPath} fill={colors.panel} stroke={colors.muted} strokeWidth={5} strokeLinejoin="round" />
    {tint > 0 ? (
      <path d={liverPath} fill={colors.yellow} fillOpacity={0.2 * tint} stroke={colors.yellow} strokeOpacity={tint} strokeWidth={5} />
    ) : null}
    {label ? <Label x={0} y={110} color="muted">Liver</Label> : null}
  </>
);

export const Panel = ({ at, children }: { at: Moment; children: ReactNode }) => {
  const shown = useRamp(at);
  return (
    <Box x={96} y={280} w={680} h={640} style={{ opacity: shown }}>
      <svg width={680} height={640} viewBox="0 0 680 640" style={{ overflow: "visible" }}>
        {children}
      </svg>
    </Box>
  );
};

type DrawProps = { d: string; progress: number; color: string; width: number; opacity?: number };

export const Draw = ({ d, progress, color, width, opacity = 1 }: DrawProps) =>
  progress === 0 || opacity === 0 ? null : (
    <path
      d={d}
      fill="none"
      stroke={colors[color]}
      strokeWidth={width}
      strokeLinecap="round"
      pathLength={1}
      strokeDasharray={1}
      strokeDashoffset={1 - progress}
      opacity={opacity}
    />
  );

type CardProps = { color: string; w: number; h?: number; title?: string; px?: number; children: ReactNode };

export const Card = ({ color, w, h, title, px = 40, children }: CardProps) => (
  <div
    style={{
      boxSizing: "border-box",
      width: w,
      height: h,
      padding: 24,
      border: `3px solid ${colors[color]}`,
      borderRadius: 16,
      backgroundColor: colors.panel,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      gap: 8,
    }}
  >
    {title ? <Txt px={px} weight={700} color={color}>{title}</Txt> : null}
    <Txt px={px}>{children}</Txt>
  </div>
);

type ArrowProps = { from: Point; to: Point; progress: number; color: string; width?: number; dashed?: boolean; opacity?: number };

export const Arrow = ({ from, to, progress, color, width = 5, dashed = false, opacity = 1 }: ArrowProps) => {
  if (progress <= 0) {
    return null;
  }
  const tip: Point = [from[0] + (to[0] - from[0]) * progress, from[1] + (to[1] - from[1]) * progress];
  const angle = Math.atan2(to[1] - from[1], to[0] - from[0]);
  const head = width * 3.2;
  const corner = (side: number): Point => [
    tip[0] - head * Math.cos(angle) + side * head * 0.6 * Math.sin(angle),
    tip[1] - head * Math.sin(angle) - side * head * 0.6 * Math.cos(angle),
  ];
  const base: Point = [tip[0] - head * Math.cos(angle), tip[1] - head * Math.sin(angle)];
  return (
    <g opacity={opacity}>
      <line
        x1={from[0]}
        y1={from[1]}
        x2={base[0]}
        y2={base[1]}
        stroke={colors[color]}
        strokeWidth={width}
        strokeDasharray={dashed ? `${width * 2.5} ${width * 2}` : undefined}
      />
      <polygon points={[tip, corner(1), corner(-1)].map((point) => point.join(",")).join(" ")} fill={colors[color]} />
    </g>
  );
};

export const Canvas = ({ children }: { children: ReactNode }) => (
  <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", left: 0, top: 0 }}>
    {children}
  </svg>
);

export const Citation = ({ at }: { at: Moment }) => (
  <Box x={96} y={984 - 36 * LINE}>
    <Appear at={at} delay={0.6}>
      <Txt px={36} color="muted" style={{ marginLeft: edgeShift(36) }}>
        {`First Aid for the USMLE Step 1 2025, p. ${script.book_page}`}
      </Txt>
    </Appear>
  </Box>
);
