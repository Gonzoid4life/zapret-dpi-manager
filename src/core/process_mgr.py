import os
import sys
import subprocess
import winreg
import time
import shutil
import ctypes
from ctypes import wintypes
from .strategy import StrategyManager

TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260)
    ]

class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD)
    ]

SC_MANAGER_CONNECT = 0x0001
SERVICE_QUERY_STATUS = 0x0004

def get_native_service_status(service_name="zapret"):
    """Instant 0.05ms Win32 SCM status check without spawning cmd.exe or sc.exe."""
    try:
        advapi32 = ctypes.windll.advapi32
        advapi32.OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        advapi32.OpenSCManagerW.restype = wintypes.HANDLE
        advapi32.OpenServiceW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
        advapi32.OpenServiceW.restype = wintypes.HANDLE
        advapi32.QueryServiceStatus.argtypes = [wintypes.HANDLE, ctypes.POINTER(SERVICE_STATUS)]
        advapi32.QueryServiceStatus.restype = wintypes.BOOL
        advapi32.CloseServiceHandle.argtypes = [wintypes.HANDLE]
        advapi32.CloseServiceHandle.restype = wintypes.BOOL

        h_scm = advapi32.OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
        if not h_scm:
            return "NOT_INSTALLED"
        try:
            h_svc = advapi32.OpenServiceW(h_scm, service_name, SERVICE_QUERY_STATUS)
            if not h_svc:
                return "NOT_INSTALLED"
            try:
                status = SERVICE_STATUS()
                if advapi32.QueryServiceStatus(h_svc, ctypes.byref(status)):
                    st = status.dwCurrentState
                    if st == 4:
                        return "RUNNING"
                    elif st == 1:
                        return "STOPPED"
                    elif st == 3:
                        return "STOP_PENDING"
                    elif st == 2:
                        return "START_PENDING"
                return "NOT_INSTALLED"
            finally:
                advapi32.CloseServiceHandle(h_svc)
        finally:
            advapi32.CloseServiceHandle(h_scm)
    except Exception:
        return "NOT_INSTALLED"

