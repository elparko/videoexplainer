import re
import tomllib
from pathlib import Path

SAMPLE_RATE = 24000


def load_lexicon(path):
    path = Path(path)
    if not path.exists():
        return {"terms": {}, "phonemes": {}}
    data = tomllib.loads(path.read_text())
    return {"terms": data.get("terms", {}), "phonemes": data.get("phonemes", {})}


def replace_terms(text, table, replacement):
    for term in sorted(table, key=len, reverse=True):
        pattern = r"(?<![\w\[-])" + re.escape(term) + r"(?![\w\]-])"
        text = re.sub(pattern, lambda match: replacement(match.group(0), table[term]), text, flags=re.IGNORECASE)
    return text


def apply_lexicon(text, lexicon):
    text = replace_terms(text, lexicon["terms"], lambda word, spoken: spoken)
    return replace_terms(text, lexicon["phonemes"], lambda word, phonemes: f"[{word}](/{phonemes}/)")


def make_pipeline(voice):
    from kokoro import KPipeline

    return KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")


def is_checkable(word):
    if not any(character.isalpha() for character in word):
        return False
    return len(word) > 3 or word.isupper()


def word_phonemes(beats, voice, lexicon):
    pipeline = make_pipeline(voice)
    words = {}
    for beat in beats:
        _, tokens = pipeline.g2p(apply_lexicon(beat["say"], lexicon))
        for token in tokens:
            if is_checkable(token.text):
                words.setdefault(token.text.lower(), (token.phonemes, getattr(token, "rating", None)))
    return words


def synthesize(beats, out_dir, voice, lexicon, speed=1.0):
    import numpy as np
    import soundfile as sf
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline = make_pipeline(voice)
    paths = []
    for beat in beats:
        text = apply_lexicon(beat["say"], lexicon)
        chunks = [result.audio.numpy() for result in pipeline(text, voice=voice, speed=speed)]
        path = out_dir / f"{beat['id']}.wav"
        sf.write(path, np.concatenate(chunks), SAMPLE_RATE)
        paths.append(path)
    return paths
