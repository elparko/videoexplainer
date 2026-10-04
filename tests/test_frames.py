from videoexplainer import frames


def test_frame_times_sit_just_before_beat_end():
    data = {"beats": [{"id": "b1", "start": 0.5, "end": 2.5}, {"id": "b2", "start": 3.0, "end": 3.05}]}
    assert frames.frame_times(data) == [("b1", 2.4), ("b2", 3.0)]
