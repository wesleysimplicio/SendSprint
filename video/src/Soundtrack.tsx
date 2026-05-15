import React from "react";
import { Audio, Sequence, staticFile } from "remotion";

type Cue = "click" | "error" | "success" | "whoosh";

const cueFile: Record<Cue, string> = {
  click: "audio/sendsprint-click.wav",
  error: "audio/sendsprint-error.wav",
  success: "audio/sendsprint-success.wav",
  whoosh: "audio/sendsprint-whoosh.wav",
};

type SoundtrackProps = {
  cues?: { frame: number; cue: Cue; volume?: number }[];
  musicVolume?: number;
};

export const Soundtrack: React.FC<SoundtrackProps> = ({
  cues = [],
  musicVolume = 0.13,
}) => (
  <>
    <Audio src={staticFile("audio/sendsprint-bed.wav")} volume={musicVolume} />
    {cues.map((item, index) => (
      <Sequence key={`${item.cue}-${item.frame}-${index}`} from={item.frame}>
        <Audio src={staticFile(cueFile[item.cue])} volume={item.volume ?? 0.55} />
      </Sequence>
    ))}
  </>
);

export const explainerCues = [
  { frame: 0, cue: "whoosh" as const, volume: 0.35 },
  { frame: 150, cue: "click" as const, volume: 0.35 },
  { frame: 300, cue: "click" as const, volume: 0.35 },
  { frame: 470, cue: "whoosh" as const, volume: 0.35 },
  { frame: 690, cue: "click" as const, volume: 0.35 },
  { frame: 880, cue: "success" as const, volume: 0.42 },
  { frame: 1120, cue: "success" as const, volume: 0.48 },
];

export const beforeAfterCues = [
  { frame: 0, cue: "whoosh" as const, volume: 0.35 },
  { frame: 180, cue: "error" as const, volume: 0.38 },
  { frame: 420, cue: "click" as const, volume: 0.35 },
  { frame: 630, cue: "whoosh" as const, volume: 0.42 },
  { frame: 990, cue: "success" as const, volume: 0.45 },
  { frame: 1230, cue: "success" as const, volume: 0.5 },
];

export const runLoopCues = [
  { frame: 0, cue: "whoosh" as const, volume: 0.35 },
  { frame: 80, cue: "click" as const, volume: 0.32 },
  { frame: 122, cue: "click" as const, volume: 0.32 },
  { frame: 164, cue: "click" as const, volume: 0.32 },
  { frame: 206, cue: "click" as const, volume: 0.32 },
  { frame: 248, cue: "error" as const, volume: 0.48 },
  { frame: 322, cue: "whoosh" as const, volume: 0.42 },
  { frame: 414, cue: "click" as const, volume: 0.34 },
  { frame: 468, cue: "click" as const, volume: 0.34 },
  { frame: 522, cue: "click" as const, volume: 0.34 },
  { frame: 575, cue: "success" as const, volume: 0.54 },
  { frame: 610, cue: "success" as const, volume: 0.62 },
];
