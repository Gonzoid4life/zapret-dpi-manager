import os
import sys
import winreg
import subprocess

class AutostartManager:
    TASK_NAME = "ZapretManager"
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    LEGACY_NAMES = ["ZapretDpiManager", "ZapretManager"]

    @classmethod
    def is_autostart_enabled(cls):
        # 1. Check Task Scheduler
        try:
            res = subprocess.run(
                ["schtasks", "/query", "/tn", cls.TASK_NAME],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if res.returncode == 0:
                return True
        except Exception:
            pass

        # 2. Check legacy registry key
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_READ)
            for name in cls.LEGACY_NAMES:
                try:
                    val, _ = winreg.QueryValueEx(key, name)
                    if val:
                        winreg.CloseKey(key)
                        return True
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

        return False

    @classmethod
    def set_autostart(cls, enabled=True, start_minimized=False):
        """
        Creates or deletes a Windows Task Scheduler task with highest privileges (UAC bypass on startup).
        Cleans up any legacy registry Run keys.
        """
        # Always clean up legacy registry keys first
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_PATH, 0, winreg.KEY_SET_VALUE)
            for name in cls.LEGACY_NAMES:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

        if enabled:
            try:
                exe_path = sys.executable
                if getattr(sys, 'frozen', False):
                    cmd = f'"{exe_path}"'
                else:
                    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
                    cmd = f'"{sys.executable}" "{main_py}"'

                if start_minimized:
                    cmd += " --minimized"

                # Task Scheduler command with /rl highest (Run with highest privileges - no UAC prompt on logon)
                create_cmd = [
                    "schtasks", "/create",
                    "/tn", cls.TASK_NAME,
                    "/tr", cmd,
                    "/sc", "onlogon",
                    "/rl", "highest",
                    "/f"
                ]
                res = subprocess.run(
                    create_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if res.returncode == 0:
                    return True, "Автозагрузка через Планировщик Windows успешно настроена (без запросов UAC)"
                else:
                    return False, f"Ошибка Task Scheduler: {res.stderr.strip() or res.stdout.strip()}"
            except Exception as e:
                return False, f"Ошибка создания задачи: {e}"
        else:
            try:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", cls.TASK_NAME, "/f"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return True, "Автозагрузка успешно отключена"
            except Exception as e:
                return False, f"Ошибка удаления задачи: {e}"
