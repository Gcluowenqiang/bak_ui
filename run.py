import webbrowser
from threading import Timer
from app import app

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == "__main__":
    # 延时 1.5 秒打开浏览器，确保服务已启动
    Timer(1.5, open_browser).start()
    print("正在启动微信备份工具...")
    print("如果浏览器没有自动打开，请访问 http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)

