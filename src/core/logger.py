import datetime
import threading
from collections import deque

class AppLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_logger()
            return cls._instance

    def _init_logger(self):
        self._entries = deque(maxlen=500)
        self._listeners = []
        self._mutex = threading.Lock()
        self.info("APP", "Инициализация подсистемы логирования ZapretManager")

    def subscribe(self, callback):
        with self._mutex:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unsubscribe(self, callback):
        with self._mutex:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def log(self, level, category, message):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": now_str,
            "level": level.upper(),
            "category": category.upper(),
            "message": str(message)
        }
        with self._mutex:
            self._entries.append(entry)
            listeners_copy = list(self._listeners)

        for cb in listeners_copy:
            try:
                cb(entry)
            except Exception:
                pass

    def info(self, category, message):
        self.log("INFO", category, message)

    def success(self, category, message):
        self.log("SUCCESS", category, message)

    def warn(self, category, message):
        self.log("WARN", category, message)

    def error(self, category, message):
        self.log("ERROR", category, message)

    def get_entries(self):
        with self._mutex:
            return list(self._entries)

    def get_full_text(self):
        with self._mutex:
            lines = [f"[{e['time']}] [{e['level']}] [{e['category']}] {e['message']}" for e in self._entries]
            return "\n".join(lines)

    def clear(self):
        with self._mutex:
            self._entries.clear()
            listeners_copy = list(self._listeners)
        for cb in listeners_copy:
            try:
                cb(None)
            except Exception:
                pass

# Global singleton helper
logger = AppLogger()
