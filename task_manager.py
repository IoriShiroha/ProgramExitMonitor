import psutil
import schedule
import time
import threading
from datetime import datetime
import logging
from typing import Dict, Callable
from config import TaskConfig


class TaskManager:
    def __init__(self, message_sender, config_manager):
        self.message_sender = message_sender
        self.config_manager = config_manager
        self.logger = logging.getLogger("ProgramMonitor")
        self.running = False
        self.monitor_thread = None
        self.process_status = {}  # 记录进程状态

    def start_monitoring(self):
        """开始监控所有任务"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("开始监控进程")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("停止监控进程")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.check_processes()
            except Exception as e:
                self.logger.error(f"监控过程中发生错误: {e}")
                print(f"监控过程中发生错误: {e}")

            # 每秒检查一次
            time.sleep(1)

    def check_processes(self):
        """检查所有配置的进程"""
        current_processes = {
            p.info['name'].lower(): p for p in psutil.process_iter(['pid', 'name'])}

        for task in self.config_manager.config.tasks:
            if not task.enabled:
                # 即使任务被禁用，也要更新状态为False
                self.process_status[task.name] = False
                continue

            process_found = any(
                proc_name.lower() in current_processes
                for proc_name in task.process_name.split('|')
            )

            # 检查状态变化
            if task.name in self.process_status:
                was_running = self.process_status[task.name]
                if was_running and not process_found:
                    # 进程已退出
                    self.logger.info(f"进程退出: {task.name}")
                    self.message_sender.send_notification(
                        "程序退出通知",
                        f"程序 {task.name} 已退出",
                        5000
                    )
                elif not was_running and process_found:
                    # 进程已启动
                    self.logger.info(f"进程启动: {task.name}")
                    self.message_sender.send_notification(
                        "程序启动通知",
                        f"程序 {task.name} 已启动",
                        5000
                    )

            # 更新状态
            self.process_status[task.name] = process_found

    def add_task(self, name, process_name, check_interval=5, enabled=True):
        """添加新任务"""
        task = TaskConfig(
            name=name,
            process_name=process_name,
            check_interval=check_interval,
            enabled=enabled
        )
        # 初始化任务状态
        self.process_status[name] = False
        result = self.config_manager.add_task(task)
        self.logger.info(f"添加任务: {name}")
        return result

    def remove_task(self, task_name):
        """移除任务"""
        if task_name in self.process_status:
            del self.process_status[task_name]
        result = self.config_manager.remove_task(task_name)
        self.logger.info(f"移除任务: {task_name}")
        return result

    def update_task(self, task):
        """更新任务"""
        result = self.config_manager.update_task(task)
        self.logger.info(f"更新任务: {task.name}")
        return result

    def get_task_status(self, task_name):
        """获取任务状态"""
        return self.process_status.get(task_name, False)