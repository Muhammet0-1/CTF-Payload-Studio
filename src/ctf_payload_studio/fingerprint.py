"""Metni çalıştırmadan kararlı parmak izi ve basit istatistikler üretir."""

from __future__ import annotations

import hashlib
import math
from collections import Counter

from ctf_payload_studio.models import Fingerprint
from ctf_payload_studio.validation import validate_text


def fingerprint_text(text: str) -> Fingerprint:
    text = validate_text(text)
    raw = text.encode("utf-8")
    if raw:
        counts = Counter(raw)
        entropy = -sum(
            (count / len(raw)) * math.log2(count / len(raw)) for count in counts.values()
        )
    else:
        entropy = 0.0
    printable = sum(character.isprintable() or character in "\n\r\t" for character in text)
    ratio = printable / len(text) if text else 1.0
    return Fingerprint(
        sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw),
        characters=len(text),
        entropy=round(entropy, 4),
        printable_ratio=round(ratio, 4),
    )
