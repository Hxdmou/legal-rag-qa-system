"""
部署日志系统（轻量级）
安全原则：异步写入、定时清理、文件大小限制
"""

import time
import os
import threading
import json

class DeployLogger:
    def __init__(self, log_dir="logs", max_file_size_mb=10, max_backup=5):
        self.log_dir = log_dir
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_backup = max_backup
        self._queue = []
        self._writing = False
        self._lock = threading.Lock()

        os.makedirs(log_dir, exist_ok=True)

    def _get_log_filename(self):
        return os.path.join(self.log_dir, f"deploy_{time.strftime('%Y%m%d')}.log")

    def _check_rotate(self, filepath):
        if os.path.exists(filepath) and os.path.getsize(filepath) > self.max_file_size:
            for i in range(self.max_backup - 1, 0, -1):
                old = f"{filepath}.{i}"
                new = f"{filepath}.{i + 1}"
                if os.path.exists(old):
                    os.rename(old, new)
            os.rename(filepath, f"{filepath}.1")
            print(f"[LOG] 日志文件已轮转")

    def log(self, level, message, **kwargs):
        entry = {
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            **kwargs
        }

        with self._lock:
            self._queue.append(entry)

        print(f"[{level}] {message}")

        if len(self._queue) > 10:
            self._flush()

    def info(self, message, **kwargs):
        self.log("INFO", message, **kwargs)

    def warn(self, message, **kwargs):
        self.log("WARN", message, **kwargs)

    def error(self, message, **kwargs):
        self.log("ERROR", message, **kwargs)

    def success(self, message, **kwargs):
        self.log("SUCCESS", message, **kwargs)

    def _flush(self):
        if self._writing:
            return

        with self._lock:
            if not self._queue:
                return
            entries = self._queue[:]
            self._queue = []

        self._writing = True
        try:
            filepath = self._get_log_filename()
            self._check_rotate(filepath)

            with open(filepath, "a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"[LOG] 写入失败: {e}")
        finally:
            self._writing = False

    def close(self):
        self._flush()
        print("[LOG] 日志系统已关闭")

    def get_latest_entries(self, count=10):
        filepath = self._get_log_filename()
        entries = []

        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-count:]
                    for line in lines:
                        try:
                            entries.append(json.loads(line.strip()))
                        except:
                            pass
        except Exception as e:
            print(f"[LOG] 读取日志失败: {e}")

        return entries
