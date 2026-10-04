import re
import tomllib
from pathlib import Path

SAMPLE_RATE = 24000


def load_lexicon(path):
    path = Path(path)
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text()).get("terms", {})


def apply_lexicon(text, lexicon):
    for term in sorted(lexicon, key=len, reverse=True):
        pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
        text = re.sub(pattern, lexicon[term], text, flags=re.IGNORECASE)
    return text


def synthesize(beats, out_dir, voice, lexicon, speed=1.0):
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")
    paths = []
    for beat in beats:
        text = apply_lexicon(beat["say"], lexicon)
        chunks = [result.audio.numpy() for result in pipeline(text, voice=voice, speed=speed)]
        path = out_dir / f"{beat['id']}.wav"
        sf.write(path, np.concatenate(chunks), SAMPLE_RATE)
        paths.append(path)
    return paths
