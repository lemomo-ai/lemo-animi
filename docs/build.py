#!/usr/bin/env python3
"""build.py: the lemo-animi gallery site and its media, from docs/content.json and styles/*/style.json.

    ~/lemo-animi-env/venv/bin/python docs/build.py            # build what is missing or out of date
    ~/lemo-animi-env/venv/bin/python docs/build.py --force    # rebuild all media
    ... --films DIR      folder with the sample films <id>-vN.mp4 (default: $LEMO_ANIMI_FILMS; without it existing media are kept)

Writes (all under docs/):
    media/<id>.webp        poster still (styles/<id>/poster.jpg, or a frame of the sample film), <= 150 KB
    media/<id>.mp4         ~6 s muted seamless loop from the middle of the latest sample film, 640 px, <= 900 KB
    media/manifest.json    what each media file was cut from (so re-runs skip unchanged ones)
    content.json           styles.<id>.film.seconds refreshed from the released files (ffprobe, whole seconds), when --films is given
    media/process/p1-4.webp  the four "how it works" panes, the same drawing as readme/process.webp (needs --src and --films)
    readme/cast.webp, readme/process.webp, readme/cards/<id>-<lang>.webp   pictures for the READMEs
    index.html, zh/index.html                     the gallery (English, Chinese)
    ../README.md, ../README.zh-CN.md              only the style cards between the styles:start / styles:end markers

Content and presentation are kept apart: all page text and the sample-film details live in docs/content.json;
style names, one-liners and good/bad-for lists come from style.json. page() below only lays them out; the look is
docs/assets/site.css, built on the design system in docs/DESIGN.md (shared with scripts/review.py).
The full sample films are not in the repository: the page links them from the GitHub release named in content.json.
Needs: Python 3 + Pillow (webp), ffmpeg/ffprobe.
"""
import argparse, html, json, os, re, shutil, subprocess, sys
from io import BytesIO
from pathlib import Path

from PIL import Image

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
SKILL_DIR = ROOT / 'plugin' / 'skills' / 'lemo-animi'   # the skill itself (the plugin's only skill)
STYLES = SKILL_DIR / 'styles'
MEDIA = DOCS / 'media'
FILMS_DIR = None

# The released styles, in this order. Only these appear on the site and in the READMEs.
PUBLISHED = ['clay', 'papercraft', 'tin', 'felt', 'cardboard', 'wood', 'crochet', 'fabric']

REPO_URL = 'https://github.com/lemomo-ai/lemo-animi'

# Styles without poster.jpg take a frame of the sample film at this time (s). Loops start mid-film unless set here.
POSTER_AT = {'tin': 24.0}
LOOP_AT = {'papercraft': 34.5, 'wood': 10.0}
LOOP_LEN, XFADE = 6.0, 0.5
LOOP_MAX, POSTER_MAX = 880_000, 150_000
ENC = 'h264-q2'  # bump when the loop encoding changes, so re-runs re-encode
# The films carry burned-in subtitles at ~85-91% of the height: film-derived media keep a 16:9 window above them.
CROP = 'crop=trunc(iw*0.8/2)*2:trunc(ih*0.8/2)*2:trunc(iw*0.1/2)*2:trunc(ih*0.02/2)*2'

# The cast: each style's lead from its sample film's character sheet (front, 3/4, side, back on a transparent
# background), and the clay film's sheets, background and a frame for "how it works". Paths are inside the sample film projects (--src).
CAST = {'clay': 'clay/src/char_bobo.png', 'papercraft': 'papercraft/src/char_fox.png', 'tin': 'tin/src/char_dudu.png',
        'felt': 'felt/src/char_tt.png', 'cardboard': 'cardboard/src/char_fang.png', 'wood': 'wood/src/char_lizi.png',
        'crochet': 'crochet/src/char_pupu.png', 'fabric': 'fabric/src/char_dou.png'}
PROCESS = {'sheet': 'clay/src/char_bobo.png', 'action': 'clay/src/sheet_bobo_toss.png', 'bg': 'clay/src/bg_stove_mid.png',
           'film': 'clay', 'at': 17.5}
CAST_H = 320                 # px, height of one view in the cast sprites
README = DOCS / 'readme'

CONTENT = json.loads((DOCS / 'content.json').read_text(encoding='utf-8'))
e = html.escape


CJK = r'[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]'


def tx(text, heading=False):
    """Escape page text and set its line breaks (paired with .nb { white-space: nowrap } in site.css):
    {a phrase} in content.json never breaks inside. In running text the last two words (English, when short) or the
    last four characters (Chinese) stay together, so no line ends a paragraph with one word or one character alone.
    Hyphenated words ("Wind-up", "hard-edged"; any length in a heading) never break at the hyphen."""
    out = re.sub(r'(?<![\w{-])([\w.]+(?:-[\w.]+)+)', lambda m: '{' + m.group(1) + '}' if heading or len(m.group(1)) <= 16 else m.group(1), e(text))
    out = re.sub(r'(\d[\d.]*–\d[\d.]*)', r'{\1}', out)                                         # 3.11–3.13
    out = re.sub(r'(\d) (?=(?:GB|MB|KB|s|min|px)\b)', r'\1&nbsp;', out)                         # 1.7 GB
    if heading:
        pass
    elif re.search(CJK, out):
        out = re.sub(r'((?:%s|[\w.]){4}[\s\u3000-\u303f\uff00-\uffef]*)$' % CJK, r'{\1}', out)   # last four characters
    else:
        out = re.sub(r'(^|\s)(\S{1,8}) (\S{1,7})$', r'\1\2&nbsp;\3', out)                          # last two short words
    out = re.sub(r'\{([^{}]*)\{([^{}]*)\}([^{}]*)\}', r'{\1\2\3}', out)                       # nested glue: keep the outer
    return re.sub(r'\{([^{}]+)\}', r'<span class="nb">\1</span>', out)


def hd(text):
    """A heading or label: tx() with hyphenated words kept whole."""
    return tx(text, heading=True)


def film_seconds(films):
    """The length the viewer gets: each released film's real duration (title and end cards included), whole seconds,
    written back to content.json so builds without the films, and the READMEs, show the same number."""
    if not films:
        return
    changed = []
    for sid in PUBLISHED:
        film = latest_film(films, sid)
        if not film:
            continue
        f = CONTENT['styles'][sid]['film']
        secs = round(duration(film))
        if f.get('seconds') != secs:
            changed.append(f'{sid} {f.get("seconds")} -> {secs}')
            f['seconds'] = secs
    if changed:
        (DOCS / 'content.json').write_text(json.dumps(CONTENT, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print('  content.json: film seconds ' + ', '.join(changed))

# --------------------------------------------------------------------------------------------- styles

def load_styles():
    out = {}
    for sid in PUBLISHED:
        d = json.loads((STYLES / sid / 'style.json').read_text(encoding='utf-8'))
        out[sid] = {k: d.get(k) for k in ('id', 'num', 'name', 'en', 'line', 'line_en')}
    return out


def style_text(s, lang):
    return (s['en'], s['line_en']) if lang == 'en' else (s['name'], s['line'])


# --------------------------------------------------------------------------------------------- media

def latest_film(films, sid):
    best = None
    if films and films.is_dir():
        for p in films.iterdir():
            m = re.fullmatch(re.escape(sid) + r'-v(\d+)\.mp4', p.name)
            if m and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), p)
    return best[1] if best else None


def duration(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def save_webp(im, dst, limit=POSTER_MAX):
    im = im.convert('RGB')
    if im.width > 960:
        im = im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS)
    for q in (82, 76, 70, 64, 58, 50, 42):
        buf = BytesIO(); im.save(buf, 'WEBP', quality=q, method=6)
        if buf.tell() <= limit:
            break
    dst.write_bytes(buf.getvalue())
    return q


def film_frame(film, t):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', str(film), '-frames:v', '1',
                        '-vf', CROP, '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True)
    return Image.open(BytesIO(r.stdout))


def encode_loop(film, start, dst):
    # one extra crossfade length, then fade the tail into the head: the last frame leads straight into the first
    fc = (f'[0:v]{CROP},scale=640:-2:flags=lanczos,setsar=1,fps=24,split[a][b];'
          f'[a]trim={XFADE}:{LOOP_LEN + XFADE},setpts=PTS-STARTPTS[m];'
          f'[b]trim=0:{XFADE},setpts=PTS-STARTPTS[h];'
          f'[m][h]xfade=transition=fade:duration={XFADE}:offset={LOOP_LEN - XFADE},format=yuv420p[v]')
    for crf in (22, 24, 26, 28, 30, 32, 34):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.3f}', '-t', f'{LOOP_LEN + XFADE + 0.1:.3f}',
                        '-i', str(film), '-filter_complex', fc, '-map', '[v]', '-an',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-profile:v', 'high',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(dst)], check=True)
        if dst.stat().st_size <= LOOP_MAX:
            break
    return crf


def build_media(styles, films, force):
    MEDIA.mkdir(parents=True, exist_ok=True)
    mf_path = MEDIA / 'manifest.json'
    old = json.loads(mf_path.read_text()) if mf_path.exists() else {}
    man = {}
    for sid in styles:
        prev, entry = old.get(sid, {}), {}
        film = latest_film(films, sid)
        poster_src = STYLES / sid / 'poster.jpg'
        # poster
        webp = MEDIA / f'{sid}.webp'
        if poster_src.exists():
            key = f'poster.jpg@{int(poster_src.stat().st_mtime)}'
        elif film:
            key = f'{film.name}@{POSTER_AT.get(sid, 20.0)}'
        else:
            key = prev.get('poster')
        if key and (force or not webp.exists() or prev.get('poster') != key):
            im = Image.open(poster_src) if poster_src.exists() else film_frame(film, POSTER_AT.get(sid, 20.0))
            q = save_webp(im, webp)
            print(f'  {sid}.webp  {key}  q{q}  {webp.stat().st_size // 1024} KB')
        entry['poster'] = key if webp.exists() else None
        # loop
        mp4 = MEDIA / f'{sid}.mp4'
        if film:
            d = duration(film)
            start = LOOP_AT.get(sid, d / 2 - (LOOP_LEN + XFADE) / 2)
            start = round(max(4.0, min(start, d - 4.0 - LOOP_LEN - XFADE)), 2)
            key = f'{film.name}@{start}+{LOOP_LEN} {ENC}'
            if force or not mp4.exists() or prev.get('loop') != key:
                crf = encode_loop(film, start, mp4)
                print(f'  {sid}.mp4   {key}  crf{crf}  {mp4.stat().st_size // 1024} KB')
            entry['loop'] = key
        elif mp4.exists():
            entry['loop'] = prev.get('loop')
            print(f'  {sid}: no sample film found, keeping media/{sid}.mp4')
        else:
            entry['loop'] = None
            print(f'  {sid}: no sample film found, card shows the still only')
        man[sid] = entry
    mf_path.write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    return man

