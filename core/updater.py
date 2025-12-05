import os
import requests
import webbrowser
from core.logger import Logger
from core.version import VERSION, GITHUB_REPO

class Updater:
    def __init__(self):
        self.logger = Logger()
        self.github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        self.github_url = f"https://github.com/{GITHUB_REPO}"

    def check_for_updates(self):
        """
        检查更新
        Returns: (has_update, version, body, download_url)
        """
        try:
            self.logger.info(f"正在检查更新: {self.github_api_url}...")
            response = requests.get(self.github_api_url, timeout=10)
            
            if response.status_code == 404:
                self.logger.info("未找到发布版本 (404).")
                return False, None, "未找到发布版本", None
                
            response.raise_for_status()
            data = response.json()
            
            latest_tag = data.get("tag_name", "").lstrip("v")
            body = data.get("body", "")
            html_url = data.get("html_url", self.github_url)
            
            if self._compare_versions(latest_tag, VERSION) > 0:
                return True, latest_tag, body, html_url
            else:
                return False, latest_tag, body, None
                
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            return False, None, str(e), None

    def _compare_versions(self, v1, v2):
        """比较版本号 v1 和 v2。 v1 > v2 返回 1, v1 < v2 返回 -1, 相等返回 0"""
        def parse(v):
            try:
                return [int(x) for x in v.lstrip('v').split('.')]
            except:
                return [0]
            
        try:
            p1 = parse(v1)
            p2 = parse(v2)
            
            # 补齐长度
            max_len = max(len(p1), len(p2))
            p1.extend([0] * (max_len - len(p1)))
            p2.extend([0] * (max_len - len(p2)))
            
            if p1 > p2: return 1
            if p1 < p2: return -1
            return 0
        except:
            return 0

    def open_browser_download(self, url):
        """打开浏览器下载"""
        webbrowser.open(url)

