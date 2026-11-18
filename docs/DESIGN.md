# lemo-animi design system

One system for the two pages: the gallery (`docs/build.py` → `docs/assets/site.css`, `site.js`) and the review page
(`scripts/review.py`, one self-contained file). The idea is **the studio bench**: warm paper, masking-tape labels,
film strips with sprocket holes, dark viewing equipment, sticker-like buttons with a hard shadow. Everything moves
the way the films do: in steps, never eased. It should read as an animation studio's tool and showcase, not an app.

**Keeping the two in sync.** The token block lives in `docs/assets/site.css` between `tokens:start` and
`tokens:end`, and a copy of it sits at the top of the `<style>` in `scripts/review.py` (`review.py` must stay a
single file, so it cannot link the stylesheet). When you change a token, change it in both files; the two blocks
differ only in whitespace. The button, pill and tape rules are also duplicated and must match.

## Colour

Light is paper on the bench by daylight; dark is the studio after hours with the work lamp on. Every token has a
role, never a hue name; the page never uses a raw hex outside the token block (the only exceptions are pure black
behind video and white on video overlays).

| Role | Token | Light | Dark | Use |
|---|---|---|---|---|
| Surface 0 | `--surface-0` | `#f4ede1` | `#15120f` | Page background (the bench) |
| Surface 1 | `--surface-1` | `#ebe2d2` | `#1d1814` | Sunk panels: shelf, footer, inline code, hover wash |
| Surface 2 | `--surface-2` | `#fdf8ef` | `#26201a` | Raised cards, pads, buttons |
| Ink | `--ink` | `#1e1915` | `#f1e8da` | Text, primary buttons, playhead |
| Ink 2 | `--ink-2` | `#645a4e` | `#b3a694` | Secondary text (≥ 5.2:1 on every surface) |
| Ink 3 | `--ink-3` | `#6b6053` | `#9a8d7e` | Meta text, placeholders, hints (≥ 4.6:1; never below 12 px) |
| Line | `--line` | `#d9cdb8` | `#38302a` | Hairlines, card outlines |
| Line 2 | `--line-2` | `#c9bca4` | `#4a4038` | Stronger rules: shelf edge, input borders, kbd |
| Accent | `--accent` | `#d2402f` | `#ef6a56` | Marks and fills: pins, bullets, primary-button shadow, caret |
| Accent ink | `--accent-ink` | `#b4321f` | `#ff8a76` | Accent used *as text* (the raw accent fails AA on light paper) |
| Accent soft | `--accent-soft` | `#f7ddd6` | `#3f231e` | Tinted backgrounds: timecode chips, the hot note, the default row |
| On accent | `--on-accent` | `#fff` | `#15120f` | Text on an accent fill |
| Success / waiting | `--ok`, `--ok-soft` | `#237057` / `#d9ede3` | `#5fc49b` / `#173327` | Approved, Fixed, "agent is waiting" |
| Info / sent | `--info`, `--info-soft` | `#3c5fa6` / `#dde6f6` | `#8fb3ea` / `#1c2a42` | Sent, replies |
| Warning | `--warn`, `--warn-soft` | `#8f5b00` / `#f8e9c4` | `#e9b949` / `#3a2f12` | Drafts not sent, known issues, new version |
| Danger | `--danger`, `--danger-soft` | `#b02a1d` / `#f6d9d4` | `#ff7f6c` / `#45201b` | Delete hover only |
| Deck | `--deck`, `--deck-2` | `#27211b` / `#352d25` | `#0f0d0b` / `#1c1813` | Dark equipment: film frames, the viewer deck, code blocks |
| Deck ink | `--deck-ink`, `--deck-mute` | `#f1e8d8` / `#a89a86` | `#efe6d6` / `#9a8d7e` | Text on the deck |
| Hole | `--hole` | `rgba(244,237,225,.78)` | `#3a332a` | Sprocket holes punched in the deck |
| Tape | `--tape`, `--tape-ink` | `rgba(236,221,182,.85)` / `#5b4d35` | `rgba(120,100,60,.45)` / `#e8d9b5` | Masking-tape labels |

Rules:

