import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from config import ConfigManager, setup_logger
from message_sender import MessageSender
from task_manager import TaskManager
from ui_main import MainWindow

# 程序监控
class ProgramMonitorApp:
    def __init__(self):
        # 初始化日志
        self.logger = setup_logger()
        self.logger.info("程序监控应用启动")
        
        self.app = QApplication(sys.argv)
        
        # 加载样式表
        self.load_stylesheet()

        # 初始化组件
        self.config_manager = ConfigManager()
        self.message_sender = MessageSender(self.config_manager)
        self.task_manager = TaskManager(
            self.message_sender, self.config_manager)

        # 启动监控
        self.task_manager.start_monitoring()

        # 创建主窗口
        self.main_window = MainWindow(
            self.task_manager, self.message_sender, self.config_manager)

        # 连接信号
        self.message_sender.show_main_window.connect(self.show_main_window)
        self.message_sender.quit_application.connect(self.quit_application)

    def load_stylesheet(self):
        """加载QSS样式表"""
        try:
            if getattr(sys, 'frozen', False):
                # 如果程序是打包后的exe文件
                # PyInstaller 6.0+ 将资源文件放在 _internal 目录中
                application_path = os.path.dirname(sys.executable)
                stylesheet_path = os.path.join(application_path, '_internal', 'ui', 'styles.qss')
            else:
                # 如果是直接运行的.py文件
                application_path = os.path.dirname(os.path.abspath(__file__))
                stylesheet_path = os.path.join(application_path, 'ui', 'styles.qss')
            
            if os.path.exists(stylesheet_path):
                with open(stylesheet_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                    self.app.setStyleSheet(stylesheet)
                    
                self.logger.info("样式表加载成功")
            else:
                self.logger.warning(f"样式表文件不存在: {stylesheet_path}")
        except Exception as e:
            self.logger.error(f"样式表加载失败: {e}")

    def show_main_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def quit_application(self):
        self.logger.info("程序正在退出")
        self.task_manager.stop_monitoring()
        self.app.quit()

    def run(self):
        self.main_window.show()
        self.logger.info("主窗口已显示")
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    monitor_app = ProgramMonitorApp()
    monitor_app.run()