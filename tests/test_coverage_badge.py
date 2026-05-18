from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "generate_coverage_badge.py"
spec = importlib.util.spec_from_file_location("generate_coverage_badge", SCRIPT_PATH)
assert spec and spec.loader
coverage_badge = importlib.util.module_from_spec(spec)
sys.modules["generate_coverage_badge"] = coverage_badge
spec.loader.exec_module(coverage_badge)


def test_parse_coverage_percent(tmp_path: Path) -> None:
    xml = tmp_path / "coverage.xml"
    xml.write_text('<coverage line-rate="0.875"></coverage>', encoding="utf-8")
    assert coverage_badge.parse_coverage_percent(xml) == 87.5


def test_coverage_color_thresholds() -> None:
    assert coverage_badge.coverage_color(95.0) == "#2ea043"
    assert coverage_badge.coverage_color(82.0) == "#3fb950"
    assert coverage_badge.coverage_color(72.0) == "#9a6700"
    assert coverage_badge.coverage_color(61.0) == "#bf8700"
    assert coverage_badge.coverage_color(40.0) == "#cf222e"


def test_main_writes_svg(tmp_path: Path) -> None:
    xml = tmp_path / "coverage.xml"
    svg = tmp_path / "coverage-badge.svg"
    xml.write_text('<coverage line-rate="0.913"></coverage>', encoding="utf-8")
    rc = coverage_badge.main(["--coverage", str(xml), "--output", str(svg)])
    assert rc == 0
    content = svg.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "coverage" in content
    assert "91.3%" in content
