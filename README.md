# CTF Payload Studio

CTF Payload Studio; kısa metin örneklerini **çalıştırmadan**, **ağa göndermeden** ve harici araç
başlatmadan analiz etmek için tasarlanmış çevrimdışı bir savunma laboratuvarıdır. Kodlama katmanlarını
incelemeyi, şüpheli sözdizimlerini açıklamayı ve doğru çıktı bağlamı savunmasını öğretir.

> Bu sürüm payload, reverse shell veya zararlı dosya üretmez; `msfvenom`, `msfconsole`, kabuk,
> `subprocess`, socket, `eval` ya da `exec` çağırmaz. Eski v3 davranışı güvenlik nedeniyle kaldırılmıştır.

## Neler sunar?

- URL, Base64, hex, HTML entity ve Unicode escape kodlama/çözme
- En fazla 8 katmanlı, döngü algılayan otomatik çözme
- XSS-benzeri HTML, SQL kontrol sözcükleri, path traversal, shell metakarakterleri ve SSTI-benzeri
  şablon ifadeleri için salt-okunur statik sinyaller
- HTML metni, HTML özniteliği, URL bileşeni, SQL değeri, kabuk argümanı, dosya yolu ve şablon
  bağlamlarına özel savunma önerileri
- Text, JSON, JSONL ve analiz araçlarıyla uyumlu SARIF 2.1.0 raporları
- İsteğe bağlı PyQt5 arayüzü ve tam özellikli CLI

## İleri özellikler

### 1. Açıklanabilir risk puanı

Her bulgu; kararlı kural kimliği, önem seviyesi, puan katkısı, görünür hâle getirilmiş kanıt,
gerekçe ve düzeltme önerisi taşır. Toplam 0–100 puan yalnız bir **önceliklendirme sinyalidir**;
zafiyet kanıtı değildir.

### 2. Dönüşüm provenance grafiği

Birden fazla dönüşüm tek zincirde uygulanabilir. Her adım giriş/çıkış SHA-256 değerini, boyut
değişimini ve mümkünse round-trip bütünlük sonucunu kaydeder. Rapor, doğrudan dokümana
yapıştırılabilen küçük bir Mermaid grafiği de üretir.

### 3. Güvenli karşılaştırma çalışma alanı

İki örnek; Unicode NFKC ve satır sonu normalizasyonundan sonra karşılaştırılır. Benzerlik oranı,
sınırlı fark parçaları, iki tarafın risk puanı ve risk farkı birlikte gösterilir. İçerik hiçbir zaman
çalıştırılmaz.

### 4. Parmak izi ve entropi

SHA-256, UTF-8 bayt/karakter sayısı, yazdırılabilir karakter oranı ve Shannon entropisi üretilir.
Yüksek entropi yalnızca kodlama ihtimaline ilişkin bilgi sinyalidir.

### 5. SARIF çıktısı

`--format sarif`, statik sinyalleri SARIF 2.1.0 olarak verir. Böylece raporlar bir CI artefaktı veya
kod tarama iş akışına **pasif veri** olarak eklenebilir.

## Güvenlik sınırları

- Tek girdi en fazla 64 KiB, dönüşüm zinciri en fazla 12 adımdır.
- Otomatik çözme derinliği 1–8 arasındadır ve tekrar eden çıktıda durur.
- `--input-file` yalnız normal, en fazla 64 KiB UTF-8 dosyalarını kabul eder; symlink ve FIFO reddedilir.
- Arşiv açma, dosya üretme, payload çalıştırma, ağ erişimi, tarama, listener ve süreç başlatma yoktur.
- GUI ve terminal hata/kanıt metinlerinde kontrol karakterleri çalıştırılmaz; görünür kaçışlara çevrilir.
- Araç bir zafiyet doğrulayıcısı değildir. Bulgular insan incelemesi ve bağlam doğrulaması gerektirir.

## Kurulum

Python 3.10–3.13 desteklenir.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

GUI gerekmiyorsa çekirdek kurulum bağımlılıksızdır:

```bash
python -m pip install .
```

## Kullanım

### Statik analiz

```bash
payload-studio analyze '{{ USER_INPUT }}' --context template
payload-studio analyze '&lt;etiket&gt;' --context html-text --format json
payload-studio analyze 'ornek' --format sarif > rapor.sarif
```

### Dönüşüm zinciri

```bash
payload-studio transform 'Merhaba Dünya' \
  --step url-encode \
  --step base64-encode \
  --format json

payload-studio transform 'TWVyaGFiYQ==' --step auto-decode --auto-depth 4
```

### Karşılaştırma ve parmak izi

```bash
payload-studio compare 'café' $'cafe\u0301' --context generic
payload-studio fingerprint 'yalnızca yerel örnek'
```

### GUI

```bash
payload-studio-gui
# veya eski giriş noktası:
python studio.py
```

GUI; Analiz, Dönüşüm Zinciri ve Karşılaştırma sekmelerini aynı test edilen çekirdek üzerinden
kullanır. Otomatik pano okuma/yazma yapmaz.

## Geliştirici doğrulaması

Bağımlılıklar bir kez kurulduktan sonra aşağıdaki tek komut ağsız çalışır:

```bash
make verify PYTHON=.venv/bin/python
```

Bu hedef format, lint, strict mypy, pytest, byte-compilation, ağsız/no-isolation sdist+wheel build,
paket içeriği ve CLI smoke kontrollerini çalıştırır. GitHub Actions da Python 3.10–3.13 için aynı
hedefi çağırır.

## Etik kullanım

Yalnızca yasal eğitim, CTF ve savunma amaçlı metin incelemelerinde kullanın. Bir örneği analiz
etmek, onu gerçek bir sisteme göndermek için izin vermez. Scope ve program kuralları her zaman
ayrıca doğrulanmalıdır.

## Lisans

[MIT](LICENSE)

