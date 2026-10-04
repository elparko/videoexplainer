import fcntl
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REMOTION_DIR = ROOT / "remotion"
SHARED_FILES = ["timeline.json", "script.json", "topic.json"]
DEFAULT_OUT = "/Volumes/T7/videoexplainer"


def out_dir():
    path = Path(os.environ.get("VX_OUT", DEFAULT_OUT))
    if path.is_relative_to("/Volumes") and not Path(*path.parts[:3]).is_mount():
        raise SystemExit(f"{Path(*path.parts[:3])} is not mounted. Connect the drive or set VX_OUT.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_path(slug, renderer):
    return out_dir() / f"{slug}-{renderer}.mp4"


def render_manim(build_dir, style):
    scene_dir = build_dir / "manim"
    env = os.environ | {"VX_BUILD": str(build_dir), "VX_STYLE": str(ROOT / "style.json")}
    subprocess.run(
        [
            "manim", "render", "scene.py", "Explainer",
            "--resolution", f"{style['width']},{style['height']}",
            "--fps", str(style["fps"]),
            "--format", "mp4",
            "--media_dir", "media",
            "--output_file", "silent.mp4",
            "--disable_caching",
            "--progress_bar", "none",
        ],
        cwd=scene_dir,
        env=env,
        check=True,
    )
    return next((scene_dir / "media").rglob("silent.mp4"))


def render_remotion(build_dir, style):
    topics_dir = REMOTION_DIR / "topics"
    topics_dir.mkdir(exist_ok=True)
    silent = build_dir / "remotion-silent.mp4"
    with open(topics_dir / ".render.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = topics_dir / "current"
        shutil.rmtree(current, ignore_errors=True)
        shutil.copytree(build_dir / "remotion", current)
        for name in SHARED_FILES:
            shutil.copy(build_dir / name, current / name)
        shutil.copy(ROOT / "style.json", current / "style.json")
        subprocess.run(
            ["npx", "remotion", "render", "src/index.ts", "Explainer", str(silent), "--muted", "--log=error"],
            cwd=REMOTION_DIR,
            check=True,
        )
    return silent


def mux(silent, narration, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(silent), "-i", str(narration),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(out),
        ],
        check=True,
    )


def render(slug, renderer):
    build_dir = ROOT / "build" / slug
    style = json.loads((ROOT / "style.json").read_text())
    silent = render_manim(build_dir, style) if renderer == "manim" else render_remotion(build_dir, style)
    out = output_path(slug, renderer)
    mux(silent, build_dir / "narration.wav", out)
    shutil.copy(build_dir / "captions.srt", out_dir() / f"{slug}.srt")
    return out
