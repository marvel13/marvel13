#!/usr/bin/env python3
"""Generate neofetch-style GitHub profile SVG with half-block pixel art."""

import html, json, re, pathlib, argparse

# ── Args ──────────────────────────────────────────────────
# --pokemon PATH  overrides the default sprite (used by GitHub Actions)
_parser = argparse.ArgumentParser()
_parser.add_argument("--pokemon", default=None, help="Path to colorscript file")
_args = _parser.parse_args()

REPO_DIR = pathlib.Path(__file__).parent
SPRITE_FILE = _args.pokemon or (
    "/Users/salwynmathew/pokemon-colorscripts/colorscripts/small/regular/gengar"
)
OUT_DARK = str(REPO_DIR / "dark_mode.svg")
FONT_B64 = (REPO_DIR / "font_jbmono.b64").read_text().strip()

# ── Stats (written by fetch_stats.py) ────────────────────
try:
    _stats = json.loads((REPO_DIR / "stats.json").read_text())
except FileNotFoundError:
    _stats = {
        "repos": 10,
        "contributed": 12,
        "stars": 0,
        "commits": 60,
        "followers": 3,
        "loc_add": 0,
        "loc_del": 0,
        "loc_total": 0,
    }

# ── Palette ──────────────────────────────────────────────
BG = "#161b22"
FG = "#c9d1d9"
KEY = "#ffa657"
VAL = "#a5d6ff"
DOT = "#616e7f"
GRN = "#3fb950"
RED = "#f85149"
WHT = "#ffffff"
SEC = "#c9d1d9"

# ── Typography ───────────────────────────────────────────
FONT_NAME = "JetBrainsMono"
FONT = f"'{FONT_NAME}','JetBrains Mono','Courier New',monospace"
INFO_FS = 21
INFO_LH = 24
INFO_CW = 11.60

# ── Layout ───────────────────────────────────────────────
PAD = 20
GAP = 36
TOTAL = 56  # monospace columns for key+dots+value

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
PREFIX = ". "


def _key_spans(key):
    """Split 'Languages.Programming:' into colored spans matching Andrew6rant's style."""
    base = key.rstrip(":")
    parts = base.split(".")
    spans = []
    for i, part in enumerate(parts):
        spans.append((part, KEY))
        if i < len(parts) - 1:
            spans.append((".", FG))
    spans.append((":", FG))
    return spans


def kv(key, val):
    used = len(PREFIX) + len(key) + 2 + len(val)
    if used > TOTAL - 2:
        val = val[: TOTAL - len(PREFIX) - len(key) - 5] + "..."
        used = len(PREFIX) + len(key) + 2 + len(val)
    dots_count = max(2, TOTAL - used)
    return (
        [(PREFIX, DOT)]
        + _key_spans(key)
        + [(" " + "." * dots_count + " ", DOT), (val, VAL)]
    )


def header(t):
    dashes = "—" * max(0, TOTAL - len(t) - 1)
    return [(t + " ", WHT), (dashes, DOT)]


def section(t):
    dashes = "—" * max(0, TOTAL - len(t) - 3)
    return [("- ", DOT), (t + " ", SEC), (dashes, DOT)]


def stat_repos(repos, contributed, stars):
    repos_str, contrib_str, stars_str = str(repos), str(contributed), str(stars)
    left_dots = " .... "
    contrib_block = f" {{Contributed: {contrib_str}}}"
    sep = " | "
    right_space = TOTAL - (
        len(PREFIX)
        + len("Repos:")
        + len(left_dots)
        + len(repos_str)
        + len(contrib_block)
        + len(sep)
        + len("Stars:")
        + len(stars_str)
    )
    right_dots = " " + "." * max(1, right_space - 2) + " "
    return [
        (PREFIX, DOT),
        ("Repos", KEY),
        (":", FG),
        (left_dots, DOT),
        (repos_str, VAL),
        (" {", FG),
        ("Contributed", KEY),
        (": ", FG),
        (contrib_str, VAL),
        ("}", FG),
        (sep, FG),
        ("Stars", KEY),
        (":", FG),
        (right_dots, DOT),
        (stars_str, VAL),
    ]


def stat_commits(commits, followers):
    commits_str, followers_str = str(commits), str(followers)
    sep = " | "
    fixed = (
        len(PREFIX)
        + len("Commits:")
        + len(commits_str)
        + len(sep)
        + len("Followers:")
        + len(followers_str)
    )
    total_dot_space = TOTAL - fixed
    left_dot_chars = (total_dot_space * 2) // 3
    right_dot_chars = total_dot_space - left_dot_chars
    left_dots = " " + "." * max(1, left_dot_chars - 2) + " "
    right_dots = " " + "." * max(1, right_dot_chars - 2) + " "
    return [
        (PREFIX, DOT),
        ("Commits", KEY),
        (":", FG),
        (left_dots, DOT),
        (commits_str, VAL),
        (sep, FG),
        ("Followers", KEY),
        (":", FG),
        (right_dots, DOT),
        (followers_str, VAL),
    ]


def stat_loc(total, additions, deletions):
    total_str = f"{total:,}"
    add_str = f"{additions:,}"
    del_str = f"{deletions:,}"
    sep, end = " ( ", " )"
    fixed = (
        len(PREFIX)
        + len("Lines of Code on GitHub:")
        + len(". ")
        + len(total_str)
        + len(sep)
        + len(add_str)
        + len("++")
        + len(", ")
        + len(" ")
        + len(del_str)
        + len("--")
        + len(end)
    )
    extra_dots = max(0, TOTAL - fixed - 1)
    loc_dots = ". " + "." * extra_dots + " " if extra_dots else ". "
    return [
        (PREFIX, DOT),
        ("Lines of Code on GitHub", KEY),
        (":", FG),
        (loc_dots, DOT),
        (total_str, VAL),
        (sep, FG),
        (add_str, GRN),
        ("++", GRN),
        (", ", FG),
        (" ", FG),
        (del_str, RED),
        ("--", RED),
        (end, FG),
    ]


def blank():
    return []


rows = [
    header("salwyn@mathew"),
    kv("OS:", "macOS Sequoia"),
    kv("Host:", "MikeLegal"),
    kv("Role:", "SDE AI"),
    kv("IDE:", "VS Code, Claude Code"),
    blank(),
    kv("Languages.Programming:", "Python, JS, TypeScript"),
    kv("Languages.Computer:", "HTML, CSS, JSON, YAML"),
    blank(),
    kv("Hobbies.Software:", "LLM pipelines, MCP servers"),
    kv("Hobbies.IRL:", "Guitar, Bird Watching"),
    blank(),
    section("Contact"),
    kv("LinkedIn:", "Salwyn Mathew"),
    kv("Blog:", "marvel13.github.io/blog/"),
    kv("Email.Personal:", "salwynmathew13@gmail.com"),
    kv("Email.Work:", "salwyn.mathew@mikelegal.com"),
    blank(),
    section("GitHub Stats"),
    stat_repos(_stats["repos"], _stats["contributed"], _stats["stars"]),
    stat_commits(_stats["commits"], _stats["followers"]),
    stat_loc(_stats["loc_total"], _stats["loc_add"], _stats["loc_del"]),
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
        f".i{{font-size:{INFO_FS}px;letter-spacing:-1px;"
        f"paint-order:stroke fill;stroke:currentColor;stroke-width:0.4px;stroke-linejoin:round;}}"
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
