"""Uygulamanın kullanıcıya güvenle gösterilebilen hata türleri."""


class StudioError(Exception):
    """Tüm beklenen uygulama hatalarının tabanı."""


class ValidationError(StudioError):
    """Girdi veya yapılandırma güvenli sınırların dışındadır."""


class TransformError(StudioError):
    """İstenen metin dönüşümü uygulanamadı."""
