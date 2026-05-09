import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { IntroScene } from "./scenes/IntroScene";
import { WhatIsScene } from "./scenes/WhatIsScene";
import { TriggerScene } from "./scenes/TriggerScene";
import { StepsScene } from "./scenes/StepsScene";
import { IDEsScene } from "./scenes/IDEsScene";
import { SetupScene } from "./scenes/SetupScene";
import { OutroScene } from "./scenes/OutroScene";
import { SCENES } from "./theme";

export const SendSprintExplainer: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#03050d" }}>
      <Sequence from={SCENES.intro.start} durationInFrames={SCENES.intro.dur}>
        <IntroScene />
      </Sequence>
      <Sequence from={SCENES.whatIs.start} durationInFrames={SCENES.whatIs.dur}>
        <WhatIsScene />
      </Sequence>
      <Sequence
        from={SCENES.triggers.start}
        durationInFrames={SCENES.triggers.dur}
      >
        <TriggerScene />
      </Sequence>
      <Sequence from={SCENES.steps.start} durationInFrames={SCENES.steps.dur}>
        <StepsScene />
      </Sequence>
      <Sequence from={SCENES.ides.start} durationInFrames={SCENES.ides.dur}>
        <IDEsScene />
      </Sequence>
      <Sequence from={SCENES.setup.start} durationInFrames={SCENES.setup.dur}>
        <SetupScene />
      </Sequence>
      <Sequence from={SCENES.outro.start} durationInFrames={SCENES.outro.dur}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
