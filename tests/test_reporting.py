from __future__ import annotations

import json

from ctf_payload_studio.analyzer import analyze_text
from ctf_payload_studio.compare import compare_texts
from ctf_payload_studio.models import Context, TransformName
from ctf_payload_studio.pipeline import run_pipeline
from ctf_payload_studio.reporting import (
    analysis_sarif,
    render_analysis,
    render_comparison,
    render_pipeline,
    sanitize_terminal,
)


def test_json_and_jsonl_are_valid_and_finite() -> None:
    report = analyze_text("{{ örnek }}", Context.TEMPLATE)
    assert json.loads(render_analysis(report, "json"))["risk_score"] > 0
    assert json.loads(render_analysis(report, "jsonl"))["context"] == "template"
    assert "NaN" not in render_analysis(report, "json")


def test_sarif_contains_rules_and_results_without_source_path() -> None:
    document = json.loads(analysis_sarif(analyze_text("{{ value }}", Context.TEMPLATE)))
    run = document["runs"][0]
    assert document["version"] == "2.1.0"
    assert run["tool"]["driver"]["rules"][0]["id"] == "PTS006"
    assert run["results"][0]["ruleId"] == "PTS006"
    assert "locations" not in run["results"][0]


def test_pipeline_and_comparison_renderers() -> None:
    pipeline = run_pipeline("abc", [TransformName.HEX_ENCODE])
    comparison = compare_texts("a", "b")
    assert json.loads(render_pipeline(pipeline, "json"))["output"] == "616263"
    assert "Benzerlik" in render_comparison(comparison, "text")


def test_terminal_control_characters_are_visible() -> None:
    sanitized = sanitize_terminal("önce\x1b[31m\nsonra\x00")
    assert "\x1b" not in sanitized
    assert "\\x1b" in sanitized
    assert "\\x0a" in sanitized
    assert "\\x00" in sanitized
