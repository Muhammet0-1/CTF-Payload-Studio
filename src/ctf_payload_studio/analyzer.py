"""Metni çalıştırmadan açıklanabilir savunma sinyalleri üretir."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ctf_payload_studio.context import recommendations_for
from ctf_payload_studio.fingerprint import fingerprint_text
from ctf_payload_studio.models import AnalysisReport, Context, Finding, Severity
from ctf_payload_studio.validation import validate_text


@dataclass(frozen=True)
class _Rule:
    rule_id: str
    title: str
    pattern: re.Pattern[str]
    severity: Severity
    score: int
    explanation: str
    recommendation: str
    contexts: frozenset[Context] = frozenset()


_RULES = (
    _Rule(
        "PTS001",
        "HTML/etiket yapısı",
        re.compile(r"(?i)<\s*(?:script|iframe|svg|object|embed)\b"),
        Severity.HIGH,
        32,
        "Aktif içerik taşıyabilen bir HTML etiketi benzeri yapı görüldü.",
        "Değeri HTML olarak yorumlamayın; metin düğümünde bağlama uygun kodlayın.",
        frozenset({Context.HTML_TEXT, Context.HTML_ATTRIBUTE, Context.GENERIC}),
    ),
    _Rule(
        "PTS002",
        "Olay işleyici benzeri öznitelik",
        re.compile(r"(?i)\bon[a-z]{3,24}\s*="),
        Severity.HIGH,
        28,
        "Tarayıcı olay işleyicisine benzeyen bir öznitelik görüldü.",
        "İzin verilen öznitelikleri listeleyin ve olay işleyicilerini kabul etmeyin.",
        frozenset({Context.HTML_ATTRIBUTE, Context.HTML_TEXT, Context.GENERIC}),
    ),
    _Rule(
        "PTS003",
        "SQL sözdizimi birleşimi",
        re.compile(r"(?i)\b(?:union\s+(?:all\s+)?select|or\s+\d+\s*=\s*\d+|sleep\s*\()"),
        Severity.HIGH,
        30,
        "Kullanıcı değerine ait olmaması gereken SQL kontrol sözcükleri birlikte görüldü.",
        "Parametreli sorgu ve tipli bağlama kullanın; metin birleştirmeyin.",
        frozenset({Context.SQL_VALUE, Context.GENERIC}),
    ),
    _Rule(
        "PTS004",
        "Üst dizin geçişi",
        re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)"),
        Severity.MEDIUM,
        22,
        "Yolun üst dizine çıkmayı deneyebilecek bir bileşeni var.",
        "Yolu sabit kök altında çözümleyip containment denetimi uygulayın.",
        frozenset({Context.FILESYSTEM_PATH, Context.GENERIC}),
    ),
    _Rule(
        "PTS005",
        "Kabuk kontrol karakteri",
        re.compile(r"(?:&&|\|\||[;`])"),
        Severity.MEDIUM,
        20,
        "Kabukta komut ayırma veya ikame anlamına gelebilen karakter görüldü.",
        "Kabuk kullanmayın; sabit programı ayrı argüman listesiyle çağırın.",
        frozenset({Context.SHELL_ARGUMENT, Context.GENERIC}),
    ),
    _Rule(
        "PTS006",
        "Şablon ifadesi",
        re.compile(r"(?:\{\{.{0,120}?\}\}|\$\{.{0,120}?\}|<%.{0,120}?%>)", re.DOTALL),
        Severity.MEDIUM,
        21,
        "Bir şablon motoru ifadesine benzeyen sınırlayıcılar görüldü.",
        "Şablon kaynağını sabit tutup girdiyi yalnız veri değişkeni olarak bağlayın.",
        frozenset({Context.TEMPLATE, Context.GENERIC}),
    ),
    _Rule(
        "PTS007",
        "URL tabanlı betik şeması",
        re.compile(r"(?i)\bjavascript\s*:"),
        Severity.HIGH,
        32,
        "Tarayıcıda kod yorumlanmasına yol açabilen bir URL şeması görüldü.",
        "Şemaları izin listesiyle sınırlandırın ve URL ayrıştırıcısıyla doğrulayın.",
        frozenset({Context.URL_COMPONENT, Context.HTML_ATTRIBUTE, Context.GENERIC}),
    ),
)


def _evidence(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 20)
    end = min(len(text), match.end() + 20)
    snippet = text[start:end]
    return snippet.encode("unicode_escape").decode("ascii")[:160]


def _label(score: int) -> str:
    if score >= 70:
        return "yüksek"
    if score >= 40:
        return "orta"
    if score >= 15:
        return "düşük"
    return "bilgi"


def analyze_text(text: str, context: Context = Context.GENERIC) -> AnalysisReport:
    text = validate_text(text)
    findings: list[Finding] = []
    score = 0
    for rule in _RULES:
        match = rule.pattern.search(text)
        if match is None:
            continue
        contextual = not rule.contexts or context in rule.contexts
        contribution = rule.score if contextual else max(5, rule.score // 2)
        score += contribution
        findings.append(
            Finding(
                rule_id=rule.rule_id,
                title=rule.title,
                severity=rule.severity if contextual else Severity.LOW,
                score=contribution,
                evidence=_evidence(text, match),
                explanation=rule.explanation,
                recommendation=rule.recommendation,
            )
        )
    fingerprint = fingerprint_text(text)
    if fingerprint.entropy >= 5.5 and fingerprint.bytes >= 32:
        contribution = 8
        score += contribution
        findings.append(
            Finding(
                rule_id="PTS008",
                title="Yüksek metin entropisi",
                severity=Severity.INFO,
                score=contribution,
                evidence=f"entropy={fingerprint.entropy}",
                explanation=(
                    "Metin kodlanmış veya sıkıştırılmış veriye benzeyebilir; "
                    "tek başına zafiyet değildir."
                ),
                recommendation=(
                    "İçeriği çalıştırmadan, sınırlı dönüşüm zinciriyle katmanları inceleyin."
                ),
            )
        )
    capped = min(score, 100)
    return AnalysisReport(
        context=context,
        risk_score=capped,
        risk_label=_label(capped),
        fingerprint=fingerprint,
        findings=tuple(findings),
        recommendations=recommendations_for(context),
    )
