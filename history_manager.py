import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

HISTORY_FILE = 'backup_history.json'

class HistoryManager:
    def __init__(self, file_path=HISTORY_FILE):
        self.file_path = file_path
        self.history = self._load_history()

    def _load_history(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            return []

    def _save_history(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def add_record(self, src, dst):
        # 检查是否已存在相同记录，若存在则更新时间并移到最前
        existing = next((item for item in self.history if item['src'] == src and item['dst'] == dst), None)
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing:
            self.history.remove(existing)
            existing['last_used'] = now
            self.history.insert(0, existing)
        else:
            new_record = {
                'src': src,
                'dst': dst,
                'last_used': now,
                'created_at': now
            }
            self.history.insert(0, new_record)
        
        # 限制只保留最近 10 条
        if len(self.history) > 10:
            self.history = self.history[:10]
            
        self._save_history()

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self._save_history()

