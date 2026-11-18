---
name: lemo-animi
description: Make a short stop-motion animated film from one line ("story + style + length + size") in one of the fixed stop-motion styles (clay and more). Default 40 s (20 s to 2 min) with score and foley; narration and subtitles on request, in Chinese or English. 定格动画系列短片：一句话「故事 + 风格 + 时长 + 尺寸」做一支定格动画。Use when the user says "用 lemo-animi 做…" or "make … with lemo-animi", asks for a stop-motion, claymation or cartoon short (定格动画、黏土动画、动画短片、做个动画短片、做个会动的小片子、让角色动起来讲个小故事), or gives a story idea about a character or animal to animate. Not for photorealistic footage (see references/realism.md), animating one existing image, or editing existing videos.
---

# lemo-animi: a stop-motion short from one line

**Image generation makes it look right; code makes it move.** Every style has fixed prompt templates; you only fill the slots (character, action, scene). Assets are transparent PNGs, sliced and composited shot by shot in Python (on twos, anchors, camera, transitions, grading, subtitles). Sound comes from one sound sheet: score, foley, optional narration, mix.

**Read files whole.** A tool output may be cut short: read files over ~120 lines in chunks (`sed -n '1,120p' <file>`, then the rest); never act on a truncated read.

## 1. Talking to the user

**Language.** The skill is in English. Talk to the user in the language they write in, whatever it is (questions, options, every progress note between tool calls, review-page replies, report). If nothing shows it (no words from the user and no language set by your own instructions), ask that alone first (item L), then everything else in the chosen language.
- **The film's own text** (narration, subtitles, title and end cards) is Chinese or English: Chinese for a Chinese-speaking user, English for everyone else unless they ask for Chinese; when the user writes neither, the narration question says so. Set it with `init_film.py --lang zh|en` (it goes into `sound.json` `"lang"`, `references/sound.md`).
- **The review page**: `review.py add … --lang <the user's language code>` (zh, en, ja, …): Chinese gets the Chinese page, every other language the English page.
- **Style list**: `animi.py styles --lang zh|en`; for other languages use `en` and translate the one-liners.

| Item | Default and handling |
|---|---|
| Story | May be just a title. **Write the full story yourself** in the story skeleton for its length (directing §1: setup, tries, low point, turn, payoff; beats, side characters, narration); don't ask back. A given plot: follow it, fill the skeleton's missing parts with beats and shots. A character image (their original character, a pet): generate the character sheet from it in this style's material and match every sheet to it. No real faces or franchise characters: steer to an original. |
| Style | Fixed styles only (`animi.py styles`; Chinese name, English name or id). Off the list: say it's experimental; if they insist, `references/new-style.md`. Photorealism: `references/realism.md`. |
| Length | 40 s; options 20 / 40 / 60 s, or any length the user types from 20 s to 2 min. **The final film's length, title and end cards included.** Over 60 s: before starting, tell the user roughly how many images and how long it takes (§3 table). |
| Size | landscape 1920×1080 / portrait 1080×1920 / square 1080×1080. |
| Narration | Off (score + foley, no subtitles). On: lively female or child voice, subtitles in the film's language; bilingual subtitles on request. Needs network (edge-tts sends the narration text to Microsoft): if `sound.py vo` can't connect, request access with the justification it prints; if refused, make the film without narration and say so. Never a local offline voice. |
| Preview | Off: work straight through. On (or the user sent a character image): show character sheets and main backgrounds once on the review page, continue after approval. |
| Title and end cards | Off. On: title and credit come in the same question. No title given: title it from the story and say so in a progress note. Never invent a credit. Each card is 3 s, so the story runs the length minus 6 s. |

**Ask everything once, before starting** (before reading the style package). First run `sh "$S/setup.sh" check`. Then ask, in one round, every item of the list below that the user's line didn't settle, in the list's order:
- **Each item is its own question.** Never merge items, never fold them into one "use the defaults / adjust" question, never ask one question per call or per message.
- **With a question tool, all questions go in one call** (item L, when needed, goes alone before it). Codex: `request_user_input_async` in default mode when it's there. In Plan mode `request_user_input` works, but Plan mode can't make the film: after the answers, tell the user in one line to switch to default mode and say go. Claude's `AskUserQuestion` takes at most 4 questions per call: fill the calls in list order, 4 each, back to back with nothing in between (every item open: 0–3, then 4–7); a leftover item gets a call of its own, never folded into another question.
- **Few options per question** (Claude 2–4, Codex 2–3). The style item names every style with its one-liner in the question text; its options are the style that best fits this story (Recommended), a second fitting one, and "you decide"; any other style by free text. The other items fit as listed.
- Options in the user's language, default first and marked "(Recommended)" in their language. Free text (story, title, credit, wishes) goes in the tool's free-text box, never an extra "I'll type it" option; if the tool has no free-text box, ask those in one plain follow-up message.
- Only with no question tool at all: one message, numbered questions, each with options and default; "all defaults" means defaults.
- **Download notice, not a question**: if `check` found the Python env or instrument samples missing, the text right before the questions (or the top of the message) says once: about 1.7 GB (Python env ~300 MB + score instrument samples ~1.4 GB) goes to `~/lemo-animi-env` and starts as soon as they answer. Nothing is downloaded before the answer. If `check` passed (an earlier install by Codex or Claude Code on this machine counts), don't mention it.
- **What you can't install, say now**: ffmpeg missing → the user installs it (macOS `brew install ffmpeg`, Linux the package manager). In Claude Code, `check` also reports the image tool: neither Codex CLI nor an adapter → the user installs and logs in to Codex (`npm i -g @openai/codex`, then `codex login`); no zsh (some Linux) → the user installs zsh. Put these in the same notice; after the answers, install what you can and wait for them.
- In Claude Code, the same text says once that a film runs a few hundred commands and auto mode (Shift+Tab, or `claude --permission-mode auto`) saves an approval for each; never suggest skipping permissions.

