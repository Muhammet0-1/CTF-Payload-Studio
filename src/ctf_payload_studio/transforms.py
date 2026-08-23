"""Standart kütüphane tabanlı, sınırlı ve deterministik metin dönüşümleri."""

from __future__ import annotations

import base64
import binascii
import html
import re
import unicodedata
from urllib.parse import quote, unquote_to_bytes

from ctf_payload_studio.errors import TransformError, ValidationError
from ctf_payload_studio.models import AutoDecodeResult, TransformName
from ctf_payload_studio.validation import MAX_INPUT_BYTES, MAX_PIPELINE_STEPS, validate_text

_MALFORMED_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
_BASE64_TEXT = re.compile(r"[A-Za-z0-9+/]*={0,2}")
_HEX_TEXT = re.compile(r"(?:[0-9A-Fa-f]{2})+")
_UNICODE_ESCAPE = re.compile(r"\\(?:u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|x[0-9A-Fa-f]{2}|[\\nrt])")


def _decode_utf8(raw: bytes, name: str) -> str:
    try:
        result = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TransformError(f"{name} sonucu geçerli UTF-8 değil") from exc
    return validate_text(result, label="dönüşüm sonucu")


def _unicode_unescape(text: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "\\":
            output.append(text[index])
            index += 1
            continue
        if index + 1 >= len(text):
            raise TransformError("sonda tek başına ters eğik çizgi var")
        kind = text[index + 1]
        if kind in {"\\", "n", "r", "t"}:
            output.append({"\\": "\\", "n": "\n", "r": "\r", "t": "\t"}[kind])
            index += 2
            continue
        length = {"x": 2, "u": 4, "U": 8}.get(kind)
        if length is None or index + 2 + length > len(text):
            raise TransformError("desteklenmeyen veya eksik Unicode kaçışı")
        digits = text[index + 2 : index + 2 + length]
        if not all(character in "0123456789abcdefABCDEF" for character in digits):
            raise TransformError("Unicode kaçışında geçersiz onaltılık değer")
        value = int(digits, 16)
        if value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            raise TransformError("Unicode kaçışı geçerli bir skaler değer değil")
        output.append(chr(value))
        index += 2 + length
    return "".join(output)


def apply_transform(text: str, name: TransformName) -> str:
    text = validate_text(text)
    try:
        if name is TransformName.URL_ENCODE:
            result = quote(text, safe="")
        elif name is TransformName.URL_DECODE:
            if _MALFORMED_PERCENT.search(text):
                raise TransformError("URL kodlamasında eksik/geçersiz yüzde dizisi")
            result = _decode_utf8(unquote_to_bytes(text), name.value)
        elif name is TransformName.BASE64_ENCODE:
            result = base64.b64encode(text.encode()).decode("ascii")
        elif name is TransformName.BASE64_DECODE:
            compact = "".join(text.split())
            if len(compact) % 4 or not _BASE64_TEXT.fullmatch(compact):
                raise TransformError("Base64 girdisi kanonik biçimde değil")
            decoded = base64.b64decode(compact, validate=True)
            if base64.b64encode(decoded).decode("ascii") != compact:
                raise TransformError("Base64 girdisi kanonik biçimde değil")
            result = _decode_utf8(decoded, name.value)
        elif name is TransformName.HEX_ENCODE:
            result = text.encode().hex()
        elif name is TransformName.HEX_DECODE:
            compact = "".join(text.split())
            if not compact or not _HEX_TEXT.fullmatch(compact):
                raise TransformError("hex girdisi çift sayıda onaltılık karakter içermeli")
            result = _decode_utf8(bytes.fromhex(compact), name.value)
        elif name is TransformName.HTML_ENCODE:
            result = html.escape(text, quote=True)
        elif name is TransformName.HTML_DECODE:
            result = html.unescape(text)
        elif name is TransformName.UNICODE_ESCAPE:
            result = "".join(
                character
                if character.isascii() and character.isprintable() and character != "\\"
                else f"\\u{ord(character):04x}"
                if ord(character) <= 0xFFFF
                else f"\\U{ord(character):08x}"
                for character in text
            )
        elif name is TransformName.UNICODE_UNESCAPE:
            result = _unicode_unescape(text)
        elif name is TransformName.NORMALIZE:
            result = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
        else:
            raise TransformError(f"{name.value} doğrudan uygulanamaz")
    except (binascii.Error, ValueError) as exc:
        raise TransformError(f"{name.value} dönüşümü başarısız") from exc
    if len(result.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValidationError(f"dönüşüm sonucu {MAX_INPUT_BYTES} bayt sınırını aşıyor")
    return result


def inverse_for(name: TransformName) -> TransformName | None:
    pairs = {
        TransformName.URL_ENCODE: TransformName.URL_DECODE,
        TransformName.URL_DECODE: TransformName.URL_ENCODE,
        TransformName.BASE64_ENCODE: TransformName.BASE64_DECODE,
        TransformName.BASE64_DECODE: TransformName.BASE64_ENCODE,
        TransformName.HEX_ENCODE: TransformName.HEX_DECODE,
        TransformName.HEX_DECODE: TransformName.HEX_ENCODE,
        TransformName.HTML_ENCODE: TransformName.HTML_DECODE,
        TransformName.UNICODE_ESCAPE: TransformName.UNICODE_UNESCAPE,
    }
    return pairs.get(name)


def _candidate_decoder(text: str) -> TransformName | None:
    compact = "".join(text.split())
    if "%" in text and not _MALFORMED_PERCENT.search(text):
        return TransformName.URL_DECODE
    if "&" in text and ";" in text and html.unescape(text) != text:
        return TransformName.HTML_DECODE
    if _UNICODE_ESCAPE.search(text):
        return TransformName.UNICODE_UNESCAPE
    if len(compact) >= 2 and _HEX_TEXT.fullmatch(compact):
        return TransformName.HEX_DECODE
    if len(compact) >= 4 and len(compact) % 4 == 0 and _BASE64_TEXT.fullmatch(compact):
        return TransformName.BASE64_DECODE
    return None


def auto_decode(text: str, *, max_depth: int = 4) -> AutoDecodeResult:
    text = validate_text(text)
    if not 1 <= max_depth <= min(8, MAX_PIPELINE_STEPS):
        raise ValidationError("otomatik çözme derinliği 1 ile 8 arasında olmalıdır")
    current = text
    seen = {current}
    steps: list[TransformName] = []
    for _ in range(max_depth):
        candidate = _candidate_decoder(current)
        if candidate is None:
            break
        try:
            decoded = apply_transform(current, candidate)
        except TransformError:
            break
        if decoded == current or decoded in seen:
            break
        current = decoded
        seen.add(current)
        steps.append(candidate)
    return AutoDecodeResult(output=current, detected_steps=tuple(steps))