- Text contrast is AA or better: `--ink-2` and `--ink-3` are tuned for every surface, `--accent-ink` for accent
  text. `--accent`, `--ok`, `--warn` and `--danger` are used for text only on their own `-soft` backgrounds, where
  they pass.
- The soft tints (`*-soft`) are the only coloured backgrounds for text; never put text on `--accent` except with
  `--on-accent`.
- Dark mode is `prefers-color-scheme` with a `data-theme` override on `<html>` (`light` / `dark`), set by the theme
  button (gallery) or `?theme=` (review page). Both selectors carry the full dark block.

### The eight style accents

Each sample film carries its own accent from `docs/content.json` (`styles.<id>.accent`): clay `#d9473b`, papercraft
`#e07b3f`, tin `#2f7d6c`, felt `#4a6aa5`, cardboard `#b0814b`, wood `#8b5a2b`, crochet `#e0a92a`, fabric `#d85f4a`.
A film block sets `--accent` to it; inside the block the accent appears as **marks only**: the numbered reel label,
the rule, the bullets and the hard shadow under the Watch button. Text in the accent uses
`--accent-ink: color-mix(in srgb, var(--accent) 62%, var(--ink))`, which darkens it on paper and lightens it in the
dark. No style accent is ever a fill behind text (several are far too light for white text).

## Type

| Role | Stack | Where |
|---|---|---|
| Display | `"Fraunces", "Songti SC", "Noto Serif SC", "Source Han Serif SC", Georgia, serif` | Headings, film titles, names |
| Text / UI | `system-ui, -apple-system, "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif` | Body, buttons, pills |
| Mono | `"IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace` | Timecodes, frame counts, reel numbers, tape labels, commands, ids |

Fraunces and IBM Plex Mono come from Google Fonts (the only external resource). Offline the review page falls
back to the system serif and `ui-monospace` and must still look right, so nothing depends on a web-font metric.
Fraunces uses `SOFT 100`; the hero `h1` turns on `WONK 1`. Chinese headings use the system serif with normal
letter-spacing and `line-height: 1.2`; uppercase mono labels (tape, kickers, table heads) switch to the sans in
`:lang(zh-CN)` with `.06–.1em` tracking, since CJK has no case.

Scale (px): `--t-xs 12` · `--t-sm 13` · `--t-md 15` · `--t-lg 17` · `--t-xl 20` · 22 (review title) · 24 · 32 · 44 · display
`clamp(36px, 7.4vw, 100px)` (gallery h1; `min(10vw, 44px)` on phones), `clamp(32px, 4.4vw, 52px)` (h2), `clamp(26px, 3.2vw, 38px)` (`h2.sm`).
Body is 17/1.65 on the gallery and 15/1.6 on the review page. Numbers that line up use `.num` (tabular figures).

Line breaks: headings and the hero's centred texts are `text-wrap: balance`, paragraphs, list items and captions
`text-wrap: pretty`. All page text goes through `build.py`'s `tx()` / `hd()`, which glue with `<span class="nb">`
(`white-space: nowrap`): hyphenated words ("Wind-up", "hard-edged"), version ranges ("3.11–3.13"), a number and its
unit ("1.7 GB"), the last two short words of an English paragraph and the last four characters of a Chinese one (no
line ends a text with one word or one character alone), and any `{phrase}` marked in `content.json` (used for
Chinese phrases that must not split, such as `{定格动画短片}`). Chinese pages set `word-break: keep-all` with
`overflow-wrap: anywhere`: lines break at punctuation and spaces first, so 提示词 or 审片台 stay whole, and an overlong
run still wraps instead of overflowing. Check every section at 360, 390 and 1440 px in both languages.

The hero is the same height in English and Chinese (within a few px from 360 to 1440): the h1 is two lines in both
(the English h1 is capped at `9.6em` so it breaks after "shorts"), the two ledes are written to the same line count,
and on phones the Chinese lede and both "you say" lines sit in boxes as tall as the English ones. When you change hero
copy, measure both languages again. Film lengths are the released file's real duration (`ffprobe`, whole seconds, title and
end cards included), the number a viewer actually gets; the "Film length" table is the same thing for a request.

## Space, radius, elevation

