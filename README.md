# ⚡ CTF Payload Studio

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Metasploit](https://img.shields.io/badge/Tool-Metasploit-red?style=for-the-badge)

**CTF Payload Studio**, sızma testleri ve CTF yarışmaları için geliştirilmiş, **GUI (Grafik Arayüzlü)** bir payload üretim ve yönetim merkezidir. Karmaşık `msfvenom` komutlarını ezberlemek yerine, bu araçla saniyeler içinde zararlı yükler oluşturabilir ve dinleyiciler başlatabilirsiniz.

## 🚀 Özellikler

### 1. 🚀 Quick Shells (Hızlı Kabuklar)
CTF sırasında en çok ihtiyaç duyulan "Reverse Shell One-Liner" kodlarını anında üretir.
* **Desteklenenler:** Bash, Python, Netcat (Traditional & OpenBSD), PHP, Perl, Powershell.
* IP ve Port girin, kodu alın ve kopyalayın.

### 2. 🛠️ Payload Generator
`msfvenom` arayüzü sayesinde hata yapmadan payload oluşturun.
* **Platformlar:** Windows, Linux, Android, Web.
* **Formatlar:** exe, elf, apk, php, asp, jsp, war, py...
* **Otomasyon:** Komutu arka planda çalıştırır ve çıktıyı kaydeder.

### 3. 🎧 Listener Manager
Oluşturduğunuz payload için `msfconsole` dinleyicisini tek tıkla, ayrı bir terminalde başlatır. `.rc` dosyalarıyla uğraşmanıza gerek kalmaz.

## 🛠️ Kurulum

Arch Linux ve diğer dağıtımlar için:

```bash
# Projeyi klonlayın
git clone [https://github.com/Muhammet0-1/CTF-Payload-Studio.git](https://github.com/Muhammet0-1/CTF-Payload-Studio.git)
cd CTF-Payload-Studio

# Gereksinimleri yükleyin
pip install PyQt5
# Metasploit Framework'ün sistemde yüklü olması gerekir.