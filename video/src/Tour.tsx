import React from "react";
import { Sequence } from "remotion";
import { Bg } from "./components/ui";
import {
  D,
  SceneAgents,
  SceneDashboard,
  SceneFeatures,
  SceneIntro,
  SceneOutro,
  SceneValue,
} from "./components/scenes";

const OVERLAP = 10; // frames of cross-fade between scenes

const SCENES: { key: keyof typeof D; El: React.FC }[] = [
  { key: "intro", El: SceneIntro },
  { key: "value", El: SceneValue },
  { key: "dash", El: SceneDashboard },
  { key: "agents", El: SceneAgents },
  { key: "features", El: SceneFeatures },
  { key: "outro", El: SceneOutro },
];

export const TOTAL =
  Object.values(D).reduce((a, b) => a + b, 0) - OVERLAP * (SCENES.length - 1);

export const Tour: React.FC = () => {
  let from = 0;
  return (
    <Bg>
      {SCENES.map(({ key, El }) => {
        const dur = D[key];
        const node = (
          <Sequence key={key} from={from} durationInFrames={dur} layout="none">
            <El />
          </Sequence>
        );
        from += dur - OVERLAP;
        return node;
      })}
    </Bg>
  );
};