- Spacing scale `--s-1 … --s-9`: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96. Section rhythm on the gallery is
  `clamp(40px, 5vw, 68px)` (compact: a film block is `clamp(40px, 5vw, 64px)` from the next, the footer
  `clamp(48px, 6vw, 80px)` below the licence); the page gutter `clamp(16px, 4vw, 40px)`; the review room padding 24 (16 on phones).
- Radii: `--r-sm 6` (chips, inline code, screens inside a frame) · `--r-md 10` (buttons, cards in lists, code
  blocks) · `--r-lg 16` (pads, viewer, frames) · `--r-xl 22` · `999px` for pills only.
- Shadows: `--sh-1` resting card · `--sh-2` raised (viewer, film frames, toast) · `--sh-hard 2px 2px 0 <colour>` the
  sticker shadow on buttons (`--sh-hard-up 3px 3px 0` on hover). Cards add `0 0 0 1px var(--line)` so they hold in
  dark mode. Elevation order: page → sunk panel → card → viewer/frame → sticky header → toast.
- Sticky header: page surface at 86–88 % with `backdrop-filter: blur(12px)`, hairline only once scrolled (gallery)
  or always (review page).

## Buttons: one system

`.btn` is the only button. Same markup on both pages: `<a class="btn …">` or `<button class="btn …">`, icon SVG first,
text after.

| | Height | Padding | Font | Radius |
|---|---|---|---|---|
| `.btn.sm` | 32 | 0 12 | 600 13px | 8 |
| `.btn` (md) | 40 | 0 16 | 600 14px | 10 |
| `.btn.lg` | 48 | 0 22 | 600 15px | 12 |
| `.icon` | square of the size | 0 | — | same |

Variants:

