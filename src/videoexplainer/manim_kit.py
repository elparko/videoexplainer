import json
import os
from pathlib import Path

import numpy as np
from manim import DOWN, UP, FadeIn, FadeOut, Group, Scene, Text, config

FONT_SIZE_PER_PX = 100 / 187.5
ANCHORS = {
    "tl": (-1, 1), "tc": (0, 1), "tr": (1, 1),
    "cl": (-1, 0), "c": (0, 0), "cr": (1, 0),
    "bl": (-1, -1), "bc": (0, -1), "br": (1, -1),
}


class ExplainerScene(Scene):
    def setup(self):
        build = Path(os.environ["VX_BUILD"])
        self.style = json.loads(Path(os.environ["VX_STYLE"]).read_text())
        self.timeline = json.loads((build / "timeline.json").read_text())
        self.script = json.loads((build / "script.json").read_text())
        self.topic = json.loads((build / "topic.json").read_text())
        self.colors = self.style["colors"]
        self.starts = {beat["id"]: beat["start"] for beat in self.timeline["beats"]}
        self.ends = {beat["id"]: beat["end"] for beat in self.timeline["beats"]}
        self.unit = config.frame_height / self.style["height"]
        self.camera.background_color = self.colors["bg"]

    def now(self):
        return self.renderer.time

    def px(self, pixels):
        return pixels * self.unit

    def point(self, x, y):
        return np.array([
            (x - self.style["width"] / 2) * self.unit,
            (self.style["height"] / 2 - y) * self.unit,
            0,
        ])

    def place(self, mobject, x, y, anchor="tl"):
        ax, ay = ANCHORS[anchor]
        mobject.move_to(self.point(x, y), aligned_edge=np.array([ax, ay, 0]))
        return mobject

    def text(self, string, px=44, color="text", weight="NORMAL", max_width=None, **kwargs):
        mobject = Text(
            string,
            font=self.style["font"],
            font_size=px * FONT_SIZE_PER_PX,
            color=self.colors.get(color, color),
            weight=weight,
            **kwargs,
        )
        if max_width and mobject.width > self.px(max_width):
            mobject.scale_to_fit_width(self.px(max_width))
        return mobject

    def hold_until(self, seconds):
        remaining = seconds - self.now()
        if remaining > 1 / config.frame_rate:
            self.wait(remaining)
        elif remaining < -0.05:
            print(f"LATE by {-remaining:.2f} s at t={seconds:.2f}")

    def at(self, beat_id, offset=0.0):
        self.hold_until(self.starts[beat_id] + offset)

    def appear(self, *mobjects, run_time=0.5, shift=24):
        self.play(*[FadeIn(m, shift=UP * self.px(shift)) for m in mobjects], run_time=run_time)

    def clear(self, *mobjects, run_time=0.4):
        targets = mobjects or self.mobjects
        if targets:
            self.play(FadeOut(Group(*targets)), run_time=run_time)

    def check_bounds(self, label=""):
        margin = self.style["margin"]
        limit_x = (self.style["width"] / 2 - margin) * self.unit
        limit_y = (self.style["height"] / 2 - margin) * self.unit
        for mobject in self.mobjects:
            if mobject.width == 0 and mobject.height == 0:
                continue
            left, right = mobject.get_left()[0], mobject.get_right()[0]
            bottom, top = mobject.get_bottom()[1], mobject.get_top()[1]
            if left < -limit_x - 0.01 or right > limit_x + 0.01 or bottom < -limit_y - 0.01 or top > limit_y + 0.01:
                print(f"OUTSIDE SAFE AREA {label}: {type(mobject).__name__} x[{left:.2f},{right:.2f}] y[{bottom:.2f},{top:.2f}]")

    def finish(self):
        self.hold_until(self.timeline["total"])
