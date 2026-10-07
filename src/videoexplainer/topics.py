import json
import os
import re
import unicodedata
from pathlib import Path

import pymupdf
from rapidfuzz import fuzz, process

DEFAULT_PDF = "~/Library/Mobile Documents/com~apple~CloudDocs/School/MS1/Textbooks/first aid.pdf"
PAGE_OFFSET = 21
FIRST_PDF_PAGE = 52
LAST_PDF_PAGE = 759
HEADING_FONTS = {"MyriadPro-Bold", "MyriadPro-BoldIt"}
TEXT_FLAGS = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
HEADING_X = {1: 69, 0: 87}
CONTENT_TOP = 72
CONTENT_BOTTOM = 826
GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "κ": "kappa", "μ": "mu"}
SYMBOLS = {
    "Wingdings3": {"q": "↑", "r": "↓", "p": "→", "`": "▸"},
    "Wingdings": {"\x83": "•"},
}


def pdf_path():
    return Path(os.environ.get("FA_PDF", DEFAULT_PDF)).expanduser()


def slugify(title):
    for letter, name in GREEK.items():
        title = title.replace(letter, name)
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def is_heading_line(spans, pdf_page):
    fonts = {span["font"] for span in spans}
    return (
        abs(spans[0]["bbox"][0] - HEADING_X[pdf_page % 2]) <= 6
        and any(span["font"] in HEADING_FONTS and abs(span["size"] - 10) < 0.3 for span in spans)
        and "MyriadPro-Semibold" not in fonts
        and len("".join(span["text"] for span in spans).strip()) > 1
    )


def page_dict(page, clip=None):
    return page.get_text("dict", clip=clip, flags=TEXT_FLAGS)


def page_heading_lines(page, pdf_page):
    lines = []
    for block in page_dict(page)["blocks"]:
        for line in block["lines"]:
            spans = line["spans"]
            if is_heading_line(spans, pdf_page):
                text = "".join(span["text"] for span in spans)
                lines.append({"text": text, "y0": spans[0]["bbox"][1], "y1": spans[0]["bbox"][3]})
    return sorted(lines, key=lambda l: l["y0"])


def merge_wrapped(lines, max_gap=4):
    merged = []
    for line in lines:
        if merged and line["y0"] - merged[-1]["y1"] <= max_gap:
            prev = merged[-1]
            joiner = "" if prev["text"].endswith(("-", "/")) else " "
            prev["text"] = prev["text"].rstrip() + joiner + line["text"].strip()
            prev["y1"] = line["y1"]
        else:
            merged.append({"text": line["text"].strip(), "y0": line["y0"], "y1": line["y1"]})
    return merged


def page_chapter(page):
    parts = []
    for block in page_dict(page)["blocks"]:
        for line in block["lines"]:
            for span in line["spans"]:
                if span["bbox"][1] < 70 and span["font"] == "MyriadPro-Cond":
                    parts.append(span["text"])
    return "".join(parts).strip().title()


def unique_slugs(topics):
    seen = {}
    for topic in topics:
        slug = slugify(topic["title"])
        seen[slug] = seen.get(slug, 0) + 1
        topic["slug"] = slug if seen[slug] == 1 else f"{slug}-{seen[slug]}"
    return topics


def build_topics(doc):
    topics = []
    for pdf_page in range(FIRST_PDF_PAGE, LAST_PDF_PAGE + 1):
        page = doc[pdf_page - 1]
        chapter = page_chapter(page)
        for heading in merge_wrapped(page_heading_lines(page, pdf_page)):
            if heading["text"].endswith("(continued)"):
                continue
            topics.append(
                {
                    "title": heading["text"],
                    "chapter": chapter,
                    "pdf_page": pdf_page,
                    "book_page": pdf_page - PAGE_OFFSET,
                    "y0": round(heading["y0"], 1),
                }
            )
    return unique_slugs(topics)


def find_topics(topics, query, limit=5):
    titles = [t["title"] for t in topics]
    matches = process.extract(query, titles, scorer=fuzz.WRatio, limit=limit)
    return [(topics[index], score) for _, score, index in matches]


def topic_regions(topics, slug):
    index = next(i for i, t in enumerate(topics) if t["slug"] == slug)
    topic = topics[index]
    following = topics[index + 1] if index + 1 < len(topics) else None
    last_page = following["pdf_page"] if following else topic["pdf_page"]
    regions = []
    for pdf_page in range(topic["pdf_page"], last_page + 1):
        top = topic["y0"] - 4 if pdf_page == topic["pdf_page"] else CONTENT_TOP
        bottom = following["y0"] - 4 if following and pdf_page == following["pdf_page"] else CONTENT_BOTTOM
        if bottom - top > 40:
            regions.append({"pdf_page": pdf_page, "top": top, "bottom": bottom})
    return regions


def region_text(page, clip):
    lines = []
    for block in page_dict(page, clip)["blocks"]:
        for line in block["lines"]:
            text = "".join(
                "".join(SYMBOLS.get(s["font"], {}).get(c, c) for c in s["text"]) for s in line["spans"]
            )
            if text.strip():
                lines.append((line["bbox"][1], line["bbox"][0], text.replace("\xa0", " ")))
    lines.sort()
    rows = []
    for y, x, text in lines:
        if rows and abs(y - rows[-1][0]) < 4:
            rows[-1][1].append((x, text))
        else:
            rows.append((y, [(x, text)]))
    return "\n".join("\t".join(t for _, t in sorted(cells)) for _, cells in rows)


def write_source(doc, topics, slug, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    topic = next(t for t in topics if t["slug"] == slug)
    texts = []
    crops = []
    for stale in out_dir.glob("source-p*.png"):
        stale.unlink()
    for region in topic_regions(topics, slug):
        page = doc[region["pdf_page"] - 1]
        clip = pymupdf.Rect(0, region["top"], page.rect.width, region["bottom"])
        texts.append(region_text(page, clip))
        crop = out_dir / f"source-p{region['pdf_page'] - PAGE_OFFSET}.png"
        page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=clip).save(crop)
        crops.append(crop)
    header = f"{topic['title']} | {topic['chapter']} | First Aid 2025 p. {topic['book_page']}\n\n"
    (out_dir / "source.txt").write_text(header + "\n\n".join(texts) + "\n")
    (out_dir / "topic.json").write_text(json.dumps(topic, indent=2))
    return out_dir / "source.txt", crops
