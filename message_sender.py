from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal
import os
import requests
import sys
import logging


class MessageSender(QObject):
    message_sent = pyqtSignal(str, str)
    show_main_window = pyqtSignal()
    quit_application = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger("ProgramMonitor")
        self.tray_icon = None
        self.setup_tray_icon()

    def setup_tray_icon(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()

        # 创建托盘图标菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QMenu::item {
                color: black;
                background-color: #f0f0f0;
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #d0d0d0;
            }
        """)

        # 添加菜单项
        show_action = QAction("显示", self)
        quit_action = QAction("退出", self)

        show_action.triggered.connect(self._show_main_window_triggered)
        quit_action.triggered.connect(self._quit_application_triggered)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 设置图标 - 支持多种格式和路径
        # 尝试多种可能的图标路径
        icon_paths = []
        
        # 如果是打包后的exe，尝试在exe同目录下查找
        if getattr(sys, 'frozen', False):
            # PyInstaller打包的程序会设置frozen属性
            application_path = os.path.dirname(sys.executable)
            icon_paths.append(os.path.join(application_path, "icon.png"))
        # 开发环境或打包后在当前目录查找
        script_dir = os.path.dirname(__file__)
        icon_paths.append(os.path.join(script_dir, "icon.png"))

        
        icon_set = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
                self.logger.info(f"托盘图标已设置: {icon_path}")
                icon_set = True
                break
        
        if not icon_set:
            # 如果图标文件不存在，使用默认图标
            self.tray_icon.setIcon(QIcon())
            self.logger.warning("托盘图标文件未找到，使用默认图标")
            
        # 显示托盘图标
        self.tray_icon.show()
        self.logger.info("托盘图标已显示")

    # TODO:拆分通知功能
    def send_notification(self, title, message, timeout=5000):
        """
        发送系统通知
        """
        self._send_system_tray_notification(title, message, timeout)
        self._send_http_notification(message)
        self.message_sent.emit(title, message)
        self.logger.info(f"通知已发送: {title} - {message}")

    def _send_system_tray_notification(self, title, message, timeout=5000):
        """
        发送系统托盘通知
        """
        # 输出到控制台
        print(f"{title}: {message}")

        # 显示系统通知
        if self.tray_icon:
            self.tray_icon.showMessage(
                title, message, QSystemTrayIcon.Information, timeout)

    def _send_http_notification(self, message):
        """
        发送HTTP通知
        """
        try:
            apiUrl = self.config_manager.config.api_url
            sendkey = self.config_manager.config.sendkey
            data = {
                'sendkey': sendkey,  
                "msgtype": "text",
                "text": f"WinServer进程监控:警告！{message}"
            }
        
            response = requests.post(apiUrl, data=data)
            self.logger.info(f"HTTP通知发送结果: {response.text}")
            print(response.text)
        except Exception as e:
            self.logger.error(f"发送HTTP通知时出错: {e}")

    
    def _show_main_window_triggered(self):
        """当点击托盘菜单的显示选项时触发"""
        self.show_main_window.emit()

    def _quit_application_triggered(self):
        """当点击托盘菜单的退出选项时触发"""
        self.quit_application.emit()