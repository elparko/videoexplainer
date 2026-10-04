import json
from pathlib import Path

import typer

from videoexplainer import coverage, frames as frames_module, render as render_module, timeline as timeline_module
from videoexplainer import topics as topics_module, tts as tts_module

ROOT = render_module.ROOT
DATA = ROOT / "data"
BUILD = ROOT / "build"

app = typer.Typer(no_args_is_help=True)
topics_app = typer.Typer(no_args_is_help=True)
app.add_typer(topics_app, name="topics")


def read_json(path):
    return json.loads(Path(path).read_text())


def load_topics():
    return read_json(DATA / "topics.json")


def load_style():
    return read_json(ROOT / "style.json")


@topics_app.command("build")
def topics_build():
    import pymupdf

    topics = topics_module.build_topics(pymupdf.open(topics_module.pdf_path()))
    DATA.mkdir(exist_ok=True)
    (DATA / "topics.json").write_text(json.dumps(topics, indent=1))
    typer.echo(f"{len(topics)} topics -> data/topics.json")


@topics_app.command("find")
def topics_find(query: str):
    for topic, score in topics_module.find_topics(load_topics(), query):
        typer.echo(f"{score:5.1f}  {topic['slug']}  |  {topic['title']}  |  {topic['chapter']}  p. {topic['book_page']}")


@app.command()
def source(slug: str):
    import pymupdf

    doc = pymupdf.open(topics_module.pdf_path())
    text_path, crops = topics_module.write_source(doc, load_topics(), slug, BUILD / slug)
    for path in [text_path, *crops]:
        typer.echo(path.relative_to(ROOT))


@app.command()
def check(slug: str):
    facts = read_json(BUILD / slug / "facts.json")
    script = read_json(BUILD / slug / "script.json")
    errors = coverage.check(facts, script)
    for error in errors:
        typer.echo(error)
    beat_count = len(coverage.beats(script))
    typer.echo(f"{len(facts)} facts, {beat_count} beats, estimated {coverage.estimated_minutes(script):.1f} min")
    if errors:
        raise typer.Exit(1)


@app.command()
def tts(slug: str, voice: str = ""):
    script = read_json(BUILD / slug / "script.json")
    lexicon = tts_module.load_lexicon(ROOT / "pronunciations.toml")
    paths = tts_module.synthesize(
        coverage.beats(script), BUILD / slug / "audio", voice or load_style()["voice"], lexicon
    )
    typer.echo(f"{len(paths)} audio files -> build/{slug}/audio")


@app.command()
def timeline(slug: str):
    script = read_json(BUILD / slug / "script.json")
    result = timeline_module.write_timeline(BUILD / slug, coverage.beats(script), load_style()["fps"])
    typer.echo(f"{len(result['beats'])} beats, {result['total']:.1f} s -> build/{slug}/timeline.json")


@app.command()
def render(slug: str, renderer: str = ""):
    out = render_module.render(slug, renderer or load_style()["renderer"])
    typer.echo(out)


@app.command()
def frames(slug: str, renderer: str = ""):
    renderer = renderer or load_style()["renderer"]
    paths = frames_module.extract_frames(
        render_module.output_path(slug, renderer),
        read_json(BUILD / slug / "timeline.json"),
        BUILD / slug / f"frames-{renderer}",
    )
    typer.echo(f"{len(paths)} frames -> build/{slug}/frames-{renderer}")


@app.command()
def done(slug: str):
    path = DATA / "progress.json"
    progress = read_json(path) if path.exists() else {}
    progress[slug] = {"renderer": load_style()["renderer"]}
    path.write_text(json.dumps(progress, indent=1))
    typer.echo(f"{len(progress)} topics finished")
