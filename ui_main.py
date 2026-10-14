import sys
import os
import json
from dataclasses import asdict
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QSystemTrayIcon, QMenu, QAction, QFileDialog
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import uic

# 获取UI文件路径
def get_ui_file(filename):
    if getattr(sys, 'frozen', False):
        # 如果程序是打包后的exe文件
        # PyInstaller 6.0+ 将资源文件放在 _internal 目录中
        application_path = os.path.dirname(sys.executable)
        internal_path = os.path.join(application_path, '_internal', 'ui', filename)
        if os.path.exists(internal_path):
            return internal_path
        
        # 兼容旧版本PyInstaller或其他打包方式
        legacy_path = os.path.join(application_path, 'ui', filename)
        if os.path.exists(legacy_path):
            return legacy_path
            
    else:
        # 如果是直接运行的.py文件
        application_path = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(application_path, 'ui', filename)
        if os.path.exists(ui_file):
            return ui_file
    
    raise FileNotFoundError(f"无法找到UI文件: {filename}")

from ui_add_task import AddTaskDialog
from ui_settings import SettingsDialog
from config import TaskConfig

class MainWindow(QMainWindow):
    def __init__(self, task_manager, message_sender, config_manager):
        super().__init__()
        self.task_manager = task_manager
        self.message_sender = message_sender
        self.config_manager = config_manager

        # 动态加载UI
        uic.loadUi(get_ui_file('main_window.ui'), self)
        
        self.setup_ui()
        self.load_tasks()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新一次状态

    def setup_ui(self):
        # 连接按钮信号
        self.addButton.clicked.connect(self.add_task)
        self.editButton.clicked.connect(self.edit_task)
        self.removeButton.clicked.connect(self.remove_task)
        self.toggleButton.clicked.connect(self.toggle_task)
        self.settingsButton.clicked.connect(self.open_settings)

        # 设置任务表格
        self.taskTable.horizontalHeader().setSectionResizeMode(0)  # 第一列自适应
        self.taskTable.setSelectionBehavior(self.taskTable.SelectRows)
        self.taskTable.setAlternatingRowColors(True)
        # 禁止直接编辑表格
        self.taskTable.setEditTriggers(self.taskTable.NoEditTriggers)
        
        # 设置选中行样式
        self.taskTable.setStyleSheet("""
            QTableWidget::item:selected {
                color: black;
                background-color: #d0d0d0;
            }
        """)

        # 连接菜单栏动作
        self.actionImportConfig.triggered.connect(self.import_config)
        self.actionExportConfig.triggered.connect(self.export_config)
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)
        
        # 连接任务菜单动作
        self.actionAddTask.triggered.connect(self.add_task)
        self.actionEditTask.triggered.connect(self.edit_task)
        self.actionRemoveTask.triggered.connect(self.remove_task)
        self.actionToggleTask.triggered.connect(self.toggle_task)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def load_tasks(self):
        self.taskTable.setRowCount(0)
        for task in self.config_manager.config.tasks:
            row = self.taskTable.rowCount()
            self.taskTable.insertRow(row)

            self.taskTable.setItem(row, 0, QTableWidgetItem(task.name))
            self.taskTable.setItem(row, 1, QTableWidgetItem(task.process_name))

            status_item = QTableWidgetItem("未知")
            self.taskTable.setItem(row, 2, status_item)

            # 添加启用状态列
            enabled_item = QTableWidgetItem("启用" if task.enabled else "禁用")
            enabled_item.setTextAlignment(Qt.AlignCenter)
            # 使用自定义属性标记启用状态
            if task.enabled:
                enabled_item.setData(Qt.UserRole, True)
            else:
                enabled_item.setData(Qt.UserRole, False)
                # 设置禁用任务的字体颜色为灰色
                enabled_item.setForeground(QColor(128, 128, 128))  # 灰色
            self.taskTable.setItem(row, 3, enabled_item)

            interval_item = QTableWidgetItem(f"{task.check_interval}秒")
            self.taskTable.setItem(row, 4, interval_item)

    def update_status(self):
        for row in range(self.taskTable.rowCount()):
            task_name = self.taskTable.item(row, 0).text()
            status = self.task_manager.get_task_status(task_name)
            status_item = self.taskTable.item(row, 2)

            if status:
                status_item.setText("运行中")
                # 设置运行中状态的背景色
                status_item.setBackground(QColor(200, 255, 200))  # 浅绿色
            else:
                status_item.setText("未运行")
                # 设置未运行状态的背景色
                status_item.setBackground(QColor(255, 200, 200))  # 浅红色

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
        selected = self.taskTable.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.taskTable.item(selected, 0).text()  # 使用列索引0获取任务名称
        task = next(
            (t for t in self.config_manager.config.tasks if t.name == task_name), None)

        if task:
            dialog = AddTaskDialog(self, task)
            if dialog.exec_():
                data = dialog.get_task_data()
                # 修复任务更新bug：直接使用TaskConfig创建新任务对象
                updated_task = TaskConfig(**data)
                if self.task_manager.update_task(updated_task):
                    self.load_tasks()
                    self.statusBar().showMessage("任务更新成功")
                else:
                    QMessageBox.warning(self, "错误", "更新任务失败")

    def remove_task(self):
        selected = self.taskTable.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.taskTable.item(selected, 0).text()  # 使用列索引0获取任务名称

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
        selected = self.taskTable.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return

        task_name = self.taskTable.item(selected, 0).text()
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

    def open_settings(self):
        """打开设置窗口"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_():
            self.statusBar().showMessage("设置已保存")

    def import_config(self):
        """导入配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON Files (*.json)")
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 保存当前配置作为备份
                backup_path = file_path + ".backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.config_manager.config), f, ensure_ascii=False, indent=2)
                
                # 加载新配置
                self.config_manager.load_config_from_dict(config_data)
                self.load_tasks()
                self.statusBar().showMessage("配置导入成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {str(e)}")

    def export_config(self):
        """导出配置文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "config.json", "JSON Files (*.json)")
        
        if file_path:
            try:
                config_data = asdict(self.config_manager.config)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                self.statusBar().showMessage("配置导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置失败: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于程序运行监控", 
                         "程序运行监控工具\n\n"
                          "用于监控Windows系统中指定进程的运行状态，当进程状态发生变化时发送通知。"
                         "")

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到系统托盘"""
        event.ignore()
        self.hide()
        
        # self.message_sender.send_notification(
        #     "程序监控",
        #     "程序已最小化到系统托盘，继续在后台运行",
        #     2000
        # )