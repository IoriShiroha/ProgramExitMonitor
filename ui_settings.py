import sys
import os
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5 import uic
from config import AppConfig

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


class SettingsDialog(QDialog):
    """
    设置窗口，左右两栏布局
    """
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        # 动态加载UI
        uic.loadUi(get_ui_file('settings_dialog.ui'), self)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        '''
        设置UI
        '''
        # 左侧分类列表
        self.categoryList.addItem("通知设置")
        self.categoryList.currentRowChanged.connect(self.switch_category)
        
        # 底部按钮
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def switch_category(self, index):
        """
        切换设置分类
        """
        self.stackedWidget.setCurrentIndex(index)
        
    def load_settings(self):
        """
        加载当前设置到输入框
        """
        self.apiUrlInput.setText(self.config_manager.config.api_url)
        self.sendkeyInput.setText(self.config_manager.config.sendkey)
        
    def accept(self):
        """
        保存设置
        """
        self.config_manager.config.api_url = self.apiUrlInput.text()
        self.config_manager.config.sendkey = self.sendkeyInput.text()
        self.config_manager.save_config()
        super().accept()