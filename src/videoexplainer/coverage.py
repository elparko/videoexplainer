WORDS_PER_MINUTE = 150
MAX_MINUTES = 4


def beats(script):
    return [beat for scene in script["scenes"] for beat in scene["beats"]]


def estimated_minutes(script):
    words = sum(len(beat.get("say", "").split()) for beat in beats(script))
    return words / WORDS_PER_MINUTE


def check(facts, script):
    errors = []
    fact_ids = [fact["id"] for fact in facts]
    if len(set(fact_ids)) != len(fact_ids):
        errors.append("facts.json has duplicate fact ids")
    all_beats = beats(script)
    beat_ids = [beat["id"] for beat in all_beats]
    if len(set(beat_ids)) != len(beat_ids):
        errors.append("script.json has duplicate beat ids")
    used = set()
    for beat in all_beats:
        if not beat.get("say", "").strip():
            errors.append(f"beat {beat['id']} has no say text")
        for fact_id in beat.get("facts", []):
            if fact_id not in fact_ids:
                errors.append(f"beat {beat['id']} lists unknown fact {fact_id}")
            used.add(fact_id)
    for fact in facts:
        if fact["id"] not in used:
            errors.append(f"fact {fact['id']} is not covered: {fact['text']}")
    minutes = estimated_minutes(script)
    if minutes > MAX_MINUTES:
        errors.append(f"estimated length {minutes:.1f} min is over {MAX_MINUTES} min")
    return errors
