from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QSpinBox, QCheckBox
)
from PySide6.QtGui import QCursor, QDesktopServices
from PySide6.QtCore import QUrl
import subprocess
from PySide6.QtGui import QIcon
import os
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
from brute_core import SimpleBruteForcer
import sys


QSS = """
* { color: #d5d7da; font-family: Segoe UI, Inter, Arial; }
QWidget { background-color: #0f141b; }
QLineEdit, QTextEdit, QSpinBox {
    background-color: #151b22; border: 1px solid #232b36; border-radius: 6px; padding: 8px;
}
QPushButton {
    background-color: #1e2733; border: 1px solid #2a3442; border-radius: 8px; padding: 10px;
}
QPushButton#startBtn { background-color: #1f6f43; }
QPushButton#pauseBtn { background-color: #2a3442; }
QPushButton#stopBtn  { background-color: #7a2a2a; }
QPushButton:hover { filter: brightness(1.1); }
QLabel#title { color: #d24b2a; font-size: 34px; font-weight: 800; letter-spacing: 2px; }
QLabel#subtitle { color: #6fb3c8; font-size: 16px; }
"""


class BruteForceThread(QThread):
    log_signal = Signal(str)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.engine = SimpleBruteForcer(**cfg)
        self.engine.set_log_callback(self.log_signal.emit)

    def run(self):
        self.engine.run()


class RoptcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROPTCHER GUI v1.6")

        icon_path = os.path.join(os.path.dirname(__file__), "icons", "Roptcher_icon.png")
        self.setWindowIcon(QIcon(icon_path))

        self.setMinimumSize(760, 680)
        self.setStyleSheet(QSS)
        self.thread = None

        root = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("ROPTCHER")
        title.setObjectName("title")
        subtitle = QLabel("GUI v1.6  |  Man in the Mask")
        subtitle.setObjectName("subtitle")
        header_text = QVBoxLayout()
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch(1)
        root.addLayout(header)

        grid = QGridLayout()
        self.url_input = QLineEdit()
        self.user_input = QLineEdit()
        self.wordlist_input = QLineEdit()
        self.proxy_input = QLineEdit()
        self.use_proxies = QCheckBox("Use proxies (one per line)")
        self.threads = QSpinBox()
        self.threads.setRange(1, 50)
        self.threads.setValue(5)

        browse = QPushButton("Browse")
        browse.setIcon(QIcon(os.path.join('icons', 'file_icon.png')))
        browse.clicked.connect(self.browse_wordlist)

        grid.addWidget(QLabel("Target URL"), 0, 0)
        grid.addWidget(self.url_input, 0, 1, 1, 2)
        grid.addWidget(QLabel("Username"), 1, 0)
        grid.addWidget(self.user_input, 1, 1, 1, 2)
        grid.addWidget(QLabel("Wordlist"), 2, 0)
        grid.addWidget(self.wordlist_input, 2, 1)
        grid.addWidget(browse, 2, 2)
        grid.addWidget(QLabel("Threads"), 3, 0)
        grid.addWidget(self.threads, 3, 1)

        proxy_browse = QPushButton("Browse")
        proxy_browse.setIcon(QIcon(os.path.join('icons', 'file_icon.png')))
        proxy_browse.clicked.connect(self.browse_proxy)
        grid.addWidget(QLabel("Proxies"), 4, 0)
        grid.addWidget(self.proxy_input, 4, 1)
        grid.addWidget(proxy_browse, 4, 2)
        grid.addWidget(self.use_proxies, 5, 1)

        root.addLayout(grid)

        btns = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("startBtn")
        self.pause_btn = QPushButton("Ⅱ Pause")
        self.pause_btn.setObjectName("pauseBtn")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.start_btn.clicked.connect(self.start)
        self.pause_btn.clicked.connect(self.pause)
        self.stop_btn.clicked.connect(self.stop)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.pause_btn)
        btns.addWidget(self.stop_btn)
        root.addLayout(btns)

        root.addWidget(QLabel("Output Console"))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        root.addWidget(self.console, 1)

        footer = QLabel("🔗 github.com/joshyboo25/roptcher")
        footer.setAlignment(Qt.AlignRight)
        footer.setStyleSheet("""
            QLabel {
                color: #444;
                font-size: 10px;
                padding: 5px;
            }
            QLabel:hover {
                color: #6fb3c8;
                text-decoration: underline;
            }
        """)
        footer.setCursor(QCursor(Qt.PointingHandCursor))
        footer.mousePressEvent = lambda event: open_url("https://github.com/joshyboo25/Roptcher-GUI/releases/tag/v1.6.0")

        root.addWidget(footer)


        def open_url(url: str):
            candidates = []

            if sys.platform.startswith("win"):
                candidates = [
                    "msedge",
                    "chrome",
                    "firefox",
                    "brave",
                    "opera"
                ]
            elif sys.platform.startswith("darwin"):
                candidates = [
                    "open -a Safari",
                    "open -a Google Chrome",
                    "open -a Firefox",
                    "open -a Brave Browser"
                ]
            else:
                candidates = [
                    "xdg-open",
                    "google-chrome",
                    "firefox",
                    "brave-browser"
                ]

            for browser in candidates:
                try:
                    cmd = browser.split() + [url]
                    if shutil.which(cmd[0]):
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
                except Exception:
                    pass

            QDesktopServices.openUrl(QUrl(url))


    def browse_proxy(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Proxy List", "", "Text Files (*.txt)")
        if file:
            self.proxy_input.setText(file)

    def browse_wordlist(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Wordlist", "", "Text Files (*.txt)")
        if file:
            self.wordlist_input.setText(file)

    def log(self, msg):
        self.console.append(msg)

    def start(self):
        cfg = dict(
            url=self.url_input.text().strip(),
            username=self.user_input.text().strip(),
            wordlist=self.wordlist_input.text().strip(),
            threads=self.threads.value(),
            proxy_file=self.proxy_input.text().strip() if self.use_proxies.isChecked() else None,
        )
        self.thread = BruteForceThread(cfg)
        self.thread.log_signal.connect(self.log)
        self.thread.start()

    def pause(self):
        if self.thread:
            self.thread.engine.toggle_pause()
            self.log("[*] Pause toggled")

    def stop(self):
        if self.thread:
            self.thread.engine.stop()
            self.log("[*] Stop requested")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RoptcherGUI()
    w.show()
    sys.exit(app.exec())


