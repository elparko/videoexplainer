---
name: explain
description: Make one narrated explainer video for a First Aid topic. Use when the user types /explain <topic>.
---

# /explain <topic>

Make one 1920x1080 explainer video for one First Aid 2025 topic. Run every step in order.
Do not stop for review. The checks below replace it.

All commands run from the repo root with `uv run vx ...`. Working files go in `build/<slug>/`.

## Steps

1. Find the topic and extract the source.
   - `uv run vx topics find "<topic>"`. Pick the best match. If `data/topics.json` is missing, run `uv run vx topics build` first.
   - `uv run vx source <slug>`. Read `source.txt` and every `source-p<N>.png`. The image is the authority when the text looks scrambled (tables).
2. Write `build/<slug>/facts.json`: every atomic fact in the entry, numbered from 1.
   `[{"id": 1, "text": "..."}]`. One claim per fact. Keep every qualifier (ages, sex, "most common", "in adults", "eg").
3. Write `build/<slug>/script.json`:
   ```json
   {"title": "...", "slug": "...", "book_page": 399, "scenes": [
     {"id": "s1", "title": "...", "beats": [
       {"id": "s1b1", "say": "...", "caption": "...", "facts": [1, 2], "visual": "..."}
     ]}
   ]}
   ```
   - A scene may set `"tag"` (short caps label under the title, for example "BENIGN") and `"color"` (a color name from `style.json`). `"kind": "overview"` hides the scene title for a full-screen opening.
   - One beat is one spoken sentence. `say` is original wording, not copied from the book.
   - Keep the book's strength of claim: "associated with" stays "associated with", "include" stays "include", "may" stays "may".
   - `say` is written for speech: spell out numbers and abbreviations that the voice would misread, or add them to `pronunciations.toml`.
   - `caption` is the on-screen text for the beat. `visual` says what is drawn or changes.
   - Target 60-120 seconds at about 150 words per minute. Up to 4 minutes for a long topic. Never drop a fact to save time.
4. Check the script.
   - `uv run vx check <slug>` must pass.
   - Start one subagent with fresh context (Agent tool; if that is not available, `claude -p "<prompt>"` from the shell). Give it only the paths to `source.txt`, the page crops, `facts.json`, and `script.json`. Ask for two lists: (a) source facts missing from or wrong in `facts.json`; (b) statements in `say`, `caption`, or `visual` that the source does not support or that change its meaning.
   - Fix every item, rerun `vx check`, and repeat the subagent review until both lists are empty.
5. Check pronunciation, then make the audio.
   - `uv run vx phonemes <slug>`. It lists every word with the phonemes Kokoro will speak. `guess` means the word was not in Kokoro's dictionary. `dictionary` words can still be wrong: noun/verb pairs ("contrast", "lead"), and medical terms with unusual stress.
   - Read the whole list. For every medical term, drug name, organism, eponym, and noun/verb pair, compare the phonemes with the standard American medical pronunciation.
   - Fix each wrong word in `pronunciations.toml`: `[phonemes]` for a phoneme string (preferred), `[terms]` for abbreviations and symbols that need different words. Add plural and adjective forms as separate entries. Use a two-word key when the fix depends on context ("contrast CT").
   - Run `vx phonemes` again and confirm each fix shows as `override` with the intended phonemes.
   - `uv run vx tts <slug>` then `uv run vx timeline <slug>`. This writes one wav per beat, `narration.wav`, `timeline.json`, and `captions.srt`.
6. Write the scene code for the renderer named in `style.json` (`renderer`).
   - Manim: `build/<slug>/manim/scene.py`, a class `Explainer(ExplainerScene)` from `videoexplainer.manim_kit`.
   - Remotion: `build/<slug>/remotion/Video.tsx`, exporting `Video`, built on `remotion/src/kit.tsx` (import path `../../src/kit`).
7. Render and check layout.
   - `uv run vx render <slug>` then `uv run vx frames <slug>`.
   - Read every PNG in `build/<slug>/frames-<renderer>/`. Each one is the frame 0.1 s before the beat's audio ends.
   - Fix text overflow, overlap, items outside the safe margin, text smaller than 36 px, and empty frames. Render again.
   - At most 3 passes. After that, report what is still wrong.
8. `uv run vx done <slug>`. Report: output path, duration, fact count, beat count, and any check that did not pass.

## Scene code rules

- Timing comes from `timeline.json`. A beat's visual change starts at the beat's `start` and finishes before its `end`. Never hard-code seconds for beat starts.
- Colors, font, and margin come from `style.json`. No other colors or fonts.
- Dark background. One idea per beat. Build diagrams piece by piece. Clear the screen between scenes.
- Text is at least 36 px at 1920x1080. Everything stays inside the 96 px margin.
- Label every drawn line, arrow, and shape that stands for a structure or a process. The label is text of at least 36 px placed next to the item, in the item's color, and it appears with the item. A viewer must be able to pause on any frame and name everything drawn. Do not use a line for decoration.
- A line or arrow starts and ends exactly on the things it connects. Compute its endpoints from the same coordinates used to place those things.
- Alignment: rows in a column share one left edge. A row's dot is centered on the row's first text line. Chips in a row share one height and one baseline. Use one spacing value per list.
- Draw original schematic shapes. No figures, photos, or tables from the book.
- Every fact in the beat's `facts` must be readable on screen or spoken; on-screen wording must not be stronger than the source.
- The last scene shows the citation: `First Aid for the USMLE Step 1 2025, p. <book_page>`.
- Manim: use `self.text(...)` (Pango `Text`), not `MathTex`. LaTeX is not installed. Use `self.at("<beat id>")` to wait for a beat, `self.place(mobject, x, y, anchor)` for pixel positions from the top-left, `self.check_bounds()` to print items outside the safe area, and `self.finish()` at the end.
- Remotion: use `<Appear at="<beat id>">`, `useRamp`, `seconds()`, `<Box>`, `<Txt>`, and `<Screen>` from `remotion/src/kit.tsx` (import as `../../src/kit`).
- Remotion: build the layout from `remotion/src/parts.tsx` (import as `../../src/parts`): `Scene` (title, tag, fade between scenes), `Panel` (left drawing area), `Rows`, `Row`, `CaptionRows`, `Heading`, `Chip`, `Label`, `Draw`, `cap()`, `part()`, curve helpers, and the layout constants. Read that file before writing a scene. Do not edit `kit.tsx` or `parts.tsx` during a topic; put topic-specific components in `build/<slug>/remotion/` and report any helper that should move into the shared files.
- Standard layout: title at x=96, y=96; tag under it; drawing in the left panel (x 96-776, y 280-920); fact rows in the right column (x 840-1824, from y=280). A scene with no useful drawing may use the full width for rows, a table, or a flow diagram.
- All animation is a function of the current frame. No CSS transitions, no timers.
- A finished example, if present on this machine: `build/liver-tumors/remotion/Video.tsx`.
- Several topics may be in progress at once. Touch only `build/<slug>/` for your topic. `vx render` handles `remotion/topics/current/` and waits its turn.
