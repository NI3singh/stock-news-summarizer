import "./index.css";
import { Composition } from "remotion";
import { Tour, TOTAL } from "./Tour";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Tour"
      component={Tour}
      durationInFrames={TOTAL}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
