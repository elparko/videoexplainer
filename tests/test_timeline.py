import json

import numpy as np
import soundfile as sf

from videoexplainer import timeline


def test_build_timeline_adds_gap_lead_in_and_tail():
    result = timeline.build_timeline([("b1", 2.0), ("b2", 3.0)], fps=30, gap=0.25, lead_in=0.5, tail=1.5)
    assert result["beats"] == [
        {"id": "b1", "start": 0.5, "end": 2.5},
        {"id": "b2", "start": 2.75, "end": 5.75},
    ]
    assert result["total"] == 7.25


def test_srt_time():
    assert timeline.srt_time(3723.5) == "01:02:03,500"


def test_build_srt():
    data = {"beats": [{"id": "b1", "start": 0.5, "end": 2.5}]}
    assert timeline.build_srt(data, {"b1": "Hello."}) == "1\n00:00:00,500 --> 00:00:02,500\nHello.\n"


def test_write_timeline_outputs_match(tmp_path):
    (tmp_path / "audio").mkdir()
    for beat_id, seconds in [("b1", 1.0), ("b2", 2.0)]:
        sf.write(tmp_path / "audio" / f"{beat_id}.wav", np.ones(round(24000 * seconds), dtype="float32") * 0.1, 24000)
    beats = [{"id": "b1", "say": "One."}, {"id": "b2", "say": "Two."}]
    result = timeline.write_timeline(tmp_path, beats, fps=30)
    narration, rate = sf.read(tmp_path / "narration.wav")
    assert abs(len(narration) / rate - result["total"]) < 0.001
    assert json.loads((tmp_path / "timeline.json").read_text()) == result
    assert narration[0] == 0
    assert narration[round(0.6 * rate)] > 0
