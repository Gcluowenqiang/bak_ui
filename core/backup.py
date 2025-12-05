import os
import shutil
import time
import stat
from core.logger import Logger

class BackupManager:
    def __init__(self):
        self.stop_flag = False
        self.logger = Logger()

    def stop(self):
        self.stop_flag = True

    def _remove_file_safe(self, file_path, max_retries=3):
        """
        安全删除文件，处理 Windows 权限问题
        返回: (success, error_message)
        """
        import time as time_module
        
        for attempt in range(max_retries):
            try:
                # 尝试移除只读属性
                if os.path.exists(file_path):
                    try:
                        os.chmod(file_path, stat.S_IWRITE)
                    except:
                        pass  # 如果无法修改属性，继续尝试删除
                    
                    # 尝试删除
                    os.remove(file_path)
                    return True, None
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # 等待一小段时间后重试（文件可能正在被释放）
                    time_module.sleep(0.5)
                    continue
                else:
                    return False, f"权限拒绝 (可能被其他程序占用): {str(e)}"
            except Exception as e:
                return False, str(e)
        
        return False, "删除失败，已达到最大重试次数"

    def _remove_dir_safe(self, dir_path, max_retries=3):
        """
        安全删除目录，处理 Windows 权限问题
        返回: (success, error_message)
        """
        import time as time_module
        
        for attempt in range(max_retries):
            try:
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    # 尝试移除只读属性（递归）
                    def make_writable(path):
                        try:
                            os.chmod(path, stat.S_IWRITE)
                        except:
                            pass
                    
                    # 先尝试使所有文件可写
                    for root, dirs, files in os.walk(dir_path):
                        for d in dirs:
                            make_writable(os.path.join(root, d))
                        for f in files:
                            make_writable(os.path.join(root, f))
                    
                    # 删除目录
                    shutil.rmtree(dir_path)
                    return True, None
            except PermissionError as e:
                if attempt < max_retries - 1:
                    time_module.sleep(0.5)
                    continue
                else:
                    return False, f"权限拒绝 (可能被其他程序占用): {str(e)}"
            except Exception as e:
                return False, str(e)
        
        return False, "删除失败，已达到最大重试次数"

    def _is_modified(self, src_path, dst_path):
        """
        判断文件是否需要复制
        """
        if not os.path.exists(dst_path):
            return True
        
        try:
            src_stat = os.stat(src_path)
            dst_stat = os.stat(dst_path)

            if src_stat.st_size != dst_stat.st_size:
                return True
            
            # 允许 2 秒的时间误差
            if src_stat.st_mtime > dst_stat.st_mtime + 2:
                return True
            
            return False
        except OSError:
            return True

    def start_backup(self, src_dir, dst_dir, progress_callback=None, sync_mode=False):
        """
        执行备份
        progress_callback: function(current, total, message)
        sync_mode: True=同步备份(完全一致), False=增量备份(仅复制变更)
        """
        if sync_mode:
            self._start_sync_backup(src_dir, dst_dir, progress_callback)
        else:
            self._start_incremental_backup(src_dir, dst_dir, progress_callback)

    def _start_incremental_backup(self, src_dir, dst_dir, progress_callback=None):
        """
        增量备份：仅复制变更的文件
        """
        self.stop_flag = False
        
        if not os.path.exists(src_dir):
            self.logger.error(f"源目录不存在: {src_dir}")
            if progress_callback:
                progress_callback(0, 0, f"源目录不存在: {src_dir}")
            return

        self.logger.info(f"开始增量备份扫描: {src_dir}")
        if progress_callback:
            progress_callback(0, 0, "正在扫描文件...")
        
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
                        self.logger.warning(f"无法访问文件 {src_path}: {e}")
        except Exception as e:
            self.logger.error(f"扫描出错: {str(e)}")
            return

        total_files = len(files_to_process)
        self.logger.info(f"扫描完成: {total_files} 个文件, 共 {total_bytes} 字节")
        
        # 2. 复制阶段
        processed_files = 0
        copied_files = 0
        processed_bytes = 0
        start_time = time.time()
        
        if total_files == 0:
             if progress_callback:
                progress_callback(100, 100, "目录为空，无需备份")
             return

        for rel_path, size in files_to_process:
            if self.stop_flag:
                self.logger.info("备份已停止")
                if progress_callback:
                    progress_callback(processed_files, total_files, "备份已停止")
                break

            src_path = os.path.join(src_dir, rel_path)
            dst_path = os.path.join(dst_dir, rel_path)
            
            try:
                dst_file_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_file_dir):
                    os.makedirs(dst_file_dir, exist_ok=True)

                action = "skipped"
                if self._is_modified(src_path, dst_path):
                    shutil.copy2(src_path, dst_path)
                    copied_files += 1
                    action = "copied"

                processed_files += 1
                processed_bytes += size

                # 计算进度
                percent = (processed_files / total_files) * 100
                
                # 限制回调频率
                if total_files <= 10 or processed_files % 5 == 0 or size > 1024*1024*10 or processed_files == total_files:
                    if progress_callback:
                        msg = f"[{processed_files}/{total_files}] {action}: {rel_path}"
                        progress_callback(percent, total_files, msg)

            except Exception as e:
                self.logger.error(f"复制失败 {src_path}: {e}")

        if not self.stop_flag:
            duration = time.time() - start_time
            self.logger.info(f"增量备份完成! 用时: {duration:.2f}s, 复制: {copied_files}, 总计: {total_files}")
            if progress_callback:
                progress_callback(100, total_files, "增量备份完成")

    def _start_sync_backup(self, src_dir, dst_dir, progress_callback=None):
        """
        同步备份：确保目标目录与源目录完全一致
        1. 复制/更新源目录中的所有文件
        2. 删除目标目录中源目录不存在的文件和目录
        """
        self.stop_flag = False
        
        if not os.path.exists(src_dir):
            self.logger.error(f"源目录不存在: {src_dir}")
            if progress_callback:
                progress_callback(0, 0, f"源目录不存在: {src_dir}")
            return

        self.logger.info(f"开始同步备份扫描: {src_dir}")
        if progress_callback:
            progress_callback(0, 0, "正在扫描源目录...")
        
        # 1. 扫描源目录（包括空目录）
        src_files = set()
        src_dirs = set()
        files_to_process = []
        total_bytes = 0
        
        try:
            # 使用 os.walk 扫描文件和目录
            for root, dirs, files in os.walk(src_dir):
                if self.stop_flag:
                    break
                rel_root = os.path.relpath(root, src_dir)
                if rel_root != '.':
                    src_dirs.add(rel_root)
                
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, src_dir)
                    src_files.add(rel_path)
                    try:
                        size = os.path.getsize(src_path)
                        files_to_process.append((rel_path, size))
                        total_bytes += size
                    except OSError as e:
                        self.logger.warning(f"无法访问文件 {src_path}: {e}")
            
            
        except Exception as e:
            self.logger.error(f"扫描源目录出错: {str(e)}")
            return

        # 2. 扫描目标目录（如果存在）
        dst_files = set()
        dst_dirs = set()
        if os.path.exists(dst_dir):
            if progress_callback:
                progress_callback(0, 0, "正在扫描目标目录...")
            try:
                for root, dirs, files in os.walk(dst_dir):
                    if self.stop_flag:
                        break
                    rel_root = os.path.relpath(root, dst_dir)
                    if rel_root != '.':
                        dst_dirs.add(rel_root)
                    
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), dst_dir)
                        dst_files.add(rel_path)
            except Exception as e:
                self.logger.warning(f"扫描目标目录出错: {str(e)}")

        # 3. 计算需要删除的文件和目录
        files_to_delete = dst_files - src_files
        
        # 对于目录删除，需要确保删除所有不在源目录中的目录
        # 构建源目录的所有路径（包括所有父路径）
        src_all_paths = set()
        src_all_paths.add('.')  # 根目录
        for rel_dir in src_dirs:
            src_all_paths.add(rel_dir)
            # 添加所有父路径
            parts = rel_dir.split(os.sep)
            for i in range(1, len(parts)):
                parent = os.sep.join(parts[:i])
                src_all_paths.add(parent)
        
        # 对于文件，也要添加其父目录路径
        for rel_file in src_files:
            parent_dir = os.path.dirname(rel_file)
            if parent_dir and parent_dir != '.':
                src_all_paths.add(parent_dir)
                # 添加所有父路径
                parts = parent_dir.split(os.sep)
                for i in range(1, len(parts)):
                    parent = os.sep.join(parts[:i])
                    src_all_paths.add(parent)
        
        # 计算需要删除的目录：目标目录中不在源目录路径集合中的目录
        dirs_to_delete = []
        for dst_dir_path in dst_dirs:
            if dst_dir_path not in src_all_paths:
                dirs_to_delete.append(dst_dir_path)
        
        # 计算需要创建的目录（源目录中存在但目标目录中不存在的空目录）
        dirs_to_create = []
        for src_dir_path in src_dirs:
            dst_dir_path = os.path.join(dst_dir, src_dir_path)
            if not os.path.exists(dst_dir_path):
                dirs_to_create.append(src_dir_path)
        
        total_ops = len(files_to_process) + len(files_to_delete) + len(dirs_to_delete) + len(dirs_to_create)
        self.logger.info(f"扫描完成: 源文件 {len(files_to_process)} 个, 源目录 {len(src_dirs)} 个, 需删除文件 {len(files_to_delete)} 个, 需删除目录 {len(dirs_to_delete)} 个, 需创建目录 {len(dirs_to_create)} 个")
        
        if total_ops == 0:
            if progress_callback:
                progress_callback(100, 100, "目录已同步，无需操作")
            return

        # 4. 执行操作
        processed_ops = 0
        copied_files = 0
        deleted_files = 0
        deleted_dirs = 0
        start_time = time.time()

        # 4.1 删除多余的文件
        failed_deletes = []
        for rel_path in sorted(files_to_delete, reverse=True):
            if self.stop_flag:
                break
            dst_path = os.path.join(dst_dir, rel_path)
            success, error_msg = self._remove_file_safe(dst_path)
            if success:
                deleted_files += 1
                self.logger.info(f"删除文件: {rel_path}")
            else:
                failed_deletes.append((rel_path, error_msg))
                self.logger.warning(f"删除文件失败 {rel_path}: {error_msg}")
            
            processed_ops += 1
            if progress_callback:
                percent = (processed_ops / total_ops) * 100
                status = "删除" if success else "删除失败"
                msg = f"[{processed_ops}/{total_ops}] {status}: {rel_path}"
                progress_callback(percent, total_ops, msg)

        # 4.2 删除多余的目录（从深层到浅层，使用 rmtree 确保完全删除）
        failed_dir_deletes = []
        for rel_dir in sorted(dirs_to_delete, key=lambda x: x.count(os.sep), reverse=True):
            if self.stop_flag:
                break
            dst_path = os.path.join(dst_dir, rel_dir)
            success, error_msg = self._remove_dir_safe(dst_path)
            if success:
                deleted_dirs += 1
                self.logger.info(f"删除目录: {rel_dir}")
            else:
                failed_dir_deletes.append((rel_dir, error_msg))
                self.logger.warning(f"删除目录失败 {rel_dir}: {error_msg}")
            
            processed_ops += 1
            if progress_callback:
                percent = (processed_ops / total_ops) * 100
                status = "删除目录" if success else "删除目录失败"
                msg = f"[{processed_ops}/{total_ops}] {status}: {rel_dir}"
                progress_callback(percent, total_ops, msg)

        # 4.3 创建所有源目录（包括空目录）
        # 确保所有源目录都被创建，即使它们是空的
        created_dirs = 0
        for rel_dir in dirs_to_create:
            if self.stop_flag:
                break
            dst_dir_path = os.path.join(dst_dir, rel_dir)
            try:
                os.makedirs(dst_dir_path, exist_ok=True)
                created_dirs += 1
                self.logger.info(f"创建目录: {rel_dir}")
            except Exception as e:
                self.logger.warning(f"创建目录失败 {rel_dir}: {e}")
            
            processed_ops += 1
            if progress_callback:
                percent = (processed_ops / total_ops) * 100
                msg = f"[{processed_ops}/{total_ops}] 创建目录: {rel_dir}"
                progress_callback(percent, total_ops, msg)

        # 4.4 复制/更新文件
        for rel_path, size in files_to_process:
            if self.stop_flag:
                self.logger.info("备份已停止")
                if progress_callback:
                    progress_callback(processed_ops, total_ops, "备份已停止")
                break

            src_path = os.path.join(src_dir, rel_path)
            dst_path = os.path.join(dst_dir, rel_path)
            
            try:
                dst_file_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_file_dir):
                    os.makedirs(dst_file_dir, exist_ok=True)

                action = "skipped"
                if self._is_modified(src_path, dst_path):
                    shutil.copy2(src_path, dst_path)
                    copied_files += 1
                    action = "updated"
                else:
                    action = "synced"

                processed_ops += 1

                # 计算进度
                percent = (processed_ops / total_ops) * 100
                
                # 限制回调频率
                if total_ops <= 10 or processed_ops % 5 == 0 or size > 1024*1024*10 or processed_ops == total_ops:
                    if progress_callback:
                        msg = f"[{processed_ops}/{total_ops}] {action}: {rel_path}"
                        progress_callback(percent, total_ops, msg)

            except Exception as e:
                self.logger.error(f"复制失败 {src_path}: {e}")

        if not self.stop_flag:
            duration = time.time() - start_time
            summary = f"同步备份完成! 用时: {duration:.2f}s, 更新: {copied_files}, 创建目录: {created_dirs}, 删除文件: {deleted_files}, 删除目录: {deleted_dirs}"
            if failed_deletes or failed_dir_deletes:
                summary += f"\n警告: {len(failed_deletes)} 个文件删除失败, {len(failed_dir_deletes)} 个目录删除失败 (可能被其他程序占用)"
                self.logger.warning(summary)
            else:
                self.logger.info(summary)
            
            if progress_callback:
                msg = f"同步备份完成 (更新 {copied_files}, 创建 {created_dirs} 目录, 删除 {deleted_files} 文件, {deleted_dirs} 目录)"
                if failed_deletes or failed_dir_deletes:
                    msg += f" - {len(failed_deletes) + len(failed_dir_deletes)} 项删除失败"
                progress_callback(100, total_ops, msg)

