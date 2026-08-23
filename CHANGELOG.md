# Değişiklik Günlüğü

## 4.0.0 - 2026-08-23

### Eklendi

- Kurulabilir `src/` paket yapısı, CLI ve isteğe bağlı PyQt5 GUI.
- Sınırlı URL, Base64, hex, HTML entity ve Unicode dönüşümleri.
- Açıklanabilir risk puanı ve bağlama duyarlı savunma önerileri.
- SHA-256/entropi parmak izi, round-trip kontrolü ve Mermaid provenance grafiği.
- Normalize edilmiş iki örnek karşılaştırması ve risk farkı.
- Text, JSON, JSONL ve SARIF raporları.
- Ağsız test izolasyonu, Python 3.10–3.13 CI ve tek komutlu `make verify`.

### Değişti

- `studio.py`, yeni güvenli GUI giriş noktasına dönüştürüldü.
- Projenin amacı çalıştırılabilir payload üretiminden çevrimdışı savunma analizine çevrildi.

### Kaldırıldı

- Reverse shell şablonları.
- `msfvenom` payload üretimi ve `msfconsole` listener yönetimi.
- Kabuk, `subprocess`, harici terminal, ağ ve otomatik dosya üretimi.

