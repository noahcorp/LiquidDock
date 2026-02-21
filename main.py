import sys
import json
import os
import webbrowser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QFileDialog, QLineEdit, QHBoxLayout, QLabel, QFrame, 
                             QFileIconProvider, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QFileInfo, QSize

CONFIG_FILE = "dock_config.json"
GITHUB_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&start_radio=1"

class GlassDock(QWidget):
    def __init__(self):
        super().__init__()
        
        config_data = self.load_config()
        if isinstance(config_data, list):
            self.apps = config_data
            self.side = "right"
            self.win_pos = None
        else:
            self.apps = config_data.get("apps", [])
            self.side = config_data.get("side", "right")
            self.win_pos = config_data.get("pos", None)
        
        self.settings_open = False
        self.initUI()
        
        if self.win_pos:
            self.move(self.win_pos[0], self.win_pos[1])

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(10)

        # --- DOCK ---
        self.dock_frame = QFrame()
        self.dock_frame.setFixedWidth(95)
        self.dock_frame.setStyleSheet("""
            background-color: rgba(30, 30, 30, 180);
            border: 1px solid rgba(255, 255, 255, 40);
            border-radius: 35px;
        """)
        
        self.dock_layout = QVBoxLayout(self.dock_frame)
        self.dock_layout.setContentsMargins(10, 20, 10, 20)
        self.dock_layout.setSpacing(10)
        
        # Poignée
        self.handle = QFrame()
        self.handle.setFixedHeight(4); self.handle.setFixedWidth(35)
        self.handle.setStyleSheet("background-color: rgba(255, 255, 255, 100); border-radius: 2px;")
        self.dock_layout.addWidget(self.handle, alignment=Qt.AlignmentFlag.AlignCenter)

        # ZONE DE SCROLL (LA CORRECTION EST ICI)
        self.scroll_apps = QScrollArea()
        self.scroll_apps.setWidgetResizable(True)
        self.scroll_apps.setStyleSheet("background: transparent; border: none;")
        self.scroll_apps.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Ce widget contiendra les icônes
        self.apps_container = QWidget()
        self.apps_container.setStyleSheet("background: transparent;")
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setContentsMargins(0, 5, 0, 5)
        self.apps_layout.setSpacing(15)
        self.apps_layout.addStretch() # Stretch interne pour pousser les icônes vers le haut
        
        self.scroll_apps.setWidget(self.apps_container)
        self.dock_layout.addWidget(self.scroll_apps)

        # Bouton Paramètres
        self.btn_toggle_settings = QPushButton("⚙️")
        self.btn_toggle_settings.setFixedSize(65, 65)
        self.btn_toggle_settings.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 15); border-radius: 32px; color: white; font-size: 26px; border: none; }
            QPushButton:hover { background: rgba(255, 255, 255, 30); }
        """)
        self.btn_toggle_settings.clicked.connect(self.toggle_settings)
        self.dock_layout.addWidget(self.btn_toggle_settings, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- PANNEAU DE REGLAGES ---
        self.side_panel = QFrame()
        self.side_panel.setFixedWidth(250)
        self.side_panel.setVisible(False)
        self.side_panel.setStyleSheet("background: rgba(30, 30, 30, 220); border: 1px solid rgba(255, 255, 255, 30); border-radius: 25px; color: white;")
        
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.setContentsMargins(15, 15, 15, 15)
        self.side_layout.addWidget(QLabel("<b>DOCK SETTINGS</b>"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.name_in = QLineEdit(); self.name_in.setPlaceholderText("Nom...")
        self.path_in = QLineEdit(); self.path_in.setPlaceholderText("Chemin...")
        for w in [self.name_in, self.path_in]:
            w.setStyleSheet("background: rgba(255,255,255,10); border:none; padding: 10px; color: white; border-radius: 8px;")
            self.side_layout.addWidget(w)

        btn_browse = QPushButton("📁 Parcourir"); btn_browse.clicked.connect(self.browse_file)
        btn_add = QPushButton("✨ Ajouter l'App"); btn_add.clicked.connect(self.add_app)
        btn_add.setStyleSheet("background: #007AFF; font-weight: bold; padding: 10px; border-radius: 8px; color: white;")
        
        self.side_layout.addWidget(btn_browse)
        self.side_layout.addWidget(btn_add)
        self.side_layout.addStretch()
        
        self.btn_pos = QPushButton(f"Menu : {self.side.upper()}")
        self.btn_pos.setStyleSheet("background: rgba(255,255,255,10); padding: 8px; border-radius: 8px; color: white;")
        self.btn_pos.clicked.connect(self.switch_side)
        self.side_layout.addWidget(self.btn_pos)

        btn_git = QPushButton("🚀 GitHub Project")
        btn_git.clicked.connect(self.go_to_github)
        btn_git.setStyleSheet("background: rgba(255,255,255,10); padding: 8px; border-radius: 8px; color: #aaa;")
        self.side_layout.addWidget(btn_git)
        
        btn_quit = QPushButton("🔴 Fermer le Dock")
        btn_quit.setStyleSheet("background: rgba(255, 59, 48, 40); border-radius: 8px; padding: 10px; color: #ff3b30; font-weight: bold;")
        btn_quit.clicked.connect(QApplication.instance().quit)
        self.side_layout.addWidget(btn_quit)

        self.apply_layout_order()
        self.refresh_buttons()

    def refresh_buttons(self):
        # On vide tout sauf le stretch
        for i in reversed(range(self.apps_layout.count())): 
            item = self.apps_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        icon_provider = QFileIconProvider()
        for idx, app in enumerate(self.apps):
            btn = QPushButton()
            path = app['path']
            btn.setIcon(icon_provider.icon(QFileInfo(path)))
            btn.setIconSize(QSize(45, 45))
            btn.setFixedSize(70, 70)
            btn.setToolTip(app['name'])
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda p, i=idx: self.remove_app(i))
            btn.setStyleSheet("""
                QPushButton { background: rgba(255,255,255,10); border: 1px solid rgba(255,255,255,15); border-radius: 20px; }
                QPushButton:hover { background: rgba(255,255,255,40); border: 1px solid white; }
            """)
            btn.clicked.connect(lambda chk, p=path: os.startfile(p) if os.path.exists(p) else None)
            self.apps_layout.insertWidget(idx, btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Calcul de la hauteur : chaque icône fait 70 + 15 de spacing
        # On limite la hauteur pour ne pas que ça devienne géant
        content_height = len(self.apps) * 85
        if content_height > 500: content_height = 500
        if content_height < 85 and len(self.apps) > 0: content_height = 85
        
        self.scroll_apps.setFixedHeight(content_height if len(self.apps) > 0 else 20)
        self.adjust_size()

    def apply_layout_order(self):
        self.layout_principal.removeWidget(self.dock_frame)
        self.layout_principal.removeWidget(self.side_panel)
        if self.side == "right":
            self.layout_principal.addWidget(self.dock_frame); self.layout_principal.addWidget(self.side_panel)
        else:
            self.layout_principal.addWidget(self.side_panel); self.layout_principal.addWidget(self.dock_frame)

    def switch_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.btn_pos.setText(f"Menu : {self.side.upper()}")
        self.apply_layout_order(); self.save_config()

    def toggle_settings(self):
        self.settings_open = not self.settings_open
        self.side_panel.setVisible(self.settings_open)
        self.adjust_size()

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", "Tous les fichiers (*)")
        if f: 
            self.path_in.setText(f)
            if not self.name_in.text(): self.name_in.setText(QFileInfo(f).baseName().capitalize())

    def go_to_github(self): webbrowser.open(GITHUB_URL)

    def add_app(self):
        if self.name_in.text() and self.path_in.text():
            self.apps.append({"name": self.name_in.text(), "path": self.path_in.text()})
            self.save_config(); self.refresh_buttons()
            self.name_in.clear(); self.path_in.clear()

    def remove_app(self, index):
        del self.apps[index]; self.save_config(); self.refresh_buttons()

    def adjust_size(self):
        self.adjustSize()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try: 
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        data = {"side": self.side, "apps": self.apps, "pos": [self.x(), self.y()]}
        with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=4)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            self.save_config()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dock = GlassDock()
    dock.show()
    sys.exit(app.exec())
