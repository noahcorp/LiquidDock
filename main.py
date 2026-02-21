import sys
import json
import os
import webbrowser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QFileDialog, QLineEdit, QHBoxLayout, QLabel, QFrame, 
                             QFileIconProvider, QScrollArea)
from PyQt6.QtCore import Qt, QFileInfo, QSize

# --- CONFIGURATION ---
CONFIG_FILE = "dock_config.json"
# METS TON LIEN GITHUB ICI
GITHUB_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&start_radio=1"

class GlassDock(QWidget):
    def __init__(self):
        super().__init__()
        
        # Chargement de la config (Apps, Position Menu, Position Fenêtre)
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
        
        # Replacer le dock là où il était
        if self.win_pos:
            self.move(self.win_pos[0], self.win_pos[1])

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout_principal = QHBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(10)

        # --- LE DOCK ---
        self.dock_frame = QFrame()
        self.dock_frame.setFixedWidth(95)
        self.dock_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 30);
            border: 1px solid rgba(255, 255, 255, 45);
            border-radius: 30px;
        """)
        
        self.dock_layout = QVBoxLayout(self.dock_frame)
        self.dock_layout.setContentsMargins(10, 15, 10, 15)
        self.dock_layout.setSpacing(15)
        
        # Poignée de déplacement
        self.handle = QFrame()
        self.handle.setFixedHeight(4); self.handle.setFixedWidth(40)
        self.handle.setStyleSheet("background-color: rgba(255, 255, 255, 200); border-radius: 2px;")
        self.dock_layout.addWidget(self.handle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Scroll Area pour les Apps
        self.scroll_apps = QScrollArea()
        self.scroll_apps.setWidgetResizable(True)
        self.scroll_apps.setStyleSheet("background: transparent; border: none;")
        self.scroll_apps.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.apps_container = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_layout.setSpacing(12)
        self.scroll_apps.setWidget(self.apps_container)
        self.dock_layout.addWidget(self.scroll_apps)

        self.refresh_buttons()
        self.dock_layout.addStretch()

        # Bouton Paramètres
        self.btn_toggle_settings = QPushButton("⚙️")
        self.btn_toggle_settings.setFixedSize(60, 60)
        self.btn_toggle_settings.setStyleSheet("""
            QPushButton { background: rgba(0,0,0,40); border-radius: 30px; color: white; font-size: 24px; border: none; }
            QPushButton:hover { background: rgba(0,0,0,80); }
        """)
        self.btn_toggle_settings.clicked.connect(self.toggle_settings)
        self.dock_layout.addWidget(self.btn_toggle_settings, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- PANNEAU DE CONFIGURATION ---
        self.side_panel = QFrame()
        self.side_panel.setFixedWidth(250)
        self.side_panel.setVisible(False)
        self.side_panel.setStyleSheet("background: rgba(255, 255, 255, 25); border: 1px solid rgba(255, 255, 255, 40); border-radius: 25px; color: white;")
        
        self.side_layout = QVBoxLayout(self.side_panel)
        self.side_layout.addWidget(QLabel("<b>AJOUTER UNE APP / JEU</b>"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.name_in = QLineEdit(); self.name_in.setPlaceholderText("Nom...")
        self.path_in = QLineEdit(); self.path_in.setPlaceholderText("Chemin ou fichier...")
        for w in [self.name_in, self.path_in]:
            w.setStyleSheet("background: rgba(0,0,0,60); border:none; padding: 10px; color: white; border-radius: 10px;")
            self.side_layout.addWidget(w)

        btn_browse = QPushButton("📁 Parcourir"); btn_browse.clicked.connect(self.browse_file)
        btn_add = QPushButton("✨ Ajouter"); btn_add.clicked.connect(self.add_app)
        btn_add.setStyleSheet("background: #007AFF; font-weight: bold; padding: 10px; border-radius: 10px;")
        
        self.side_layout.addWidget(btn_browse)
        self.side_layout.addWidget(btn_add)
        self.side_layout.addStretch()
        
        # Position du menu
        self.btn_pos = QPushButton(f"Position Menu : {self.side.upper()}")
        self.btn_pos.setStyleSheet("background: rgba(255,255,255,20); padding: 8px; border-radius: 10px;")
        self.btn_pos.clicked.connect(self.switch_side)
        self.side_layout.addWidget(self.btn_pos)

        #(Mise à jour)
        btn_git = QPushButton("Mise a Jour")
        btn_git.setStyleSheet("background: rgba(0,0,0,50); padding: 8px; border-radius: 10px; color: #ddd;")
        btn_git.clicked.connect(self.go_to_github)
        self.side_layout.addWidget(btn_git)
        
        # Bouton Quitter
        btn_quit = QPushButton("🔴 Quitter le Dock")
        btn_quit.setStyleSheet("""
            QPushButton { background: rgba(200, 50, 50, 60); border-radius: 10px; padding: 10px; font-weight: bold; margin-top: 10px; }
            QPushButton:hover { background: rgba(200, 50, 50, 150); }
        """)
        btn_quit.clicked.connect(QApplication.instance().quit)
        self.side_layout.addWidget(btn_quit)

        self.apply_layout_order()
        self.adjust_size()

    def refresh_buttons(self):
        for i in reversed(range(self.apps_layout.count())): 
            widget = self.apps_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
        
        icon_provider = QFileIconProvider()
        for idx, app in enumerate(self.apps):
            btn = QPushButton()
            path = app['path']
            btn.setIcon(icon_provider.icon(QFileInfo(path)))
            btn.setIconSize(QSize(40, 40))
            btn.setToolTip(f"{app['name']}\n(Clic droit pour supprimer)")
            btn.setFixedSize(70, 70)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda p, i=idx: self.remove_app(i))
            btn.setStyleSheet("QPushButton { background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,30); border-radius: 20px; } QPushButton:hover { background: rgba(255,255,255,80); border: 1px solid white; }")
            btn.clicked.connect(lambda chk, p=path: os.startfile(p) if os.path.exists(p) else print("Erreur : Fichier introuvable"))
            self.apps_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.adjust_size()

    def apply_layout_order(self):
        self.layout_principal.removeWidget(self.dock_frame); self.layout_principal.removeWidget(self.side_panel)
        if self.side == "right":
            self.layout_principal.addWidget(self.dock_frame); self.layout_principal.addWidget(self.side_panel)
        else:
            self.layout_principal.addWidget(self.side_panel); self.layout_principal.addWidget(self.dock_frame)

    def switch_side(self):
        self.side = "left" if self.side == "right" else "right"
        self.btn_pos.setText(f"Position Menu : {self.side.upper()}")
        self.apply_layout_order(); self.save_config()

    def toggle_settings(self):
        self.settings_open = not self.settings_open
        self.side_panel.setVisible(self.settings_open); self.adjust_size()

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Choisir un fichier", "", "Tous les fichiers (*)")
        if f: 
            self.path_in.setText(f)
            if not self.name_in.text(): self.name_in.setText(QFileInfo(f).baseName().capitalize())

    def go_to_github(self):
        webbrowser.open(GITHUB_URL)

    def add_app(self):
        if self.name_in.text() and self.path_in.text():
            self.apps.append({"name": self.name_in.text(), "path": self.path_in.text()})
            self.save_config(); self.refresh_buttons()
            self.name_in.clear(); self.path_in.clear()

    def remove_app(self, index):
        del self.apps[index]; self.save_config(); self.refresh_buttons()

    def adjust_size(self): self.adjustSize()

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
