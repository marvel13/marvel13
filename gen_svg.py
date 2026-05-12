#!/usr/bin/env python3
"""Generate neofetch-style GitHub profile SVG."""
import html, sys

ART_FILE = '/Users/salwynmathew/Downloads/ascii-art.txt'
OUT_DARK  = '/Users/salwynmathew/Code/profile-readme/dark_mode.svg'

# ── Palette ──────────────────────────────────────────────
BG  = '#161b22'
FG  = '#c9d1d9'
KEY = '#ffa657'
VAL = '#a5d6ff'
DOT = '#616e7f'
GRN = '#3fb950'
RED = '#f85149'
WHT = '#ffffff'
SEC = '#c9d1d9'

# ── Typography ───────────────────────────────────────────
FONT    = "Consolas,'Courier New',monospace"
ART_FS  = 9
ART_LH  = 13
ART_CW  = 5.41    # char width at Consolas 9px

INFO_FS = 13
INFO_LH = 21
INFO_CW = 7.82    # char width at Consolas 13px

# ── Layout ───────────────────────────────────────────────
PAD = 18
GAP = 32
TOTAL = 62        # monospace columns for key+dots+value

# ── ASCII art ────────────────────────────────────────────
with open(ART_FILE, encoding='utf-8', errors='replace') as f:
    art = f.read().splitlines()
while art and not art[-1].strip():
    art.pop()

art_cols   = max(len(l) for l in art)
art_px_w   = art_cols * ART_CW
art_px_h   = len(art) * ART_LH

# ── Canvas ───────────────────────────────────────────────
info_x  = PAD + art_px_w + GAP
info_w  = TOTAL * INFO_CW
SVG_W   = int(info_x + info_w + PAD * 2)
SVG_H   = max(int(PAD + art_px_h + PAD), 560)

# ── Row builders ─────────────────────────────────────────
def kv(key, val):
    space = TOTAL - len(key) - len(val)
    if space < 4:
        val = val[:TOTAL - len(key) - 6] + '...'
        space = 5
    dots = ' ' + '.' * (space - 2) + ' '
    return [(key, KEY), (dots, DOT), (val, VAL)]

def header(text):
    return [(text, WHT)]

def divider():
    return [('—' * TOTAL, DOT)]

def section(text):
    pad = '—' * max(0, TOTAL - len(text) - 1)
    return [(text + ' ', SEC), (pad, DOT)]

def blank():
    return []

# ── Info rows ────────────────────────────────────────────
rows = [
    header('salwyn@mathew'),
    divider(),
    kv('OS:',    'macOS Sequoia'),
    kv('Host:',  'MikeLegal'),
    kv('Role:',  'SDE AI'),
    kv('IDE:',   'VS Code, Claude Code'),
    blank(),
    kv('Languages.Programming:', 'Python, JavaScript, TypeScript'),
    kv('Languages.Computer:',    'HTML, CSS, JSON, YAML'),
    blank(),
    kv('Hobbies.Software:', 'LLM pipelines, MCP servers'),
    kv('Hobbies.IRL:',      'Guitar, Bird Watching'),
    blank(),
    section('— Contact'),
    kv('LinkedIn:',  'salwyn-mathew-4579381b7'),
    kv('GitHub:',    'marvel13'),
    kv('Instagram:', '_salwinator'),
    blank(),
    section('— GitHub Stats'),
    [('Repos: ', KEY), ('10', GRN), ('  |  Followers: ', KEY), ('3', GRN)],
    [('Commits: ', KEY), ('78', GRN), ('  |  Stars: ', KEY), ('0', GRN)],
]

# ── Render ───────────────────────────────────────────────
def render(out_file, bg=BG):
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">\n'
        f'<defs><style>'
        f'text{{font-family:{FONT};white-space:pre;}}'
        f'.a{{font-size:{ART_FS}px;fill:{FG};}}'
        f'.i{{font-size:{INFO_FS}px;}}'
        f'</style></defs>\n'
        f'<rect width="{SVG_W}" height="{SVG_H}" rx="12" fill="{bg}"/>\n'
    )

    # ASCII art lines
    for i, line in enumerate(art):
        y = PAD + ART_FS + i * ART_LH
        esc = html.escape(line) if line else ' '
        parts.append(
            f'<text class="a" x="{PAD}" y="{y}" xml:space="preserve">{esc}</text>\n'
        )

    # Info lines
    for i, row in enumerate(rows):
        if not row:
            continue
        y = PAD + INFO_FS + i * INFO_LH
        spans = ''.join(
            f'<tspan fill="{c}">{html.escape(t)}</tspan>'
            for t, c in row
        )
        parts.append(
            f'<text class="i" x="{info_x:.1f}" y="{y}" xml:space="preserve">{spans}</text>\n'
        )

    parts.append('</svg>')
    svg = ''.join(parts)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"✓ {out_file}  ({SVG_W}×{SVG_H}px, {len(art)} art lines, {sum(1 for r in rows if r)} info rows)")

render(OUT_DARK)
