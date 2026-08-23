"""Serileştirilebilir, değişmez alan modelleri."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Context(str, Enum):
    GENERIC = "generic"
    HTML_TEXT = "html-text"
    HTML_ATTRIBUTE = "html-attribute"
    URL_COMPONENT = "url-component"
    SQL_VALUE = "sql-value"
    SHELL_ARGUMENT = "shell-argument"
    FILESYSTEM_PATH = "filesystem-path"
    TEMPLATE = "template"


class TransformName(str, Enum):
    AUTO_DECODE = "auto-decode"
    URL_ENCODE = "url-encode"
    URL_DECODE = "url-decode"
    BASE64_ENCODE = "base64-encode"
    BASE64_DECODE = "base64-decode"
    HEX_ENCODE = "hex-encode"
    HEX_DECODE = "hex-decode"
    HTML_ENCODE = "html-encode"
    HTML_DECODE = "html-decode"
    UNICODE_ESCAPE = "unicode-escape"
    UNICODE_UNESCAPE = "unicode-unescape"
    NORMALIZE = "normalize"


@dataclass(frozen=True)
class Fingerprint:
    sha256: str
    bytes: int
    characters: int
    entropy: float
    printable_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: Severity
    score: int
    evidence: str
    explanation: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass(frozen=True)
class AnalysisReport:
    context: Context
    risk_score: int
    risk_label: str
    fingerprint: Fingerprint
    findings: tuple[Finding, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.value,
            "risk_score": self.risk_score,
            "risk_label": self.risk_label,
            "fingerprint": self.fingerprint.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "recommendations": list(self.recommendations),
        }


@dataclass(frozen=True)
class TransformStep:
    index: int
    name: TransformName
    input_sha256: str
    output_sha256: str
    input_bytes: int
    output_bytes: int
    reversible: bool
    round_trip_ok: bool | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["name"] = self.name.value
        return data


@dataclass(frozen=True)
class PipelineResult:
    output: str
    steps: tuple[TransformStep, ...]
    graph: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "steps": [step.to_dict() for step in self.steps],
            "graph": self.graph,
        }


@dataclass(frozen=True)
class AutoDecodeResult:
    output: str
    detected_steps: tuple[TransformName, ...]


@dataclass(frozen=True)
class Difference:
    operation: str
    left: str
    right: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ComparisonReport:
    identical: bool
    normalized_identical: bool
    similarity: float
    left: AnalysisReport
    right: AnalysisReport
    risk_delta: int
    differences: tuple[Difference, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "identical": self.identical,
            "normalized_identical": self.normalized_identical,
            "similarity": self.similarity,
            "risk_delta": self.risk_delta,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "differences": [difference.to_dict() for difference in self.differences],
        }
