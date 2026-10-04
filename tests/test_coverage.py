from videoexplainer import coverage

FACTS = [{"id": 1, "text": "one"}, {"id": 2, "text": "two"}]


def script(*beats):
    return {"scenes": [{"id": "s1", "beats": list(beats)}]}


def test_passes_when_every_fact_is_used():
    result = coverage.check(FACTS, script({"id": "b1", "say": "first", "facts": [1, 2]}))
    assert result == []


def test_reports_unused_fact():
    result = coverage.check(FACTS, script({"id": "b1", "say": "first", "facts": [1]}))
    assert result == ["fact 2 is not covered: two"]


def test_reports_unknown_fact_and_empty_say():
    result = coverage.check(FACTS, script({"id": "b1", "say": " ", "facts": [1, 2, 9]}))
    assert "beat b1 has no say text" in result
    assert "beat b1 lists unknown fact 9" in result


def test_reports_duplicate_beat_ids():
    beat = {"id": "b1", "say": "first", "facts": [1, 2]}
    assert "script.json has duplicate beat ids" in coverage.check(FACTS, script(beat, beat))


def test_reports_length_over_limit():
    long_beat = {"id": "b1", "say": "word " * 700, "facts": [1, 2]}
    assert any("over 4 min" in error for error in coverage.check(FACTS, script(long_beat)))