def is_process_running_native(process_names):
    """0.1ms Win32 Toolhelp snapshot without cmd.exe or tasklist.exe."""
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32FirstW.restype = wintypes.BOOL
        kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32NextW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not h_snap or h_snap == wintypes.HANDLE(-1).value or h_snap == -1 or h_snap == 0xFFFFFFFF:
            return False
        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if kernel32.Process32FirstW(h_snap, ctypes.byref(pe)):
                targets = [n.lower() for n in process_names]
                while True:
                    exe_name = pe.szExeFile.lower()
                    for target in targets:
                        if target in exe_name:
                            return True
                    if not kernel32.Process32NextW(h_snap, ctypes.byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(h_snap)
    except Exception:
        pass
    return False

class ProcessManager:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)
        self.bin_dir = os.path.join(self.zapret_dir, "bin")
        if os.path.exists(os.path.join(self.bin_dir, "winws2.exe")):
            self.winws_exe = os.path.join(self.bin_dir, "winws2.exe")
        elif os.path.exists(os.path.join(self.zapret_dir, "winws2.exe")):
            self.winws_exe = os.path.join(self.zapret_dir, "winws2.exe")
        elif os.path.exists(os.path.join(self.bin_dir, "winws.exe")):
            self.winws_exe = os.path.join(self.bin_dir, "winws.exe")
        else:
            self.winws_exe = os.path.join(self.zapret_dir, "winws.exe")

        self.strategy_mgr = StrategyManager(self.zapret_dir)
        self.current_process = None

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def is_winws_running(self):
        try:
            if is_process_running_native(["winws.exe", "winws2.exe"]):
                return True
            srv_status = self.get_service_status()
            if srv_status == "RUNNING":
                return True
        except Exception:
            pass
        return False

    def is_service_installed(self):
        status = get_native_service_status("zapret")
        if status != "NOT_INSTALLED":
            return True
        try:
            output = subprocess.check_output('sc query zapret', shell=True, text=True, stderr=subprocess.DEVNULL, timeout=0.4, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
            return "SERVICE_NAME: zapret" in output or "zapret" in output.lower()
        except Exception:
            return False

    def get_service_status(self):
        """Returns 'RUNNING', 'STOPPED', or 'NOT_INSTALLED' in 0.05ms"""
        status = get_native_service_status("zapret")
        if status != "NOT_INSTALLED":
            return status
        # Fallback to sc query only if native API returns NOT_INSTALLED
        try:
            output = subprocess.check_output('sc query zapret', shell=True, text=True, stderr=subprocess.DEVNULL, timeout=0.4, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
            if "STATE" in output or "СОСТОЯНИЕ" in output:
                if "RUNNING" in output or "РАБОТАЕТ" in output or " 4 " in output:
                    return "RUNNING"
                elif "STOPPED" in output or "ОСТАНОВЛЕНА" in output or " 1 " in output:
                    return "STOPPED"
                elif "STOP_PENDING" in output or " 3 " in output:
                    return "STOP_PENDING"
            return "NOT_INSTALLED"
        except Exception:
            return "NOT_INSTALLED"

    def get_installed_service_strategy(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Services\zapret", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "zapret-discord-youtube")
            winreg.CloseKey(key)
            if val:
                val_str = str(val).strip()
                if not val_str.lower().endswith(".bat"):
                    val_str += ".bat"
                return val_str
        except Exception:
            pass
        return None

    def enable_tcp_timestamps(self):
        try:
            subprocess.run('netsh interface tcp set global timestamps=enabled', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def stop_all(self):
        """Stops any running winws.exe, zapret service, and cleans up WinDivert."""
        # 1. Kill winws/winws2 processes immediately so socket & pipe handles are released
        try:
            subprocess.run('taskkill /IM winws.exe /F /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.5, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /IM winws2.exe /F /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.5, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        # 2. Stop zapret service if running
        try:
            subprocess.run('net stop zapret', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=6.0, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('sc delete zapret', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3.0, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        # 3. Clean up WinDivert
        for drv in ['WinDivert', 'WinDivert14']:
            try:
                subprocess.run(f'net stop {drv}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4.0, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(f'sc delete {drv}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

        self.current_process = None

        # Poll up to 2.5 seconds to confirm process is dead
        for _ in range(25):
            if not self.is_winws_running():
                break
            time.sleep(0.1)

        return not self.is_winws_running()

    def start_as_process(self, strategy_filename):
        """Starts winws.exe directly in the background with arguments parsed from strategy file."""
        self.stop_all()
        self.enable_tcp_timestamps()

        args = self.strategy_mgr.parse_strategy_command_args(strategy_filename)
        exe_path = self.winws_exe
        if "winws2" in strategy_filename.lower() or os.path.exists(os.path.join(self.bin_dir, "winws2.exe")):
            if os.path.exists(os.path.join(self.bin_dir, "winws2.exe")):
                exe_path = os.path.join(self.bin_dir, "winws2.exe")
            elif os.path.exists(os.path.join(self.zapret_dir, "winws2.exe")):
                exe_path = os.path.join(self.zapret_dir, "winws2.exe")

        cwd_dir = self.bin_dir if os.path.exists(self.bin_dir) else self.zapret_dir

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            self.current_process = subprocess.Popen(
                f'"{exe_path}" {args}',
                cwd=cwd_dir,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
            time.sleep(0.4)
            if self.is_winws_running():
                return True
        except Exception:
            pass

        try:
            res = ctypes.windll.shell32.ShellExecuteW(None, "open", exe_path, args, cwd_dir, 0)
            time.sleep(0.4)
            return self.is_winws_running() or (res > 32)
        except Exception as e:
            print(f"Failed to start winws: {e}")
            return False

    def set_ipset_mode(self, mode="any"):
        lists_dir = os.path.join(self.zapret_dir, "lists")
        ipset_file = os.path.join(lists_dir, "ipset-all.txt")
        backup_file = os.path.join(lists_dir, "ipset-all.test-backup.txt")

        try:
            if mode == "any":
                if os.path.exists(ipset_file) and not os.path.exists(backup_file):
                    shutil.copy2(ipset_file, backup_file)
                # Write 0.0.0.0/0 to intercept and benchmark all target IPs!
                with open(ipset_file, "w", encoding="utf-8") as f:
                    f.write("0.0.0.0/0\n::/0\n")
            elif mode in ["restore", "loaded"] or mode != "any":
                if os.path.exists(backup_file):
                    if os.path.exists(ipset_file):
                        try:
                            os.remove(ipset_file)
                        except Exception:
                            pass
                    shutil.move(backup_file, ipset_file)
        except Exception as e:
            print(f"Error managing ipset mode: {e}")

    def start_strategy_for_test(self, strategy_filename):
        """
        Launches winws.exe directly with parsed strategy arguments in 100% hidden mode.
        """
        try:
            subprocess.run('net stop zapret', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /F /IM winws.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /F /IM winws2.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        time.sleep(0.1)
        self.enable_tcp_timestamps()

        args = self.strategy_mgr.parse_strategy_command_args(strategy_filename)
        exe_path = self.winws_exe
        if "winws2" in strategy_filename.lower() or os.path.exists(os.path.join(self.bin_dir, "winws2.exe")):
            if os.path.exists(os.path.join(self.bin_dir, "winws2.exe")):
                exe_path = os.path.join(self.bin_dir, "winws2.exe")

        cwd_dir = self.bin_dir if os.path.exists(self.bin_dir) else self.zapret_dir

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            self.current_process = subprocess.Popen(
                f'"{exe_path}" {args}',
                cwd=cwd_dir,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
            time.sleep(0.3)
            if self.is_winws_running():
                return True
        except Exception:
            pass

        try:
            res = ctypes.windll.shell32.ShellExecuteW(None, "open", exe_path, args, cwd_dir, 0)
            time.sleep(0.3)
            return self.is_winws_running() or (res > 32)
        except Exception as e:
            print("Failed to start winws for test:", e)
            return False

    def stop_strategy_after_test(self):
        """Flowseal standard cleanup between test configs."""
        try:
            subprocess.run('taskkill /F /IM winws.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /F /IM winws2.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
        if self.current_process:
            try:
                self.current_process.terminate()
            except Exception:
                pass
            self.current_process = None

    def start_as_service(self, strategy_filename, autostart=True):
        """Installs and starts zapret as a Windows Service."""
        self.stop_all()
        self.enable_tcp_timestamps()

        args = self.strategy_mgr.parse_strategy_command_args(strategy_filename)
        binpath = f'\\"{self.winws_exe}\\" {args}'
        start_type = "auto" if autostart else "demand"

        # Create service
        create_cmd = f'sc create zapret binPath= "{binpath}" DisplayName= "zapret" start= {start_type}'
        subprocess.run(create_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        # Set description
        subprocess.run('sc description zapret "Zapret DPI bypass software"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

        # Store strategy name in registry
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Services\zapret")
            strategy_clean = strategy_filename[:-4] if strategy_filename.endswith(".bat") else strategy_filename
            winreg.SetValueEx(key, "zapret-discord-youtube", 0, winreg.REG_SZ, strategy_clean)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to write registry key: {e}")

        # Start service
        subprocess.run('sc start zapret', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(0.6)
        return self.get_service_status() == "RUNNING" or self.is_winws_running()

    def set_autostart(self, enabled=True, strategy_filename="general.bat", mode="service"):
        """Configures autostart via Service start=auto or Registry Run key."""
        if mode == "service":
            if self.is_service_installed():
                start_type = "auto" if enabled else "demand"
                subprocess.run(f'sc config zapret start= {start_type}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Also maintain Registry Run key for standalone mode if chosen
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enabled and mode == "process":
                app_exe = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                winreg.SetValueEx(key, "ZapretManager", 0, winreg.REG_SZ, f'"{app_exe}" --minimized')
            else:
                try:
                    winreg.DeleteValue(key, "ZapretManager")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass
