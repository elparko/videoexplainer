# videoexplainer

Narrated explainer videos for First Aid for the USMLE Step 1 2025 topics. One video per topic.
Claude Code reads the source, writes the fact list, the script, and the scene code. Python (`vx`) does the fixed steps. Kokoro makes the narration locally.

## Rules

- This repo is public. Never commit book content. `data/`, `build/`, `out/`, and `remotion/topics/` are gitignored and hold everything derived from the PDF.
- Narration wording and visuals are original. No book figures or tables on screen. The final card cites the book page.
- Every fact in the First Aid entry must appear in the video. `vx check` enforces that each fact id is used by a beat.
- Python 3.12 (the `kokoro` package does not support 3.13). Use `uv`.

## Pipeline

`/explain <topic>` runs the steps in `.claude/skills/explain/SKILL.md`.

| Command | Does |
|---|---|
| `vx topics build` | Index topic headings from the PDF into `data/topics.json`. PDF path: `FA_PDF` env var. |
| `vx topics find <query>` | Fuzzy search of topic titles. |
| `vx source <slug>` | Topic text and page crop into `build/<slug>/`. |
| `vx check <slug>` | Fail if a fact is unused, a beat has no speech, or the script is over 4 minutes. |
| `vx phonemes <slug>` | List the phonemes Kokoro will speak for each word in the script. |
| `vx tts <slug>` | One Kokoro wav per beat. Applies `pronunciations.toml` (word replacements and phoneme overrides). |
| `vx timeline <slug>` | `timeline.json`, `narration.wav`, `captions.srt`. |
| `vx render <slug> --renderer manim\|remotion` | Silent render, then ffmpeg adds narration. Output in `/Volumes/T7/videoexplainer/` (override with `VX_OUT`). Stops if the drive is not mounted. |
| `vx frames <slug> --renderer ...` | One still per beat for the layout check. |
| `vx done <slug>` | Record the topic in `data/progress.json`. |

## Layout

- `src/videoexplainer/` — `topics.py`, `coverage.py`, `tts.py`, `timeline.py`, `render.py`, `frames.py`, `manim_kit.py`, `cli.py`
- `remotion/` — Node project. `src/kit.tsx` has the helpers. `topics/current/` is filled at render time.
- `style.json` — size, frame rate, colors, font, margin, voice, and default renderer for both renderers.
- `tests/` — one file per module. `uv run pytest`.

## Setup

`uv sync`, `cd remotion && npm install`, `brew install ffmpeg espeak-ng cairo pango pkgconf`.
