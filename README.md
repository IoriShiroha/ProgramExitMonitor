# 程序运行监控工具

一个基于 Python + PyQt5 的 Windows 进程监控小工具，在程序**启动**或**退出**时立刻推送通知（系统托盘气泡 + 可选 HTTP 接口）。

## 环境要求

PyQt5、psutil、requests

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
python main.py
```

程序启动后会直接显示主窗口，同时常驻系统托盘。

1. 点击 **添加任务**；
2. 填写 **任务名称**；
3. 在下方进程列表中选择要监控的进程；如果目标程序当前没在运行，先启动它再点 **刷新进程列表**；
4. 设置 **检测间隔**（秒），确认 **启用** 已勾选，点 **确定**。

之后目标程序启动或退出时就会收到通知。

### 系统托盘

关闭主窗口不会退出程序，而是最小化到托盘。右键托盘图标：

- **显示** —— 重新打开主窗口；
- **退出** —— 真正结束程序（主窗口菜单 `文件 → 退出` 效果相同）。

### HTTP 推送格式

配置了 `api_url` 时，每次通知都会以表单形式发送一个 POST 请求：

| 字段 | 值 |
| --- | --- |
| `sendkey` | 配置中的 `sendkey` |
| `msgtype` | 固定为 `text` |
| `text` | `<message_title>: <通知内容>` |

请求超时为 5 秒；网络异常只记录日志，不会影响界面与后续监控。

## 打包成 exe

```bash
pip install pyinstaller
pyinstaller ProgramExMonitor.spec
```

## 开源协议

本项目基于 [MIT License](LICENSE) 开源。
