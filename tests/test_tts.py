from videoexplainer import tts


def test_apply_lexicon_replaces_whole_terms_only():
    lexicon = {"AFP": "A F P", "HBV": "hepatitis B virus"}
    assert tts.apply_lexicon("Serum AFP rises with HBV.", lexicon) == "Serum A F P rises with hepatitis B virus."
    assert tts.apply_lexicon("AFPX stays", lexicon) == "AFPX stays"


def test_apply_lexicon_prefers_longer_term():
    lexicon = {"fetoprotein": "wrong", "α-fetoprotein": "alpha-fetoprotein"}
    assert tts.apply_lexicon("α-fetoprotein", lexicon) == "alpha-fetoprotein"


def test_load_lexicon_missing_file(tmp_path):
    assert tts.load_lexicon(tmp_path / "none.toml") == {}
