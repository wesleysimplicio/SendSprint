import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

type Props = {
  text: string;
  delay?: number;
  size?: number;
  weight?: number;
  color?: string;
  gradient?: boolean;
  letterStagger?: number;
  align?: "left" | "center" | "right";
  font?: "sans" | "mono";
  style?: React.CSSProperties;
};

export const AnimatedText: React.FC<Props> = ({
  text,
  delay = 0,
  size = 80,
  weight = 800,
  color = theme.text,
  gradient = false,
  letterStagger = 2,
  align = "center",
  font = "sans",
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const letters = Array.from(text);

  return (
    <div
      style={{
        display: "flex",
        justifyContent:
          align === "center"
            ? "center"
            : align === "left"
              ? "flex-start"
              : "flex-end",
        gap: 0,
        flexWrap: "wrap",
        fontSize: size,
        fontWeight: weight,
        letterSpacing: -0.5,
        lineHeight: 1.05,
        fontFamily: font === "mono" ? theme.fontMono : theme.fontSans,
        ...style,
      }}
    >
      {letters.map((ch, i) => {
        const local = frame - delay - i * letterStagger;
        const s = spring({
          frame: local,
          fps,
          config: { damping: 14, stiffness: 140, mass: 0.6 },
        });
        const y = interpolate(s, [0, 1], [40, 0]);
        const opacity = interpolate(s, [0, 1], [0, 1], {
          extrapolateRight: "clamp",
        });
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              transform: `translateY(${y}px)`,
              opacity,
              whiteSpace: "pre",
              ...(gradient
                ? {
                    background: theme.gradient,
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }
                : { color }),
            }}
          >
            {ch === " " ? " " : ch}
          </span>
        );
      })}
    </div>
  );
};
