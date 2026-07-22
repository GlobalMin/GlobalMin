#!/usr/bin/env python3
"""Generate assets/stats-card.svg and assets/header.svg data from the GitHub API.

Replaces both the github-readme-stats top-langs card and the
streak-stats.demolab.com card with one self-contained SVG (no external
services to rate-limit, no external fonts — GitHub's camo proxy strips
those anyway). Styled to match the profile mockup: #f6f8fa card,
#d0d7de border, language bar + legend, then contributions / current
streak / longest streak.

Requires GITHUB_TOKEN (the streak numbers need the GraphQL API).
"""

import datetime
import json
import os
import urllib.request

USER = "GlobalMin"
TOP_N = 4
ACCENT = "#0969da"
WIDTH, HEIGHT = 760, 200
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats-card.svg")

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
TOKEN = os.environ.get("GITHUB_TOKEN")


def rest(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "gen-stats-card",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": "gen-stats-card",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def get_languages():
    totals = {}
    for repo in rest(f"/users/{USER}/repos?per_page=100&type=owner"):
        if repo["fork"]:
            continue
        for lang, size in rest(f"/repos/{USER}/{repo['name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + size
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP_N]
    total = sum(size for _, size in ranked) or 1
    return [(name, size / total) for name, size in ranked]


def get_streaks():
    """Total contributions + streaks over the last 12 months.

    Note: the GraphQL calendar only covers one year, so a streak that
    started earlier than that is under-counted at the year boundary.
    """
    q = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }"""
    cal = graphql(q, {"login": USER})["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    today = datetime.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]

    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)

    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif d["date"] == today:
            continue  # today can still get contributions
        else:
            break
    return cal["totalContributions"], current, longest


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def main():
    langs = get_languages()
    total, current, longest = get_streaks()

    bar_x, bar_y, bar_w, bar_h = 26, 50, WIDTH - 52, 10
    x = bar_x
    segments = []
    for name, frac in langs:
        w = bar_w * frac
        segments.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" '
            f'fill="{COLORS.get(name, FALLBACK)}"/>'
        )
        x += w

    legend = []
    col_w = bar_w / TOP_N
    for i, (name, frac) in enumerate(langs):
        lx = bar_x + i * col_w
        legend.append(
            f'<circle cx="{lx + 5:.0f}" cy="80" r="5" fill="{COLORS.get(name, FALLBACK)}"/>'
            f'<text x="{lx + 16:.0f}" y="84" font-size="11.5" fill="#424a53">{name} {frac * 100:.1f}%</text>'
        )

    third = bar_w / 3
    centers = [bar_x + third * (i + 0.5) for i in range(3)]
    stats = [
        (fmt(total), "Total Contributions", "#1f2328"),
        (f"{current} \U0001f525", "Current Streak", ACCENT),
        (str(longest), "Longest Streak", "#1f2328"),
    ]
    stat_svg = []
    for cx, (num, lab, cls) in zip(centers, stats):
        stat_svg.append(
            f'<text x="{cx:.0f}" y="150" text-anchor="middle" font-size="26" font-weight="800" fill="{cls}">{num}</text>'
            f'<text x="{cx:.0f}" y="172" text-anchor="middle" font-size="11" fill="#656d76">{lab}</text>'
        )

    # NOTE: GitHub-safe SVG — no <style> block (some pipelines strip it);
    # all typography is presentation attributes on each element.
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Most used languages and contribution streaks" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif">
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="#f6f8fa" stroke="#d0d7de"/>
  <text x="26" y="34" font-size="13" font-weight="700" fill="#1f2328">Most Used Languages</text>
  <text x="{WIDTH - 26}" y="34" text-anchor="end" font-family="ui-monospace, 'SFMono-Regular', 'SF Mono', Menlo, Consolas, monospace" font-size="11" font-weight="500" fill="#656d76">last 12 months</text>
  <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5"/></clipPath>
  <g clip-path="url(#bar)">
    {"".join(segments)}
  </g>
  {"".join(legend)}
  <line x1="26" y1="104" x2="{WIDTH - 26}" y2="104" stroke="#d0d7de"/>
  <line x1="{bar_x + third:.0f}" y1="122" x2="{bar_x + third:.0f}" y2="176" stroke="#d0d7de"/>
  <line x1="{bar_x + 2 * third:.0f}" y1="122" x2="{bar_x + 2 * third:.0f}" y2="176" stroke="#d0d7de"/>
  {"".join(stat_svg)}
</svg>
"""
    with open(OUT, "w") as f:
        f.write(svg)
    print(
        f"wrote {os.path.normpath(OUT)}: "
        + ", ".join(f"{n} {f * 100:.1f}%" for n, f in langs)
        + f" | {total} contributions, streak {current}/{longest}"
    )


if __name__ == "__main__":
    main()
