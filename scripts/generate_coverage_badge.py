"""Generate a simple SVG coverage badge from a coverage.xml report."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_coverage_percent(path: Path) -> float:
    root = ET.parse(path).getroot()
    return round(float(root.attrib["line-rate"]) * 100, 1)


def coverage_color(percent: float) -> str:
    if percent >= 90:
        return "#2ea043"
    if percent >= 80:
        return "#3fb950"
    if percent >= 70:
        return "#9a6700"
    if percent >= 60:
        return "#bf8700"
    return "#cf222e"


def render_badge(label: str, value: str, color: str) -> str:
    label_width = max(52, len(label) * 7 + 16)
    value_width = max(54, len(value) * 7 + 16)
    width = label_width + value_width
    value_x = label_width + value_width / 2
    font_family = "Verdana,Geneva,DejaVu Sans,sans-serif"
    return f"""<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{width}"
  height="20"
  role="img"
  aria-label="{label}: {value}"
>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="{font_family}" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{value_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_x}" y="14">{value}</text>
  </g>
</svg>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, required=True, help="Path to coverage.xml")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the SVG")
    parser.add_argument("--label", default="coverage", help="Badge label (default: coverage)")
    args = parser.parse_args(argv)

    percent = parse_coverage_percent(args.coverage)
    value = f"{percent:.1f}%"
    badge = render_badge(args.label, value, coverage_color(percent))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(badge, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