# --------------------------------------------------------------------------------------------- cast and process

def sheet_views(im, n=4):
    """Split a character sheet (views side by side on transparency) into its n widest column runs, left to right."""
    import numpy as np
    col = (np.asarray(im)[:, :, 3] > 40).sum(0) > 2
    runs, x = [], 0
    while x < len(col):
        if col[x]:
            s = x
            while x < len(col) and col[x]:
                x += 1
            if runs and s - runs[-1][1] < 12:
                runs[-1][1] = x
            else:
                runs.append([s, x])
        x += 1
    runs = sorted(sorted(runs, key=lambda r: r[0] - r[1])[:n])
    return [im.crop((a, 0, b, im.height)).crop(im.crop((a, 0, b, im.height)).getbbox()) for a, b in runs]


def cast_sprite(path):
    """Four views on one transparent strip, equal cells, feet on the bottom edge, all views at one scale."""
    views = sheet_views(Image.open(path).convert('RGBA'))
    k = CAST_H / max(v.height for v in views)
    views = [v.resize((round(v.width * k), round(v.height * k)), Image.LANCZOS) for v in views]
    cw = max(v.width for v in views) + 8
    out = Image.new('RGBA', (cw * len(views), CAST_H), (0, 0, 0, 0))
    for i, v in enumerate(views):
        out.paste(v, (i * cw + (cw - v.width) // 2, CAST_H - v.height), v)
    return out, cw


def stamp(p):
    return f'{p.name}@{int(p.stat().st_mtime)}'


def build_cast(src, force):
    """media/cast/<id>.webp sprites, readme/cast.webp, the process panes. Returns {id: cell width} for the page."""
    mf_path = MEDIA / 'cast.json'
    old = json.loads(mf_path.read_text()) if mf_path.exists() else {}
    if not src:
        return old
    (MEDIA / 'cast').mkdir(parents=True, exist_ok=True)
    man, sprites = {}, {}
    for sid, rel in CAST.items():
        p = src / rel
        dst = MEDIA / 'cast' / f'{sid}.webp'
        if not p.exists():
            if sid in old:
                man[sid] = old[sid]
            continue
        key = stamp(p)
        if force or not dst.exists() or (old.get(sid) or {}).get('key') != key or not README.joinpath('cast.webp').exists():
            sp, cw = cast_sprite(p)
            sp.save(dst, 'WEBP', quality=86, method=6)
            sprites[sid] = (sp, cw)
            print(f'  cast/{sid}.webp  {sp.width}x{sp.height}  {dst.stat().st_size // 1024} KB')
            man[sid] = dict(key=key, cw=cw, w=sp.width)
        else:
            man[sid] = old[sid]
    if sprites or force or not (README / 'cast.webp').exists():
        readme_cast(src)
    if force or not all((MEDIA / 'process' / f'p{i}.webp').exists() for i in range(1, 5)) or not (README / 'process.webp').exists():
        readme_process(src)
    mf_path.write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    return man


def readme_cast(src):
    """readme/cast.webp: the eight leads in a row on warm paper; one after another they turn round, on twos."""
    README.mkdir(exist_ok=True)
    order = [s for s in PUBLISHED if (src / CAST[s]).exists()]
    H, W, pad, CH = 250, 1600, 40, 360
    floor = CH - 52
    views = {}
    for sid in order:
        vs = sheet_views(Image.open(src / CAST[sid]).convert('RGBA'))
        k = H / max(v.height for v in vs)
        views[sid] = [v.resize((round(v.width * k), round(v.height * k)), Image.LANCZOS) for v in vs]
    slot = (W - 2 * pad) / len(order)
    turn = [0, 1, 2, 3, -2, -1, 0]           # front, 3/4, side, back, side and 3/4 mirrored, front: a full turn
    lag, hold = 3, 14
    n = lag * (len(order) - 1) + len(turn) + hold
    from PIL import ImageDraw, ImageFilter
    base = Image.new('RGB', (W, CH), (245, 239, 228))
    sh = Image.new('L', (W, CH), 0); d = ImageDraw.Draw(sh)
    for i, sid in enumerate(order):
        cx = pad + slot * (i + .5)
        w = views[sid][0].width * .42
        d.ellipse((cx - w, floor - 10, cx + w, floor + 12), fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    base.paste(Image.new('RGB', (W, CH), (122, 96, 66)), (0, 0), sh)
    frames = []
    for f in range(n):
        im = base.copy()
        for i, sid in enumerate(order):
            j = f - i * lag
            v = turn[j] if 0 <= j < len(turn) else 0
            pic = views[sid][abs(v)]
            if v < 0:
                pic = pic.transpose(Image.FLIP_LEFT_RIGHT)
            cx = pad + slot * (i + .5)
            im.paste(pic, (round(cx - pic.width / 2), floor - pic.height), pic)
        frames.append(im)
    frames[0].save(README / 'cast.webp', 'WEBP', save_all=True, append_images=frames[1:], duration=[1200] + [125] * (n - 1),
                   loop=0, quality=80, method=6)
    frames[0].save(README / 'cast.png')
    print(f'  readme/cast.webp  {n} frames  {(README / "cast.webp").stat().st_size // 1024} KB')

# --------------------------------------------------------------------------------------------- page
# Layout only: the look is docs/assets/site.css, the behaviour docs/assets/site.js, the words docs/content.json.

GH_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
THEME_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></svg>'
PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>'
COPY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>'

INSTALL = [
    [('Codex', 'codex plugin marketplace add lemomo-ai/lemo-animi\ncodex plugin add lemo-animi@lemomo-ai'),
     ('Claude Code', '/plugin install lemo-animi --marketplace lemomo-ai/lemo-animi')],
    [],
]


def links(lang):
    rd = f'{REPO_URL}/blob/main/' + ('README.md' if lang == 'en' else 'README.zh-CN.md')
    return rd, rd + ('#install' if lang == 'en' else '#安装'), f'{REPO_URL}/blob/main/plugin/skills/lemo-animi/SKILL.md'


def sprite(sid, pre, cast, cls='sprite'):
    c = cast.get(sid) or {}
    if not c.get('cw'):
        return ''
    return (f'<span class="{cls}" style="aspect-ratio:{c["cw"]}/{CAST_H};'
            f'background-image:url({pre}media/cast/{sid}.webp)"></span>')


def listing(xs, lang):
    return ''.join(f'<li>{tx(x)}</li>' for x in xs)


def film_block(sid, s, i, lang, pre, man, cast):
    t, c = CONTENT['text'][lang], CONTENT['styles'][sid]
    f = c['film']
    name, line = style_text(s, lang)
    title = f['title'][lang]
    loop = (MEDIA / f'{sid}.mp4').exists() and (man.get(sid) or {}).get('loop')
    screen = (f'<video data-loop src="{pre}media/{sid}.mp4" poster="{pre}media/{sid}.webp" muted loop playsinline preload="none" '
              f'aria-label="{e(title)}: {e(t["loop"])}"></video>' if loop else
              f'<img src="{pre}media/{sid}.webp" alt="{e(title)}" loading="lazy">')
    mini = sprite(sid, pre, cast)
    return f'''<article class="film" id="{sid}" style="--accent:{c['accent']}">
  <div class="frame"><div class="screen">{screen}<span class="tag">{e(t['loop'])}</span></div></div>
  <div>
    <div class="meta"><span class="no">{i:02d}</span><span class="kind">{hd(name)}</span><span class="rule"></span></div>
    <div class="who">{f'<span class="mini" data-turn tabindex="-1">{mini}</span>' if mini else ''}<div>
      <h3>{hd(title)}</h3><div class="len num">{f['seconds']:g} {e(t['seconds'])}</div></div></div>
    <p class="story">{tx(f['story'][lang])}</p>
    <div class="row"><a class="btn primary" href="{CONTENT['films_url'] + f['file']}">{PLAY_ICON}{e(t['films_watch'])}</a>
      <span class="say-id">{e(t['say'])} <code>{sid}</code></span></div>
    <div class="fit"><div><b>{e(t['good'])}</b><ul>{listing(c['good_for'][lang], lang)}</ul></div>
      <div class="no"><b>{e(t['bad'])}</b><ul>{listing(c['bad_for'][lang], lang)}</ul></div></div>
  </div>
</article>'''


def page(styles, lang, man, cast):
    t = CONTENT['text'][lang]
    pre = '' if lang == 'en' else '../'
    other = 'zh/' if lang == 'en' else '../'
    readme, install, skill = links(lang)
    nav, mail = t['nav'], CONTENT['contact']
    actors = '\n'.join(
        f'<a class="actor" href="#{sid}" data-turn><span class="pup">{sprite(sid, pre, cast)}</span>'
        f'<span class="label"><b>{hd(style_text(styles[sid], lang)[0].replace(" Stop-motion", "").replace("定格", ""))}</b><span>{sid}</span></span></a>'
        for sid in PUBLISHED)
    films = '\n'.join(film_block(sid, styles[sid], i + 1, lang, pre, man, cast) for i, sid in enumerate(PUBLISHED))
    # the same four panes as readme/process.webp (character sheet, action sheet, background, the frame in the film)
    proc = ''.join(f'<figure><div class="pane"><img src="{pre}media/process/p{i + 1}.webp" alt="" width="744" height="560" loading="lazy"></div>'
                   f'<figcaption><b>{hd(a)}</b>{tx(b)}</figcaption></figure>' for i, (a, b) in enumerate(t['proc']))
    steps = ''.join(f'<li><b>{hd(a)}</b><span>{tx(b)}</span></li>' for a, b in t['how'])
    lens_h = ''.join(f'<th>{e(x)}</th>' for x in t['len_h'])
    lens = ''.join(f'<tr{" class=def" if i == 1 else ""}>' + ''.join(f'<td>{e(x)}</td>' for x in row) + '</tr>' for i, row in enumerate(t['lens']))
    cmds = ''
    for (h, p), block in zip(t['install_steps'], INSTALL):
        # each command is a block: a header row (who it is for, the copy button) above the command, which scrolls sideways
        codes = ''.join(f'<div class="code"><div class="code-h"><span class="who">{e(w)}</span>'
                        f'<button class="btn sm quiet copy" type="button" data-done="{e(t["copied"])}">{COPY_ICON}<span>{e(t["copy"])}</span></button></div>'
                        f'<pre class="cmd">{e(cmd)}</pre></div>' for w, cmd in block)
        cmds += f'<li><div class="h"><span>{hd(h)}</span></div>{codes}{f"<div class=p>{tx(p)}</div>" if p else ""}</li>'
    more = ''.join(f'<a href="{u}"><b>{e(n)}</b><span>{tx(d)}</span></a>' for n, u, d in t['more'])
    rpts = ''.join(f'<li><span class="pin"><i>{i + 1}</i></span><div><b>{hd(a)}</b><span>{tx(b)}</span></div></li>' for i, (a, b) in enumerate(t['review_pts']))
    lic = ''.join(f'<li><b>{hd(a)}{". " if lang == "en" else "："}</b>{tx(b)}</li>' for a, b in t['licence_pts'])
    rshot = f"{pre}readme/review{'' if lang == 'en' else '-zh'}.webp"
    return f'''<!doctype html>
<html lang="{'en' if lang == 'en' else 'zh-CN'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t['title'])}</title>
<meta name="description" content="{e(t['desc'])}">
<meta property="og:title" content="{e(t['title'])}">
<meta property="og:description" content="{e(t['desc'])}">
<meta property="og:image" content="https://lemomo-ai.github.io/lemo-animi/readme/cast.png">
<link rel="alternate" hreflang="{'zh-CN' if lang == 'en' else 'en'}" href="{other}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%23d9473b'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,500..700,0..100,0..1&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{pre}assets/site.css">
</head>
<body>
<header class="top"><div class="wrap">
  <a class="mark" href="#top" id="top-link"><i></i>lemo-animi</a>
  <nav><a href="#films">{e(nav['films'])}</a><a href="#how">{e(nav['how'])}</a><a href="#review">{e(nav['review'])}</a><a href="#install">{e(nav['install'])}</a><a href="#licence">{e(nav['licence'])}</a></nav>
  <div class="tools"><a class="btn sm" href="{other}" hreflang="{'zh-CN' if lang == 'en' else 'en'}">{e(t['switch'])}</a>
    <button class="btn sm icon" id="theme" type="button" aria-label="{e(t['theme'])}" title="{e(t['theme'])}">{THEME_ICON}</button>
    <a class="btn sm gh" href="{REPO_URL}" aria-label="GitHub">{GH_ICON}<span>GitHub</span></a></div>
</div></header>

<main id="top">
<div class="hero"><div class="wrap">
  <div class="tape flat">{e(t['kicker'])}</div>
  <h1>{hd(t['h1'])}</h1>
  <p class="lede">{tx(t['lede'])}</p>
  <div class="say"><b>{e(t['you_say'])}</b><div class="say-l"><q>{hd(t['ask'])}</q></div></div>
  <div class="cta"><a class="btn lg primary" href="#films">{PLAY_ICON}{e(t['cta_films'])}</a><a class="btn lg" href="#install">{e(t['cta_install'])}</a></div>
</div>
<div class="shelf" aria-label="{e(t['cast_h'])}"><div class="cast">
{actors}
</div></div>
<div class="wrap"><p class="cast-p">{tx(t['cast_p'])}</p></div>
</div>

<section id="films"><div class="wrap">
  <div class="sec-head"><div class="tape">{e(t['styles_h'])}</div><h2>{hd(t['films_h'])}</h2>
    <p class="lede">{tx(t['films_p'] + (' ' if lang == 'en' else '') + t['styles_p'])}</p><p class="note">{tx(t['loop_note'])}</p></div>
{films}
</div></section>

<section id="how"><div class="wrap">
  <div class="tape">{e(t['how_h'])}</div>
  <h2>{hd(t['proc_h'])}</h2>
  <p class="lede">{tx(t['proc_p'])}</p>
  <div class="proc">{proc}</div>
  <h2 class="sm steps-h">{hd(t['steps_h'])}</h2>
  <ol class="xsheet">{steps}</ol>
  <div class="tablewrap"><table class="lens num"><thead><tr>{lens_h}</tr></thead><tbody>{lens}</tbody></table></div>
</div></section>

<section id="review"><div class="wrap">
  <div class="tape">{e(t['review_eyebrow'])}</div>
  <h2>{hd(t['review_h'])}</h2>
  <p class="lede">{tx(t['review_p'])}</p>
  <div class="rv">
    <figure class="desk"><img src="{rshot}" alt="{e(t['review_alt'])}" width="1600" height="960" loading="lazy"></figure>
    <div class="rv-side">
      <ol class="rv-pts">{rpts}</ol>
      <div class="rv-wait"><span class="pill ok live">{e(t['review_pill'])}</span><b>{hd(t['review_wait_h'])}</b><p>{tx(t['review_wait'])}</p></div>
    </div>
  </div>
</div></section>

<section id="install"><div class="wrap inst">
  <div><div class="tape">{e(t['install_h'])}</div><h2>{hd(t['install_h2'])}</h2>
    <p class="lede">{tx(t['install_p'])}</p><p class="need">{tx(t['need'])}</p><p class="need model">{tx(t['model'])}</p>
    <p class="need"><a href="{install}">{e(t['install_link'])}</a>&nbsp;·&nbsp;<a href="{skill}">{e(t['skill'])}</a></p></div>
  <ol class="cmds">{cmds}</ol>
</div></section>

<section id="licence"><div class="wrap">
  <div class="lic"><a class="stamp" href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a><div>
    <h2 class="xs">{hd(t['licence_h'])}</h2>
    <ul>{lic}</ul>
    <p class="lic-c">{e(t['licence_contact'])} <span class="nb"><a href="mailto:{mail}">{mail}</a> · <a href="{REPO_URL}/blob/main/LICENSE">LICENSE</a></span></p></div></div>
</div></section>
</main>

<footer><div class="wrap">
  <div class="tape">{e(t['more_h'])}</div>
  <div class="more">{more}</div>
  <div class="foot"><span>{e(t['by'])}</span><a href="https://x.com/lemomo_ai">@lemomo_ai</a><a href="mailto:{mail}">{mail}</a>
    <span class="sp"></span><a href="{readme}">{e(t['readme'])}</a><a href="{skill}">{e(t['skill'])}</a><a href="{other}">{e(t['switch'])}</a></div>
  <p class="foot made">{tx(t['foot'])}</p>
</div></footer>
<script src="{pre}assets/site.js"></script>
</body>
</html>
'''

# --------------------------------------------------------------------------------------------- README styles
# GitHub strips CSS, so the README's style section is pictures plus plain inline HTML, laid out like the opuscar
# README: two rows of four cards (the label is drawn into each card, one card per language), each row followed by one
# small line with the four ids and full-film links.

SITE_URL = 'https://lemomo-ai.github.io/lemo-animi/'
CARD_W = 520
README_TEXT = {
    'en': dict(file='README.md', site=SITE_URL, films='▶ Full films: ',
               alt='{n} · {name}: {line}. Sample film: {title}, {len}. Opens it in the gallery.'),
    'zh': dict(file='README.zh-CN.md', site=SITE_URL + 'zh/', films='▶ 完整样片：',
               alt='{n} · {name}：{line}。样片《{title}》，{len}。在画廊里打开。'),
}


def mmss(sec):
    return f'{int(sec) // 60}:{int(sec) % 60:02d}'


def short_name(s, lang):
    name = style_text(s, lang)[0]
    return name.replace(' Stop-motion', '').replace('定格', '')


def mix(c1, c2, k):
    return tuple(round(a * k + b * (1 - k)) for a, b in zip(c1, c2))


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def readme_card(sid, s, lang, i):
    """One style card, on a transparent margin with a soft shadow so it sits on GitHub's light and dark pages alike:
    a paper card holding a film frame (the gallery's sprocket holes) with the poster and its length, then the reel
    number, the style and the film's title."""
    from PIL import ImageDraw, ImageFilter, ImageFont
    font = SKILL_DIR / 'fonts' / 'SourceHanSansCN-Bold.otf'
    F = lambda px: ImageFont.truetype(str(font), px)
    c = CONTENT['styles'][sid]
    f = c['film']
    paper, line, ink, ink2 = (253, 248, 239), (217, 205, 184), (30, 25, 21), (100, 90, 78)
    deck, hole = (39, 33, 27), (199, 192, 181)
    acc_ink = mix(hexrgb(c['accent']), ink, .62)
    W, m, pad = CARD_W, 14, 12
    cw = W - 2 * m
    fw = cw - 2 * pad                       # film frame
    sw = fw - 2 * 10                        # screen inside it
    sh = round(sw * 9 / 16)
    fh = sh + 2 * 15
    th = 22 + 30 + 14 + 26 + 4              # gap, title, gap, style
    ch = pad + fh + th + 22
    H = ch + 2 * m + 6
    im = Image.new('RGBA', (W, H), (60, 40, 20, 0))
    shadow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((m, m + 5, m + cw, m + ch + 5), 20, fill=70)
    im.putalpha(shadow.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((m, m, m + cw - 1, m + ch - 1), 20, fill=paper, outline=line, width=2)
    fx, fy = m + pad, m + pad
    d.rounded_rectangle((fx, fy, fx + fw - 1, fy + fh - 1), 14, fill=deck)
    for y in (fy + 7, fy + fh - 8):                                   # sprocket holes
        for x in range(fx + 12, fx + fw - 8, 16):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=hole)
    poster = Image.open(MEDIA / f'{sid}.webp').convert('RGB')
    r = max(sw / poster.width, sh / poster.height)
    poster = poster.resize((round(poster.width * r), round(poster.height * r)), Image.LANCZOS)
    poster = poster.crop(((poster.width - sw) // 2, (poster.height - sh) // 2, (poster.width - sw) // 2 + sw, (poster.height - sh) // 2 + sh))
    pm = Image.new('L', (sw, sh), 0); ImageDraw.Draw(pm).rounded_rectangle((0, 0, sw - 1, sh - 1), 7, fill=255)
    sx, sy = fx + 10, fy + 15
    im.paste(poster, (sx, sy), pm)
    # the film's length, as the gallery's tag: a dark pill with a play mark
    ft = F(24); label = mmss(f['seconds'])
    tw = d.textlength(label, font=ft)
    px0, py1 = sx + 12, sy + sh - 12
    pill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle((px0, py1 - 38, px0 + 50 + tw, py1), 19, fill=(20, 16, 12, 170))
    im = Image.alpha_composite(im, pill); d = ImageDraw.Draw(im)
    d.polygon([(px0 + 15, py1 - 27), (px0 + 15, py1 - 11), (px0 + 29, py1 - 19)], fill=(255, 255, 255))
    d.text((px0 + 37, py1 - 19), label, font=ft, fill=(255, 255, 255), anchor='lm')
    # the film's title on the first line, small and quiet; then the reel number and the style
    tx0 = fx + 10                                                     # aligned with the poster's left edge
    ty = fy + fh + 22
    title = f['title'][lang] if lang == 'en' else f'《{f["title"][lang]}》'
    size = 21
    while d.textlength(title, font=F(size)) > cw - 2 * pad - 20 and size > 16:
        size -= 1
    d.text((tx0 - (6 if lang == 'zh' else 0), ty), title, font=F(size), fill=(138, 126, 110), anchor='lt')
    no, kind = f'{i:02d}', short_name(s, lang)
    ks = 31
    while d.textlength(f'{no}  {kind}', font=F(ks)) > cw - 2 * pad - 20 and ks > 24:
        ks -= 1
    fs = fn = F(ks)
    base = ty + 30 + 14 + round(ks * .8)                              # title line, gap, style cap height
    d.text((tx0, base), no, font=fn, fill=acc_ink, anchor='ls')
    d.text((tx0 + d.textlength(no, font=fn) + 10, base), kind, font=fs, fill=ink, anchor='ls')
    return im


def readme_cards(styles):
    """readme/cards/<id>-<lang>.webp, rewritten only when the picture changed."""
    out = README / 'cards'
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for lang in README_TEXT:
        for i, sid in enumerate(PUBLISHED):
            if not (MEDIA / f'{sid}.webp').exists():
                continue
            buf = BytesIO(); readme_card(sid, styles[sid], lang, i + 1).save(buf, 'WEBP', quality=86, method=6)
            dst = out / f'{sid}-{lang}.webp'
            if not dst.exists() or dst.read_bytes() != buf.getvalue():
                dst.write_bytes(buf.getvalue()); n += 1
    if n:
        print(f'  readme/cards: {n} cards written')


def update_readmes(styles):
    """Rewrite the style cards between <!-- styles:start ...--> and <!-- styles:end --> in both READMEs."""
    readme_cards(styles)
    for lang, rt in README_TEXT.items():
        p = ROOT / rt['file']
        if not p.exists():
            continue
        cards, films = [], []
        for i, sid in enumerate(PUBLISHED):
            s, c = styles[sid], CONTENT['styles'][sid]
            f = c['film']
            name, line = style_text(s, lang)
            title = f['title'][lang] if lang == 'en' else f'《{f["title"][lang]}》'
            alt = rt['alt'].format(n=f'{i + 1:02d}', name=name, line=line, title=f['title'][lang], len=mmss(f['seconds']))
            cards.append(f'<a href="{rt["site"]}#{sid}"><img src="docs/readme/cards/{sid}-{lang}.webp" width="25%" align="top" alt="{e(alt)}"></a>')
            films.append(f'<code>{sid}</code> <a href="{CONTENT["films_url"] + f["file"]}">{e(title)}</a>')
        rows = []
        for k in (0, 4):                                    # a row of four cards, then its films, as the opuscar README does
            rows += [''.join(cards[k:k + 4]), '', f'<sub>{rt["films"]}' + ' · '.join(films[k:k + 4]) + '</sub>', '']
        block = '\n'.join(rows).rstrip('\n')
        text = p.read_text(encoding='utf-8')
        new, n = re.subn(r'(<!-- styles:start[^\n]*-->\n).*?(\n<!-- styles:end -->)', lambda mm: mm.group(1) + block + mm.group(2),
                         text, flags=re.S)
        if n and new != text:
            p.write_text(new, encoding='utf-8')
            print(f'  {rt["file"]}: style cards updated')


def process_panes(src, k=1):
    """The four "how it works" panes at k times 372 x 280: character sheet and action sheet on a transparency checker,
    each centred both ways, then the empty background and the film's frame, cropped to fill. None without the film."""
    from PIL import ImageDraw
    film = latest_film(FILMS_DIR, PROCESS['film']) if FILMS_DIR else None
    if not film:
        return None
    sheet = Image.open(src / PROCESS['sheet']).convert('RGBA')
    act = Image.open(src / PROCESS['action']).convert('RGBA')
    bg = Image.open(src / PROCESS['bg']).convert('RGB')
    frame = film_frame(film, PROCESS['at']).convert('RGB')
    pw, ph, sq = 372 * k, 280 * k, 14 * k

    def checker():
        c = Image.new('RGB', (pw, ph), (255, 250, 241)); cd = ImageDraw.Draw(c)
        for y in range(0, ph, sq):
            for x in range(0, pw, sq):
                if (x // sq + y // sq) % 2: cd.rectangle((x, y, x + sq - 1, y + sq - 1), fill=(236, 227, 211))
        return c

    def fit(im, box_w, box_h):
        im = im.copy(); im.thumbnail((box_w, box_h), Image.LANCZOS); return im

    def cover(im):
        r = max(pw / im.width, ph / im.height)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        return im.crop(((im.width - pw) // 2, (im.height - ph) // 2, (im.width - pw) // 2 + pw, (im.height - ph) // 2 + ph))

    panes = []
    for im, mx, my in ((sheet, 24, 40), (act, 24, 24)):
        pn = checker(); v = fit(im, pw - mx * k, ph - my * k)
        pn.paste(v, ((pw - v.width) // 2, (ph - v.height) // 2), v); panes.append(pn)
    return panes + [cover(bg), cover(frame)]


def readme_process(src):
    """readme/process.webp: character sheet, action sheet, empty background, the frame in the film; left to right.
    The site shows the same four panes (media/process/p1-4.webp, drawn at twice the size) in a row that wraps."""
    from PIL import ImageDraw
    panes = process_panes(src)
    if not panes:
        return
    pw, ph, gap, pad = 372, 280, 40, 24
    W = pad * 2 + pw * 4 + gap * 3
    out = Image.new('RGB', (W, ph + pad * 2), (245, 239, 228))
    d = ImageDraw.Draw(out)
    mask = Image.new('L', (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw - 1, ph - 1), 16, fill=255)
    for i, pn in enumerate(panes):
        x = pad + i * (pw + gap)
        out.paste(pn, (x, pad), mask)
        if i < 3:
            cx, cy = x + pw + gap // 2, pad + ph // 2
            d.line((cx - 8, cy - 9, cx + 4, cy, cx - 8, cy + 9), fill=(34, 29, 23), width=4, joint='curve')
    README.mkdir(exist_ok=True)
    out.save(README / 'process.webp', 'WEBP', quality=84, method=6)
    print(f'  readme/process.webp  {(README / "process.webp").stat().st_size // 1024} KB')
    (MEDIA / 'process').mkdir(parents=True, exist_ok=True)
    for i, pn in enumerate(process_panes(src, 2)):
        save_webp(pn, MEDIA / 'process' / f'p{i + 1}.webp', 90_000)
    print('  media/process/p1-4.webp')

# --------------------------------------------------------------------------------------------- main

def du(p):
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--films', default=os.environ.get('LEMO_ANIMI_FILMS', ''), help='folder with the sample films <id>-vN.mp4')
    ap.add_argument('--src', default=os.environ.get('LEMO_ANIMI_SRC', ''), help='folder with the sample film projects (<style>/src/...), for the cast')
    ap.add_argument('--force', action='store_true', help='rebuild all media')
    a = ap.parse_args()
    global FILMS_DIR
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            sys.exit(f'{tool} not found')
    styles = load_styles()
    films = Path(a.films) if a.films else Path('/nonexistent')
    film_seconds(films if films.is_dir() else None)
    print(f'media  (films: {films if films.is_dir() else "not found, keeping existing media"})')
    man = build_media(styles, films if films.is_dir() else None, a.force)
    FILMS_DIR = films if films.is_dir() else None
    src = Path(a.src) if a.src and Path(a.src).is_dir() else None
    print(f'cast  (src: {src or "not found, keeping existing cast"})')
    cast = build_cast(src, a.force)
    print('pages')
    (DOCS / 'index.html').write_text(page(styles, 'en', man, cast), encoding='utf-8')
    (DOCS / 'zh').mkdir(exist_ok=True)
    (DOCS / 'zh' / 'index.html').write_text(page(styles, 'zh', man, cast), encoding='utf-8')
    print('  index.html, zh/index.html')
    update_readmes(styles)
    print(f'docs/ total: {du(DOCS) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
