from videoexplainer import tts


def lexicon(terms=None, phonemes=None):
    return {"terms": terms or {}, "phonemes": phonemes or {}}


def test_terms_replace_whole_words_only():
    table = lexicon(terms={"AFP": "A F P", "HBV": "hepatitis B virus"})
    assert tts.apply_lexicon("Serum AFP rises with HBV.", table) == "Serum A F P rises with hepatitis B virus."
    assert tts.apply_lexicon("AFPX stays", table) == "AFPX stays"


def test_terms_prefer_longer_match():
    table = lexicon(terms={"fetoprotein": "wrong", "α-fetoprotein": "alpha-fetoprotein"})
    assert tts.apply_lexicon("α-fetoprotein", table) == "alpha-fetoprotein"


def test_phonemes_wrap_word_and_keep_its_case_and_punctuation():
    table = lexicon(phonemes={"aspergillus": "ˌæspəɹʤˈɪləs"})
    assert tts.apply_lexicon("from Aspergillus.", table) == "from [Aspergillus](/ˌæspəɹʤˈɪləs/)."


def test_phonemes_apply_after_terms_and_never_nest():
    table = lexicon(terms={"HCC": "hepatocellular carcinoma"}, phonemes={"carcinoma": "kˌɑɹsənˈOmə", "hepatocellular carcinoma": "x"})
    assert tts.apply_lexicon("HCC", table) == "[hepatocellular carcinoma](/x/)"


def test_load_lexicon_missing_file(tmp_path):
    assert tts.load_lexicon(tmp_path / "none.toml") == lexicon()


def test_is_checkable_keeps_hyphenated_words_and_abbreviations():
    assert tts.is_checkable("Zollinger-Ellison")
    assert tts.is_checkable("CT")
    assert not tts.is_checkable("the")
    assert not tts.is_checkable("12")
