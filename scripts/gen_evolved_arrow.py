#!/usr/bin/env python3
"""Write assets/evolved-arrow.svg (animated arrow for the tech-stack table).

The SVG carries a SMIL <animateTransform> for the subtle horizontal bob.
It is generated from this script rather than committed directly so no
tooling in the chain can strip the animation element. Run once (or let
the update-stats workflow do it):

    python scripts/gen_evolved_arrow.py
"""

import os

ACCENT = "#0969da"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "evolved-arrow.svg")

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="72" height="92" viewBox="0 0 72 92" role="img" aria-label="evolved">
  <g>
    <animateTransform attributeName="transform" type="translate" values="-3 0; 3 0; -3 0" dur="1.6s" repeatCount="indefinite" calcMode="spline" keyTimes="0; 0.5; 1" keySplines="0.45 0 0.55 1; 0.45 0 0.55 1"/>
    <circle cx="36" cy="30" r="23" fill="{ACCENT}"/>
    <path d="M26 30h18M38 22l8 8-8 8" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <text x="36" y="74" text-anchor="middle" font-family="ui-monospace, 'SFMono-Regular', 'SF Mono', Menlo, Consolas, monospace" font-size="10" font-weight="700" letter-spacing="1" fill="{ACCENT}">EVOLVED</text>
</svg>
"""

if __name__ == "__main__":
    with open(OUT, "w") as f:
        f.write(SVG)
    print(f"wrote {os.path.normpath(OUT)}")
