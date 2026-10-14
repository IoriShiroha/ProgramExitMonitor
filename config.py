import json
import os
from dataclasses import dataclass, asdict
from typing import List
import logging
from datetime import datetime


@dataclass
class TaskConfig:
    name: str
    process_name: str
    check_interval: int = 5  # 检查间隔(秒)
    enabled: bool = True


@dataclass
class AppConfig:
    tasks: List[TaskConfig]
    message_title: str = "程序监控通知"
    message_timeout: int = 5000  # 消息显示时间(毫秒)
    api_url: str = ""
    sendkey: str = ""


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks = [TaskConfig(**task)
                             for task in data.get('tasks', [])]
                    return AppConfig(
                        tasks=tasks,
                        message_title=data.get('message_title', "程序监控通知"),
                        message_timeout=data.get('message_timeout', 5000),
                        api_url=data.get('api_url', ""),
                        sendkey=data.get('sendkey', "")
                    )
            except Exception as e:
                print(f"加载配置失败: {e}")

        # 返回默认配置
        return AppConfig(tasks=[])

    def load_config_from_dict(self, data):
        """从字典加载配置"""
        try:
            tasks = [TaskConfig(**task) for task in data.get('tasks', [])]
            self.config = AppConfig(
                tasks=tasks,
                message_title=data.get('message_title', "程序监控通知"),
                message_timeout=data.get('message_timeout', 5000),
                api_url=data.get('api_url', ""),
                sendkey=data.get('sendkey', "")
            )
            return self.save_config()
        except Exception as e:
            print(f"从字典加载配置失败: {e}")
            return False

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def add_task(self, task: TaskConfig):
        self.config.tasks.append(task)
        return self.save_config()

    def remove_task(self, task_name: str):
        self.config.tasks = [
            t for t in self.config.tasks if t.name != task_name]
        return self.save_config()

    def update_task(self, task: TaskConfig):
        for i, t in enumerate(self.config.tasks):
            if t.name == task.name:
                self.config.tasks[i] = task
                return self.save_config()
        return False


def setup_logger():
    """
    设置日志记录器，按月存储日志
    """
    # 确保logs目录存在，使用绝对路径
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 按月生成日志文件名
    current_month = datetime.now().strftime("%Y-%m")
    log_filename = os.path.join(logs_dir, f"program_monitor_{current_month}.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    return logging.getLogger("ProgramMonitor")
