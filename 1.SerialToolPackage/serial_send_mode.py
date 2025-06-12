import os
import serial
import serial.tools.list_ports
import json
import time
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
                             QCheckBox, QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog, QSplitter, QDialog, QFormLayout, QDialogButtonBox, QSpinBox,
                             QInputDialog, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QCloseEvent
from PyQt5.QtWidgets import QApplication, QAction, QMenuBar


class ConfigManager:
    """配置管理类，用于保存和加载串口工具配置"""
    def __init__(self, config_file="serial_tool_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
        return {}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_serial_config(self):
        """获取串口配置"""
        return self.config.get("serial", {})
    
    def set_serial_config(self, config):
        """设置串口配置"""
        self.config["serial"] = config
        self.save_config()
    
    def get_ui_config(self):
        """获取UI配置"""
        return self.config.get("ui", {})
    
    def set_ui_config(self, config):
        """设置UI配置"""
        self.config["ui"] = config
        self.save_config()
    
    def get_custom_commands(self):
        """获取自定义指令"""
        return self.config.get("custom_commands", [])
    
    def set_custom_commands(self, commands):
        """设置自定义指令"""
        self.config["custom_commands"] = commands
        self.save_config()


class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        self.buffer = ""  # 数据缓冲区

    def run(self):
        self.running = True
        while self.running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        try:
                            data_str = data.decode('utf-8')
                        except UnicodeDecodeError:
                            data_str = data.decode('gbk', errors='replace')

                        # 将新数据添加到缓冲区
                        self.buffer += data_str

                        # 处理完整的行
                        self.process_buffer()
                time.sleep(0.002)  # 避免CPU占用过高
            except Exception as e:
                self.data_received.emit(f"串口错误{e}\n")
                self.running = False

    def process_buffer(self):
        """处理缓冲区中的数据，只发送完整的行"""
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)

            # 只发送非空行
            if line.strip():
                self.data_received.emit(line.strip() + '\n')

    def stop(self):
        self.running = False
        self.wait()


class RefreshComboBox(QComboBox):
    def showPopup(self):
        if hasattr(self, 'refresh_func'):
            self.refresh_func()
        super().showPopup()


class CommandRow(QWidget):
    """统一的指令行组件，确保新增和加载的指令布局完全一致"""
    def __init__(self, note, text, is_hex, parent=None):
        super().__init__(parent)
        self.note = note
        self.text = text
        self.is_hex = is_hex
        self.init_ui()
    
    def init_ui(self):
        # 主布局：三列（备注、指令、操作）
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # 备注标签
        note_label = QLabel(self.note)
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #666666;")
        note_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        main_layout.addWidget(note_label, 1)  # 权重为1
        
        # 指令标签
        text_label = QLabel(self.text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        main_layout.addWidget(text_label, 1)  # 权重为1
        
        # 操作区布局
        op_layout = QHBoxLayout()
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(5)
        
        # HEX/TXT切换按钮
        toggle_btn = QPushButton("HEX" if self.is_hex else "TXT")
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(self.is_hex)
        toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        toggle_btn.setFixedSize(50, 30)  # 固定尺寸
        toggle_btn.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        toggle_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #46b1fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
            QPushButton:checked {
                background-color: #199bf5;
            }
        """)
        op_layout.addWidget(toggle_btn)
        
        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        send_btn.setFixedSize(60, 30)
        send_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #46b1fa;
                color: white;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        op_layout.addWidget(send_btn)
        
        # 编辑按钮
        edit_btn = QPushButton("✎")
        edit_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        edit_btn.setFixedSize(30, 30)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        op_layout.addWidget(edit_btn)
        
        # 删除按钮
        rm_btn = QPushButton("❌")
        rm_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        rm_btn.setFixedSize(30, 30)
        rm_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        op_layout.addWidget(rm_btn)
        
        # 将操作区添加到主布局
        main_layout.addLayout(op_layout, 1)  # 权重为1
        
        # 保存对按钮的引用，以便后续连接信号
        self.note_label = note_label
        self.text_label = text_label
        self.toggle_btn = toggle_btn
        self.send_btn = send_btn
        self.edit_btn = edit_btn
        self.rm_btn = rm_btn


class SerialSendMode(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("发送模式 - 串口工具")
        self.serial_port = None
        self.reader_thread = None
        self.custom_baudrate = 1500000
        self.data_bits = 8
        self.stop_bits = 1
        self.parity = 'None'
        self.flow_control = 'None'
        self.config_manager = ConfigManager()
        self.init_ui()
        self.load_config()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # 左侧：主区块
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 接收区
        self.receive_text = QTextEdit()
        self.receive_text.setReadOnly(True)
        self.receive_text.setFont(QFont("Consolas", 9))
        left_layout.addWidget(QLabel("接收区："))
        left_layout.addWidget(self.receive_text, 3)

        # 串口设置 - 调整为两列布局
        config_layout = QHBoxLayout()

        # 第一列：串口基本设置和按钮
        first_column = QVBoxLayout()
        first_column.addWidget(QLabel("串口："))
        self.port_combo = RefreshComboBox()
        self.port_combo.refresh_func = self.refresh_ports
        self.refresh_ports()
        first_column.addWidget(self.port_combo)
        
        first_column.addWidget(QLabel("波特率："))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '115200', '38400', '1500000'])
        self.baudrate_combo.setCurrentText('1500000')
        self.baudrate_combo.currentTextChanged.connect(self.on_baudrate_changed)
        first_column.addWidget(self.baudrate_combo)
        
        # 蓝色按钮样式
        button_style = """
            QPushButton {
                font-weight: bold;
                background-color: #46b1fa;
                color: white;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """
        
        self.open_button = QPushButton("打开串口")
        self.open_button.clicked.connect(self.toggle_port)
        self.open_button.setMinimumWidth(120)
        self.open_button.setMinimumHeight(40)
        self.open_button.setStyleSheet(button_style)
        first_column.addWidget(self.open_button)
        
        self.more_button = QPushButton("更多设置")
        self.more_button.clicked.connect(self.show_more_settings)
        self.more_button.setMinimumWidth(120)
        self.more_button.setMinimumHeight(40)
        self.more_button.setStyleSheet(button_style)
        first_column.addWidget(self.more_button)

        # 第二列：勾选选择框
        second_column = QVBoxLayout()
        self.hex_checkbox = QCheckBox("HEX发送")
        second_column.addWidget(self.hex_checkbox)
        
        self.hex_display_checkbox = QCheckBox("HEX显示")
        self.hex_display_checkbox.setChecked(False)
        second_column.addWidget(self.hex_display_checkbox)
        
        self.newline_checkbox = QCheckBox("自动换行")
        second_column.addWidget(self.newline_checkbox)
        
        self.timestamp_checkbox = QCheckBox("时间戳")
        second_column.addWidget(self.timestamp_checkbox)
      

        # 设置两列布局容器
        settings_container = QWidget()
        settings_layout = QHBoxLayout(settings_container)
        settings_layout.addLayout(first_column)
        settings_layout.addLayout(second_column)
        settings_layout.setSpacing(20)  # 设置两列间距
        
        # 发送区
        send_layout = QVBoxLayout()
        self.send_text = QTextEdit()
        self.send_text.setFont(QFont("Consolas", 10))
        self.send_text.setMinimumHeight(80)
        self.send_text.setMaximumHeight(120)
        send_layout.addWidget(QLabel("发送区："))
        send_layout.addWidget(self.send_text)

        # 发送按钮保持红色
        self.send_button = QPushButton("发送")
        self.send_button.setMinimumWidth(120)
        self.send_button.setMinimumHeight(50)
        self.send_button.clicked.connect(self.send_text_data)
        self.send_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #fa6b6b;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #fa5858;
            }
        """)
        send_layout.addWidget(self.send_button)

        # 将设置和发送区域添加到主布局
        config_layout.addWidget(settings_container, 1)
        config_layout.addLayout(send_layout, 1)
        config_layout.setStretchFactor(settings_container, 1)
        config_layout.setStretchFactor(send_layout, 1)

        left_layout.addLayout(config_layout)
        left_panel.setLayout(left_layout)

        # 右侧：自定义指令
        right_panel = QWidget()
        right_panel.setMinimumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("自定义指令："))

        # 添加列标题
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.addWidget(QLabel("备注"), 1)
        header_layout.addWidget(QLabel("指令"), 1)
        header_layout.addWidget(QLabel("操作"), 1)
        right_layout.addWidget(header_widget)

        self.cmd_list = QListWidget()
        self.cmd_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cmd_list.customContextMenuRequested.connect(self.show_context_menu)
        right_layout.addWidget(self.cmd_list, 3)

        cmd_input_layout = QHBoxLayout()
        self.cmd_note_input = QLineEdit()
        self.cmd_note_input.setMinimumWidth(120)
        self.cmd_note_input.setMinimumHeight(45)
        self.cmd_note_input.setMaximumHeight(45)
        self.cmd_note_input.setPlaceholderText("备注")
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setMinimumWidth(120)
        self.cmd_input.setMinimumHeight(45)
        self.cmd_input.setMaximumHeight(45)
        
        self.cmd_hex_checkbox = QCheckBox("HEX")
        self.cmd_hex_checkbox.setMinimumHeight(45)
        self.cmd_hex_checkbox.setMaximumHeight(45)
        
        self.add_cmd_button = QPushButton("添加")
        self.add_cmd_button.setMinimumWidth(80)
        self.add_cmd_button.setMinimumHeight(45)
        self.add_cmd_button.setMaximumHeight(45)
        self.add_cmd_button.clicked.connect(self.add_command)
        self.add_cmd_button.setStyleSheet(button_style)  # 使用相同的蓝色样式

        cmd_input_layout.addWidget(self.cmd_note_input, 1)
        cmd_input_layout.addWidget(self.cmd_input, 1)
        cmd_input_layout.addWidget(self.cmd_hex_checkbox, 0)
        cmd_input_layout.addWidget(self.add_cmd_button, 0)
        right_layout.addLayout(cmd_input_layout)

        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([800, 400])

    def on_baudrate_changed(self, value):
        try:
            self.custom_baudrate = int(value)
            if self.serial_port and self.serial_port.is_open:
                self.toggle_port()
                self.toggle_port()
        except ValueError:
            pass

    def show_more_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("更多串口设置")
        layout = QFormLayout(dialog)
        
        baud_spin = QSpinBox()
        baud_spin.setRange(1, 2000000)
        baud_spin.setValue(self.custom_baudrate)
        layout.addRow("自定义波特率:", baud_spin)
        
        databits = QComboBox()
        databits.addItems(['5', '6', '7', '8'])
        databits.setCurrentText(str(self.data_bits))
        layout.addRow("数据位:", databits)
        
        stopbits = QComboBox()
        stopbits.addItems(['1', '1.5', '2'])
        stopbits.setCurrentText(str(self.stop_bits))
        layout.addRow("停止位:", stopbits)
        
        parity = QComboBox()
        parity.addItems(['None', 'Even', 'Odd', 'Mark', 'Space'])
        parity.setCurrentText(self.parity)
        layout.addRow("校验:", parity)
        
        flow = QComboBox()
        flow.addItems(['None', 'RTS/CTS', 'XON/XOFF'])
        flow.setCurrentText(self.flow_control)
        layout.addRow("流控:", flow)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        
        if dialog.exec_():
            self.custom_baudrate = baud_spin.value()
            self.data_bits = int(databits.currentText())
            self.stop_bits = float(stopbits.currentText())
            self.parity = parity.currentText()
            self.flow_control = flow.currentText()
            self.baudrate_combo.setCurrentText(str(self.custom_baudrate))
            
            if self.serial_port and self.serial_port.is_open:
                self.toggle_port()
                self.toggle_port()

    def refresh_ports(self):
        self.port_combo.clear()
        for port in serial.tools.list_ports.comports():
            # 格式化为 "设备路径 - 描述（截断）"
            desc = port.description[:20] if port.description else "未知设备"
            self.port_combo.addItem(f"{port.device} - {desc}")

    def toggle_port(self):
        if self.serial_port and self.serial_port.is_open:
            if self.reader_thread:
                self.reader_thread.stop()
                self.reader_thread = None
            self.serial_port.close()
            self.serial_port = None
            self.open_button.setText("打开串口")
            self.open_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    background-color: #46b1fa;
                    color: white;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #199bf5;
                }
            """)
        else:
            try:
                port = self.port_combo.currentText().split('-')[0].strip()
                baud = self.custom_baudrate
                bytesize = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}[self.data_bits]
                stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}[self.stop_bits]
                parity_map = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN, 'Odd': serial.PARITY_ODD, 'Mark': serial.PARITY_MARK, 'Space': serial.PARITY_SPACE}
                parity_val = parity_map.get(self.parity, serial.PARITY_NONE)
                
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=bytesize,
                    stopbits=stopbits,
                    parity=parity_val,
                    timeout=0.1,
                    rtscts=(self.flow_control == 'RTS/CTS'),
                    xonxoff=(self.flow_control == 'XON/XOFF')
                )
                
                self.reader_thread = SerialReaderThread(self.serial_port)
                self.reader_thread.data_received.connect(self.display_received)
                self.reader_thread.start()
                
                self.open_button.setText("关闭串口")
                self.open_button.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;
                        background-color: #ff0000;
                        color: white;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #cc0000;
                    }
                """)
            except Exception as e:
                QMessageBox.critical(self, "串口错误", str(e))

    def display_received(self, data):
        """显示接收到的数据，支持HEX格式"""
        try:
            text_data = data.encode().decode('utf-8')
        except UnicodeDecodeError:
            text_data = data
        
        if self.hex_display_checkbox.isChecked():
            try:
                hex_data = ' '.join([f'{b:02X}' for b in data.encode('utf-8')])
                display_data = hex_data
            except:
                display_data = data
        else:
            display_data = text_data
        
        if self.timestamp_checkbox.isChecked():
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self.receive_text.append(f"<span style='color:#888888;'>[RX {ts}]</span> {display_data.strip()}")
        else:
            self.receive_text.append(f"[RX] {display_data.strip()}")

    def send_text_data(self):
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "未打开串口", "请先打开串口")
            return
            
        text = self.send_text.toPlainText()
        if self.newline_checkbox.isChecked():
            text += '\r\n'
            
        if self.hex_checkbox.isChecked():
            try:
                data = bytes.fromhex(text.strip())
            except Exception as e:
                QMessageBox.critical(self, "HEX格式错误", str(e))
                return
        else:
            data = text.encode('utf-8')
            
        self.serial_port.write(data)
        
        if self.timestamp_checkbox.isChecked():
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self.receive_text.append(f"<span style='color:#888888;'>[TX {ts}]</span> {text.strip()}")
        else:
            self.receive_text.append(f"[TX] {text.strip()}")

    def add_command(self):
        text = self.cmd_input.text().strip()
        note = self.cmd_note_input.text().strip()
        if not text:
            return
            
        is_hex = self.cmd_hex_checkbox.isChecked()
        
        # 使用CommandRow组件创建指令行
        cmd_row = CommandRow(note, text, is_hex)
        item = QListWidgetItem()
        item.setSizeHint(cmd_row.sizeHint())
        self.cmd_list.addItem(item)
        self.cmd_list.setItemWidget(item, cmd_row)
        
        # 连接按钮信号
        cmd_row.send_btn.clicked.connect(lambda: self.send_command(text, is_hex))
        cmd_row.edit_btn.clicked.connect(lambda: self.edit_command(item, note, text, is_hex))
        cmd_row.rm_btn.clicked.connect(lambda: self.cmd_list.takeItem(self.cmd_list.row(item)))
        cmd_row.toggle_btn.clicked.connect(lambda _, b=cmd_row.toggle_btn: self.toggle_cmd_format(b))
        
        self.cmd_input.clear()
        self.cmd_note_input.clear()

    def toggle_cmd_format(self, button):
        if button.isChecked():
            button.setText("HEX")
        else:
            button.setText("TXT")
        # 确保文本变化后尺寸不变
        button.setFixedSize(button.size())

    def edit_command(self, item, current_note, current_text, is_hex):
        """编辑指令"""
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑指令")
        layout = QFormLayout(dialog)
        
        note_input = QLineEdit(current_note)
        layout.addRow("备注:", note_input)
        
        text_input = QLineEdit(current_text)
        layout.addRow("指令:", text_input)
        
        hex_checkbox = QCheckBox("HEX格式")
        hex_checkbox.setChecked(is_hex)
        layout.addRow("", hex_checkbox)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(btns)
        
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        
        if dialog.exec_():
            new_note = note_input.text().strip()
            new_text = text_input.text().strip()
            new_is_hex = hex_checkbox.isChecked()
            
            if not new_text:
                QMessageBox.warning(self, "警告", "指令内容不能为空!")
                return
                
            # 直接更新现有CommandRow的内容
            widget = self.cmd_list.itemWidget(item)
            widget.note_label.setText(new_note)
            widget.text_label.setText(new_text)
            widget.toggle_btn.setText("HEX" if new_is_hex else "TXT")
            widget.toggle_btn.setChecked(new_is_hex)
            
            # 更新发送按钮的连接
            widget.send_btn.disconnect()
            widget.send_btn.clicked.connect(lambda: self.send_command(new_text, new_is_hex))

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.cmd_list.itemAt(position)
        if item:
            menu = QMenu()
            edit_action = QAction("编辑", self)
            delete_action = QAction("删除", self)
            
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            
            action = menu.exec_(self.cmd_list.mapToGlobal(position))
            
            if action == edit_action:
                widget = self.cmd_list.itemWidget(item)
                note = widget.note_label.text()
                text = widget.text_label.text()
                is_hex = widget.toggle_btn.text() == "HEX"
                self.edit_command(item, note, text, is_hex)
                
            elif action == delete_action:
                self.cmd_list.takeItem(self.cmd_list.row(item))

    def send_command(self, text, is_hex):
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "未打开串口", "请先打开串口")
            return
            
        if self.newline_checkbox.isChecked():
            text += '\r\n'
            
        try:
            data = bytes.fromhex(text) if is_hex else text.encode('utf-8')
            self.serial_port.write(data)
            
            if self.timestamp_checkbox.isChecked():
                ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                self.receive_text.append(f"<span style='color:#888888;'>[TX {ts}]</span> {text.strip()}")
            else:
                self.receive_text.append(f"[TX] {text.strip()}")
        except Exception as e:
            QMessageBox.critical(self, "发送失败", str(e))

    def save_config(self):
        """保存当前配置"""
        try:
            # 保存串口配置
            serial_config = {
                "port": self.port_combo.currentText(),
                "baudrate": self.custom_baudrate,
                "data_bits": self.data_bits,
                "stop_bits": self.stop_bits,
                "parity": self.parity,
                "flow_control": self.flow_control
            }
            self.config_manager.set_serial_config(serial_config)
            
            # 保存UI配置
            ui_config = {
                "hex_send": self.hex_checkbox.isChecked(),
                "newline": self.newline_checkbox.isChecked(),
                "timestamp": self.timestamp_checkbox.isChecked(),
                "hex_display": self.hex_display_checkbox.isChecked(),
                # 保存分割器配置
                "splitter_sizes": self.splitter.sizes()  # 获取分割器中各部分的大小
            }
            self.config_manager.set_ui_config(ui_config)
            
            # 保存自定义指令
            commands = []
            for i in range(self.cmd_list.count()):
                item = self.cmd_list.item(i)
                widget = self.cmd_list.itemWidget(item)
                
                # 获取备注和指令
                note = widget.note_label.text()
                text = widget.text_label.text()
                
                # 获取HEX/TXT状态
                is_hex = widget.toggle_btn.text() == "HEX"
                
                commands.append({
                    "text": text,
                    "note": note,
                    "is_hex": is_hex
                })
                
            self.config_manager.set_custom_commands(commands)
            print("配置已保存")
            self.close_serial();
            
        except Exception as e:
            print(f"保存配置时出错: {e}")

    def load_config(self):
        """加载配置"""
        try:
            # 加载串口配置
            serial_config = self.config_manager.get_serial_config()
            if serial_config:
                self.port_combo.setCurrentText(serial_config.get("port", ""))
                self.custom_baudrate = serial_config.get("baudrate", 1500000)
                self.baudrate_combo.setCurrentText(str(self.custom_baudrate))
                self.data_bits = serial_config.get("data_bits", 8)
                self.stop_bits = serial_config.get("stop_bits", 1)
                self.parity = serial_config.get("parity", "None")
                self.flow_control = serial_config.get("flow_control", "None")
            
            # 加载UI配置
            ui_config = self.config_manager.get_ui_config()
            if ui_config:
                self.hex_checkbox.setChecked(ui_config.get("hex_send", False))
                self.newline_checkbox.setChecked(ui_config.get("newline", False))
                self.timestamp_checkbox.setChecked(ui_config.get("timestamp", False))
                self.hex_display_checkbox.setChecked(ui_config.get("hex_display", False))
                # 恢复分割器配置
                splitter_sizes = ui_config.get("splitter_sizes")
                if splitter_sizes:
                    self.splitter.setSizes(splitter_sizes)
            
            # 加载自定义指令
            commands = self.config_manager.get_custom_commands()
            for cmd in commands:
                text = cmd.get("text", "")
                note = cmd.get("note", "")
                is_hex = cmd.get("is_hex", False)
                
                if not text:
                    continue
                    
                # 使用CommandRow组件创建指令行
                cmd_row = CommandRow(note, text, is_hex)
                item = QListWidgetItem()
                item.setSizeHint(cmd_row.sizeHint())
                self.cmd_list.addItem(item)
                self.cmd_list.setItemWidget(item, cmd_row)
                
                # 连接按钮信号
                cmd_row.send_btn.clicked.connect(lambda _, t=text, h=is_hex: self.send_command(t, h))
                cmd_row.edit_btn.clicked.connect(lambda _, i=item, n=note, t=text, h=is_hex: self.edit_command(i, n, t, h))
                cmd_row.rm_btn.clicked.connect(lambda _, i=item: self.cmd_list.takeItem(self.cmd_list.row(i)))
                cmd_row.toggle_btn.clicked.connect(lambda _, b=cmd_row.toggle_btn: self.toggle_cmd_format(b))
            
            print("配置已加载")
            
        except Exception as e:
            print(f"加载配置时出错: {e}")

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        self.save_config()
        if self.reader_thread:
            self.reader_thread.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

    def close_serial(self):
        """关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()


class SerialTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("串口工具")
        self.setMinimumSize(1000, 700)
        self.init_ui()
        
    def init_ui(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        save_action = QAction("保存配置", self)
        save_action.triggered.connect(self.save_config)
        file_menu.addAction(save_action)
        
        load_action = QAction("加载配置", self)
        load_action.triggered.connect(self.load_config)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 模式菜单
        mode_menu = menubar.addMenu("模式")
        
        send_mode_action = QAction("发送模式", self)
        send_mode_action.triggered.connect(self.show_send_mode)
        mode_menu.addAction(send_mode_action)
        
        # 初始化发送模式窗口
        self.send_mode = SerialSendMode()
        
        # 设置中心部件
        self.setCentralWidget(self.send_mode.centralWidget())
        self.statusBar().showMessage("就绪")
        
    def show_send_mode(self):
        """显示发送模式"""
        self.setCentralWidget(self.send_mode.centralWidget())
        self.setWindowTitle("发送模式 - 串口工具")
        
    def save_config(self):
        """保存配置"""
        self.send_mode.save_config()
        self.statusBar().showMessage("配置已保存")
        
    def load_config(self):
        """加载配置"""
        self.send_mode.load_config()
        self.statusBar().showMessage("配置已加载")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SerialTool()
    window.show()
    sys.exit(app.exec_())