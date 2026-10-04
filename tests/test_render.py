import pytest

from videoexplainer import render


def test_output_path_uses_vx_out(tmp_path, monkeypatch):
    monkeypatch.setenv("VX_OUT", str(tmp_path / "videos"))
    assert render.output_path("liver-tumors", "manim") == tmp_path / "videos" / "liver-tumors-manim.mp4"
    assert (tmp_path / "videos").is_dir()


def test_out_dir_stops_when_volume_is_not_mounted(monkeypatch):
    monkeypatch.setenv("VX_OUT", "/Volumes/not-a-real-drive/videos")
    with pytest.raises(SystemExit):
        render.out_dir()
