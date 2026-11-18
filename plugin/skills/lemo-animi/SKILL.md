---
name: lemo-animi
description: Make a short stop-motion animated film from one line ("story + style + length + size") in one of the fixed stop-motion styles (clay and more). Default 40 s (20 s to 2 min) with score and foley; narration and subtitles on request, in Chinese or English. 定格动画系列短片：一句话「故事 + 风格 + 时长 + 尺寸」做一支定格动画。Use when the user says "用 lemo-animi 做…" or "make … with lemo-animi", asks for a stop-motion, claymation or cartoon short (定格动画、黏土动画、动画短片、做个动画短片、做个会动的小片子、让角色动起来讲个小故事), or gives a story idea about a character or animal to animate. Not for photorealistic footage (see references/realism.md), animating one existing image, or editing existing videos.
---

# lemo-animi: a stop-motion short from one line

**Image generation makes it look right; code makes it move.** Every style has fixed prompt templates; you only fill the slots (character, action, scene). Assets are transparent PNGs, sliced and composited shot by shot in Python (on twos, anchors, camera, transitions, grading, subtitles). Sound comes from one sound sheet: score, foley, optional narration, mix.

**Read files whole.** A tool output may be cut short: read files over ~120 lines in chunks (`sed -n '1,120p' <file>`, then the rest); never act on a truncated read.

## 1. Talking to the user

**Language.** The skill is in English; talk to the user in their language (questions, options, progress notes, report). If they wrote nothing to infer it from, the first question asks it ("语言 Language": 中文 / English). That is also the film's language unless they ask otherwise: `sound.json` `"lang": "zh" | "en"` sets narration, subtitles and card text (`references/sound.md`); `review.py add … --lang` sets the page; `animi.py styles --lang` lists styles.

| Item | Default and handling |
|---|---|
| Story | May be just a title. **Write the full story yourself** in the story skeleton for its length (directing §1: setup, tries, low point, turn, payoff; beats, side characters, narration); don't ask back. A given plot: follow it, fill the skeleton's missing parts with beats and shots. A character image (their original character, a pet): generate the character sheet from it in this style's material and match every sheet to it. No real faces or franchise characters: steer to an original. |
| Style | Fixed styles only (`animi.py styles`; Chinese name, English name or id). Off the list: say it's experimental; if they insist, `references/new-style.md`. Photorealism: `references/realism.md`. |
| Length | 40 s; options 20 / 40 / 60 s, or any length the user types from 20 s to 2 min. **The final film's length, title and end cards included.** Over 60 s: before starting, tell the user roughly how many images and how long it takes (§3 table). |
| Size | landscape 1920×1080 / portrait 1080×1920 / square 1080×1080. |
| Narration | Off (score + foley, no subtitles). On: lively female or child voice, subtitles in the film's language; bilingual subtitles on request. Needs network (edge-tts sends the narration text to Microsoft): if `sound.py vo` can't connect, request access with the justification it prints; if refused, make the film without narration and say so. Never a local offline voice. |
| Preview | Off: work straight through. On (or the user sent a character image): show character sheets and main backgrounds once on the review page, continue after approval. |
| Title and end cards | Off. On: title and credit come in the same question. No title given: title it from the story and say so in a progress note. Never invent a credit. Each card is 3 s, so the story runs the length minus 6 s. |

