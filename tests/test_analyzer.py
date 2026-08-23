from __future__ import annotations

from ctf_payload_studio.analyzer import analyze_text
from ctf_payload_studio.context import defensive_preview, recommendations_for
from ctf_payload_studio.models import Context


def test_plain_text_has_no_findings() -> None:
    report = analyze_text("Merhaba güvenli eğitim örneği", Context.HTML_TEXT)
    assert report.risk_score == 0
    assert report.risk_label == "bilgi"
    assert report.findings == ()


def test_explainable_rules_contribute_to_score() -> None:
    report = analyze_text("<script>ornek</script>", Context.HTML_TEXT)
    assert report.risk_score == 32
    finding = report.findings[0]
    assert finding.rule_id == "PTS001"
    assert finding.score == 32
    assert finding.explanation
    assert finding.recommendation


def test_context_reduces_out_of_context_signal() -> None:
    generic = analyze_text("../ornek", Context.FILESYSTEM_PATH)
    unrelated = analyze_text("../ornek", Context.SQL_VALUE)
    assert generic.risk_score > unrelated.risk_score


def test_multiple_signals_are_capped() -> None:
    report = analyze_text(
        "<script onload=x> javascript: union select ../x; {{ value }}", Context.GENERIC
    )
    assert report.risk_score == 100
    assert len(report.findings) >= 6


def test_evidence_control_characters_are_escaped() -> None:
    report = analyze_text("\x1b<script>", Context.HTML_TEXT)
    assert "\\x1b" in report.findings[0].evidence
    assert "\x1b" not in report.findings[0].evidence


def test_context_recommendations_and_previews() -> None:
    assert "parametreli" in recommendations_for(Context.SQL_VALUE)[0].lower()
    assert defensive_preview("<örnek>", Context.HTML_TEXT) == "&lt;örnek&gt;"
    assert defensive_preview("a b", Context.URL_COMPONENT) == "a%20b"
    assert defensive_preview("değer", Context.SQL_VALUE) is None
