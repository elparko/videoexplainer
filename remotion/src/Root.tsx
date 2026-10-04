import { Composition } from "remotion";
import { Video } from "../topics/current/Video";
import { style, timeline } from "./kit";

export const Root = () => (
  <Composition
    id="Explainer"
    component={Video}
    durationInFrames={Math.ceil(timeline.total * style.fps)}
    fps={style.fps}
    width={style.width}
    height={style.height}
  />
);
