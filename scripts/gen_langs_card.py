#!/usr/bin/env python3
"""Generate assets/top-langs.svg from the GitHub API.

Replaces the github-readme-stats.vercel.app top-langs card, whose shared
instance rate-limits (503) often enough to leave a broken image on the
profile. Styled to match that card's `transparent` compact theme so it
pairs with the streak-stats card next to it.
"""

import json
import os
import urllib.request

USER = "GlobalMin"
TOP_N = 6
WIDTH, HEIGHT = 380, 165
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "top-langs.svg")

# GitHub linguist colors for languages that show up in this account,
# fallback gray for anything else.
COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B",
    "Swift": "#F05138",
    "CSS": "#563d7c",
    "HTML": "#e34c26",
    "Shell": "#89e051",
    "Makefile": "#427819",
    "Svelte": "#ff3e00",
    "Dockerfile": "#384d54",
}
FALLBACK = "#858585"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "gen-langs-card",
            **(
                {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
                if os.environ.get("GITHUB_TOKEN")
                else {}
            ),
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    totals = {}
    for repo in repos:
        if repo["fork"]:
            continue
        for lang, size in api(f"/repos/{USER}/{repo['name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + size

    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP_N]
    total = sum(size for _, size in ranked) or 1
    langs = [(name, size / total) for name, size in ranked]

    # Stacked progress bar
    bar_x, bar_y, bar_w, bar_h = 25, 50, WIDTH - 50, 8
    x = bar_x
    segments = []
    for name, frac in langs:
        w = bar_w * frac
        segments.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" '
            f'fill="{COLORS.get(name, FALLBACK)}" />'
        )
        x += w

    # Two-column legend
    legend = []
    col_w = (WIDTH - 50) / 2
    for i, (name, frac) in enumerate(langs):
        lx = bar_x + (i % 2) * col_w
        ly = bar_y + 30 + (i // 2) * 24
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{COLORS.get(name, FALLBACK)}" />'
            f'<text x="{lx + 16}" y="{ly}" class="lang">{name} '
            f'<tspan class="pct">{frac * 100:.1f}%</tspan></text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" role="img" aria-label="Most used languages">
  <style>
    .title {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #2f80ed; }}
    .lang {{ font: 400 11px 'Segoe UI', Ubuntu, sans-serif; fill: #434d58; }}
    .pct {{ fill: #858585; }}
  </style>
  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="none" />
  <text x="25" y="33" class="title">Most Used Languages</text>
  <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4" /></clipPath>
  <g clip-path="url(#bar)">
    {'\n    '.join(segments)}
  </g>
  {'\n  '.join(legend)}
</svg>
"""
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)}: " + ", ".join(f"{n} {f*100:.1f}%" for n, f in langs))


if __name__ == "__main__":
    main()
