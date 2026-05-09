import React from "react";
import { AbsoluteFill } from "remotion";
import { RunLoopScene } from "./scenes/RunLoopScene";

/**
 * Standalone composition for the run-loop demo. Embedded in web/README.md as
 * the visual explanation of what RunScreen does on every sprint delivery.
 */
export const RunLoopVideo: React.FC = () => (
  <AbsoluteFill style={{ background: "#03050d" }}>
    <RunLoopScene />
  </AbsoluteFill>
);

export const RUN_LOOP_DURATION = 660; // 22s @ 30fps
