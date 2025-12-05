import sys
import os

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

if __name__ == "__main__":
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Critical Error: {e}")
        input("Press Enter to exit...")

