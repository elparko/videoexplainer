import json
from pathlib import Path

GAP = 0.25
LEAD_IN = 0.5
TAIL = 1.5


def build_timeline(durations, fps, gap=GAP, lead_in=LEAD_IN, tail=TAIL):
    beats = []
    cursor = lead_in
    for beat_id, seconds in durations:
        beats.append({"id": beat_id, "start": round(cursor, 3), "end": round(cursor + seconds, 3)})
        cursor += seconds + gap
    total = round(cursor - gap + tail, 3) if beats else 0
    return {"fps": fps, "total": total, "beats": beats}


def srt_time(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def build_srt(timeline, text_by_beat):
    entries = []
    for number, beat in enumerate(timeline["beats"], start=1):
        entries.append(
            f"{number}\n{srt_time(beat['start'])} --> {srt_time(beat['end'])}\n{text_by_beat[beat['id']]}\n"
        )
    return "\n".join(entries)


def write_timeline(build_dir, beats, fps):
    import numpy as np
    import soundfile as sf

    build_dir = Path(build_dir)
    audio = {}
    for beat in beats:
        samples, rate = sf.read(build_dir / "audio" / f"{beat['id']}.wav")
        audio[beat["id"]] = samples
    timeline = build_timeline([(beat["id"], len(audio[beat["id"]]) / rate) for beat in beats], fps)
    narration = np.zeros(round(timeline["total"] * rate), dtype="float32")
    for beat in timeline["beats"]:
        start = round(beat["start"] * rate)
        narration[start : start + len(audio[beat["id"]])] = audio[beat["id"]]
    sf.write(build_dir / "narration.wav", narration, rate)
    (build_dir / "timeline.json").write_text(json.dumps(timeline, indent=2))
    (build_dir / "captions.srt").write_text(build_srt(timeline, {beat["id"]: beat["say"] for beat in beats}))
    return timeline
