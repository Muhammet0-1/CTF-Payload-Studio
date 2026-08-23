# Güvenlik Politikası

## Desteklenen sürüm

Yalnız en güncel `main` sürümü güvenlik düzeltmeleri alır.

## Güvenlik bildirimi

Hassas bir sorunu herkese açık issue ile paylaşmayın. GitHub deposundaki **Security → Report a
vulnerability** kanalını kullanın. Şunları ekleyin:

- Etkilenen sürüm ve işletim sistemi
- Yeniden üretim için zararsız, yerel ve en küçük örnek
- Beklenen ve gözlenen davranış
- Olası etki ve önerilen düzeltme

Gerçek hedef, token, parola, kişisel veri veya çalıştırılabilir zararlı örnek eklemeyin.

## Tasarım varsayımları

CTF Payload Studio girdiyi güvenilmez veri kabul eder. Araç metni çalıştırmaz ve ağa göndermez.
64 KiB girdi, sınırlı decoder derinliği, sınırlı diff ve provenance boyutu güvenlik sözleşmesinin
parçasıdır. Bunları aşan davranışlar desteklenmez.

Statik eşleşmenin olmaması güvenlik garantisi, eşleşme olması da doğrulanmış zafiyet değildir.

