export const theme = {
  bg: "#070b1a",
  bgDeep: "#03050d",
  surface: "#0f1530",
  surfaceAlt: "#141d3f",
  border: "rgba(120, 145, 255, 0.18)",
  text: "#f1f4ff",
  textMuted: "#9aa3c7",
  primary: "#7c5cff",
  primarySoft: "#a78bff",
  accent: "#22d3ee",
  accentWarm: "#ff8a3d",
  success: "#34d399",
  warning: "#fbbf24",
  danger: "#f87171",
  gradient:
    "linear-gradient(135deg, #7c5cff 0%, #22d3ee 50%, #34d399 100%)",
  gradientWarm: "linear-gradient(135deg, #ff8a3d 0%, #ff5e87 100%)",
  fontSans:
    "'Inter', 'SF Pro Display', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontMono:
    "'JetBrains Mono', 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace",
} as const;

export const FPS = 30;

export const SCENES = {
  intro: { start: 0, dur: 120 },
  whatIs: { start: 120, dur: 210 },
  triggers: { start: 330, dur: 180 },
  steps: { start: 510, dur: 600 },
  ides: { start: 1110, dur: 180 },
  setup: { start: 1290, dur: 210 },
  outro: { start: 1500, dur: 180 },
} as const;

export const TOTAL_FRAMES = 1680;