- **primary** `.primary`: ink fill, paper text, hard shadow in the accent (a film block's own accent inside it).
  One per view: Send to agent, Watch, the hero's first call to action.
- **secondary** (default): surface-2 fill, 1.5 px ink border, hard ink shadow. `.ok` tones the border, text and
  shadow success-green (Approve).
- **quiet** `.quiet`: no border, no shadow, `--ink-2` text; hover washes `--surface-1`. For copy, cancel, edit,
  delete, tools in a bar.
- **icon** `.icon`: a square quiet or secondary button holding one 18 px SVG (16 at sm, 20 at lg) with
  `aria-label`.
- On the deck (dark surfaces) the same shapes are `.ib` (quiet icon, deck ink, `rgba(255,255,255,.1)` hover),
  `.ib.main` (the play button: deck-ink fill) and `.rate` (small outlined mono). They keep the system's heights.

States, every variant: **hover** lifts `translate(-1px,-1px)` and the hard shadow grows to 3 px (quiet: wash only);
**active** presses `translate(1px,1px)` with no shadow; **focus-visible** adds `--focus` (a 2 px paper gap then a
4.5 px accent ring) on top of the shadow; **disabled** is 45 % opacity, no shadow, no transform, `not-allowed`.
Transitions are `var(--step)` = `.12s steps(2, end)`.

## Pills, badges, tape

- **Pill** `.pill`: 28 px, 999 radius, 600 13px, a 7 px dot before the text. Status only, never an action. Tones:
  default (surface-1 / ink-2), `.ok`, `.info`, `.warn`; `.hollow` draws the dot as a ring (agent not waiting);
  `.live` makes the dot breathe (agent waiting).
- **Badge**: the small count on the notes label and shot thumbnails — 22/20 px round, accent fill, `--on-accent`
  mono text. Reply badges (`.bd`) are 11.5 px pills in `--info` / `--ok` with white text.
- **Tape** `.tape`: a strip of masking tape, 12 px mono uppercase in `--tape-ink` on `--tape`, 7–8 px vertical
  padding, torn ends via `clip-path`, rotated −1.2° from its left edge (`.flat` for centred ones). It is the section
  kicker on the gallery and the label on the notes pad. Never put a tape inside a button.
- **Timecode chip** `.tc`: accent-soft fill, accent-ink mono 12 px, radius 6; a button when it seeks.
- **Pin** `.pin` / `.mk`: a 22–26 px teardrop (`border-radius: 50% 50% 50% 0/4px`, rotated −45°) in the accent, green
  when fixed, with the note number upright inside.
- **Stamp** `.stamp`: a double-ring rubber stamp in accent ink, rotated −3°, for the licence.

## Fields, cards, code

- **Compose box** `.compose`: an index card on surface-0 with a 1.5 px `--line-2` border, radius 10; on focus the
  border turns ink, the card lifts to surface-2 and gets the hard shadow. Textareas have no border of their own,
  grow with their content and use `--ink-3` placeholders.
- **Cards** (`.sheet`, `.rv-wait`, `.more a`, `.lic`): surface-2, radius 16 (10 in lists), `--sh-1` + a 1 px line.
  Hover on a link card lifts it to the hard shadow.
- **Frame** `.frame`: a film frame around a screen: deck fill, 14/10 px padding, radius 16, sprocket holes top and
  bottom (`--hole` dots on a 16 × 14 grid; `.sm` = 10/7 px, 12 × 10). The review page's reel uses the same holes.
- **Viewer** `.viewer`: the review page's screen plus its control deck fused in one radius-16 block.
- **Code block** `.code`: deck fill, radius 10, a header row (uppercase mono "who it is for" on the left, a quiet
  `.btn.sm.copy` on the right) above a `pre.cmd` that scrolls sideways. The button never overlaps the command.
- **Tables** `.lens`: hairline rows, mono digits, the default row on accent-soft; cells never wrap (the wrapper
  scrolls sideways if it must), heads may. **X-sheet** `.xsheet`: the six steps as an exposure sheet, numbered
  `01…06` in accent ink, ruled with lines.

## Motion

- Nothing eases. Every transition is `steps(2, end)` over 120 ms; longer motions are `steps(n)` at 8 drawings a
  second (`125 ms`): puppets turn on hover in six drawings,
  the caret blinks on `steps(1)`, the waiting dot breathes on `steps(6)`.
- Loops only play while on screen (IntersectionObserver), paused otherwise.
- `prefers-reduced-motion: reduce`: all animations off, transitions off, hover transforms off, loops wait for a
  click, smooth scrolling off. The puppets still turn on click.

## Layout

- Gallery: one column, `max-width 1180px`, gutter `clamp(16px, 4vw, 40px)`. Film blocks alternate 1.25fr / 1fr.
  Breakpoints: 960 (process 4 → 2, review 2 → 1), 860 (nav hides, films and install stack, steps 3 → 1 with
  the number beside the title), 760 (cast 8 → 4, footer cards 3 → 1), 600 (licence stacks, hero boxes per
  language, footer links wrap without the spacer), 520 (GitHub label hides, hero tape shrinks), 480 (fit lists 1 column; cast labels 14 px in a 66 px box so two-word names take two lines
  and "Needle-felt" still fits a cell). The film kicker (`.meta .kind`) never shrinks; the accent rule beside it
  keeps at least 24 px.
- Review page: `max-width 1840px`; stage `1fr` + desk `clamp(340px, 27vw, 440px)`, gap 28; the desk scrolls on its
  own at ≥ 1000. Breakpoints: 1000 (one column), 760 (bar wraps, title first, keys hidden, strip 48 px), 480 (pills
  share a row, buttons fill the row, timecode 15 px).
- "How it works" shows the same four panes as the README's `docs/readme/process.webp` (one function in `build.py`
  draws both; the site's `media/process/p1-4.webp` at twice the size): character sheet and action sheet centred both
  ways on a transparency checker, then the empty background and the frame in the film, a chevron between each.
- Only the eight released styles appear, on the site and in the READMEs. The READMEs' style section is generated
  (GitHub strips CSS): two rows of four cards (`docs/readme/cards/<id>-<lang>.webp`, drawn by `build.py`: a paper
  card with the film frame, the poster, its length, the reel number, style and film title, on a transparent shadow
  that sits on GitHub's light and dark pages), each row followed by one `<sub>` line with the ids and full-film links.
- Phone width has a 16 px gutter and no horizontal scroll; code commands scroll inside their block.
- Accessibility: every control is a real `button` or `a` with a visible focus ring; icon buttons carry
  `aria-label`; the page language is set on `<html lang>`; colour is never the only signal (dots, text and badges
  carry the state too).
