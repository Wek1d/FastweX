import sys
import os
import re
import json
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
                             QLineEdit, QFileDialog, QComboBox, QTextEdit, QGridLayout,
                             QCheckBox, QMessageBox, QProgressBar, QGroupBox,
                             QTabWidget, QHBoxLayout, QInputDialog, QSystemTrayIcon, QMenu,
                             QSplashScreen)  # Burada QSplashScreen'i ekledik
from PyQt6.QtCore import Qt, QSize, QProcess, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QTextCursor, QPalette, QAction

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_signal.emit(0, output.strip())
                    if "%" in output:
                        try:
                            progress = float(re.search(r'(\d+\.\d+)%', output).group(1))
                            self.progress_signal.emit(int(progress), "")
                        except:
                            pass

            stderr = process.stderr.read()
            if stderr:
                self.progress_signal.emit(0, stderr.strip())

            self.finished_signal.emit(process.returncode == 0, "")
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class FastweXDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_paths()
        self.check_dependencies()
        
        self.setWindowTitle("FastweX İndirici v4.1")
        self.setWindowIcon(QIcon(self.logo_path))
        self.setGeometry(100, 100, 900, 800)
        self.setMinimumSize(800, 700)
        
        # System tray setup
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.logo_path))
        self.tray_icon.setToolTip("FastweX İndirici")
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Göster", self)
        show_action.triggered.connect(self.show_normal)
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.setup_ui_theme()
        self.init_ui()
        self.load_config()

    def setup_paths(self):
        self.base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "datas")
        self.downloads_path = str(Path.home() / "Downloads")
        self.logo_path = os.path.join(self.data_dir, "logo", "fastwex.png")
        self.yt_dlp_path = os.path.join(self.data_dir, "yt-dlp", "yt-dlp.exe")
        self.gallery_dl_path = os.path.join(self.data_dir, "gallery-dl", "gallery-dl.exe")
        self.ffmpeg_dir = os.path.join(self.data_dir, "ffmpeg-codec", "bin")
        self.ffmpeg_path = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self.config_path = os.path.join(self.base_dir, "config.json")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.downloads_path, exist_ok=True)

    def check_dependencies(self):
        missing = []
        if not os.path.exists(self.yt_dlp_path):
            missing.append("yt-dlp.exe")
        if not os.path.exists(self.gallery_dl_path):
            missing.append("gallery-dl.exe")
        if not os.path.exists(self.ffmpeg_path):
            missing.append("ffmpeg.exe")
        
        if missing:
            QMessageBox.critical(self, "Hata", f"Eksik bağımlılıklar: {', '.join(missing)}")
            sys.exit(1)

    def setup_ui_theme(self):
        """Modern dark theme setup"""
        palette = QPalette()
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(63, 63, 70))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 122, 204))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            /* GENERAL STYLES */
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #f0f0f0;
            }
            
            /* GROUP BOXES */
            QGroupBox {
                border: 1px solid #3e3e42;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #2d2d30;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #f0f0f0;
            }
            
            /* BUTTONS */
            QPushButton {
                background-color: #3e3e42;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
                color: #f0f0f0;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #4e4e52;
                border-color: #5e5e62;
            }
            QPushButton:pressed {
                background-color: #2d2d30;
            }
            
            /* SPECIAL BUTTONS */
            QPushButton#download_button {
                background-color: #007acc;
                color: white;
                font-weight: bold;
                border: 1px solid #006bb3;
                font-size: 14px;
                height: 40px;
                padding-left: 20px;
                padding-right: 20px;
            }
            QPushButton#download_button:hover {
                background-color: #006bb3;
            }
            QPushButton#download_button:pressed {
                background-color: #005a9c;
            }
            
            QPushButton#browse_button, QPushButton#insta_browse_button {
                background-color: #68217a;
                color: white;
                border: 1px solid #5a1b6a;
            }
            QPushButton#browse_button:hover, QPushButton#insta_browse_button:hover {
                background-color: #5a1b6a;
            }
            
            QPushButton#add_url_button, QPushButton#load_txt_button {
                background-color: #d35400;
                color: white;
                border: 1px solid #b34700;
            }
            QPushButton#add_url_button:hover, QPushButton#load_txt_button:hover {
                background-color: #b34700;
            }
            
            QPushButton#clear_urls_button {
                background-color: #e51400;
                color: white;
                border: 1px solid #c41200;
            }
            QPushButton#clear_urls_button:hover {
                background-color: #c41200;
            }
            
            /* COMBOBOXES */
            QComboBox {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 5px;
                min-height: 28px;
            }
            QComboBox:hover {
                border-color: #5e5e62;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(:/qss_icons/rc/down_arrow.png);
                width: 10px;
                height: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                border: 1px solid #3e3e42;
                selection-background-color: #007acc;
                selection-color: white;
                outline: none;
            }
            
            /* CHECKBOXES */
            QCheckBox {
                spacing: 5px;
                color: #f0f0f0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #3e3e42;
                background-color: #252526;
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #5e5e62;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #006bb3;
                image: url(:/qss_icons/rc/checkbox_checked.png);
            }
            QCheckBox::indicator:unchecked {
                background-color: #252526;
                border: 1px solid #3e3e42;
            }
            
            /* LINE EDITS */
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 5px;
                min-height: 28px;
            }
            QLineEdit:hover {
                border-color: #5e5e62;
            }
            
            /* OTHER ELEMENTS */
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: Consolas;
                font-size: 10pt;
                border: 1px solid #3e3e42;
                border-radius: 4px;
            }
            QProgressBar {
                height: 20px;
                text-align: center;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                background-color: #252526;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                width: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                border-radius: 4px;
                margin-top: 5px;
                background-color: #2d2d30;
            }
            QTabBar::tab {
                padding: 8px 12px;
                background: #2d2d30;
                border: 1px solid #3e3e42;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                color: #f0f0f0;
            }
            QTabBar::tab:selected {
                background: #252526;
                border-bottom: 1px solid #252526;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover {
                background: #3e3e42;
            }
        """)

    def init_ui(self):
        layout = QGridLayout()

        # Logo
        self.init_logo(layout)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1, 0, 1, 4)

        # Video Tab
        self.init_video_tab()
        
        # Instagram Tab
        self.init_instagram_tab()

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar, 2, 0, 1, 4)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setPlaceholderText("İndirme logları burada görünecek...")
        layout.addWidget(self.log_output, 3, 0, 1, 4)

        # Download Button
        self.download_button = QPushButton("🚀 İNDİRMEYİ BAŞLAT")
        self.download_button.setObjectName("download_button")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button, 4, 0, 1, 4)

        self.setLayout(layout)
        
        # Startup optimization
        QTimer.singleShot(100, self.load_config)

    def init_logo(self, layout):
        self.logo_label = QLabel(self)
        if os.path.exists(self.logo_path):
            try:
                logo_pixmap = QPixmap(self.logo_path)
                self.logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
            except Exception as e:
                print(f"Logo yüklenemedi: {str(e)}")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.logo_label, 0, 3, 1, 1, Qt.AlignmentFlag.AlignRight)

    def init_video_tab(self):
        video_tab = QWidget()
        video_layout = QGridLayout()

        # URL Input
        self.url_label = QLabel("📌 Video URL(ler):")
        video_layout.addWidget(self.url_label, 0, 0)
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Her satıra bir URL girin\nVeya TXT dosyası seçin")
        self.url_input.setMaximumHeight(80)
        video_layout.addWidget(self.url_input, 0, 1, 1, 3)

        # URL Buttons
        url_button_layout = QHBoxLayout()
        
        self.add_url_button = QPushButton("URL Ekle")
        self.add_url_button.setObjectName("add_url_button")
        self.add_url_button.clicked.connect(self.add_url)
        url_button_layout.addWidget(self.add_url_button)
        
        self.load_txt_button = QPushButton("TXT Yükle")
        self.load_txt_button.setObjectName("load_txt_button")
        self.load_txt_button.clicked.connect(self.load_urls_from_txt)
        url_button_layout.addWidget(self.load_txt_button)
        
        self.clear_urls_button = QPushButton("Temizle")
        self.clear_urls_button.setObjectName("clear_urls_button")
        self.clear_urls_button.clicked.connect(self.clear_urls)
        url_button_layout.addWidget(self.clear_urls_button)
        
        video_layout.addLayout(url_button_layout, 1, 1, 1, 3)

        # Save Path
        self.path_label = QLabel("📂 Kayıt Klasörü:")
        video_layout.addWidget(self.path_label, 2, 0)
        
        self.path_input = QLineEdit(self.downloads_path)
        video_layout.addWidget(self.path_input, 2, 1, 1, 2)
        
        self.browse_button = QPushButton("Gözat")
        self.browse_button.setObjectName("browse_button")
        self.browse_button.clicked.connect(lambda: self.browse_folder(self.path_input))
        video_layout.addWidget(self.browse_button, 2, 3)

        # Format Selection
        self.format_label = QLabel("🎬 Format:")
        video_layout.addWidget(self.format_label, 3, 0)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4 (Video+Ses)", "MP3 (Sadece Ses)", "M4A (Yüksek Kalite Ses)"])
        video_layout.addWidget(self.format_combo, 3, 1, 1, 3)

        # Quality Selection
        self.quality_label = QLabel("📶 Kalite:")
        video_layout.addWidget(self.quality_label, 4, 0)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Otomatik (En İyi)", "Manuel Seçim"])
        self.quality_combo.currentIndexChanged.connect(self.toggle_manual_quality)
        video_layout.addWidget(self.quality_combo, 4, 1, 1, 3)

        # Manual Quality
        self.manual_quality_input = QLineEdit()
        self.manual_quality_input.setPlaceholderText("Örn: 720, 1080, 4K")
        self.manual_quality_input.setEnabled(False)
        video_layout.addWidget(self.manual_quality_input, 5, 1, 1, 3)

        # Alternative Download Option
        self.alternative_download_layout = QHBoxLayout()
        self.alternative_download_checkbox = QCheckBox("Alternatif İndirme (Hızlı)")
        self.alternative_download_checkbox.setToolTip("Sadece en iyi formatı indirir, diğer ayarları dikkate almaz")
        self.alternative_download_layout.addWidget(self.alternative_download_checkbox)
        video_layout.addLayout(self.alternative_download_layout, 6, 0, 1, 4)

        # Advanced Settings
        self.advanced_group = QGroupBox("⚙️ Gelişmiş Ayarlar")
        advanced_layout = QGridLayout()
        
        # Thumbnail Options
        self.embed_thumbnail_checkbox = QCheckBox("Küçük resim ekle")
        advanced_layout.addWidget(self.embed_thumbnail_checkbox, 0, 0)
        
        self.write_thumbnail_checkbox = QCheckBox("Küçük resmi kaydet")
        advanced_layout.addWidget(self.write_thumbnail_checkbox, 0, 1)
        
        # Other Options
        self.subtitles_checkbox = QCheckBox("Altyazıları indir")
        advanced_layout.addWidget(self.subtitles_checkbox, 1, 0)
        
        self.metadata_checkbox = QCheckBox("Bilgileri ekle")
        advanced_layout.addWidget(self.metadata_checkbox, 1, 1)
        
        # Unique Names Solution
        self.unique_names_checkbox = QCheckBox("Benzersiz isimler")
        self.unique_names_checkbox.setChecked(True)
        self.unique_names_checkbox.setToolTip("Aynı isimli dosyaların üzerine yazılmasını engeller")
        advanced_layout.addWidget(self.unique_names_checkbox, 2, 0, 1, 2)
        
        self.advanced_group.setLayout(advanced_layout)
        video_layout.addWidget(self.advanced_group, 7, 0, 1, 4)

        video_tab.setLayout(video_layout)
        self.tabs.addTab(video_tab, "🎥 Video İndir")

    def init_instagram_tab(self):
        insta_tab = QWidget()
        insta_layout = QGridLayout()

        # URL Input
        self.insta_url_label = QLabel("📌 Instagram URL:")
        insta_layout.addWidget(self.insta_url_label, 0, 0)
        
        self.insta_url_input = QLineEdit()
        self.insta_url_input.setPlaceholderText("Örn: https://www.instagram.com/p/...")
        insta_layout.addWidget(self.insta_url_input, 0, 1, 1, 3)

        # Save Path
        self.insta_path_label = QLabel("📂 Kayıt Klasörü:")
        insta_layout.addWidget(self.insta_path_label, 1, 0)
        
        self.insta_path_input = QLineEdit(self.downloads_path)
        insta_layout.addWidget(self.insta_path_input, 1, 1, 1, 2)
        
        self.insta_browse_button = QPushButton("Gözat")
        self.insta_browse_button.setObjectName("insta_browse_button")
        self.insta_browse_button.clicked.connect(lambda: self.browse_folder(self.insta_path_input))
        insta_layout.addWidget(self.insta_browse_button, 1, 3)

        # Options
        self.insta_options_group = QGroupBox("📷 İndirme Seçenekleri")
        options_layout = QGridLayout()
        
        self.insta_high_quality_check = QCheckBox("Yüksek kalite")
        self.insta_high_quality_check.setChecked(True)
        options_layout.addWidget(self.insta_high_quality_check, 0, 0)
        
        self.insta_captions_check = QCheckBox("Açıklamaları kaydet")
        options_layout.addWidget(self.insta_captions_check, 0, 1)
        
        self.insta_stories_check = QCheckBox("Hikayeleri indir")
        options_layout.addWidget(self.insta_stories_check, 1, 0)
        
        self.insta_igtv_check = QCheckBox("IGTV indir")
        options_layout.addWidget(self.insta_igtv_check, 1, 1)
        
        self.insta_options_group.setLayout(options_layout)
        insta_layout.addWidget(self.insta_options_group, 2, 0, 1, 4)

        # Alternative Download Option
        self.insta_alternative_layout = QHBoxLayout()
        self.insta_alternative_checkbox = QCheckBox("Alternatif İndirme (gallery-dl)")
        self.insta_alternative_checkbox.setToolTip("Instagram içeriğini gallery-dl ile indirir")
        self.insta_alternative_layout.addWidget(self.insta_alternative_checkbox)
        insta_layout.addLayout(self.insta_alternative_layout, 3, 0, 1, 4)

        insta_tab.setLayout(insta_layout)
        self.tabs.addTab(insta_tab, "📷 Instagram İndir")

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Video ayarları
                    self.path_input.setText(config.get('video_save_path', self.downloads_path))
                    self.format_combo.setCurrentIndex(config.get('format_index', 0))
                    self.quality_combo.setCurrentIndex(config.get('quality_index', 0))
                    self.manual_quality_input.setText(config.get('manual_quality', ''))
                    self.embed_thumbnail_checkbox.setChecked(config.get('embed_thumb', False))
                    self.write_thumbnail_checkbox.setChecked(config.get('write_thumb', False))
                    self.subtitles_checkbox.setChecked(config.get('subtitles', False))
                    self.metadata_checkbox.setChecked(config.get('metadata', False))
                    self.unique_names_checkbox.setChecked(config.get('unique_names', True))
                    self.alternative_download_checkbox.setChecked(config.get('alternative_download', False))
                    
                    # Instagram ayarları
                    self.insta_path_input.setText(config.get('insta_save_path', self.downloads_path))
                    self.insta_high_quality_check.setChecked(config.get('insta_high_quality', True))
                    self.insta_captions_check.setChecked(config.get('insta_captions', False))
                    self.insta_stories_check.setChecked(config.get('insta_stories', False))
                    self.insta_igtv_check.setChecked(config.get('insta_igtv', False))
                    self.insta_alternative_checkbox.setChecked(config.get('insta_alternative', False))
            except Exception as e:
                print(f"Config yüklenirken hata: {str(e)}")

    def save_config(self):
        config = {
            # Video ayarları
            'video_save_path': self.path_input.text(),
            'format_index': self.format_combo.currentIndex(),
            'quality_index': self.quality_combo.currentIndex(),
            'manual_quality': self.manual_quality_input.text(),
            'embed_thumb': self.embed_thumbnail_checkbox.isChecked(),
            'write_thumb': self.write_thumbnail_checkbox.isChecked(),
            'subtitles': self.subtitles_checkbox.isChecked(),
            'metadata': self.metadata_checkbox.isChecked(),
            'unique_names': self.unique_names_checkbox.isChecked(),
            'alternative_download': self.alternative_download_checkbox.isChecked(),
            
            # Instagram ayarları
            'insta_save_path': self.insta_path_input.text(),
            'insta_high_quality': self.insta_high_quality_check.isChecked(),
            'insta_captions': self.insta_captions_check.isChecked(),
            'insta_stories': self.insta_stories_check.isChecked(),
            'insta_igtv': self.insta_igtv_check.isChecked(),
            'insta_alternative': self.insta_alternative_checkbox.isChecked()
        }
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Config kaydedilirken hata: {str(e)}")

    def add_url(self):
        url, ok = QInputDialog.getText(self, "URL Ekle", "İndirilecek URL'yi girin:")
        if ok and url:
            self.url_input.append(url.strip())

    def load_urls_from_txt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "TXT Dosyası Seç", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip()]
                    self.url_input.setPlainText('\n'.join(urls))
                self.append_log(f"✅ {len(urls)} URL TXT dosyasından yüklendi", "success")
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Dosya okunurken hata oluştu:\n{str(e)}")

    def clear_urls(self):
        self.url_input.clear()

    def browse_folder(self, target_input):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç", self.downloads_path)
        if folder:
            target_input.setText(folder)

    def toggle_manual_quality(self):
        self.manual_quality_input.setEnabled(self.quality_combo.currentText() == "Manuel Seçim")

    def start_download(self):
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:  # Video sekmesi
            urls = [url.strip() for url in self.url_input.toPlainText().split('\n') if url.strip()]
            if not urls:
                QMessageBox.warning(self, "Uyarı", "Lütfen en az bir URL girin!")
                return
            
            self.save_config()
            self.download_videos(urls)
            
        elif current_tab == 1:  # Instagram sekmesi
            url = self.insta_url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir URL veya kullanıcı adı girin!")
                return
            
            self.save_config()
            if self.insta_alternative_checkbox.isChecked():
                self.download_instagram_with_gallery_dl(url)
            else:
                self.download_instagram(url)

    def download_videos(self, urls):
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        save_path = self.path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt klasörü seçin!")
            return

        # Çıktı şablonunu ayarla (benzersiz isimler için)
        output_template = f"{save_path}/%(title)s.%(ext)s"
        if self.unique_names_checkbox.isChecked():
            output_template = f"{save_path}/%(title)s-%(id)s.%(ext)s"

        base_command = [
            self.yt_dlp_path,
            "-o", output_template,
            "--ffmpeg-location", self.ffmpeg_dir,
            "--no-warnings",
            "--newline",
            "--no-colors",
            "--no-playlist"
        ]

        # Alternatif indirme seçeneği
        if self.alternative_download_checkbox.isChecked():
            base_command.extend(["-f", "best"])
        else:
            # Format Seçimi
            format_choice = self.format_combo.currentText()
            if format_choice == "MP4 (Video+Ses)":
                if self.quality_combo.currentText() == "Manuel Seçim" and self.manual_quality_input.text().strip().isdigit():
                    base_command.extend(["-f", f"bestvideo[height<={self.manual_quality_input.text().strip()}]+bestaudio"])
                else:
                    base_command.extend(["-f", "bestvideo+bestaudio"])
                base_command.extend(["--merge-output-format", "mp4"])
            elif format_choice == "MP3 (Sadece Ses)":
                base_command.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            elif format_choice == "M4A (Yüksek Kalite Ses)":
                base_command.extend(["-f", "bestaudio[ext=m4a]", "--audio-quality", "0"])

            # Diğer Ayarlar
            if self.embed_thumbnail_checkbox.isChecked():
                base_command.append("--embed-thumbnail")
            if self.write_thumbnail_checkbox.isChecked():
                base_command.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
            if self.subtitles_checkbox.isChecked():
                base_command.extend(["--write-subs", "--sub-langs", "all", "--convert-subs", "srt"])
            if self.metadata_checkbox.isChecked():
                base_command.append("--embed-metadata")

        # URL'leri işle
        self.total_urls = len(urls)
        self.current_url_index = 0
        self.urls = urls
        self.base_command = base_command
        
        # RAM optimizasyonu için thread kullan
        self.download_thread = DownloadThread(base_command + [urls[0]])
        self.download_thread.progress_signal.connect(self.handle_download_progress)
        self.download_thread.finished_signal.connect(self.handle_download_finished)
        self.download_thread.start()
        
        self.append_log(f"🔍 İndiriliyor: {urls[0]} (1/{self.total_urls})", "info")

    def download_instagram(self, url):
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        save_path = self.insta_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt klasörü seçin!")
            return

        try:
            import instaloader
            self.append_log("🔍 Instagram içeriği indiriliyor...", "info")
            
            L = instaloader.Instaloader(
                dirname_pattern=os.path.join(save_path, "{profile}", "{target}"),
                save_metadata=self.insta_captions_check.isChecked(),
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                compress_json=False
            )

            # İndirme seçenekleri
            options = {
                "profile": None,
                "fast_update": True,
                "download_videos": True,
                "download_pictures": True,
                "download_video_thumbnails": False,
                "download_geotags": False,
                "download_comments": False,
                "post_filter": None
            }

            if "/p/" in url:  # Tek gönderi
                post = instaloader.Post.from_shortcode(L.context, url.split("/p/")[1].split("/")[0])
                L.download_post(post, target=post.owner_username)
                self.append_log(f"✅ Gönderi indirildi: {post.shortcode}", "success")
            elif "/stories/" in url:  # Hikaye
                self.append_log("⚠️ Hikaye indirmek için giriş yapmalısınız", "warning")
                return
            else:  # Profil
                profile = instaloader.Profile.from_username(L.context, url.split("/")[-1])
                
                if self.insta_stories_check.isChecked():
                    self.append_log("⚠️ Hikaye indirmek için giriş yapmalısınız", "warning")
                
                if self.insta_igtv_check.isChecked():
                    L.download_igtv(profile)
                    self.append_log(f"✅ IGTV indirildi: {profile.username}", "success")
                
                L.download_profile(profile, profile_pic_only=False)
                self.append_log(f"✅ Profil indirildi: {profile.username}", "success")
            
            self.progress_bar.setValue(100)
            self.append_log("🎉 Instagram indirme tamamlandı!", "success")
            
        except Exception as e:
            self.append_log(f"❌ Hata: {str(e)}", "error")
            QMessageBox.warning(self, "Hata", f"Instagram indirme hatası:\n{str(e)}")

    def download_instagram_with_gallery_dl(self, url):
        self.progress_bar.setValue(0)
        self.log_output.clear()
        
        save_path = self.insta_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kayıt klasörü seçin!")
            return

        command = [
            self.gallery_dl_path,
            "--directory", save_path,
            "--no-check-certificate",
            "--filename", "%(title)s.%(ext)s"
        ]

        if self.insta_captions_check.isChecked():
            command.append("--write-metadata")

        command.append(url)

        self.append_log("🔍 Instagram içeriği indiriliyor (gallery-dl)...", "info")
        
        # RAM optimizasyonu için thread kullan
        self.download_thread = DownloadThread(command)
        self.download_thread.progress_signal.connect(self.handle_download_progress)
        self.download_thread.finished_signal.connect(self.handle_download_finished)
        self.download_thread.start()

    def handle_download_progress(self, progress, message):
        if progress > 0:
            self.progress_bar.setValue(progress)
        if message:
            self.append_log(message, "info")

    def handle_download_finished(self, success, error_message):
        if success:
            self.append_log("✅ İndirme tamamlandı", "success")
            if hasattr(self, 'current_url_index') and hasattr(self, 'total_urls'):
                self.current_url_index += 1
                if self.current_url_index < self.total_urls:
                    # Next URL in queue
                    next_url = self.urls[self.current_url_index]
                    self.append_log(f"\n🔍 İndiriliyor: {next_url} ({self.current_url_index + 1}/{self.total_urls})", "info")
                    
                    # Update command with next URL
                    command = self.base_command.copy()
                    command.append(next_url)
                    
                    # Start next download
                    self.download_thread = DownloadThread(command)
                    self.download_thread.progress_signal.connect(self.handle_download_progress)
                    self.download_thread.finished_signal.connect(self.handle_download_finished)
                    self.download_thread.start()
                else:
                    # All downloads completed
                    self.append_log("\n🎉 TÜM İNDİRMELER BAŞARIYLA TAMAMLANDI!", "success")
                    QMessageBox.information(self, "Başarılı", "Tüm indirmeler tamamlandı!")
                    self.progress_bar.setValue(100)
                    self.download_button.setEnabled(True)
        else:
            if error_message:
                self.append_log(f"❌ Hata: {error_message}", "error")
            else:
                self.append_log("❌ İndirme başarısız oldu!", "error")
            
            if hasattr(self, 'current_url_index') and hasattr(self, 'total_urls'):
                self.current_url_index += 1
                if self.current_url_index < self.total_urls:
                    # Continue with next URL despite error
                    next_url = self.urls[self.current_url_index]
                    self.append_log(f"\n⏭️ Bir sonraki URL'ye geçiliyor: {next_url}", "warning")
                    
                    command = self.base_command.copy()
                    command.append(next_url)
                    
                    self.download_thread = DownloadThread(command)
                    self.download_thread.progress_signal.connect(self.handle_download_progress)
                    self.download_thread.finished_signal.connect(self.handle_download_finished)
                    self.download_thread.start()
                else:
                    self.append_log("\n⚠️ Tüm URL'ler denendi ancak bazı hatalar oluştu!", "warning")
                    self.download_button.setEnabled(True)

    def append_log(self, message, msg_type="info"):
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if msg_type == "error":
            color = "#ff4444"  # Kırmızı
        elif msg_type == "success":
            color = "#44ff44"  # Yeşil
        elif msg_type == "warning":
            color = "#ffff44"  # Sarı
        else:
            color = "#ffffff"  # Beyaz
        
        self.log_output.setTextColor(QColor(color))
        cursor.insertText(message + "\n")
        self.log_output.setTextColor(QColor("#e0e0e0"))
        
        self.log_output.ensureCursorVisible()

    def show_normal(self):
        """Restore window from system tray"""
        self.showNormal()
        self.activateWindow()
        self.setWindowState(Qt.WindowState.WindowActive)

    def quit_app(self):
        """Clean exit from system tray"""
        self.save_config()
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Minimize to system tray instead of closing"""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "FastweX İndirici",
                "Uygulama sistem tepsisinde çalışmaya devam ediyor",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.save_config()
            event.accept()

    def minimize_to_tray(self):
        """Minimize to system tray"""
        self.hide()
        self.tray_icon.showMessage(
            "FastweX İndirici",
            "Uygulama sistem tepsisinde çalışmaya devam ediyor",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

if __name__ == "__main__":
    # Optimize application startup
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better performance
    
    # Create and show splash screen (optional)
    splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), "datas", "logo", "fastwex.png"))
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    
    # Initialize main window in background
    QTimer.singleShot(100, lambda: splash.close())
    
    window = FastweXDownloader()
    window.show()
    
    sys.exit(app.exec())
