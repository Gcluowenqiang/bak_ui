# Backup Tool

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-v1.0.0-green.svg)

一个基于 Python Tkinter 构建的轻量级桌面增量备份工具。旨在解决数据丢失问题，支持将数据文件夹高效备份到 U 盘或其他存储介质。

## 界面展示
![界面展示](./images/index.png)

## ✨ 功能特性

*   **原生 GUI**: 基于 ttkbootstrap 的现代化桌面界面，操作更流畅。
*   **增量备份**: 智能比对文件大小和修改时间，仅复制变更文件，极大提升速度。
*   **同步备份**: 确保目标目录与源目录完全一致，自动删除目标目录中源目录不存在的文件和目录。
*   **实时进度**: 进度条和日志实时展示备份状态。
*   **断点续传**: 支持中途停止，下次运行时自动跳过已备份文件。
*   **历史记录**: 自动记录最近使用的源目录和目标目录，方便快速选择。
*   **检查更新**: 内置版本检查功能，支持从 GitHub 获取最新版本。

## 🚀 快速开始

### 依赖环境

*   Python 3.8+
*   依赖库: `ttkbootstrap`, `requests`

### 安装与运行

1.  **克隆项目**:
    ```bash
    git clone https://github.com/Gcluowenqiang/bak_ui.git
    cd bak_ui
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **启动程序**:
    ```bash
    python main.py
    ```

## 🛠️ 开发说明

### 目录结构

```
bak_ui/
├── core/              # 核心逻辑
│   ├── backup.py      # 备份逻辑实现
│   ├── history.py     # 历史记录管理
│   ├── updater.py     # 更新检查
│   └── version.py     # 版本信息
├── gui/               # 界面实现
│   └── main_window.py # 主窗口代码
├── main.py            # 程序入口
├── requirements.txt   # 项目依赖
└── README.md          # 说明文档
```

### 构建发布 (生成 .exe)

为了在无 Python 环境的机器上运行，可以使用 PyInstaller 进行打包。

1.  **安装 PyInstaller**:
    ```bash
    pip install pyinstaller
    ```

2.  **执行打包脚本**:
    ```bash
    python build.py
    ```
    或者直接使用 PyInstaller 命令:
    ```bash
    pyinstaller BakUI.spec
    ```

3.  **获取文件**:
    打包完成后，在 `dist` 目录下找到 `BakUI.exe` 即可分发使用。

## 📄 许可证

MIT License
