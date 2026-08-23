# Katkıda Bulunma

Katkılar çevrimdışı, savunma odaklı ve deterministik kalmalıdır.

## Geliştirme

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
make bootstrap PYTHON=.venv/bin/python
make verify PYTHON=.venv/bin/python
```

`make verify`, bootstrap sonrasında ağsızdır. Pull request açmadan önce komutun tamamını çalıştırın.

## Kabul edilmeyen katkılar

- Reverse/bind shell, zararlı dosya veya hazır exploit üretimi
- Listener, tarayıcı, crawler, hedef keşfi ya da ağ iletişimi
- `eval`, `exec`, kabuk veya kullanıcı kontrollü subprocess
- WAF/AV/EDR atlatma, gizleme veya kalıcılık tekniği
- Gerçek hedef, kimlik bilgisi, token veya kullanıcı verisi
- Kaynak tüketimi sınırı olmayan decoder ya da regex

Yeni analiz kuralları; inert regresyon örnekleri, açık gerekçe, savunma önerisi ve yanlış pozitif
sınırlarıyla birlikte gelmelidir.

