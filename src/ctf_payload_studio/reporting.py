"""Terminal, JSON, JSONL ve SARIF raporlayıcıları."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ctf_payload_studio.models import AnalysisReport, ComparisonReport, PipelineResult


def sanitize_terminal(text: str) -> str:
    """Kontrol karakterlerini görünür kaçışlara çevirir."""
    return "".join(
        character if character.isprintable() else f"\\x{ord(character):02x}" for character in text
    )


def _json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)


def analysis_text(report: AnalysisReport) -> str:
    lines = [
        f"Bağlam: {report.context.value}",
        f"Risk: {report.risk_score}/100 ({report.risk_label})",
        f"SHA-256: {report.fingerprint.sha256}",
        f"Boyut: {report.fingerprint.bytes} bayt / {report.fingerprint.characters} karakter",
        f"Entropi: {report.fingerprint.entropy}",
        "",
        "Bulgular:",
    ]
    if not report.findings:
        lines.append("- Statik eşleşme bulunmadı (bu, içeriğin güvenli olduğunu kanıtlamaz).")
    for finding in report.findings:
        lines.extend(
            [
                f"- [{finding.severity.value}] {finding.rule_id}: "
                f"{finding.title} (+{finding.score})",
                f"  Kanıt: {sanitize_terminal(finding.evidence)}",
                f"  Neden: {finding.explanation}",
                f"  Öneri: {finding.recommendation}",
            ]
        )
    lines.extend(["", "Bağlam önerileri:"])
    lines.extend(f"- {item}" for item in report.recommendations)
    return "\n".join(lines)


def pipeline_text(result: PipelineResult) -> str:
    lines = [f"Çıktı: {sanitize_terminal(result.output)}", "", "Dönüşüm zinciri:"]
    for step in result.steps:
        round_trip = (
            "uygun"
            if step.round_trip_ok is True
            else "uygun değil"
            if step.round_trip_ok is False
            else "yok"
        )
        lines.append(
            f"- {step.index}. {step.name.value}: {step.input_bytes} B -> {step.output_bytes} B; "
            f"round-trip={round_trip}"
        )
    lines.extend(["", "Mermaid provenance grafiği:", result.graph])
    return "\n".join(lines)


def comparison_text(report: ComparisonReport) -> str:
    lines = [
        f"Aynı: {'evet' if report.identical else 'hayır'}",
        f"Normalize edilince aynı: {'evet' if report.normalized_identical else 'hayır'}",
        f"Benzerlik: {report.similarity:.4f}",
        f"Risk farkı (sağ-sol): {report.risk_delta:+d}",
        f"Sol risk: {report.left.risk_score}/100",
        f"Sağ risk: {report.right.risk_score}/100",
        "",
        "Fark parçaları:",
    ]
    if not report.differences:
        lines.append("- Yok")
    for difference in report.differences:
        lines.append(
            f"- {difference.operation}: {sanitize_terminal(difference.left)!r} -> "
            f"{sanitize_terminal(difference.right)!r}"
        )
    return "\n".join(lines)


def analysis_sarif(report: AnalysisReport) -> str:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    level_map = {"high": "error", "medium": "warning", "low": "note", "info": "note"}
    for finding in report.findings:
        rules[finding.rule_id] = {
            "id": finding.rule_id,
            "name": finding.title,
            "shortDescription": {"text": finding.explanation},
            "help": {"text": finding.recommendation},
        }
        results.append(
            {
                "ruleId": finding.rule_id,
                "level": level_map[finding.severity.value],
                "message": {"text": f"{finding.title}: {sanitize_terminal(finding.evidence)}"},
                "properties": {"scoreContribution": finding.score, "context": report.context.value},
            }
        )
    document = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CTF Payload Studio",
                        "informationUri": "https://github.com/Muhammet0-1/CTF-Payload-Studio",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "properties": {"riskScore": report.risk_score, "riskLabel": report.risk_label},
            }
        ],
    }
    return _json(document)


def render_analysis(report: AnalysisReport, format_name: str) -> str:
    if format_name == "text":
        return analysis_text(report)
    if format_name == "sarif":
        return analysis_sarif(report)
    data = report.to_dict()
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if format_name == "jsonl"
        else _json(data)
    )


def render_pipeline(result: PipelineResult, format_name: str) -> str:
    if format_name == "text":
        return pipeline_text(result)
    data = result.to_dict()
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if format_name == "jsonl"
        else _json(data)
    )


def render_comparison(report: ComparisonReport, format_name: str) -> str:
    if format_name == "text":
        return comparison_text(report)
    data = report.to_dict()
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if format_name == "jsonl"
        else _json(data)
    )
