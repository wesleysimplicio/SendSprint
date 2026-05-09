import React from "react";
import { Composition } from "remotion";
import { SendSprintExplainer } from "./Video";
import { RunLoopVideo, RUN_LOOP_DURATION } from "./RunLoopVideo";
import { FPS, TOTAL_FRAMES } from "./theme";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="SendSprintExplainer"
        component={SendSprintExplainer}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="SendSprintExplainer1080Square"
        component={SendSprintExplainer}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1080}
        height={1080}
      />
      <Composition
        id="SendSprintRunLoop"
        component={RunLoopVideo}
        durationInFrames={RUN_LOOP_DURATION}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
