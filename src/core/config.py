import json
import os
import sys

DEFAULT_TEST_TARGETS = [
    {"name": "Discord Main", "url": "https://discord.com", "category": "discord"},
    {"name": "Discord Gateway", "url": "https://gateway.discord.gg", "category": "discord"},
    {"name": "Discord CDN", "url": "https://cdn.discordapp.com", "category": "discord"},
    {"name": "Discord Updates", "url": "https://updates.discord.com", "category": "discord"},
    {"name": "YouTube Web", "url": "https://www.youtube.com", "category": "youtube"},
    {"name": "YouTube Short", "url": "https://youtu.be", "category": "youtube"},
    {"name": "YouTube Image", "url": "https://i.ytimg.com", "category": "youtube"},
    {"name": "YouTube Video Redirect", "url": "https://redirector.googlevideo.com", "category": "youtube"},
    {"name": "Google Main", "url": "https://www.google.com", "category": "general"},
    {"name": "Google Gstatic", "url": "https://www.gstatic.com", "category": "general"},
    {"name": "Cloudflare Web", "url": "https://www.cloudflare.com", "category": "general"},
    {"name": "Cloudflare CDN", "url": "https://cdnjs.cloudflare.com", "category": "general"},
]

class Config:
    @staticmethod
    def get_device_id():
        """
        Generates a unique, deterministic fingerprint of the local Windows environment.
        Uses MachineGuid from registry combined with username and computername.
        """
        guid = ""
        try:
            import winreg
            k = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )
            guid, _ = winreg.QueryValueEx(k, "MachineGuid")
            winreg.CloseKey(k)
        except Exception:
            pass

        comp = os.environ.get("COMPUTERNAME", "").strip().lower()
        user = os.environ.get("USERNAME", "").strip().lower()
        raw = f"{guid}_{comp}_{user}" if guid else f"{comp}_{user}"
        import hashlib
        return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

    def __init__(self, base_dir=None):
        if base_dir and os.path.exists(base_dir):
            self.base_dir = os.path.abspath(base_dir)
        else:
            if getattr(sys, 'frozen', False):
                self.base_dir = os.path.dirname(sys.executable)
            else:
                self.base_dir = os.path.abspath(os.getcwd())
                
        self.config_path = os.path.join(self.base_dir, "manager_config.json")
        self.is_new_pc = False
        self.data = {
            "device_id": "",
            "zapret_dir": self.base_dir,
            "active_strategy": "",
            "run_mode": "service",  # "service" or "process"
            "autostart": False,
            "theme": "dark",
            "test_targets": DEFAULT_TEST_TARGETS,
            "strategy_ratings": {},
            "last_autotune_time": "",
            "last_autotune_results": [],
            "last_check_update": 0,
            "auto_failover": True,
            "minimize_to_tray": True,
            "start_minimized": False
        }
        self.load()

    def load(self):
        current_device_id = self.get_device_id()
        is_new_pc = False

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    
                    saved_device_id = loaded.get("device_id")
                    saved_zapret_dir = loaded.get("zapret_dir", "")
                    current_user = os.environ.get("USERNAME", "").strip().lower()

                    # Check if running on a new/different PC or different Windows profile
                    if saved_device_id:
                        if saved_device_id != current_device_id:
                            is_new_pc = True
                    else:
                        # Legacy config: check if directory references another user
                        if saved_zapret_dir:
                            path_lower = saved_zapret_dir.lower()
                            if f"users\\{current_user}" not in path_lower and f"users/{current_user}" not in path_lower:
                                is_new_pc = True

                    if is_new_pc:
                        # Clear machine-specific and test data from previous user
                        loaded["active_strategy"] = ""
                        loaded["strategy_ratings"] = {}
                        loaded["last_autotune_time"] = ""
                        loaded["last_autotune_results"] = []
                        loaded["autostart"] = False

                    self.data.update(loaded)
            except Exception as e:
                print(f"Error loading config: {e}")

        self.data["device_id"] = current_device_id
        self.is_new_pc = is_new_pc

        # Always enforce local zapret_dir if running portable in a new location
        if is_new_pc or not self.data.get("zapret_dir") or not os.path.exists(self.data.get("zapret_dir")):
            self.data["zapret_dir"] = self.base_dir
        elif os.path.exists(os.path.join(self.base_dir, "bin")) or os.path.exists(os.path.join(self.base_dir, "lists")):
            self.data["zapret_dir"] = self.base_dir

        # Always synchronize test_targets to latest Flowseal endpoints
        if len(self.data.get("test_targets", [])) != len(DEFAULT_TEST_TARGETS):
            self.data["test_targets"] = DEFAULT_TEST_TARGETS

        self.save()

    def clean_for_export(self):
        """
        Cleans machine-specific test history and unselects active strategy
        so the folder can be cleanly zipped and sent to a friend.
        """
        self.data["device_id"] = ""
        self.data["active_strategy"] = ""
        self.data["strategy_ratings"] = {}
        self.data["last_autotune_time"] = ""
        self.data["last_autotune_results"] = []
        self.data["autostart"] = False
        self.save()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
