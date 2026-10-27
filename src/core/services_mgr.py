import os
import re
import urllib.request
import subprocess
from .service_data import SERVICE_CATEGORIES

class ServicesManager:
    def __init__(self, zapret_dir=None):
        self.zapret_dir = zapret_dir
        self.hosts_path = os.path.expandvars(r"%SystemRoot%\System32\drivers\etc\hosts")
        self.remote_url = "https://raw.githubusercontent.com/mashakulina/Zapret-DPI-for-Steam-Deck/main/core/service_data.py"

    def get_all_categories(self):
        return {
            "Искусственный интеллект": ["chatgpt", "gemini", "claude", "copilot", "grok"],
            "Соцсети": ["telegram", "instagram", "facebook", "tiktok"],
            "Музыка": ["spotify", "soundcloud"],
            "Торренты": ["rutracker", "rutor"],
            "Игры и Стриминг": ["discord", "twitch"],
            "Работа": ["notion"]
        }

    def get_service_mapping(self):
        import json
        if self.zapret_dir:
            custom_path = os.path.join(self.zapret_dir, "config", "service_data.json")
            if os.path.exists(custom_path):
                try:
                    with open(custom_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return SERVICE_CATEGORIES

    def get_enabled_services(self):
        """Parse hosts file and return a set of currently enabled service keys."""
        enabled = set()
        if not os.path.exists(self.hosts_path):
            return enabled

        try:
            with open(self.hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            mapping = self.get_service_mapping()
            for srv_key, domains in mapping.items():
                # We check if a unique marker exists for this service
                marker = f"# === ZAPRET SERVICE: {srv_key.upper()} ==="
                if marker in content:
                    enabled.add(srv_key)
        except Exception:
            pass
        return enabled

    def apply_services(self, selected_services):
        """
        Applies selected services to the hosts file.
        selected_services is a list/set of service keys (e.g. ['gemini', 'chatgpt'])
        """
        try:
            mapping = self.get_service_mapping()
            existing_content = ""
            if os.path.exists(self.hosts_path):
                with open(self.hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                    existing_content = f.read()

            # First, strip out all previous Zapret service blocks
            # We use regex to remove anything between markers
            pattern = re.compile(r"# === ZAPRET SERVICE: [A-Z0-9_]+ ===.*?# === END ZAPRET SERVICE ===\n?", re.DOTALL)
            clean_content = pattern.sub("", existing_content)

            # Ensure ends with newline
            if clean_content and not clean_content.endswith("\n"):
                clean_content += "\n"

            # Append newly selected services
            for srv_key in selected_services:
                if srv_key in mapping:
                    block = f"# === ZAPRET SERVICE: {srv_key.upper()} ===\n"
                    for domain, ip in mapping[srv_key].items():
                        block += f"{ip} {domain}\n"
                    block += "# === END ZAPRET SERVICE ===\n"
                    clean_content += block

            with open(self.hosts_path, "w", encoding="utf-8") as f:
                f.write(clean_content)

            try:
                subprocess.run(["ipconfig", "/flushdns"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass
                
            return True, "Успешно: записи обновлены в файле hosts, кэш DNS сброшен. Перезапустите браузер для применения."
        except PermissionError:
            return False, "Ошибка: Недостаточно прав для записи в файл hosts. Запустите программу от имени Администратора."
        except Exception as e:
            return False, f"Ошибка: {e}"

    def update_database(self):
        """Downloads latest service_data.py from GitHub and injects Antigravity."""
        urls = [
            self.remote_url,
            "https://gh-proxy.com/" + self.remote_url,
            "https://cdn.jsdelivr.net/gh/mashakulina/Zapret-DPI-for-Steam-Deck@main/core/service_data.py",
            "https://ghproxy.net/" + self.remote_url
        ]
        
        data = None
        for url in urls:
            try:
                # Add headers to impersonate browser to avoid basic blocks
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                data = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
                if "SERVICE_CATEGORIES =" in data:
                    break
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                continue
                
        if not data or "SERVICE_CATEGORIES =" not in data:
            return False, "Не удалось загрузить базу ни с одного из зеркал (ошибка сети/таймаут)."
            
        try:
                # Внедряем Antigravity сразу после объявления словаря
                antigravity_block = '''
    "antigravity": {
        "alkalimakersuite-pa.clients6.google.com": "103.27.157.38",
        "generativelanguage.googleapis.com": "103.27.157.38",
        "aistudio.google.com": "103.27.157.38",
        "gemini.google.com": "103.27.157.38"
    },'''
                data = data.replace("SERVICE_CATEGORIES = {", f"SERVICE_CATEGORIES = {{{antigravity_block}")
                
                # Sanitize the fetched data to remove malicious Microsoft NCSI domains that break Internet Connectivity tests
                import re
                bad_patterns = r'"[^"]*(msftconnecttest|msftncsi|ncsi-geo|ncsiv6-geo|akadns\.net|akamaiedge\.net|akamai\.net|edgekey\.net|win1910\.ipv6\.microsoft\.com)[^"]*":\s*"[^"]*",?\s*'
                data = re.sub(bad_patterns, "", data)
                
                # Extract dictionary safely using exec in local namespace
                local_vars = {}
                try:
                    exec(data, {}, local_vars)
                except Exception as e:
                    return False, f"Ошибка парсинга базы: {e}"
                
                if "SERVICE_CATEGORIES" not in local_vars:
                    return False, "Не найден словарь SERVICE_CATEGORIES в базе."
                    
                new_mapping = local_vars["SERVICE_CATEGORIES"]
                
                import json
                config_dir = os.path.join(self.zapret_dir, "config")
                os.makedirs(config_dir, exist_ok=True)
                local_path = os.path.join(config_dir, "service_data.json")
                with open(local_path, "w", encoding="utf-8") as f:
                    json.dump(new_mapping, f, indent=4, ensure_ascii=False)
                    
                return True, "База IP-адресов сервисов успешно обновлена с GitHub!"
        except Exception as e:
            return False, f"Ошибка загрузки базы: {e}"
