import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import os

from core.logger import Logger
from core.history import HistoryManager
from core.backup import BackupManager
from core.updater import Updater
from core.version import VERSION

class MainWindow:
    def __init__(self):
        self.logger = Logger()
        self.history_manager = HistoryManager()
        self.backup_manager = BackupManager()
        self.updater = Updater()
        
        self.root = ttk.Window(themename="cosmo")
        self.root.title(f"BakUI - 备份工具 {VERSION}")
        self.root.geometry("700x500")
        
        # 连接日志回调
        self.logger.set_gui_callback(self.append_log)
        
        self._init_ui()
        self._init_menu()
        
    def _init_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label=f"版本: {VERSION}", state="disabled")
        help_menu.add_separator()
        help_menu.add_command(label="检查更新", command=self._check_update)

    def _init_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 1. 历史记录下拉框 (快速选择)
        history_frame = ttk.Labelframe(main_frame, text="快速选择 (历史记录)", padding=10)
        history_frame.pack(fill=X, pady=5)
        
        self.history_combo = ttk.Combobox(history_frame, state="readonly")
        self.history_combo.pack(fill=X, side=LEFT, expand=YES)
        self.history_combo.bind("<<ComboboxSelected>>", self._on_history_select)
        
        ttk.Button(history_frame, text="清除历史", command=self._clear_history, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)
        
        self._refresh_history_combo()

        # 2. 路径选择区域
        path_frame = ttk.Labelframe(main_frame, text="备份配置", padding=10)
        path_frame.pack(fill=X, pady=5)
        
        # 源目录
        ttk.Label(path_frame, text="源目录:").grid(row=0, column=0, sticky=W, pady=5)
        self.src_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.src_var).grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self._browse_dir(self.src_var), bootstyle=INFO).grid(row=0, column=2)
        
        # 目标目录
        ttk.Label(path_frame, text="目标目录:").grid(row=1, column=0, sticky=W, pady=5)
        self.dst_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.dst_var).grid(row=1, column=1, sticky=EW, padx=5)
        ttk.Button(path_frame, text="浏览", command=lambda: self._browse_dir(self.dst_var), bootstyle=INFO).grid(row=1, column=2)
        
        path_frame.columnconfigure(1, weight=1)
        
        # 备份模式选择
        mode_frame = ttk.Frame(path_frame)
        mode_frame.grid(row=2, column=0, columnspan=3, sticky=W, pady=10)
        
        ttk.Label(mode_frame, text="备份模式:").pack(side=LEFT, padx=(0, 10))
        self.backup_mode_var = tk.StringVar(value="incremental")
        ttk.Radiobutton(mode_frame, text="增量备份", variable=self.backup_mode_var, value="incremental").pack(side=LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="同步备份", variable=self.backup_mode_var, value="sync").pack(side=LEFT, padx=5)
        
        # 模式说明
        mode_info = ttk.Label(mode_frame, text="(增量:仅复制变更 | 同步:完全一致)", font=("微软雅黑", 8), foreground="gray")
        mode_info.pack(side=LEFT, padx=10)
        
        # 3. 操作按钮
        btn_frame = ttk.Frame(main_frame, padding=10)
        btn_frame.pack(fill=X)
        
        self.start_btn = ttk.Button(btn_frame, text="开始备份", command=self._start_backup, bootstyle=SUCCESS, width=15)
        self.start_btn.pack(side=LEFT, padx=20)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self._stop_backup, bootstyle=DANGER, state="disabled", width=15)
        self.stop_btn.pack(side=RIGHT, padx=20)
        
        # 4. 进度和日志
        log_frame = ttk.Labelframe(main_frame, text="执行日志", padding=10)
        log_frame.pack(fill=BOTH, expand=YES, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(log_frame, variable=self.progress_var, maximum=100, bootstyle=STRIPED)
        self.progress_bar.pack(fill=X, pady=(0, 5))
        
        self.status_label = ttk.Label(log_frame, text="就绪")
        self.status_label.pack(anchor=W)
        
        self.log_text = tk.Text(log_frame, height=8, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # Scrollbar
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.log_text.configure(yscrollcommand=scroll.set)

    def _browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path.replace('/', os.sep))

    def _refresh_history_combo(self):
        history = self.history_manager.get_history()
        values = [f"{h['src']} -> {h['dst']}" for h in history]
        self.history_combo['values'] = values
        if values:
            self.history_combo.current(0)

    def _on_history_select(self, event):
        idx = self.history_combo.current()
        if idx >= 0:
            record = self.history_manager.get_history()[idx]
            self.src_var.set(record['src'])
            self.dst_var.set(record['dst'])

    def _clear_history(self):
        if messagebox.askyesno("确认", "确定要清除所有历史记录吗？"):
            self.history_manager.clear_history()
            self.history_combo.set('')
            self._refresh_history_combo()

    def _start_backup(self):
        src = self.src_var.get()
        dst = self.dst_var.get()
        
        if not src or not dst:
            messagebox.showwarning("提示", "请选择源目录和目标目录")
            return
            
        if not os.path.exists(src):
            messagebox.showerror("错误", "源目录不存在")
            return

        # 保存历史
        self.history_manager.add_record(src, dst)
        self._refresh_history_combo()
        
        # UI 状态
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_var.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, END)
        self.log_text.configure(state="disabled")
        
        # 启动线程
        threading.Thread(target=self._run_backup_thread, args=(src, dst), daemon=True).start()

    def _run_backup_thread(self, src, dst):
        sync_mode = (self.backup_mode_var.get() == "sync")
        self.backup_manager.start_backup(src, dst, self._update_progress, sync_mode=sync_mode)
        
        # 结束后恢复 UI
        self.root.after(0, self._on_backup_finished)

    def _update_progress(self, percent, total, message):
        self.progress_var.set(percent)
        self.status_label.configure(text=message)
        
    def append_log(self, message):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert(END, message + "\n")
            self.log_text.see(END)
            self.log_text.configure(state="disabled")
        self.root.after(0, _do)

    def _stop_backup(self):
        self.backup_manager.stop()
        self.status_label.configure(text="正在停止...")

    def _on_backup_finished(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if not self.backup_manager.stop_flag:
             messagebox.showinfo("完成", "备份任务已结束")
        else:
             messagebox.showinfo("提示", "备份已中止")

    def _check_update(self):
        self.logger.info("正在检查更新...")
        threading.Thread(target=self._do_check_update, daemon=True).start()

    def _do_check_update(self):
        has_update, version, body, url = self.updater.check_for_updates()
        
        def _show_result():
            if has_update:
                msg = f"发现新版本: v{version}\n\n{body}\n\n是否前往下载？"
                if messagebox.askyesno("发现更新", msg):
                    self.updater.open_browser_download(url)
            else:
                messagebox.showinfo("检查更新", f"当前已是最新版本 ({VERSION})")
                self.logger.info("当前已是最新版本。")
                
        self.root.after(0, _show_result)

    def run(self):
        self.root.mainloop()

