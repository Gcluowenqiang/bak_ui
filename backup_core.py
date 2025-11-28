import os
import shutil
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def _is_modified(self, src_path, dst_path):
        """
        判断文件是否需要复制
        策略:
        1. 目标文件不存在 -> True
        2. 源文件大小 != 目标文件大小 -> True
        3. 源文件修改时间 > 目标文件修改时间 (允许2秒误差) -> True
        """
        if not os.path.exists(dst_path):
            return True
        
        try:
            src_stat = os.stat(src_path)
            dst_stat = os.stat(dst_path)

            if src_stat.st_size != dst_stat.st_size:
                return True
            
            # 允许 2 秒的时间误差（某些文件系统精度问题）
            if src_stat.st_mtime > dst_stat.st_mtime + 2:
                return True
            
            return False
        except OSError:
            return True

    def backup_generator(self, src_dir, dst_dir):
        """
        执行备份并生成进度信息
        """
        if not os.path.exists(src_dir):
            yield {'type': 'error', 'message': f'源目录不存在: {src_dir}'}
            return

        yield {'type': 'phase', 'phase': 'scanning', 'message': '正在扫描文件...'}
        
        files_to_process = []
        total_bytes = 0
        
        # 1. 扫描阶段
        try:
            for root, dirs, files in os.walk(src_dir):
                if self.stop_flag:
                    break
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, src_dir)
                    try:
                        size = os.path.getsize(src_path)
                        files_to_process.append((rel_path, size))
                        total_bytes += size
                    except OSError as e:
                        logger.warning(f"无法访问文件 {src_path}: {e}")
        except Exception as e:
            yield {'type': 'error', 'message': f'扫描出错: {str(e)}'}
            return

        total_files = len(files_to_process)
        yield {'type': 'scan_result', 'total_files': total_files, 'total_bytes': total_bytes}

        # 2. 复制阶段
        processed_files = 0
        copied_files = 0
        processed_bytes = 0
        start_time = time.time()

        for rel_path, size in files_to_process:
            if self.stop_flag:
                yield {'type': 'info', 'message': '备份已停止'}
                break

            src_path = os.path.join(src_dir, rel_path)
            dst_path = os.path.join(dst_dir, rel_path)
            
            try:
                # 确保目标目录存在
                dst_file_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_file_dir):
                    os.makedirs(dst_file_dir, exist_ok=True)

                if self._is_modified(src_path, dst_path):
                    shutil.copy2(src_path, dst_path) # copy2 保留元数据
                    copied_files += 1
                    action = 'copied'
                else:
                    action = 'skipped'

                processed_files += 1
                processed_bytes += size

                # 计算速率
                elapsed = time.time() - start_time
                speed = processed_bytes / elapsed if elapsed > 0 else 0
                
                # 优化进度上报频率：
                # 1. 文件数很少时 (<=5)，每处理一个都上报
                # 2. 大文件 (>10MB)，每处理一个都上报
                # 3. 普通情况，每 5 个文件上报一次
                if total_files <= 5 or processed_files % 5 == 0 or size > 1024*1024*10: 
                    yield {
                        'type': 'progress',
                        'current_file': rel_path,
                        'processed_files': processed_files,
                        'total_files': total_files,
                        'processed_bytes': processed_bytes,
                        'total_bytes': total_bytes,
                        'speed': speed,
                        'action': action
                    }

            except Exception as e:
                logger.error(f"复制失败 {src_path}: {e}")
                yield {'type': 'log', 'level': 'error', 'message': f"Failed: {rel_path} - {str(e)}"}

        if not self.stop_flag:
            yield {'type': 'complete', 'message': '备份完成', 'stats': {'copied': copied_files, 'total': total_files}}

