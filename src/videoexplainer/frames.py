import shutil
import subprocess
from pathlib import Path

END_OFFSET = 0.1


def frame_times(timeline):
    return [(beat["id"], round(max(beat["start"], beat["end"] - END_OFFSET), 3)) for beat in timeline["beats"]]


def extract_frames(video, timeline, out_dir):
    out_dir = Path(out_dir)
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)
    paths = []
    for beat_id, seconds in frame_times(timeline):
        path = out_dir / f"{beat_id}.png"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", str(seconds), "-i", str(video),
                "-frames:v", "1", "-vf", "scale=960:-1",
                str(path),
            ],
            check=True,
        )
        paths.append(path)
    return paths
