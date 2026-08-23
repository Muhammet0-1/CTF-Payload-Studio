"""Türkçe komut satırı arayüzü."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ctf_payload_studio import __version__
from ctf_payload_studio.analyzer import analyze_text
from ctf_payload_studio.compare import compare_texts
from ctf_payload_studio.context import defensive_preview
from ctf_payload_studio.errors import StudioError, ValidationError
from ctf_payload_studio.fingerprint import fingerprint_text
from ctf_payload_studio.models import Context, TransformName
from ctf_payload_studio.pipeline import run_pipeline
from ctf_payload_studio.reporting import (
    render_analysis,
    render_comparison,
    render_pipeline,
    sanitize_terminal,
)
from ctf_payload_studio.validation import read_text_file, validate_text


def _context(value: str) -> Context:
    try:
        return Context(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"geçersiz bağlam: {value}") from exc


def _transform(value: str) -> TransformName:
    try:
        return TransformName(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"geçersiz dönüşüm: {value}") from exc


def _add_input(parser: argparse.ArgumentParser, name: str = "text") -> None:
    parser.add_argument(name, nargs="?", help="İncelenecek UTF-8 metin")
    parser.add_argument("--input-file", type=Path, help="En fazla 64 KiB normal UTF-8 dosyası")


def _resolve_input(value: str | None, path: Path | None, label: str = "metin") -> str:
    if value is not None and path is not None:
        raise ValidationError(f"{label} ile --input-file birlikte kullanılamaz")
    if path is not None:
        return read_text_file(path)
    if value is None:
        raise ValidationError(f"{label} veya --input-file gereklidir")
    return validate_text(value, label=label)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="payload-studio",
        description="Çevrimdışı, sınırlı ve açıklanabilir payload metni analiz stüdyosu.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Statik risk sinyallerini açıkla")
    _add_input(analyze)
    analyze.add_argument("--context", type=_context, default=Context.GENERIC)
    analyze.add_argument("--format", choices=("text", "json", "jsonl", "sarif"), default="text")
    analyze.add_argument("--show-defensive-preview", action="store_true")

    transform = subparsers.add_parser("transform", help="İzlenebilir dönüşüm zinciri uygula")
    _add_input(transform)
    transform.add_argument("--step", type=_transform, action="append", required=True)
    transform.add_argument("--auto-depth", type=int, default=4)
    transform.add_argument("--format", choices=("text", "json", "jsonl"), default="text")

    compare = subparsers.add_parser("compare", help="İki metni ve risk farkını karşılaştır")
    compare.add_argument("left")
    compare.add_argument("right")
    compare.add_argument("--context", type=_context, default=Context.GENERIC)
    compare.add_argument("--format", choices=("text", "json", "jsonl"), default="text")

    fingerprint = subparsers.add_parser("fingerprint", help="Çalıştırmadan parmak izi çıkar")
    _add_input(fingerprint)

    subparsers.add_parser("catalog", help="Desteklenen bağlam ve dönüşümleri listele")
    subparsers.add_parser("self-test", help="Ağsız çekirdek öz sınamasını çalıştır")
    return parser


def _self_test() -> None:
    encoded = run_pipeline("Merhaba", [TransformName.BASE64_ENCODE, TransformName.BASE64_DECODE])
    if encoded.output != "Merhaba" or not all(step.round_trip_ok for step in encoded.steps):
        raise StudioError("dönüşüm öz sınaması başarısız")
    report = analyze_text("{{ USER_INPUT }}", Context.TEMPLATE)
    if not report.findings:
        raise StudioError("analiz öz sınaması başarısız")


def run(arguments: argparse.Namespace) -> str:
    if arguments.command == "analyze":
        text = _resolve_input(arguments.text, arguments.input_file)
        report = analyze_text(text, arguments.context)
        rendered = render_analysis(report, arguments.format)
        if arguments.show_defensive_preview:
            if arguments.format != "text":
                raise ValidationError("savunma önizlemesi yalnız text formatında kullanılabilir")
            preview = defensive_preview(text, arguments.context)
            rendered += "\n\nSavunma önizlemesi: " + (
                preview if preview is not None else "bu bağlamda yok"
            )
        return rendered
    if arguments.command == "transform":
        text = _resolve_input(arguments.text, arguments.input_file)
        return render_pipeline(
            run_pipeline(text, arguments.step, auto_depth=arguments.auto_depth), arguments.format
        )
    if arguments.command == "compare":
        return render_comparison(
            compare_texts(arguments.left, arguments.right, arguments.context), arguments.format
        )
    if arguments.command == "fingerprint":
        text = _resolve_input(arguments.text, arguments.input_file)
        fingerprint = fingerprint_text(text)
        import json

        return json.dumps(fingerprint.to_dict(), ensure_ascii=False, indent=2, allow_nan=False)
    if arguments.command == "catalog":
        contexts = "\n".join(f"- {item.value}" for item in Context)
        transforms = "\n".join(f"- {item.value}" for item in TransformName)
        return f"Bağlamlar:\n{contexts}\n\nDönüşümler:\n{transforms}"
    if arguments.command == "self-test":
        _self_test()
        return "Öz sınama başarılı; ağ veya harici süreç kullanılmadı."
    raise StudioError("bilinmeyen komut")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        output = run(parser.parse_args(argv))
    except (StudioError, OSError) as exc:
        print(f"Hata: {sanitize_terminal(str(exc))}", file=sys.stderr)
        return 2
    try:
        print(output)
    except BrokenPipeError:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
