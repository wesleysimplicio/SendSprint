import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { theme } from "../theme";

type Props = {
  size?: number;
  delay?: number;
};

export const Logo: React.FC<Props> = ({ size = 220, delay = 0 }) => {
  const frame = useCurrentFrame();
  const local = Math.max(0, frame - delay);
  const rot = interpolate(local, [0, 60], [-25, 0], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(local, [0, 30, 60], [0.4, 1.08, 1], {
    extrapolateRight: "clamp",
  });
  const ringRot = (frame * 1.2) % 360;
  const pulse = 0.85 + 0.15 * Math.sin(frame / 12);

  return (
    <div
      style={{
        width: size,
        height: size,
        position: "relative",
        transform: `scale(${scale}) rotate(${rot}deg)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: -size * 0.12,
          borderRadius: "50%",
          border: `2px dashed ${theme.primarySoft}55`,
          transform: `rotate(${ringRot}deg)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: -size * 0.05,
          borderRadius: "50%",
          background: theme.gradient,
          filter: `blur(${size * 0.12}px)`,
          opacity: 0.6 * pulse,
        }}
      />
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 32,
          background: theme.gradient,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 30px 80px rgba(124,92,255,0.45)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <svg
          viewBox="0 0 100 100"
          width={size * 0.6}
          height={size * 0.6}
          style={{ position: "relative", zIndex: 2 }}
        >
          <path
            d="M20 50 L45 25 L45 40 L80 40 L80 60 L45 60 L45 75 Z"
            fill="white"
            stroke="white"
            strokeLinejoin="round"
            strokeWidth={4}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(circle at 30% 20%, rgba(255,255,255,0.4), transparent 50%)",
          }}
        />
      </div>
    </div>
  );
};
