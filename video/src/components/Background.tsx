import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

type Props = {
  variant?: "deep" | "soft" | "warm";
};

export const Background: React.FC<Props> = ({ variant = "deep" }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const t = frame / 60;
  const cx1 = width * 0.3 + Math.sin(t * 0.6) * 80;
  const cy1 = height * 0.4 + Math.cos(t * 0.5) * 60;
  const cx2 = width * 0.7 + Math.cos(t * 0.4) * 100;
  const cy2 = height * 0.7 + Math.sin(t * 0.7) * 70;

  const blobA =
    variant === "warm" ? "rgba(255,138,61,0.35)" : "rgba(124,92,255,0.45)";
  const blobB =
    variant === "warm" ? "rgba(255,94,135,0.28)" : "rgba(34,211,238,0.35)";
  const base = variant === "soft" ? theme.surface : theme.bg;

  return (
    <AbsoluteFill style={{ background: base, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${cx1}px ${cy1}px, ${blobA} 0%, transparent 45%), radial-gradient(circle at ${cx2}px ${cy2}px, ${blobB} 0%, transparent 50%)`,
          filter: "blur(60px)",
          opacity: 0.9,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage:
            "radial-gradient(ellipse at center, black 30%, transparent 75%)",
          opacity: 0.5,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.0) 60%, rgba(0,0,0,0.6) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