**Ask everything once, before starting** (before reading the style package): every item the user's line didn't cover, plus "anything else?". With a question tool, put **all questions in one call** (Codex: `request_user_input` in Plan mode, `request_user_input_async` in default mode when it's there; Claude `AskUserQuestion`), options in the user's language, default first and marked "(Recommended)" in their language; free text (title, credit, wishes) goes in the tool's free-text box, never an extra "I'll type it" option. If the tool caps questions per call, use the fewest calls back to back with nothing in between; list overflow options in the question text; if the tool has no free-text box, ask the free-text questions in one plain follow-up message. Only with no question tool at all: one message, numbered questions, each with options and default; "all defaults" means defaults. Then stop and wait: don't start on defaults. Wishes in the answers go into the director's plan. After intake, **work through to the final film without asking again**, only one- or two-line progress notes; the only stop is the optional preview.

```
1. Style: animi.py styles --lang <lang>, one line each + what stories it suits   (only if no style given; first)
2. Length: 40 s (default) / 20 / 60 s (another length up to 2 min: free text)
3. Size: landscape (default) / portrait / square
4. Narration: none (default) / lively female / child (bilingual subtitles: free text)
5. Title and end cards: none (default) / yes (title and credit in free text)
6. Preview characters and backgrounds: no (default) / yes (default when the user sent a character image)
7. Anything else: no, you decide (default) / free text (plot, palette, ending, a character image)
```

## 2. Work until it passes

- **Before the director's plan read**: `styles/<id>/STYLE.md`, `references/directing.md`, `references/quality.md`, `references/pitfalls.md`. Other docs at the step that needs them.
- **Aim to pass, not to be fast**: images and time per length are in the §3 table (40 s: about 20–26 images and an hour or more). Below the asset minimums it is unfinished.
- **A failed check, bad slice or off anchor changes the plan, it doesn't stop you**: look it up in the handling table in `quality.md` (`--allow-edge`, `--clean`, `--group grid` pass after you check the image). Regenerate only real defects (max 3 times per image, one change each time), or split / recompose.
- **The first render is not the delivery.** Watch the whole film, the `selfcheck.py` sheets, consecutive frames at every cut and contact; listen to the whole soundtrack. Clear the `sound.py check` warnings and the render's `liveness` warnings (fix, or list each with its reason in `review.py add --known`). Can't listen (no audio input): write "not listened" and check what can be measured (`sound.py check`; each landing or impact sound on the drawing where it lands, `sound.py times` beside the contact frames; stems in `audio/`). Write a verdict with timecodes for each must-pass item in `quality.md`, fix, review again. What you didn't watch or hear is "not checked", never "pass".
- Edit `tools/film.py` one change at a time with the edit tool (Codex: apply_patch); batch string replacement silently hits other places.
- **Blocked**: permission denied or a tool unavailable (network, quota, system software): finish everything else, report honestly, never work around it. Image generation timeout or rate limit (429): do what doesn't need that image, retry in a few minutes; no placeholders at delivery. Any other image generation error (bad request, unsupported parameter, refused by a gateway) usually comes from the user's own setup: show the exact error, do the work that needs no images, ask how to proceed. Never read credential or config files, never switch image tool or model on your own.

## 3. Workflow (same for every style)

Commands and folders: `references/workflow.md` (also the tools list and the review page). Functions: `references/api.md`.

| Step | What | Read |
|---|---|---|
| 0 | `$S` = absolute path of the `scripts/` folder next to this file (quote it: `"$S/…"`); `$PY` = output of `sh "$S/setup.sh" python`, for every Python command. `sh "$S/setup.sh" check`; if something is missing, `sh "$S/setup.sh"` (about 1.7 GB, network, writes `~/lemo-animi-env`: tell the user the size first; in a sandbox request escalated permission for it) | workflow §0 |
| 1 | Style package: `STYLE.md`, `style.json`, `ref/` and `poster.jpg` where present | |
| 2 | **Director's plan** in `production-log.md`: logline, story skeleton with seconds per part, beat sheet, narration, shot list, layered action table, image list | directing |
| 3 | **Timing**: with narration, write it in `sound.json`, `sound.py vo` gives line lengths, shots follow; without, seconds per beat (a beat is 2–4 s and holds several events) | sound |
| 3′ | `"$PY" "$S/init_film.py" <film folder> --style <id> --dur <story seconds> --size <landscape|portrait|square> --name <name>` (creates the folder; run everything after inside it) → write `SHOTS` + `build()` → `film.py lint` | compositing |
| 4 | Images: slot file → `animi.py prompt` → generate. Character sheets and 1–2 key backgrounds first; check palette and character. Codex: built-in image_gen, references in `referenced_image_paths`, `transparent_background: true` for transparent assets, copy from the returned path | prompts, workflow §4 |
| ⏸ | Preview (only if on): register, wait for approval | workflow, review page |
| 4′ | Other backgrounds → `load()` → `film.py board` (open the `board_p*.jpg` pages); shots connect | |
| 4″ | Action sheets, close-up sheets, props, fx; set layers and textures if needed | |
| 5 | `animi.py check` → `slice` → `anchors` | workflow §4 |
| 6 | Real assets into `load()` / `render()`; `put()` applies the style's light; transition assets load from `style.json` | compositing |
| 7 | Sound: score, hits, foley (times per shot, `"shot+0.4"`; per-cell sounds via `foley_rules`) → `sound.py lint` → `build` | sound |
| 8 | lint → stills → full film → contact sheet → consecutive frames → `selfcheck.py` → must-pass items → fix → again; then bookends if on | quality |
| ⏸ | Review page: register, the user writes notes, fix, register again until approved | workflow, review page |
| 9 | Deliver (§5) | |

**Asset minimums** (short of them, the plan is underthought: split the beats again):

Columns are the film length; for other lengths take the nearest column, scaled.

| | 20 s | 40 s | 60 s | 90 s | 2 min |
|---|---|---|---|---|---|
| Shots (typical, never padded) | 2–4 | 5–8 | 6–12 | 9–16 | 12–22 |
| Backgrounds, **each a different view**, not the same composition enlarged | ≥ 2 | ≥ 4 | ≥ 6 | ≥ 8 | ≥ 10 |
| 8-cell action sheets, **one per action** | ≥ 3 | ≥ 5 | ≥ 7 | ≥ 10 | ≥ 13 |
| 2×2 close-up sheets (key reaction, payoff) | ≥ 1 | ≥ 2 | ≥ 3 | ≥ 4 | ≥ 5 |
| Prop / fx sheets | as needed; at least one fx sheet for landings and impacts | same | same | same | same |
| Total images | ~10–14 | ~20–26 | ~30–38 | ~42–52 | ~55–68 |
| Rough time | under an hour | about an hour | 1.5–2 h | 2–2.5 h | 2.5–3 h |

A prop acting alone (a lamp lights itself, a boat drifts) is prop images + fx sheets, not an action sheet.

## 4. Hard rules (details in the docs named)

1. **Fixed styles only**: every prompt from `animi.py prompt`, no style text of your own; compositing parameters from `animi.style_preset` / `animi.finish`; no hand grading.
2. **Transparent assets**: character, action and close-up sheets, props, fx are transparent PNGs; backgrounds are opaque and never contain the hero.
3. **Timing before shots**: narration lengths (or seconds per beat) first; cut between lines, inside actions or on music sections.
4. **Cut only for a reason; no zoom cuts** (directing §3): new place, a true close-up (hero > 2× the previous shot), or a real change of view for a reaction; otherwise one shot, pushing in slowly. Every shot has `place` and `view`; one place, one set (other views generated from its main background). `shots_lint` must pass.
5. **Hero big enough** (share of the short side, directing §3): wide ≥ 30%, opening and payoff wides ≥ 33%, medium ≥ 40%, medium-close ≥ 60% and full body; extreme-wide ≥ 15%, route only, at most 2, never opening or payoff; adjacent same-size shots within 1.3×.
6. **Always something happening, nothing shaking** (directing §4–5, compositing §5): a new event every 1–1.5 s, three layers moving; no per-drawing jitter or flicker; no swaying while standing; holds over 2 s are live through a local detail, idle breathing, a side character or the environment (camera motion alone doesn't count); pose to pose with anticipation and settle; no action replayed unchanged a third time; cycles ≤ 6 s, two- or three-cell loops ≤ 3 s.
7. **Effects and environment changes are generated images**, never code-drawn shapes; code may only relight (`char_light`, `warm_glow`, `darken`, `light_flood`, `self_glow`).
8. **Same character throughout**: every sheet from the character sheet as reference, one scale (`A.scale_ref`), placed by anchor; poses, facing and held objects connect across sheet changes and cuts.
9. **The image model never draws text, logos, real faces or franchise characters.** Text is set by code in Source Han Sans Bold, flat colour, style only on the plate. Cards: title ≥ 200 px, strip ≥ 60 px, credit ≥ 48 px (at 1080); narration subtitles use the style's `subtitle.size`, always at the bottom.
10. **Every action has a sound**: landings, impacts, tosses, catches in `foley`; key actions hit the music; silence before the twist (`references/sound.md`).
11. **Draw the payoff into the artwork**: character and object generated together, given a close shot; never pasted on in code; the object's path stays continuous across cuts.
12. **Self-review frame by frame**: `"$PY" "$S/selfcheck.py" out/<name>.mp4 --style <style>` in the film folder, against `quality.md` §2; fix and run again.
13. **A whole story** (directing §1): the skeleton for the film's length, every part with its seconds in the director's plan and caused by the part before; the want is set up before the first try and answered by the payoff.

## 5. Delivery

- The film: `out/<name>.mp4`, or with cards `out/<name>-bookends.mp4` + `.srt` (that one is the film: register and deliver it); `<name>.srt` if narrated without cards; `out/contact.jpg`; `production-log.md`. `<name>` = `NAME` in `film.py` = `name` in `sound.json`.
- **The last message is the report**, in the user's language, written out in full with all five numbered parts in this order, even where the app favours short replies. A link to `production-log.md` never replaces a part; item 3 lists every must-pass item on its own line.
  1. Title and logline; style; length and size; shots.
  2. Images: total, and backgrounds / action sheets / close-up sheets / props / fx; how many regenerated.
  3. Must-pass items (`quality.md`): one line each, pass / fixed / known issue / not checked.
  4. What you're least happy with, and anything not done (no network, no audio check…).
  5. Where the film and the review page are.
