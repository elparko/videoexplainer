from videoexplainer import topics


def line(text, y0):
    return {"text": text, "y0": y0, "y1": y0 + 12.4}


def test_merge_wrapped_joins_consecutive_lines():
    merged = topics.merge_wrapped([line("Hepatic ", 167), line("encephalopathy", 180), line("Liver tumors", 271)])
    assert [m["text"] for m in merged] == ["Hepatic encephalopathy", "Liver tumors"]
    assert merged[0]["y0"] == 167


def test_merge_wrapped_keeps_hyphen_tight():
    merged = topics.merge_wrapped([line("Glucose-6-", 100), line("phosphatase", 113)])
    assert merged[0]["text"] == "Glucose-6-phosphatase"


def span(text, x=87, font="MyriadPro-Bold", size=10.0):
    return {"font": font, "size": size, "bbox": (x, 0, 0, 0), "text": text}


def test_heading_line_depends_on_page_parity():
    assert topics.is_heading_line([span("Liver tumors")], 420)
    assert not topics.is_heading_line([span("Liver tumors")], 421)


def test_heading_line_rejects_figure_labels_and_subtopics():
    assert not topics.is_heading_line([span("A", size=9.0)], 420)
    assert not topics.is_heading_line([span("Week ", font="MyriadPro-Semibold"), span("2", x=110)], 420)
    assert not topics.is_heading_line([span("Body text", font="ElectraLTStd-Regular")], 420)


def test_heading_line_may_start_with_symbol_or_italic():
    alpha = [span("α", x=69, font="SymbolStd", size=9.0), span("1", x=75, size=5.8), span("-antitrypsin ", x=78)]
    assert topics.is_heading_line(alpha, 421)
    assert topics.is_heading_line([span("Nocardia ", font="MyriadPro-BoldIt"), span("vs", x=120)], 420)


def test_unique_slugs_numbers_duplicates():
    result = topics.unique_slugs([{"title": "Shock"}, {"title": "Shock"}, {"title": "α1-antitrypsin deficiency"}])
    assert [t["slug"] for t in result] == ["shock", "shock-2", "alpha1-antitrypsin-deficiency"]


def test_find_topics_ranks_exact_title_first():
    items = [{"title": "Liver tumors"}, {"title": "Bone tumors"}, {"title": "Liver tissue architecture"}]
    assert topics.find_topics(items, "liver tumors")[0][0]["title"] == "Liver tumors"


def test_topic_regions_same_page_and_page_break():
    items = [
        {"slug": "a", "pdf_page": 100, "y0": 300},
        {"slug": "b", "pdf_page": 100, "y0": 500},
        {"slug": "c", "pdf_page": 101, "y0": 400},
        {"slug": "d", "pdf_page": 102, "y0": 80},
    ]
    assert topics.topic_regions(items, "a") == [{"pdf_page": 100, "top": 296, "bottom": 496}]
    assert topics.topic_regions(items, "b") == [
        {"pdf_page": 100, "top": 496, "bottom": topics.CONTENT_BOTTOM},
        {"pdf_page": 101, "top": topics.CONTENT_TOP, "bottom": 396},
    ]
    assert topics.topic_regions(items, "c") == [{"pdf_page": 101, "top": 396, "bottom": topics.CONTENT_BOTTOM}]
