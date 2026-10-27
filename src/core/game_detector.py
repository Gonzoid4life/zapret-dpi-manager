import os
import ctypes
from ctypes import wintypes
from .logger import logger

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

KNOWN_GAMES = {
    "cs2.exe": "Counter-Strike 2",
    "csgo.exe": "CS:GO",
    "dota2.exe": "Dota 2",
    "valorant-win64-shipping.exe": "Valorant",
    "valorant.exe": "Valorant",
    "r5apex.exe": "Apex Legends",
    "rainbowsix.exe": "Rainbow Six Siege",
    "rainbowsix_vulkan.exe": "Rainbow Six Siege",
    "aces.exe": "War Thunder",
    "genshinimpact.exe": "Genshin Impact",
    "starrail.exe": "Honkai: Star Rail",
    "fortniteclient-win64-shipping.exe": "Fortnite",
    "tslgame.exe": "PUBG: Battlegrounds",
    "overwatch.exe": "Overwatch 2",
    "leagueclient.exe": "League of Legends",
    "league of legends.exe": "League of Legends",
    "gta5.exe": "GTA V / Online",
    "worldoftanks.exe": "World of Tanks",
    "wot.exe": "World of Tanks",
    "deadbydaylight-win64-shipping.exe": "Dead by Daylight",
    "rustclient.exe": "Rust",
    "helldivers2.exe": "Helldivers 2"
}

class GameDetector:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)
        self.last_detected_game = None

    def scan_for_active_game(self):
        """
        Scans all running processes via WinAPI Toolhelp in 0.1ms.
        Returns: (True, game_display_name, exe_name) or (False, None, None)
        """
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
                return False, None, None

            try:
                pe = PROCESSENTRY32W()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                if kernel32.Process32FirstW(h_snap, ctypes.byref(pe)):
                    while True:
                        exe_lower = pe.szExeFile.lower()
                        if exe_lower in KNOWN_GAMES:
                            disp = KNOWN_GAMES[exe_lower]
                            return True, disp, exe_lower
                        if not kernel32.Process32NextW(h_snap, ctypes.byref(pe)):
                            break
            finally:
                kernel32.CloseHandle(h_snap)
        except Exception:
            pass
        return False, None, None

    def apply_game_mode_protection(self, enabled=True):
        """
        When game is detected and auto-game mode is on, ensures utils/game_filter.enabled exists
        so WinDivert does not intercept high UDP game traffic.
        """
        utils_dir = os.path.join(self.zapret_dir, "utils")
        flag_file = os.path.join(utils_dir, "game_filter.enabled")
        try:
            if enabled:
                os.makedirs(utils_dir, exist_ok=True)
                if not os.path.exists(flag_file):
                    with open(flag_file, "w", encoding="utf-8") as f:
                        f.write("1\n")
                    logger.info("GAME", "Активирован фильтр игровых портов utils/game_filter.enabled")
            else:
                if os.path.exists(flag_file):
                    try:
                        os.remove(flag_file)
                        logger.info("GAME", "Фильтр игровых портов деактивирован")
                    except Exception:
                        pass
        except Exception as e:
            logger.error("GAME", f"Ошибка управления game_filter: {e}")
