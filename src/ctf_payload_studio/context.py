"""Çıktı bağlamına göre savunma tavsiyeleri ve güvenli örnekleme."""

from __future__ import annotations

import html
import shlex
from urllib.parse import quote

from ctf_payload_studio.models import Context
from ctf_payload_studio.validation import validate_text

_RECOMMENDATIONS: dict[Context, tuple[str, ...]] = {
    Context.GENERIC: (
        "Girdiyi veri olarak tutun; komut, sorgu veya şablon kodu olarak yorumlamayın.",
        "Çıktı bağlamını belirleyip kodlamayı mümkün olan en son noktada uygulayın.",
    ),
    Context.HTML_TEXT: (
        "HTML metin düğümünde &, < ve > karakterlerini bağlama uygun kodlayın.",
        "Kullanıcı girdisini innerHTML yerine textContent ile yerleştirin.",
    ),
    Context.HTML_ATTRIBUTE: (
        "Öznitelik değerini tırnak içine alın ve &, <, >, tek/çift tırnağı kodlayın.",
        "Olay işleyici ve URL taşıyan özniteliklere kullanıcı girdisi yerleştirmeyin.",
    ),
    Context.URL_COMPONENT: (
        "Tam URL yerine yalnız ilgili bileşeni RFC 3986 kurallarına göre kodlayın.",
        "Şema ve hedef alanı ayrı bir izin listesiyle doğrulayın.",
    ),
    Context.SQL_VALUE: (
        "Değeri kaçışla birleştirmek yerine parametreli sorgu ve tipli bağlama kullanın.",
        "Veritabanı hesabına yalnız gerekli en düşük yetkileri verin.",
    ),
    Context.SHELL_ARGUMENT: (
        "Mümkünse kabuk çağırmayın; argüman listesini doğrudan süreç API'sine verin.",
        "Komut adı ve seçenekleri sabit tutun, kullanıcı değerini ayrı argüman yapın.",
    ),
    Context.FILESYSTEM_PATH: (
        "Yolu sabit bir kök altında çözümleyin ve kökten kaçışı reddedin.",
        "Symlink ve özel dosya hedeflerini işlem öncesinde güvenli descriptor ile doğrulayın.",
    ),
    Context.TEMPLATE: (
        "Şablon kaynağını sabit tutun; kullanıcı girdisini yalnız veri değişkeni olarak bağlayın.",
        "Sandbox tek başına yeterli değildir; erişilebilir nesneleri izin listesiyle "
        "sınırlandırın.",
    ),
}


def recommendations_for(context: Context) -> tuple[str, ...]:
    return _RECOMMENDATIONS[context]


def defensive_preview(text: str, context: Context) -> str | None:
    """Yalnız güvenle örneklenebilen bağlamlar için kodlanmış görünüm döndürür."""
    text = validate_text(text)
    if context is Context.HTML_TEXT:
        return html.escape(text, quote=False)
    if context is Context.HTML_ATTRIBUTE:
        return html.escape(text, quote=True)
    if context is Context.URL_COMPONENT:
        return quote(text, safe="")
    if context is Context.SHELL_ARGUMENT:
        return shlex.quote(text)
    return None
