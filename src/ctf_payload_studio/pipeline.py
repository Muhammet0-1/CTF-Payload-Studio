"""Dönüşüm adımlarını izlenebilir bir provenance zinciri olarak uygular."""

from __future__ import annotations

import hashlib

from ctf_payload_studio.errors import ValidationError
from ctf_payload_studio.models import PipelineResult, TransformName, TransformStep
from ctf_payload_studio.transforms import apply_transform, auto_decode, inverse_for
from ctf_payload_studio.validation import MAX_PIPELINE_STEPS, validate_text


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _graph(steps: list[TransformStep]) -> str:
    lines = ["flowchart LR", '  N0["Girdi"]']
    for step in steps:
        status = "✓" if step.round_trip_ok is True else "?" if step.round_trip_ok is None else "!"
        lines.append(
            f'  N{step.index}["{step.index}. {step.name.value} · {step.output_bytes} B · {status}"]'
        )
        lines.append(f"  N{step.index - 1} --> N{step.index}")
    return "\n".join(lines)


def run_pipeline(text: str, names: list[TransformName], *, auto_depth: int = 4) -> PipelineResult:
    current = validate_text(text)
    if not names:
        raise ValidationError("en az bir dönüşüm adımı seçilmelidir")
    if len(names) > MAX_PIPELINE_STEPS:
        raise ValidationError(f"en fazla {MAX_PIPELINE_STEPS} dönüşüm adımı kullanılabilir")
    steps: list[TransformStep] = []
    for index, name in enumerate(names, start=1):
        source = current
        if name is TransformName.AUTO_DECODE:
            result = auto_decode(source, max_depth=auto_depth)
            current = result.output
            reversible = False
            round_trip_ok: bool | None = None
        else:
            current = apply_transform(source, name)
            inverse = inverse_for(name)
            reversible = inverse is not None
            round_trip_ok = (
                apply_transform(current, inverse) == source if inverse is not None else None
            )
        steps.append(
            TransformStep(
                index=index,
                name=name,
                input_sha256=_digest(source),
                output_sha256=_digest(current),
                input_bytes=len(source.encode()),
                output_bytes=len(current.encode()),
                reversible=reversible,
                round_trip_ok=round_trip_ok,
            )
        )
    return PipelineResult(output=current, steps=tuple(steps), graph=_graph(steps))
