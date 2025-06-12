from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QPushButton
from PyQt5.QtGui import QCloseEvent, QIcon
from serial_tool import DualSerialMonitor
from serial_send_mode import SerialSendMode
import sys
import json
import os

CONFIG_FILE = "mode_config.json"

def load_last_mode():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("last_mode", "recv")
        except:
            return "recv"
    return "recv"

def save_last_mode(mode):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"last_mode": mode}, f)
    except:
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SerialToolFree")
        self.setGeometry(100, 100, 1000, 700)

        self.tool_bar = QToolBar("Main Toolbar")
        self.addToolBar(self.tool_bar)

        self.switch_btn = QPushButton()
        self.switch_btn.clicked.connect(self.toggle_mode)
        self.tool_bar.addWidget(self.switch_btn)

        self.current_mode = None
        self.current_type = None
        if load_last_mode() == "send":
            self.load_send_mode()
        else:
            self.load_recv_mode()

    def load_send_mode(self):
        save_last_mode("send")
        self.current_type = "send"
        self.switch_mode(SerialSendMode())
        self.switch_btn.setText("切换到接收模式")
        self.switch_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;  
                background-color: #fa6b6b; /* 红色 */
                color: white;
            }
            QPushButton:hover {
                background-color: #fa5858;
            }
        """)

    def load_recv_mode(self):
        save_last_mode("recv")
        self.current_type = "recv"
        self.switch_mode(DualSerialMonitor())
        self.switch_btn.setText("切换到发送模式")
        self.switch_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;  
                background-color: #46b1fa; 
                color: white;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)

    def toggle_mode(self):
        print("toggle_mode")
        if self.current_type == "send":
            self.load_recv_mode()
        else:
            self.load_send_mode()

    def switch_mode(self, widget):
        if self.current_mode:
            if hasattr(self.current_mode, 'save_config'):
                print(f"[切换模式] 正在保存：{type(self.current_mode).__name__}")
                self.current_mode.save_config()
            self.current_mode.setParent(None)
            self.current_mode.deleteLater()
        self.current_mode = widget
        self.setCentralWidget(widget)


    def closeEvent(self, event):
        if self.current_mode and hasattr(self.current_mode, 'closeEvent'):
            temp_event = QCloseEvent()
            self.current_mode.closeEvent(temp_event)
            if not temp_event.isAccepted():
                event.ignore()
                return
        event.accept()

def get_icon_path():
    """获取图标路径（兼容开发环境和打包后环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后路径（PyInstaller的_MEIPASS目录）
        return os.path.join(sys._MEIPASS, "favicon.ico")
    else:
        # 开发环境路径（与脚本同目录）
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    icon_path = get_icon_path()
    app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())