Then stop and wait: don't start on defaults. **After the answers, environment first**: if anything was missing, run `sh "$S/setup.sh"` (in a sandbox, request escalated permission to write `~/lemo-animi-env`; never point `LEMO_ANIMI_*` at a temp folder to get around it), send one progress line while it downloads, and start the film only once `sh "$S/setup.sh" check` passes. If the download fails, show its message and stop; never start a film on a half-installed environment. Wishes in the answers go into the director's plan. From then on, **work through to the final film without asking again**, only one- or two-line progress notes; the only stop is the optional preview.

```
L. Language: English / 中文 / other (free text)   (only when nothing shows it: no words from the user and no language set by your own instructions; asked alone, first)
0. Story: you decide (default) / free text (a title or one line is enough)   (only if the user gave none)
1. Style: python3 "$S/animi.py" styles --lang zh|en (works before the env exists): all styles in the question text; options = best fit (Recommended) / second fit / you decide   (only if no style given)
2. Length: 40 s (default) / 20 / 60 s (another length up to 2 min: free text)
3. Size: landscape (default) / portrait / square
4. Narration: none (default) / lively female / child (bilingual subtitles: free text; narration and subtitles are Chinese or English, see Language)
5. Title and end cards: none (default) / yes (title and credit in free text)
6. Preview characters and backgrounds: no (default) / yes (default when the user sent a character image)
7. Anything else: no, you decide (default) / free text (plot, palette, ending, a character image)
```

## 2. Work until it passes

- **Before the director's plan read**: `styles/<id>/STYLE.md`, `references/directing.md`, `references/quality.md`, `references/pitfalls.md`. Other docs at the step that needs them.
- **Long commands**: `setup.sh` (first run), `gen.sh` (up to 10 min per image), full renders and `review.py wait` (30 min) outlast a default tool timeout. Codex: keep polling the running command. Claude Code: its Bash tool stops a command at 10 min, so run `setup.sh`, full renders and `wait` with `run_in_background: true` and carry on when it reports back; give each `gen.sh` call a 600000 ms timeout or run it in the background.
- **Aim to pass, not to be fast**: images and time per length are in the §3 table (40 s: about 20–26 images and an hour or more). Below the asset minimums it is unfinished.
- **A failed check, bad slice or off anchor changes the plan, it doesn't stop you**: look it up in the handling table in `quality.md` (`--allow-edge`, `--clean`, `--group grid` pass after you check the image). Regenerate only real defects (max 3 times per image, one change each time), or split / recompose.
- **The first render is not the delivery.** Watch the whole film, the `selfcheck.py` sheets, consecutive frames at every cut and contact; listen to the whole soundtrack. Clear the `sound.py check` warnings and the render's `liveness` warnings (fix, or list each with its reason in `review.py add --known`). Can't listen (no audio input): write "not listened" and check what can be measured (`sound.py check`; each landing or impact sound on the drawing where it lands, `sound.py times` beside the contact frames; stems in `audio/`). Write a verdict with timecodes for each must-pass item in `quality.md`, fix, review again. What you didn't watch or hear is "not checked", never "pass".
- Edit `tools/film.py` one change at a time with the edit tool (Codex: apply_patch); batch string replacement silently hits other places.
- **Blocked**: permission denied or a tool unavailable (network, quota, system software): finish everything else, report honestly, never work around it. Image generation timeout or rate limit (429): do what doesn't need that image, retry in a few minutes; no placeholders at delivery. Any other image generation error (bad request, unsupported parameter, refused by a gateway) usually comes from the user's own setup: show the exact error, do the work that needs no images, ask how to proceed. Never read credential or config files, never switch image tool or model on your own.

## 3. Workflow (same for every style)

Commands and folders: `references/workflow.md` (also the tools list and the review page). Functions: `references/api.md`.

| Step | What | Read |
|---|---|---|
| 0 | `$S` = absolute path of the `scripts/` folder next to this file (quote it: `"$S/…"`); `$PY` = output of `sh "$S/setup.sh" python`, for every Python command. `sh "$S/setup.sh" check` before the opening questions; if something is missing, a one-line notice with the questions, then `sh "$S/setup.sh"` right after the answers (about 1.7 GB, network, writes `~/lemo-animi-env`); the film starts only once `check` passes (§1) | workflow §0 |
| 1 | Style package: `STYLE.md`, `style.json`, `ref/` and `poster.jpg` where present | |
| 2 | **Director's plan** in `production-log.md`: logline, story skeleton with seconds per part, beat sheet, narration, shot list, layered action table, image list | directing |
| 3 | **Timing**: with narration, write it in `sound.json`, `sound.py vo` gives line lengths, shots follow; without, seconds per beat (a beat is 2–4 s and holds several events) | sound |
| 3′ | `"$PY" "$S/init_film.py" <film folder> --style <id> --dur <story seconds> --size <landscape|portrait|square> --name <name> --lang <zh|en>` (creates the folder; run everything after inside it) → write `SHOTS` + `build()` → `film.py lint` | compositing |
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
  3. Must-pass items (`quality.md` §3): one line each, pass / fixed / known issue / not checked.
  4. What you're least happy with, and anything not done (no network, no audio check…).
  5. Where the film and the review page are.
