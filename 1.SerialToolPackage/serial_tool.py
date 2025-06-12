import sys
import time
import json
import os
import serial #pip install pyserial
import serial.tools.list_ports
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QComboBox, QPushButton, 
                            QTextEdit, QLineEdit, QCheckBox, QMessageBox,
                            QInputDialog, QSplitter, QFileDialog, QAction, QDialog, QFormLayout, QDialogButtonBox, QSpinBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QTextCursor, QFont, QIcon

class SerialThread(QThread):
    """串口数据接收线程"""
    data_received = pyqtSignal(str, int)
    
    def __init__(self, serial_port, port_index):
        super().__init__()
        self.serial_port = serial_port
        self.port_index = port_index
        self.running = False
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
                self.data_received.emit(f"串口错误: {str(e)}\n", self.port_index)
                self.running = False
    
    def process_buffer(self):
        """处理缓冲区中的数据，只发送完整的行"""
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            
            # 只发送非空行
            if line.strip():
                self.data_received.emit(line.strip() + '\n', self.port_index)
    
    def stop(self):
        self.running = False
        self.wait()

class SmartTextEdit(QTextEdit):
    """智能文本编辑框，优化滚动行为"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auto_scroll = True
        self._force_next_scroll = False  # 新增
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        
    def on_scroll_changed(self, value):
        if self._force_next_scroll:
            self._force_next_scroll = False
            self.auto_scroll = True
            return
        scrollbar = self.verticalScrollBar()
        self.auto_scroll = (value == scrollbar.maximum())
    
    def append_smart(self, text):
        """智能添加文本，控制滚动行为"""
        scrollbar = self.verticalScrollBar()
        was_at_bottom = (scrollbar.value() == scrollbar.maximum())
        
        self.append(text)
        
        if was_at_bottom or scrollbar.maximum() == 0:
            self.moveCursor(QTextCursor.End)
            self.auto_scroll = True

    def force_auto_scroll(self):
        """强制恢复自动滚动并滚动到底部"""
        self._force_next_scroll = True
        self.moveCursor(QTextCursor.End)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.auto_scroll = True

# 在SerialWidget类定义之前添加以下代码
class RefreshComboBox(QComboBox):
    """自动刷新串口列表的下拉框（优化版）"""
    def showPopup(self):
        # 先刷新串口列表
        if hasattr(self.parent(), 'refresh_ports'):
            self.parent().refresh_ports(force=True)  # 强制刷新
        # 再显示下拉框
        super().showPopup()

    # 修改SerialWidget类中的init_ui方法中的port_combo创建部分
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 串口设置区域
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(2)
        
        settings_layout.addWidget(QLabel(f'串口{self.port_index}:'), 1)
        
        # 使用自定义的RefreshComboBox代替原来的QComboBox
        self.port_combo = RefreshComboBox()
        self.refresh_ports()
        settings_layout.addWidget(self.port_combo, 3)
    

class SerialWidget(QWidget):
    """单个串口显示和控制部件"""
    def __init__(self, port_index, config_manager, parent=None):
        super().__init__(parent)
        self.port_index = port_index
        self.config_manager = config_manager
        self.serial_port = None
        self.serial_thread = None
        self.custom_baudrate = 1500000  # 默认1.5M波特率
        self.auto_save_enabled = False
        self.auto_save_file_index = 1
        self.data_bits = 8
        self.stop_bits = 1
        self.parity = 'None'
        self.flow_control = 'None'
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 串口设置区域 - 修改此处
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)  # 将左右边距设为0
        settings_layout.setSpacing(0)  # 将控件间距设为0，使元素紧贴
        
        settings_layout.addWidget(QLabel(f'串口{self.port_index}:'), 1)
        
        # 使用自定义的RefreshComboBox
        self.port_combo = RefreshComboBox()
        self.refresh_ports()  # 初始化时加载一次
        settings_layout.addWidget(self.port_combo, 3)
        
        self.open_close_btn = QPushButton('打开')
        self.open_close_btn.setMinimumWidth(120)
        self.open_close_btn.setMaximumWidth(120)
        self.open_close_btn.clicked.connect(self.toggle_serial)
        settings_layout.addWidget(self.open_close_btn, 1)
        # 设置关闭状态的样式（蓝色背景，白色文字）
        self.open_close_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;  /* 加粗 */
                background-color: #46b1fa; /* 初始为蓝色（关闭状态） */
                color: white;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        
        # 修改：添加拉伸因子，让波特率标签和下拉框紧贴左侧
        settings_layout.addStretch(1)  # 添加一个小拉伸，分隔左侧控件组
        
        settings_layout.addWidget(QLabel('波特率:'), 1)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['9600', '115200', '38400', '57600', 
                                      '4800', '2400', '1200', '230400', '1500000'])
        self.baudrate_combo.setCurrentText('1500000')
        settings_layout.addWidget(self.baudrate_combo, 2)
        
        # 添加信号槽连接，当波特率选择变化时触发更新
        self.baudrate_combo.currentTextChanged.connect(self.on_baudrate_changed)
        
        self.more_settings_btn = QPushButton('⚙️ 更多设置')
        self.more_settings_btn.setMinimumWidth(150)
        self.more_settings_btn.setMaximumWidth(150)
        self.more_settings_btn.clicked.connect(self.show_more_settings_dialog)
        settings_layout.addWidget(self.more_settings_btn, 1)
        self.more_settings_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #46b1fa;
                color: white;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        
        layout.addLayout(settings_layout)
        
        # 过滤设置区域（新增时间戳复选框）
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(2)
        
        filter_layout.addWidget(QLabel('过滤关键字:'), 1)
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText('关键字,以"|"隔开')
        filter_layout.addWidget(self.filter_edit, 4)
        
        self.filter_case_checkbox = QCheckBox('区分大小写')
        self.filter_case_checkbox.setChecked(True)
        filter_layout.addWidget(self.filter_case_checkbox, 1)
        
        # 是否显示HEX
        self.show_hex_checkbox = QCheckBox('HEX显示')
        self.show_hex_checkbox.setChecked(False)  # 默认不显示HEX
        filter_layout.addWidget(self.show_hex_checkbox, 1)
        
        # 新增：是否显示时间戳
        self.show_timestamp_checkbox = QCheckBox('时间戳显示')
        self.show_timestamp_checkbox.setChecked(True)  # 默认显示时间戳
        filter_layout.addWidget(self.show_timestamp_checkbox, 1)
        
        layout.addLayout(filter_layout)
        
        # 操作控制区域 - 按要求分组按钮
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(2)
        
        # 左侧：保存原始和保存过滤按钮
        left_buttons_layout = QHBoxLayout()
        left_buttons_layout.setContentsMargins(0, 0, 0, 0)
        left_buttons_layout.setSpacing(2)
        
        # 保存原始数据按钮
        self.save_original_btn = QPushButton('💾 保存原始')
        self.save_original_btn.setMinimumWidth(100)
        self.save_original_btn.setMinimumHeight(30)
        self.save_original_btn.clicked.connect(self.save_original_data)
        self.save_original_btn.setStyleSheet("""
            QPushButton {
                background-color: #46b1fa; /* 蓝色 */
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        
        # 保存过滤数据按钮
        self.save_filtered_btn = QPushButton('🔍 保存过滤')
        self.save_filtered_btn.setMinimumWidth(100)
        self.save_filtered_btn.setMinimumHeight(30)
        self.save_filtered_btn.clicked.connect(self.save_filtered_data)
        self.save_filtered_btn.setStyleSheet("""
            QPushButton {
                background-color: #46b1fa; /* 蓝色 */
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        
        left_buttons_layout.addWidget(self.save_original_btn)
        left_buttons_layout.addWidget(self.save_filtered_btn)
        
        # 右侧：恢复自动滚动和清空数据按钮（顺序对调）
        right_buttons_layout = QHBoxLayout()
        right_buttons_layout.setContentsMargins(0, 0, 0, 0)
        right_buttons_layout.setSpacing(2)

        # 恢复自动滚动按钮
        self.restore_scroll_btn = QPushButton('↩️ 恢复自动滚动')
        self.restore_scroll_btn.setMinimumWidth(140)
        self.restore_scroll_btn.setMinimumHeight(30)
        self.restore_scroll_btn.clicked.connect(self.restore_auto_scroll)
        self.restore_scroll_btn.setStyleSheet("""
            QPushButton {
                background-color: #46b1fa;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #199bf5;
            }
        """)
        right_buttons_layout.addWidget(self.restore_scroll_btn)

        # 清空数据按钮
        self.clear_btn = QPushButton('🗑️ 清空数据')
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.setMinimumHeight(30)
        self.clear_btn.clicked.connect(self.clear_display)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #fa6b6b; /* 红色 */
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #fa5858;
            }
        """)
        right_buttons_layout.addWidget(self.clear_btn)

        # 将左右按钮布局添加到主控制布局
        control_layout.addLayout(left_buttons_layout, 1)  # 左侧布局占1份
        control_layout.addStretch(1)                     # 中间弹簧占1份
        control_layout.addLayout(right_buttons_layout, 1) # 右侧布局占1份
        
        layout.addLayout(control_layout)
        
        # 显示区域 - 使用QSplitter分割
        display_splitter = QSplitter(Qt.Vertical)
        
        self.receive_text = SmartTextEdit(self)  # 传递父窗口
        self.receive_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.receive_text.setFont(QFont("Consolas", 9))
        display_splitter.addWidget(self.receive_text)
        
        self.filter_preview_text = SmartTextEdit(self)
        self.filter_preview_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.filter_preview_text.setPlaceholderText("过滤结果...")
        self.filter_preview_text.setFont(QFont("Consolas", 9))
        display_splitter.addWidget(self.filter_preview_text)
        
        # 设置分割比例
        display_splitter.setSizes([200, 100])
        
        layout.addWidget(display_splitter)
        
        # 状态栏
        self.status_label = QLabel('就绪')
        layout.addWidget(self.status_label)
        
    def set_auto_save_enabled(self, enabled):
        self.auto_save_enabled = enabled
        
    def check_auto_save(self):
        text = self.receive_text.toPlainText()
        limit_mb = self.config_manager.get_auto_save_limit_mb()
        if len(text.encode('utf-8')) > limit_mb * 1024: #* 1024:
            # 自动保存到logs目录 兼容开发环境和打包后环境）
            if getattr(sys, 'frozen', False):
                # 打包后：使用exe所在目录
                base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                # 开发环境：使用脚本所在目录
                base_dir = os.path.dirname(os.path.abspath(__file__))

            logs_dir = os.path.join(base_dir, 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            filename = f"串口{self.port_index}_autosave_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.auto_save_file_index}.txt"
            file_path = os.path.join(logs_dir, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.auto_save_file_index += 1
                self.receive_text.clear()
                self.status_label.setText(f"自动保存到 {file_path}")
            except Exception as e:
                self.status_label.setText(f"自动保存失败: {e}")
        
    def on_baudrate_changed(self, value):
        """波特率选择变化时触发"""
        # 应用波特率更改
        self.apply_baudrate_change(value)

    def apply_baudrate_change(self, value):
        """应用波特率更改"""
        try:
            self.custom_baudrate = int(value)
            
            # 保存配置
            self.config_manager.set_port_config(self.port_index, self.get_config())
            
            # 显示日志
            #log_msg = f"波特率已更改为: {value}"
            #self.status_label.setText(log_msg)
            #self.receive_text.append_smart(f"[系统] {log_msg}")
            
            # 如果串口当前是打开的，应用新的波特率
            if self.serial_port and self.serial_port.is_open:
                self.close_serial()
                self.open_serial()
        except ValueError:
            self.status_label.setText(f'无效的波特率: {value}')
            
    def refresh_ports(self, force=False):
        """刷新可用串口列表（force=True时强制刷新）"""
        # 清空现有选项
        self.port_combo.clear()
        
        # 获取最新串口列表
        ports = serial.tools.list_ports.comports()
        if not ports:
            # 无串口时添加提示项
            self.port_combo.addItem("未检测到可用串口")
            return
        
        # 填充新串口
        for port in ports:
            # 格式化为 "设备路径 - 描述（截断）"
            desc = port.description[:20] if port.description else "未知设备"
            self.port_combo.addItem(f"{port.device} - {desc}")
        
        # 可选：如果force=True，尝试恢复之前选择的串口（如果有）
        if not force and self.port_combo.count() > 0:
            current_text = self.port_combo.currentText()
            if current_text in [self.port_combo.itemText(i) for i in range(self.port_combo.count())]:
                self.port_combo.setCurrentText(current_text)
    
    def toggle_serial(self):
        """打开或关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.close_serial()
            # 设置关闭状态的样式（蓝色）
            self.open_close_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;  
                    background-color: #46b1fa; 
                    color: white;
                }
                QPushButton:hover {
                    background-color: #199bf5;
                }
            """)
        else:
            # 先释放旧资源
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            if self.serial_thread and self.serial_thread.isRunning():
                self.serial_thread.stop()
                self.serial_thread = None
                
            # 在打开串口前，先更新波特率设置
            if self.baudrate_combo.currentText():
                self.custom_baudrate = int(self.baudrate_combo.currentText())
            
            # 打开串口（注意：open_serial内部会处理样式）
            self.open_serial()
    
    def show_more_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f'串口{self.port_index} 更多设置')
        layout = QFormLayout(dialog)
        # 波特率
        baudrate_spin = QSpinBox()
        baudrate_spin.setRange(1, 2000000)
        baudrate_spin.setValue(self.custom_baudrate)
        layout.addRow('自定义波特率:', baudrate_spin)
        # 数据位
        databits_combo = QComboBox()
        databits_combo.addItems(['5', '6', '7', '8'])
        databits_combo.setCurrentText(str(self.data_bits))
        layout.addRow('数据位:', databits_combo)
        # 停止位
        stopbits_combo = QComboBox()
        stopbits_combo.addItems(['1', '1.5', '2'])
        stopbits_combo.setCurrentText(str(self.stop_bits))
        layout.addRow('停止位:', stopbits_combo)
        # 校验
        parity_combo = QComboBox()
        parity_combo.addItems(['None', 'Even', 'Odd', 'Mark', 'Space'])
        parity_combo.setCurrentText(self.parity)
        layout.addRow('校验:', parity_combo)
        # 流控
        flow_combo = QComboBox()
        flow_combo.addItems(['None', 'RTS/CTS', 'XON/XOFF'])
        flow_combo.setCurrentText(self.flow_control)
        layout.addRow('流控:', flow_combo)
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_baudrate = baudrate_spin.value()
            self.data_bits = int(databits_combo.currentText())
            self.stop_bits = float(stopbits_combo.currentText())
            self.parity = parity_combo.currentText()
            self.flow_control = flow_combo.currentText()
            self.baudrate_combo.setCurrentText(str(self.custom_baudrate))
            self.config_manager.set_port_config(self.port_index, self.get_config())
            if self.serial_port and self.serial_port.is_open:
                self.close_serial()
                self.open_serial()

    def open_serial(self):
        """打开串口"""
        try:
            port_name = self.port_combo.currentText().split('-')[0].strip()
            if not port_name:
                self.status_label.setText('请选择有效串口')
                QMessageBox.warning(self, '警告', '请先选择一个有效串口')
                return
            baudrate = self.custom_baudrate if self.custom_baudrate is not None else int(self.baudrate_combo.currentText())
            data_bits = self.data_bits
            stop_bits = self.stop_bits
            parity = self.parity
            flow_control = self.flow_control
            # 转换为pyserial参数
            bytesize = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}[data_bits]
            stopbits = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}[stop_bits]
            parity_map = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN, 'Odd': serial.PARITY_ODD, 'Mark': serial.PARITY_MARK, 'Space': serial.PARITY_SPACE}
            parity_val = parity_map.get(parity, serial.PARITY_NONE)
            # 打开串口前先关闭可能存在的旧串口连接
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=bytesize,
                stopbits=stopbits,
                parity=parity_val,
                timeout=0.1,
                rtscts=(flow_control == 'RTS/CTS'),
                xonxoff=(flow_control == 'XON/XOFF')
            )
            
            if self.serial_port.is_open:
                self.status_label.setText(f'已打开: {port_name}, {baudrate}')
                self.open_close_btn.setText('关闭')
                # 设置打开状态的样式（红色）
                self.open_close_btn.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;  
                        background-color: #ff0000; 
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                    }
                """)
                
                # 启动串口接收线程
                if self.serial_thread and self.serial_thread.isRunning():
                    self.serial_thread.stop()
                self.serial_thread = SerialThread(self.serial_port, self.port_index)
                self.serial_thread.data_received.connect(self.handle_data)
                self.serial_thread.start()
            else:
                # 打开失败时回滚按钮状态
                self.status_label.setText('打开失败：串口未成功打开')
                self.open_close_btn.setText('打开')
                # 设置关闭状态的样式（蓝色）
                self.open_close_btn.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;  
                        background-color: #46b1fa; 
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #199bf5;
                    }
                """)
                QMessageBox.critical(self, '错误', '无法打开指定串口，请检查串口是否被占用')
                
        except serial.SerialException as se:
            # 串口异常时回滚按钮状态
            self.status_label.setText(f'串口错误: {str(se)}')
            self.open_close_btn.setText('打开')
            self.open_close_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;  
                    background-color: #46b1fa; 
                    color: white;
                }
                QPushButton:hover {
                    background-color: #199bf5;
                }
            """)
            QMessageBox.critical(self, '串口错误', f'打开串口失败: {str(se)}')
        except Exception as e:
            # 其他异常时回滚按钮状态
            self.status_label.setText(f'打开失败: {str(e)}')
            self.open_close_btn.setText('打开')
            self.open_close_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;  
                    background-color: #46b1fa; 
                    color: white;
                }
                QPushButton:hover {
                    background-color: #199bf5;
                }
            """)
            QMessageBox.critical(self, '错误', f'打开串口失败: {str(e)}')

    
    def close_serial(self):
        """关闭串口"""
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop()
            self.serial_thread = None
            
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None  # 增加这行，明确设置为None
            self.status_label.setText('已关闭')
            self.open_close_btn.setText('打开')
    
    def handle_data(self, data, port_index):
        """处理接收到的数据，修复>字符转义问题"""
        # 获取过滤设置
        filter_text = self.filter_edit.text().strip()
        keywords = [kw.strip() for kw in filter_text.split('|') if kw.strip()]
        case_sensitive = self.filter_case_checkbox.isChecked()
        show_hex = self.show_hex_checkbox.isChecked()
        show_timestamp = self.show_timestamp_checkbox.isChecked()  # 获取时间戳开关状态
        
        # 关键修复：移除对>的转义，仅保留必要的转义（如<）
        line = data.rstrip('\n')
        # 仅转义<（如果需要），删除对>的转义
        escaped_line = line.replace('<', '&lt;')  # 保留<的转义（可选）
        # 或者完全不转义（根据需求选择）
        # escaped_line = line
        
        # 处理时间戳（根据开关状态决定是否添加）
        timestamp = ""
        if show_timestamp:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 格式：20250605_204441_202
            timestamp_html = f'<span style="color:#888888;">[{timestamp}]</span>'
        else:
            timestamp_html = ""
        
        # 处理数据行（使用原始或仅转义<后的内容）
        processed_line = f"{timestamp_html}{escaped_line}"
        
        # 显示原始数据（添加日志确认）
        if show_hex:
            hex_data = ' '.join([f"{ord(c):02X}" for c in line])
            hex_line = f'<span style="color:#666666;">[HEX] {hex_data}</span>'
            self.receive_text.append_smart(f"{processed_line}  {hex_line}")
            print(f"[显示] 原始数据: {processed_line}")
        else:
            self.receive_text.append_smart(processed_line)
            print(f"[显示] 原始数据: {processed_line}")
        
        # 过滤数据逻辑（仅用户设置的关键字过滤）
        if not keywords:
            if show_hex:
                self.filter_preview_text.append_smart(f"{processed_line}  {hex_line}")
            else:
                self.filter_preview_text.append_smart(processed_line)
            # 自动保存逻辑
            if self.auto_save_enabled:
                self.check_auto_save()
            return
            
        line_to_check = processed_line if case_sensitive else processed_line.lower()
        
        if any(kw.lower() if not case_sensitive else kw in line_to_check for kw in keywords):
            if show_hex:
                self.filter_preview_text.append_smart(f"{processed_line}  {hex_line}")
            else:
                self.filter_preview_text.append_smart(processed_line)
            print(f"[显示] 过滤数据: {processed_line}")
        # 自动保存逻辑
        if self.auto_save_enabled:
            self.check_auto_save()
    
    def clear_display(self):
        """清空显示区域"""
        self.receive_text.clear()
        self.filter_preview_text.clear()
    
    def save_original_data(self):
        """保存原始数据到文件"""
        if not self.receive_text.toPlainText():
            QMessageBox.information(self, "提示", "没有数据可保存")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"保存串口 {self.port_index} 原始数据", 
            f"串口{self.port_index}_数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 保存纯文本，不包含HTML标签
                plain_text = self.receive_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                QMessageBox.information(self, "成功", f"数据已保存到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
    
    def save_filtered_data(self):
        """保存过滤数据到文件"""
        if not self.filter_preview_text.toPlainText():
            QMessageBox.information(self, "提示", "没有过滤数据可保存")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"保存串口 {self.port_index} 过滤数据", 
            f"串口{self.port_index}_过滤数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 保存纯文本，不包含HTML标签
                plain_text = self.filter_preview_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                QMessageBox.information(self, "成功", f"数据已保存到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
    
    def get_config(self):
        """获取当前配置（新增时间戳开关状态）"""
        cfg = {
            'port': self.port_combo.currentText(),
            'baudrate': self.baudrate_combo.currentText(),
            'custom_baudrate': self.custom_baudrate,
            'filter_text': self.filter_edit.text(),
            'filter_case': self.filter_case_checkbox.isChecked(),
            'show_hex': self.show_hex_checkbox.isChecked(),
            'show_timestamp': self.show_timestamp_checkbox.isChecked(),
            'data_bits': self.data_bits,
            'stop_bits': self.stop_bits,
            'parity': self.parity,
            'flow_control': self.flow_control,
        }
        return cfg
    
    def load_config(self):
        """加载配置（新增时间戳开关状态）"""
        config = self.config_manager.get_port_config(self.port_index)
        if config:
            try:
                # 设置串口配置
                port_text = config.get('port', '')
                if port_text:
                    index = self.port_combo.findText(port_text)
                    if index >= 0:
                        self.port_combo.setCurrentIndex(index)
                
                # 设置波特率
                baudrate = config.get('baudrate', '1500000')
                self.baudrate_combo.setCurrentText(baudrate)
                
                # 设置自定义波特率
                self.custom_baudrate = config.get('custom_baudrate', 1500000)
                self.data_bits = config.get('data_bits', 8)
                self.stop_bits = config.get('stop_bits', 1)
                self.parity = config.get('parity', 'None')
                self.flow_control = config.get('flow_control', 'None')
                
                # 设置过滤配置
                self.filter_edit.setText(config.get('filter_text', ''))
                self.filter_case_checkbox.setChecked(config.get('filter_case', True))
                self.show_hex_checkbox.setChecked(config.get('show_hex', False))
                self.show_timestamp_checkbox.setChecked(config.get('show_timestamp', True))  # 新增
            except Exception as e:
                print(f"加载串口{self.port_index}配置失败: {e}")

    def restore_auto_scroll(self):
        """恢复自动滚动"""
        self.receive_text.force_auto_scroll()
        self.filter_preview_text.force_auto_scroll()

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file="serial_monitor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
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
    
    def get_port_config(self, port_index):
        """获取指定串口的配置"""
        return self.config.get(f'port{port_index}', {})
    
    def set_port_config(self, port_index, config):
        """设置指定串口的配置"""
        self.config[f'port{port_index}'] = config
        self.save_config()
    
    def get_window_geometry(self):
        """获取窗口几何信息"""
        return self.config.get('window_geometry', None)
    
    def set_window_geometry(self, geometry):
        """设置窗口几何信息"""
        self.config['window_geometry'] = geometry
        self.save_config()
    
    def get_splitter_sizes(self):
        """获取分割器大小"""
        return self.config.get('splitter_sizes', None)
    
    def set_splitter_sizes(self, sizes):
        """设置分割器大小"""
        self.config['splitter_sizes'] = sizes
        self.save_config()
        
    # 在ConfigManager类中添加
    def get_auto_save_enabled(self):
        return self.config.get('auto_save_enabled', False)

    def set_auto_save_enabled(self, enabled):
        self.config['auto_save_enabled'] = enabled
        self.save_config()

    def get_auto_save_limit_mb(self):
        return self.config.get('auto_save_limit_mb', 50)

    def set_auto_save_limit_mb(self, mb):
        self.config['auto_save_limit_mb'] = mb
        self.save_config()

class DualSerialMonitor(QMainWindow):
    """双串口监控工具主窗口"""
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.setWindowTitle('SerialToolFree')
        # 使用更合理的初始大小
        self.resize(500, 1000) #初始宽度
        self.init_ui()
        self.load_window_config()
        print("DualSerialMonitor")
        
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        # 创建菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        # 添加自动保存开关
        self.auto_save_action = QAction('自动保存', self)
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.setChecked(self.config_manager.get_auto_save_enabled())
        self.auto_save_action.triggered.connect(self.toggle_auto_save)
        file_menu.addAction(self.auto_save_action)
        # 添加设置自动保存容量
        set_limit_action = QAction('设置自动保存容量', self)
        set_limit_action.triggered.connect(self.set_auto_save_limit)
        file_menu.addAction(set_limit_action)
        
        # 添加保存动作
        save_all_original_action = QAction('保存所有原始数据', self)
        save_all_original_action.triggered.connect(self.save_all_original_data)
        file_menu.addAction(save_all_original_action)
        
        save_all_filtered_action = QAction('保存所有过滤数据', self)
        save_all_filtered_action.triggered.connect(self.save_all_filtered_data)
        file_menu.addAction(save_all_filtered_action)
        
        # 创建水平分割器
        # 创建水平分割器时设置优化选项
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setOpaqueResize(False)  # 禁用实时拖动效果，提升性能
        #self.splitter.setChildrenCollapsible(False)  # 禁止分割器折叠
        
        # 创建两个串口部件
        self.serial_widgets = []
        for i in range(2):
            widget = SerialWidget(i+1, self.config_manager)
            self.splitter.addWidget(widget)
            self.serial_widgets.append(widget)
        
        # 设置更紧凑的初始大小比例
        self.splitter.setSizes([250, 250])
        
        main_layout.addWidget(self.splitter)
        
        # 状态栏
        self.statusBar().showMessage('就绪 - 支持2个串口同时监控')
        
        for widget in self.serial_widgets:
            widget.set_auto_save_enabled(self.auto_save_action.isChecked())
    
    def save_all_original_data(self):
        """保存所有串口的原始数据"""
        for i, widget in enumerate(self.serial_widgets):
            widget.save_original_data()
    
    def save_all_filtered_data(self):
        """保存所有串口的过滤数据"""
        for i, widget in enumerate(self.serial_widgets):
            widget.save_filtered_data()
    def toggle_auto_save(self, checked):
        self.config_manager.set_auto_save_enabled(checked)
        # 通知所有串口窗口
        for widget in self.serial_widgets:
            widget.set_auto_save_enabled(checked)
        
    def load_window_config(self):
        """加载窗口配置"""
        # 加载窗口大小和位置
        geometry = self.config_manager.get_window_geometry()
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except:
                pass
        
        # 加载分割器大小
        splitter_sizes = self.config_manager.get_splitter_sizes()
        if splitter_sizes:
            try:
                self.splitter.setSizes(splitter_sizes)
            except:
                pass
    
    def closeEvent(self, event):
        print("closeEvent")
        """窗口关闭时保存配置"""
        self.save_config()
        
        event.accept()

    def set_auto_save_limit(self):
        cur = self.config_manager.get_auto_save_limit_mb()
        val, ok = QInputDialog.getInt(self, '设置触发自动保存容量阈值', '请输入自动保存容量阈值（KB）:', cur, 1, 1024 * 1024, 1)
        if ok:
            self.config_manager.set_auto_save_limit_mb(val)
            QMessageBox.information(self, '设置成功', f'自动保存容量已设为{val}KB')
            
    def save_config(self):
        # 保存串口配置
        for i, widget in enumerate(self.serial_widgets):
            self.config_manager.set_port_config(i+1, widget.get_config())
        
        # 保存窗口几何信息
        self.config_manager.set_window_geometry(self.saveGeometry().data().hex())
        
        # 保存分割器大小
        self.config_manager.set_splitter_sizes(self.splitter.sizes())
        
        # 关闭所有串口
        for widget in self.serial_widgets:
            if widget.serial_port and widget.serial_port.is_open:
                widget.close_serial()


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
    # 设置全局字体
    font = QFont("微软雅黑", 10)  # 字体名称和大小
    app.setFont(font)
    window = DualSerialMonitor()
    window.show()
    sys.exit(app.exec_())