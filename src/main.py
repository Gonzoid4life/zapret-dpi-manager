import os
import sys
import ctypes
import argparse
import customtkinter as ctk

# Ensure proper import path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.gui.app import ZapretApp
from ctypes import wintypes

MUTEX_NAME = "Global\\ZapretManager_SingleInstance_Mutex_98a72b"
_instance_mutex = None

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def ensure_single_instance():
    global _instance_mutex
    ERROR_ALREADY_EXISTS = 183
    ERROR_ACCESS_DENIED = 5
    
    _instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_err = ctypes.windll.kernel32.GetLastError()
    
    if last_err in (ERROR_ALREADY_EXISTS, ERROR_ACCESS_DENIED) or (_instance_mutex == 0 and last_err == ERROR_ACCESS_DENIED):
        # Another instance is already running. Find its window and bring to front.
        user32 = ctypes.windll.user32

        def enum_window_proc(hwnd, lParam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if "Zapret DPI Manager" in title:
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.ShowWindow(hwnd, 5)  # SW_SHOW
                    user32.SetForegroundWindow(hwnd)
                    return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_window_proc), 0)
        sys.exit(0)

def run_as_admin():
    if not is_admin():
        # Re-run with UAC admin prompt
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        exe = sys.executable
        if getattr(sys, 'frozen', False):
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, f'"{__file__}" {params}', None, 1)
        sys.exit(0)

def main():
    ensure_single_instance()
    run_as_admin()

    parser = argparse.ArgumentParser(description="Zapret DPI Manager for Windows 11")
    parser.add_argument("--zapret-dir", help="Path to zapret directory", default=None)
    parser.add_argument("--minimized", action="store_true", help="Start minimized")
    args = parser.parse_args()

    # Determine zapret directory dynamically from executable location
    zapret_dir = args.zapret_dir
    if not zapret_dir:
        if getattr(sys, 'frozen', False):
            zapret_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            zapret_dir = os.path.abspath(os.getcwd())

    root = ctk.CTk()
    ZapretApp(root, zapret_dir=zapret_dir)

    if args.minimized:
        root.iconify()

    root.mainloop()

if __name__ == "__main__":
    main()
