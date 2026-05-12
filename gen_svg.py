#!/usr/bin/env python3
"""Generate neofetch-style GitHub profile SVG with half-block pixel art."""

import html, re, pathlib, argparse

# ── Args ──────────────────────────────────────────────────
# --pokemon PATH  overrides the default sprite (used by GitHub Actions)
_parser = argparse.ArgumentParser()
_parser.add_argument("--pokemon", default=None, help="Path to colorscript file")
_args = _parser.parse_args()

REPO_DIR    = pathlib.Path(__file__).parent
SPRITE_FILE = _args.pokemon or (
    "/Users/salwynmathew/pokemon-colorscripts/colorscripts/small/regular/gengar"
)
OUT_DARK = str(REPO_DIR / "dark_mode.svg")
FONT_B64 = (REPO_DIR / "font_regular.b64").read_text().strip()

# ── Palette ──────────────────────────────────────────────
BG = "#161b22"
FG = "#c9d1d9"
KEY = "#ffa657"
VAL = "#a5d6ff"
DOT = "#616e7f"
GRN = "#3fb950"
WHT = "#ffffff"
SEC = "#c9d1d9"

# ── Typography ───────────────────────────────────────────
FONT_NAME = "SpaceMono"
FONT = f"'{FONT_NAME}','Courier New',monospace"
INFO_FS = 13
INFO_LH = 21
INFO_CW = 7.82

# ── Layout ───────────────────────────────────────────────
PAD = 20
GAP = 36
TOTAL = 62  # monospace columns for key+dots+value

# ── Parse half-block colorscript ─────────────────────────
LOWER = "▄"  # U+2584: top=bg, bottom=fg
UPPER = "▀"  # U+2580: top=fg, bottom=bg
ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")


def parse_sprite(path):
    """Return list-of-rows; each row is list of (top_rgb, bot_rgb) or None for transparent."""
    raw = pathlib.Path(path).read_bytes().decode("utf-8", errors="replace")
    rows = []
    for line in raw.splitlines():
        cells = []
        fg = bg = (0, 0, 0)
        i = 0
        while i < len(line):
            m = ANSI_RE.match(line, i)
            if m:
                params = m.group(1).split(";")
                p = 0
                while p < len(params):
                    code = int(params[p]) if params[p] else 0
                    if code == 0:
                        fg = bg = (0, 0, 0)
                    elif code == 38 and p + 4 < len(params) and params[p + 1] == "2":
                        fg = (
                            int(params[p + 2]),
                            int(params[p + 3]),
                            int(params[p + 4]),
                        )
                        p += 4
                    elif code == 48 and p + 4 < len(params) and params[p + 1] == "2":
                        bg = (
                            int(params[p + 2]),
                            int(params[p + 3]),
                            int(params[p + 4]),
                        )
                        p += 4
                    p += 1
                i = m.end()
            elif line[i] == LOWER:
                cells.append((bg, fg))  # top half = bg, bottom half = fg
                i += 1
            elif line[i] == UPPER:
                cells.append((fg, bg))  # top half = fg, bottom half = bg
                i += 1
            elif line[i] == " ":
                cells.append(None)
                i += 1
            else:
                i += 1
        rows.append(cells)
    while rows and all(c is None for c in rows[-1]):
        rows.pop()
    return rows


def rgb_hex(t):
    return f"#{t[0]:02x}{t[1]:02x}{t[2]:02x}"


def is_bg(t):
    return t == (0, 0, 0)


sprite = parse_sprite(SPRITE_FILE)
sprite_cols = max(len(r) for r in sprite)
sprite_rows = len(sprite)


# ── Row builders ─────────────────────────────────────────
def kv(key, val):
    space = TOTAL - len(key) - len(val)
    if space < 4:
        val = val[: TOTAL - len(key) - 6] + "..."
        space = 5
    dots = " " + "." * (space - 2) + " "
    return [(key, KEY), (dots, DOT), (val, VAL)]


def header(t):
    return [(t, WHT)]


def divider():
    return [("—" * TOTAL, DOT)]


def section(t):
    pad = "—" * max(0, TOTAL - len(t) - 1)
    return [(t + " ", SEC), (pad, DOT)]


