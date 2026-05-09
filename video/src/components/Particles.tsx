import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

type Props = {
  count?: number;
  color?: string;
  speed?: number;
};

const seed = (i: number) => {
  const x = Math.sin(i * 12.9898) * 43758.5453;
  return x - Math.floor(x);
};

export const Particles: React.FC<Props> = ({
  count = 50,
  color = "rgba(255,255,255,0.7)",
  speed = 0.4,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const dots = Array.from({ length: count }).map((_, i) => {
    const x0 = seed(i + 1) * width;
    const y0 = seed(i + 7) * height;
    const r = 1.2 + seed(i + 3) * 2.8;
    const drift = (frame * speed * (0.4 + seed(i + 11))) % (height + 100);
    const y = (y0 + drift) % (height + 50) - 20;
    const x = x0 + Math.sin((frame + i * 9) / 50) * 18;
    const alpha = 0.25 + seed(i + 17) * 0.55;
    return (
      <circle
        key={i}
        cx={x}
        cy={y}
        r={r}
        fill={color}
        opacity={alpha}
      />
    );
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", height: "100%" }}
      >
        {dots}
      </svg>
    </AbsoluteFill>
  );
};
