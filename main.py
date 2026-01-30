import sys
import os
import json
import psutil
import datetime
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QMenu, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize
from PyQt6.QtGui import QMovie, QAction

# --- 模块1：配置加载 ---
def load_config():
    default_config = {
        "pet_name": "Skeleton_Guardian",
        "pet_size": 160,
        "refresh_rate": 1000,
        "cpu_busy": 30,
        "cpu_attack": 70,
        "cpu_extreme": 90,
        "mem_danger": 80,
        "actions": {
            "idle": "idle.gif",
            "walk": "walk.gif",
            "attack": "attack.gif",
            "hit": "hit.gif"
        }
    }
    path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except: pass
    return default_config

# --- 模块2：主窗口 ---
class SkeletonSentinel(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.current_state = None
        self.old_pos = QPoint()
        self.is_interacting = False # 交互状态锁
        
        self.init_ui()
        
        # 逻辑循环定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(self.config["refresh_rate"])

    def init_ui(self):
        # 窗口透明、置顶、无边框
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 状态栏 UI
        self.info_label = QLabel("Initializing...", self)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 150);
            color: #00FF00;
            border-radius: 6px;
            padding: 2px;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
        """)
        
        # 动画容器
        self.img_label = QLabel(self)
        self.img_label.setScaledContents(True)
        
        layout.addWidget(self.info_label)
        layout.addWidget(self.img_label)
        self.setLayout(layout)

        size = self.config["pet_size"]
        self.resize(size, size + 40)
        self.img_label.setFixedSize(size, size)
        
        self.update_logic()

    def update_logic(self):
        # 正在播放双击动画时暂停逻辑更新
        if self.is_interacting:
            return

        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        
        # 更新文字
        self.info_label.setText(f"CPU:{cpu}% RAM:{mem}%")
        
        # 状态判定优先级逻辑
        if cpu >= self.config["cpu_extreme"] or mem >= self.config["mem_danger"]:
            new_state = "hit"
            self.info_label.setStyleSheet("background-color: rgba(255, 0, 0, 200); color: white; border-radius: 6px;")
        elif cpu >= self.config["cpu_attack"]:
            new_state = "attack"
            self.info_label.setStyleSheet("background-color: rgba(255, 140, 0, 180); color: white; border-radius: 6px;")
        elif cpu >= self.config["cpu_busy"]:
            new_state = "walk"
            self.info_label.setStyleSheet("background-color: rgba(200, 200, 0, 180); color: black; border-radius: 6px;")
        else:
            new_state = "idle"
            self.info_label.setStyleSheet("background-color: rgba(0, 0, 0, 120); color: #00FF00; border-radius: 6px;")

        self.change_animation(new_state)

    def change_animation(self, state_key):
        if state_key != self.current_state:
            self.current_state = state_key
            gif_name = self.config["actions"].get(state_key, "idle.gif")
            gif_path = os.path.join(os.path.dirname(__file__), gif_name)
            
            if os.path.exists(gif_path):
                self.movie = QMovie(gif_path)
                size = self.config["pet_size"]
                self.movie.setScaledSize(QSize(size, size))
                self.img_label.setMovie(self.movie)
                self.movie.start()

    # --- 交互事件 ---
    def mouseDoubleClickEvent(self, event):
        self.is_interacting = True
        self.info_label.setText("CRITICAL HIT!")
        self.info_label.setStyleSheet("background-color: white; color: red; font-weight: bold; border-radius: 6px;")
        self.change_animation("hit")
        QTimer.singleShot(1500, self.reset_interaction)

    def reset_interaction(self):
        self.is_interacting = False
        self.current_state = None 
        self.update_logic()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        exit_action = QAction("驱散守卫 (Exit)", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.old_pos.isNull():
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = QPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = SkeletonSentinel()
    pet.show()
    sys.exit(app.exec())