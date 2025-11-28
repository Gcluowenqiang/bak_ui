from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json
import os
import logging
from backup_core import BackupManager
from history_manager import HistoryManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局管理器实例
backup_manager = BackupManager()
history_manager = HistoryManager()

def select_folder_dialog():
    """
    弹出文件夹选择框 (在单独的线程中可能需要特殊处理，但在 Windows 上通常直接调用即可)
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 创建隐藏的根窗口
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # 确保窗口在最前
        
        folder_path = filedialog.askdirectory()
        
        root.destroy()
        return folder_path
    except Exception as e:
        logger.error(f"打开文件夹选择框失败: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    folder_path = select_folder_dialog()
    if folder_path:
        # 统一路径分隔符
        folder_path = folder_path.replace('/', os.sep)
        return jsonify({'success': True, 'path': folder_path})
    else:
        return jsonify({'success': False, 'message': '未选择文件夹'})

@app.route('/api/history', methods=['GET'])
def get_history():
    data = history_manager.get_history()
    # #region agent log
    try:
        with open(r"d:\curosr_work\bak_ui\.cursor\debug.log", "a", encoding="utf-8") as f:
            import json, time
            f.write(json.dumps({"sessionId":"debug-session","runId":"run4","hypothesisId":"H1","location":"app.py:get_history","message":"Returning history","data":{"count":len(data), "content": data},"timestamp":int(time.time()*1000)}) + "\n")
    except: pass
    # #endregion
    return jsonify(data)

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    history_manager.clear_history()
    return jsonify({'success': True})

@app.route('/api/backup')
def backup_stream():
    src = request.args.get('src')
    dst = request.args.get('dst')

    if not src or not dst:
        return jsonify({'error': '缺少源目录或目标目录'}), 400
    
    # 保存到历史记录
    history_manager.add_record(src, dst)
    
    # 重置停止标志
    backup_manager.stop_flag = False

    def generate():
        for progress in backup_manager.backup_generator(src, dst):
            # SSE 格式: data: <json_payload>\n\n
            yield f"data: {json.dumps(progress)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/stop', methods=['POST'])
def stop_backup():
    backup_manager.stop()
    return jsonify({'success': True})

if __name__ == '__main__':
    print("启动服务...")
    # debug=True 在某些环境下可能会导致 Tkinter 问题，建议 False
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)

