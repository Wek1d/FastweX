import sys
import os
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
                             QLineEdit, QFileDialog, QComboBox, QTextEdit, QGridLayout,
                             QCheckBox, QSpinBox, QMessageBox, QProgressBar, QGroupBox,
                             QTabWidget, QFrame)
from PyQt6.QtCore import QProcess, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

class YTDownloader(QWidget):
    def __init__(self):
        super().__init__()

        # Pencere ayarları + FastweX logosu
        self.setWindowTitle("FastweX İndirici")
        self.setWindowIcon(QIcon("C:/Users/Administrator/Documents/kod/FastweX/datas/logo/fastwex.png"))
        self.setGeometry(100, 100, 800, 700)

        # Yolları kontrol et
        self.yt_dlp_path = os.path.abspath("datas/yt-dlp/yt-dlp.exe")
        self.ffmpeg_dir = os.path.abspath("datas/ffmpeg-codec/bin")
        self.ffmpeg_path = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self.ffprobe_path = os.path.join(self.ffmpeg_dir, "ffprobe.exe")
        self.logo_path = "C:/Users/Administrator/Documents/kod/FastweX/datas/logo/fastwex.png"  # Logo yolu

        if not os.path.exists(self.yt_dlp_path):
            self.error_exit("yt-dlp.exe bulunamadı! Doğru dizinde mi?")
        if not os.path.exists(self.ffmpeg_path):
            self.error_exit("ffmpeg.exe bulunamadı! Doğru dizinde mi?")
        if not os.path.exists(self.ffprobe_path):
            self.error_exit("ffprobe.exe bulunamadı! Doğru dizinde mi?")
        if not os.path.exists(self.logo_path):
            print("⚠️ Logo dosyası bulunamadı, varsayılan ikon kullanılacak!")

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # ÜST KISIM: FastweX Logosu (Sağ Üst Köşe)
        self.logo_label = QLabel(self)
        logo_pixmap = QPixmap(self.logo_path)
        self.logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.logo_label, 0, 3, 1, 1, Qt.AlignmentFlag.AlignRight)  # Sağ üste hizala

        # TAB MENÜ
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1, 0, 1, 4)

        # TEMEL AYARLAR TAB'ı
        basic_tab = QWidget()
        basic_layout = QGridLayout()

        # URL Girişi
        self.url_label = QLabel("📌 Video URL:")
        basic_layout.addWidget(self.url_label, 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Örn: https://www.youtube.com/watch?v=...")
        basic_layout.addWidget(self.url_input, 0, 1, 1, 3)

        # Kayıt Klasörü
        self.path_label = QLabel("📂 Kaydedilecek Klasör:")
        basic_layout.addWidget(self.path_label, 1, 0)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        basic_layout.addWidget(self.path_input, 1, 1, 1, 2)
        self.browse_button = QPushButton("📁 Gözat")
        self.browse_button.setIcon(QIcon(self.logo_path))  # Butona logo ekle
        self.browse_button.setIconSize(QSize(16, 16))
        self.browse_button.clicked.connect(self.browse_folder)
        basic_layout.addWidget(self.browse_button, 1, 3)

        # Format Seçimi
        self.format_label = QLabel("🎬 Format:")
        basic_layout.addWidget(self.format_label, 2, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4 (Video+Ses)", "MP3 (Sadece Ses)", "M4A (Yüksek Kalite Ses)"])
        basic_layout.addWidget(self.format_combo, 2, 1, 1, 3)

        # Kalite Seçimi
        self.quality_label = QLabel("📶 Kalite Seçimi:")
        basic_layout.addWidget(self.quality_label, 3, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Otomatik (En İyi)", "Manuel Seçim"])
        basic_layout.addWidget(self.quality_combo, 3, 1, 1, 3)

        # Manuel Kalite Girişi
        self.manual_quality_input = QLineEdit()
        self.manual_quality_input.setPlaceholderText("Örn: 720, 1080, 4K")
        self.manual_quality_input.setEnabled(False)
        basic_layout.addWidget(self.manual_quality_input, 4, 1, 1, 3)
        self.quality_combo.currentIndexChanged.connect(self.toggle_manual_quality)

        basic_tab.setLayout(basic_layout)
        self.tabs.addTab(basic_tab, "Temel Ayarlar")

        # GELİŞMİŞ AYARLAR TAB'ı
        advanced_tab = QWidget()
        advanced_layout = QGridLayout()

        # Küçük Resim Ayarları
        self.thumbnail_group = QGroupBox("🖼️ Küçük Resim Ayarları")
        thumbnail_layout = QGridLayout()
        self.embed_thumbnail_checkbox = QCheckBox("Videoya göm")
        self.write_thumbnail_checkbox = QCheckBox("Dosya olarak kaydet (JPG)")
        thumbnail_layout.addWidget(self.embed_thumbnail_checkbox, 0, 0)
        thumbnail_layout.addWidget(self.write_thumbnail_checkbox, 0, 1)
        self.thumbnail_group.setLayout(thumbnail_layout)
        advanced_layout.addWidget(self.thumbnail_group, 0, 0, 1, 2)

        # İndirme Ayarları
        self.download_group = QGroupBox("⚡ İndirme Ayarları")
        download_layout = QGridLayout()
        self.limit_rate_label = QLabel("Hız Limiti (KB/s):")
        download_layout.addWidget(self.limit_rate_label, 0, 0)
        self.limit_rate_spinbox = QSpinBox()
        self.limit_rate_spinbox.setRange(0, 100000)
        download_layout.addWidget(self.limit_rate_spinbox, 0, 1)
        self.keep_files_checkbox = QCheckBox("Mevcut dosyaları koru")
        download_layout.addWidget(self.keep_files_checkbox, 1, 0)
        self.subtitles_checkbox = QCheckBox("Altyazıları indir (Tüm diller)")
        download_layout.addWidget(self.subtitles_checkbox, 1, 1)
        self.download_group.setLayout(download_layout)
        advanced_layout.addWidget(self.download_group, 1, 0, 1, 2)

        # Ekstra Özellikler
        self.extra_group = QGroupBox("🌟 Ekstra Özellikler")
        extra_layout = QGridLayout()
        self.metadata_checkbox = QCheckBox("Video bilgilerini göm")
        self.metadata_checkbox.setChecked(True)
        extra_layout.addWidget(self.metadata_checkbox, 0, 0)
        self.split_chapters_checkbox = QCheckBox("Bölümleri ayrı dosyalara kaydet")
        extra_layout.addWidget(self.split_chapters_checkbox, 0, 1)
        self.extra_group.setLayout(extra_layout)
        advanced_layout.addWidget(self.extra_group, 2, 0, 1, 2)

        advanced_tab.setLayout(advanced_layout)
        self.tabs.addTab(advanced_tab, "Gelişmiş Ayarlar")

        # İlerleme Çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 20px; }")
        layout.addWidget(self.progress_bar, 2, 0, 1, 4)

        # Log Çıktısı
        self.log_output = QTextEdit()
        self.log_output.setPlaceholderText("İndirme logları burada görünecek...")
        layout.addWidget(self.log_output, 3, 0, 1, 4)

        # İndirme Butonu (Logolu)
        self.download_button = QPushButton("🚀 İNDİRMEYİ BAŞLAT")
        self.download_button.setIconSize(QSize(24, 24))
        self.download_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                height: 40px;
                padding-left: 20px;
                padding-right: 20px;
            }
        """)
        self.download_button.clicked.connect(self.download_video)
        layout.addWidget(self.download_button, 4, 0, 1, 4)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if folder:
            self.path_input.setText(folder)

    def toggle_manual_quality(self):
        self.manual_quality_input.setEnabled(self.quality_combo.currentText() == "Manuel Seçim")

    def error_exit(self, message):
        QMessageBox.critical(self, "Hata", message)
        self.log_output.append(f"❌ Hata: {message}")
        self.setEnabled(False)

    def download_video(self):
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        url = self.url_input.text().strip()
        save_path = self.path_input.text().strip()
        format_choice = self.format_combo.currentText()
        quality_choice = self.quality_combo.currentText()
        manual_quality = self.manual_quality_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir URL girin!")
            return
        if not save_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt klasörü seçin!")
            return

        command = [
            self.yt_dlp_path,
            "-o", f"{save_path}/%(title)s.%(ext)s",
            "--ffmpeg-location", self.ffmpeg_dir,
            "--no-warnings",
            "--newline",
            "--no-colors"
        ]

        # Format Seçimi
        if format_choice == "MP4 (Video+Ses)":
            if quality_choice == "Manuel Seçim" and manual_quality.isdigit():
                command.extend(["-f", f"bestvideo[height<={manual_quality}]+bestaudio"])
            else:
                command.extend(["-f", "bestvideo+bestaudio"])
            command.extend(["--merge-output-format", "mp4"])
        elif format_choice == "MP3 (Sadece Ses)":
            command.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
        elif format_choice == "M4A (Yüksek Kalite Ses)":
            command.extend(["-f", "bestaudio[ext=m4a]", "--audio-quality", "0"])

        # Küçük Resim Ayarları
        if self.embed_thumbnail_checkbox.isChecked():
            command.extend(["--embed-thumbnail"])
        if self.write_thumbnail_checkbox.isChecked():
            command.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])

        # Gelişmiş Seçenekler
        if self.limit_rate_spinbox.value() > 0:
            command.extend(["--limit-rate", f"{self.limit_rate_spinbox.value()}K"])
        if self.keep_files_checkbox.isChecked():
            command.append("--no-overwrites")
        if self.subtitles_checkbox.isChecked():
            command.extend(["--write-subs", "--sub-langs", "all", "--convert-subs", "srt"])
        if self.metadata_checkbox.isChecked():
            command.append("--embed-metadata")
        if self.split_chapters_checkbox.isChecked():
            command.append("--split-chapters")

        command.append(url)

        self.log_output.append("🔍 Video bilgileri alınıyor...")
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)
        self.process.start(command[0], command[1:])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors='ignore').strip()
        if stdout:
            self.log_output.append(stdout)
            if "%" in stdout:
                try:
                    progress = float(re.search(r'(\d+\.\d+)%', stdout).group(1))
                    self.progress_bar.setValue(int(progress))
                except:
                    pass

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors='ignore').strip()
        if stderr:
            self.log_output.append(f"⚠️ {stderr}")

    def handle_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.log_output.append("\n🎉 İNDİRME BAŞARIYLA TAMAMLANDI!")
            QMessageBox.information(self, "Başarılı", "İndirme tamamlandı!")
        else:
            self.log_output.append(f"\n❌ HATA! Çıkış Kodu: {exit_code}")
            QMessageBox.warning(self, "Hata", "İndirme sırasında bir hata oluştu!")
        self.progress_bar.setValue(100)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YTDownloader()
    window.show()
    sys.exit(app.exec())