import os
import re

class StrategyManager:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)
        self.bin_dir = os.path.join(self.zapret_dir, "bin")
        self.lists_dir = os.path.join(self.zapret_dir, "lists")

    def get_game_filter_ports(self):
        flag_file = os.path.join(self.zapret_dir, "utils", "game_filter.enabled")
        if not os.path.exists(flag_file):
            return {"tcp": "12", "udp": "12", "status": "disabled"}
        
        try:
            with open(flag_file, "r", encoding="utf-8") as f:
                mode = f.read().strip().lower()
        except Exception:
            mode = ""

        if mode == "all":
            return {"tcp": "1024-65535", "udp": "1024-65535", "status": "enabled (TCP+UDP)"}
        elif mode == "tcp":
            return {"tcp": "1024-65535", "udp": "12", "status": "enabled (TCP)"}
        else:
            return {"tcp": "12", "udp": "1024-65535", "status": "enabled (UDP)"}

    def parse_strategy_command_args(self, strategy_filename):
        """
        Extracts exact winws.exe arguments from any strategy batch file.
        Replaces variables (%BIN%, %LISTS%, %GameFilterTCP%, %GameFilterUDP%, %~dp0).
        """
        if not strategy_filename:
            strategy_filename = "general.bat"
        if not strategy_filename.lower().endswith(".bat") and not strategy_filename.lower().endswith(".cmd"):
            strategy_filename += ".bat"

        file_path = os.path.join(self.zapret_dir, strategy_filename)
        if not os.path.exists(file_path):
            for f in os.listdir(self.zapret_dir):
                if f.lower() == strategy_filename.lower():
                    file_path = os.path.join(self.zapret_dir, f)
                    break

        if not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return ""

        bin_dir = os.path.join(self.zapret_dir, "bin") + os.sep
        lists_dir = os.path.join(self.zapret_dir, "lists") + os.sep
        ports = self.get_game_filter_ports()
        gf_tcp = ports.get("tcp", "1024-65535")
        gf_udp = ports.get("udp", "1024-65535")

        args_parts = []
        capture = False

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("::") or line.startswith("REM") or line.startswith("echo") or line.startswith("call"):
                continue

            lower_line = line.lower()
            if "winws.exe" in lower_line or "winws2.exe" in lower_line:
                capture = True
                idx = lower_line.find("winws.exe")
                if idx == -1:
                    idx = lower_line.find("winws2.exe")
                    if idx != -1:
                        line = line[idx + len("winws2.exe"):].strip()
                else:
                    line = line[idx + len("winws.exe"):].strip()
                if line.startswith('"'):
                    line = line[1:].strip()

            if capture:
                if line.endswith("^"):
                    line = line[:-1].strip()

                line = line.replace("%BIN%", bin_dir)
                line = line.replace("%LISTS%", lists_dir)
                line = line.replace("%~dp0bin\\", bin_dir)
                line = line.replace("%~dp0lists\\", lists_dir)
                line = line.replace("%~dp0bin/", bin_dir)
                line = line.replace("%~dp0lists/", lists_dir)
                line = line.replace("%~dp0", self.zapret_dir + os.sep)
                line = line.replace("%GameFilterTCP%", gf_tcp)
                line = line.replace("%GameFilterUDP%", gf_udp)
                args_parts.append(line)

        full_args = " ".join(args_parts)
        return full_args.strip()

    def list_strategies(self):
        """Returns a list of strategy dicts: [{'name': 'general.bat', 'display_name': 'General (Standard)', 'file_path': '...', 'description': '...'}]"""
        strategies = []
        if not os.path.exists(self.zapret_dir):
            return strategies

        try:
            entries = os.listdir(self.zapret_dir)
        except Exception:
            entries = []

        for filename in entries:
            filepath = os.path.join(self.zapret_dir, filename)
            if not os.path.isfile(filepath):
                continue
            if not (filename.lower().endswith(".bat") or filename.lower().endswith(".cmd")):
                continue
            if filename.lower().startswith("service") or filename.lower().startswith("test") or filename.lower().startswith("build"):
                continue

            display_name = filename
            for ext in [".bat", ".cmd"]:
                if display_name.lower().endswith(ext):
                    display_name = display_name[:-len(ext)]
                    break

            desc = self._get_strategy_description(filename)
            strategies.append({
                "name": filename,
                "display_name": display_name,
                "file_path": filepath,
                "description": desc
            })

        # Natural sort
        try:
            import ctypes, functools
            StrCmpLogicalW = ctypes.windll.shlwapi.StrCmpLogicalW
            strategies.sort(key=functools.cmp_to_key(lambda a, b: StrCmpLogicalW(a["name"], b["name"])))
        except Exception:
            def natural_sort_key(s):
                parts = re.split(r'(\d+)', s["name"])
                return [int(p) if p.isdigit() else p.lower() for p in parts]
            strategies.sort(key=natural_sort_key)
        return strategies

    def _get_strategy_description(self, filename):
        lower = filename.lower()
        if lower == "general.bat":
            return "Основная универсальная стратегия (MultiSplit + Google/4PDA TLS)"
        elif "fake tls auto" in lower:
            return "Автоматический FAKE TLS (обход блокировок с эмуляцией валидных TLS сессий)"
        elif "simple fake" in lower:
            return "Простой FAKE (подходит для провайдеров со строгим тайм-аутом)"
        elif "alt" in lower:
            return "Альтернативный метод фрагментации пакетов и Fake QUIC/TLS"
        elif "exp" in lower:
            return "Экспериментальная стратегия для сложных провайдеров"
        return "Пользовательский пресет настроек winws"
