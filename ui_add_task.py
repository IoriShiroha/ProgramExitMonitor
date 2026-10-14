import sys
import os
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5 import uic
import psutil

# 获取UI文件路径
def get_ui_file(filename):
    if getattr(sys, 'frozen', False):
        # 如果程序是打包后的exe文件
        # PyInstaller 6.0+ 将资源文件放在 _internal 目录中
        application_path = os.path.dirname(sys.executable)
        ui_file = os.path.join(application_path, '_internal', 'ui', filename)
    else:
        # 如果是直接运行的.py文件
        application_path = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(application_path, 'ui', filename)
    
    return ui_file


class AddTaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        
        # 动态加载UI
        uic.loadUi(get_ui_file('add_task_dialog.ui'), self)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        if task:
            self.setWindowTitle("编辑任务")
            self.nameInput.setText(task.name)
            self.set_process_name(task.process_name)
            self.intervalInput.setValue(task.check_interval)
            self.enabledCheckbox.setChecked(task.enabled)
        else:
            self.setWindowTitle("添加新任务")
            self.load_processes()

        self.setup_ui()

    def setup_ui(self):
        # 连接信号
        self.refreshButton.clicked.connect(self.load_processes)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def set_process_name(self, process_name):
        """
        设置进程名称，确保即使进程未运行也能正确显示
        """
        # 先加载所有进程
        self.load_processes()
        # 查找进程名称是否已存在
        items = self.processList.findItems(process_name, Qt.MatchExactly)
        if not items:
            # 如果不存在，则添加到列表中
            self.processList.addItem(process_name)
            items = self.processList.findItems(process_name, Qt.MatchExactly)
        if items:
            items[0].setSelected(True)

    def get_task_data(self):
        """
        获取任务数据
        """
        # 获取选中的进程
        selected_processes = [item.text() for item in self.processList.selectedItems()]
        process_name = ""
        if selected_processes:
            # 如果有选中的进程，使用第一个作为进程名（保持向后兼容）
            process_name = selected_processes[0]

        return {
            "name": self.nameInput.text(),
            "process_name": process_name,
            "check_interval": self.intervalInput.value(),
            "enabled": self.enabledCheckbox.isChecked()
        }

    def load_processes(self):
        '''
        获取当前系统中的所有进程名称
        '''
        processes = sorted(list({proc.name() for proc in psutil.process_iter(['name'])}))
        
        # 保存当前选中的项目
        selected_processes = [item.text() for item in self.processList.selectedItems()]
        
        # 清空并重新添加所有进程
        self.processList.clear()
        for process in processes:
            item = QListWidgetItem(process)
            if process in selected_processes:
                item.setSelected(True)
            self.processList.addItem(item)


from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QMessageBox, QSystemTrayIcon,
                             QMenu, QAction, QStatusBar, QFormLayout, QDialog,
                             QLineEdit, QSpinBox, QCheckBox, QCompleter, QComboBox,
                             QListWidget, QListWidgetItem, QGroupBox)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QTimer
import psutil
# from ui_add_task import AddTaskDialog


class MainWindow(QMainWindow):
    def __init__(self, task_manager, message_sender, config_manager):
        super().__init__()
        self.task_manager = task_manager
        self.message_sender = message_sender
        self.config_manager = config_manager

        self.setup_ui()
        self.load_tasks()
        # 每秒更新一次状态
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  

    def setup_ui(self):
        self.setWindowTitle("后台程序监控")
        self.setGeometry(100, 100, 800, 500)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加任务")
        self.edit_button = QPushButton("编辑任务")
        self.remove_button = QPushButton("删除任务")
        self.toggle_button = QPushButton("启用/禁用")

        self.add_button.clicked.connect(self.add_task)
        self.edit_button.clicked.connect(self.edit_task)
        self.remove_button.clicked.connect(self.remove_task)
        self.toggle_button.clicked.connect(self.toggle_task)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.toggle_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["任务名称", "进程名称", "状态", "启用状态", "检测间隔"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.table)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def load_tasks(self):
        self.table.setRowCount(0)
        for task in self.config_manager.config.tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(task.name))
            self.table.setItem(row, 1, QTableWidgetItem(task.process_name))

            status_item = QTableWidgetItem("未知")
            self.table.setItem(row, 2, status_item)

            # 添加启用状态列
            enabled_item = QTableWidgetItem("启用" if task.enabled else "禁用")
            enabled_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, enabled_item)

            interval_item = QTableWidgetItem(f"{task.check_interval}秒")
            self.table.setItem(row, 4, interval_item)

            # 设置行颜色基于启用状态
            if not task.enabled:
                for col in range(5):  # 更新为5列
                    self.table.item(row, col).setBackground(
                        QColor(220, 220, 220))

    def update_status(self):
        for row in range(self.table.rowCount()):
            task_name = self.table.item(row, 0).text()
            status = self.task_manager.get_task_status(task_name)
            status_item = self.table.item(row, 2)

            if status:
                status_item.setText("运行中")
                status_item.setBackground(QColor(200, 255, 200))
            else:
                status_item.setText("未运行")
                status_item.setBackground(QColor(255, 200, 200))

    def add_task(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_():
            data = dialog.get_task_data()
            if self.task_manager.add_task(**data):
                self.load_tasks()
                self.statusBar().showMessage("任务添加成功")
            else:
                QMessageBox.warning(self, "错误", "添加任务失败")

    def edit_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.table.item(selected, 0).text()
        task = next(
            (t for t in self.config_manager.config.tasks if t.name == task_name), None)

        if task:
            dialog = AddTaskDialog(self, task)
            if dialog.exec_():
                data = dialog.get_task_data()
                updated_task = type(task)(**data)
                if self.task_manager.update_task(updated_task):
                    self.load_tasks()
                    self.statusBar().showMessage("任务更新成功")
                else:
                    QMessageBox.warning(self, "错误", "更新任务失败")

    def remove_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.table.item(selected, 0).text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务 '{task_name}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.task_manager.remove_task(task_name):
                self.load_tasks()
                self.statusBar().showMessage("任务删除成功")
            else:
                QMessageBox.warning(self, "错误", "删除任务失败")

    def toggle_task(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.table.item(selected, 0).text()
        task = next(
            (t for t in self.config_manager.config.tasks if t.name == task_name), None)

        if task:
            task.enabled = not task.enabled
            if self.task_manager.update_task(task):
                self.load_tasks()
                status = "启用" if task.enabled else "禁用"
                self.statusBar().showMessage(f"任务已{status}")
            else:
                QMessageBox.warning(self, "错误", "更新任务失败")

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到系统托盘"""
        event.ignore()
        self.hide()
        self.message_sender.send_notification(
            "程序监控",
            "程序已最小化到系统托盘，继续在后台运行",
            2000
        )