def blank():
    return []


rows = [
    header("salwyn@mathew"),
    divider(),
    kv("OS:", "macOS Sequoia"),
    kv("Host:", "MikeLegal"),
    kv("Role:", "SDE AI"),
    kv("IDE:", "VS Code, Claude Code"),
    blank(),
    kv("Languages.Programming:", "Python, JavaScript, TypeScript"),
    kv("Languages.Computer:", "HTML, CSS, JSON, YAML"),
    blank(),
    kv("Hobbies.Software:", "LLM pipelines, MCP servers"),
    kv("Hobbies.IRL:", "Guitar, Bird Watching"),
    blank(),
    section("— Contact"),
    kv("LinkedIn:", "salwyn-mathew-4579381b7"),
    kv("GitHub:", "marvel13"),
    kv("Instagram:", "_salwinator"),
    blank(),
    section("— GitHub Stats"),
    [("Repos: ", KEY), ("10", GRN), ("  |  Followers: ", KEY), ("3", GRN)],
    [("Commits: ", KEY), ("78", GRN), ("  |  Stars: ", KEY), ("0", GRN)],
]

# ── Canvas — PX is the square pixel size ─────────────────
# Each character row = 2 square pixels tall (top half + bottom half).
# Terminal chars are ~2:1 (h:w), so pixels are square — we match that here.
INFO_H = PAD + len(rows) * INFO_LH + PAD
SVG_H = max(INFO_H, 480)
# PX_OVERRIDE: set a number to fix size, or leave None for auto
PX_OVERRIDE = None
PX = PX_OVERRIDE if PX_OVERRIDE else (SVG_H - 2 * PAD) // (sprite_rows * 2)
art_px_w = sprite_cols * PX
art_px_h = sprite_rows * PX * 2  # 2 square pixels per character row
SPRITE_Y = (SVG_H - art_px_h) // 2
info_x = PAD + art_px_w + GAP
SVG_W = int(info_x + TOTAL * INFO_CW + PAD * 2)


# ── Render ───────────────────────────────────────────────
def render(out_file, bg=BG):
    parts = []
    font_face = (
        f'@font-face{{font-family:"{FONT_NAME}";font-weight:400;'
        f'src:url("data:font/woff2;base64,{FONT_B64}") format("woff2");}}'
    )
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">\n'
        f"<defs><style>"
        f"{font_face}"
        f"text{{font-family:{FONT};white-space:pre;}}"
        f".i{{font-size:{INFO_FS}px;}}"
        f"</style></defs>\n"
        f'<rect width="{SVG_W}" height="{SVG_H}" rx="12" fill="{bg}"/>\n'
    )

    # Sprite: each char row = 2 square PX×PX pixels stacked
    for row_i, row in enumerate(sprite):
        y_top = SPRITE_Y + row_i * PX * 2
        y_bot = y_top + PX
        for col_i, cell in enumerate(row):
            if cell is None:
                continue
            top_color, bot_color = cell
            x = PAD + col_i * PX
            if not is_bg(top_color):
                parts.append(
                    f'<rect x="{x}" y="{y_top}" width="{PX}" height="{PX}" fill="{rgb_hex(top_color)}"/>\n'
                )
            if not is_bg(bot_color):
                parts.append(
                    f'<rect x="{x}" y="{y_bot}" width="{PX}" height="{PX}" fill="{rgb_hex(bot_color)}"/>\n'
                )

    # Info rows
    for i, row in enumerate(rows):
        if not row:
            continue
        y = PAD + INFO_FS + i * INFO_LH
        spans = "".join(f'<tspan fill="{c}">{html.escape(t)}</tspan>' for t, c in row)
        parts.append(
            f'<text class="i" x="{info_x:.1f}" y="{y}" xml:space="preserve">{spans}</text>\n'
        )

    parts.append("</svg>")
    svg = "".join(parts)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(svg)
    print(
        f"✓ {out_file}  ({SVG_W}×{SVG_H}px, {sprite_cols}×{sprite_rows} sprite, {sum(1 for r in rows if r)} info rows)"
    )


render(OUT_DARK)
