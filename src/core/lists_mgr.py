import os
import hashlib
import glob
import shutil

class ListsManager:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)
        self.lists_dir = os.path.join(self.zapret_dir, "lists")
        self.bin_dir = os.path.join(self.zapret_dir, "bin")
        self.utils_dir = os.path.join(self.zapret_dir, "utils")
        self.ensure_user_lists()

    def ensure_user_lists(self):
        os.makedirs(self.lists_dir, exist_ok=True)
        os.makedirs(self.utils_dir, exist_ok=True)

        user_lists = {
            "ipset-exclude-user.txt": "203.0.113.113/32\n",
            "list-general-user.txt": "# Добавьте свои домены здесь (по одному на строку)\n",
            "list-exclude-user.txt": "# Домены исключений (прямое подключение без zapret)\n"
        }
        for name, default_content in user_lists.items():
            path = os.path.join(self.lists_dir, name)
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(default_content)
                except Exception:
                    pass

    # --- Game Filter ---
    def get_game_filter_mode(self):
        flag_file = os.path.join(self.utils_dir, "game_filter.enabled")
        if not os.path.exists(flag_file):
            return "disabled"
        try:
            with open(flag_file, "r", encoding="utf-8") as f:
                mode = f.read().strip().lower()
                if mode in ["all", "tcp", "udp"]:
                    return mode
                return "disabled"
        except Exception:
            return "disabled"

    def set_game_filter_mode(self, mode):
        flag_file = os.path.join(self.utils_dir, "game_filter.enabled")
        if mode == "disabled":
            if os.path.exists(flag_file):
                try:
                    os.remove(flag_file)
                except Exception:
                    pass
        else:
            try:
                with open(flag_file, "w", encoding="utf-8") as f:
                    f.write(mode)
            except Exception:
                pass

    # --- IPSet Filter ---
    def get_ipset_mode(self):
        list_file = os.path.join(self.lists_dir, "ipset-all.txt")
        if not os.path.exists(list_file):
            return "none"
        try:
            with open(list_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if l.strip()]
            if len(lines) == 0:
                return "any"
            if any("0.0.0.0/0" in l for l in lines) and len(lines) <= 2:
                return "any"
            if len(lines) == 1 and "203.0.113.113/32" in lines[0]:
                return "none"
            return "loaded"
        except Exception:
            return "loaded"

    def set_ipset_mode(self, mode):
        list_file = os.path.join(self.lists_dir, "ipset-all.txt")
        backup_file = os.path.join(self.lists_dir, "ipset-all.txt.backup")
        alt_backup = os.path.join(self.lists_dir, "ipset-all.test-backup.txt")

        current_mode = self.get_ipset_mode()
        if mode == current_mode:
            return

        if mode == "none":
            # Backup if currently loaded
            if current_mode == "loaded" and os.path.exists(list_file):
                try:
                    shutil.copyfile(list_file, backup_file)
                except Exception:
                    pass
            with open(list_file, "w", encoding="utf-8") as f:
                f.write("203.0.113.113/32\n")

        elif mode == "any":
            if current_mode == "loaded" and os.path.exists(list_file):
                try:
                    shutil.copyfile(list_file, backup_file)
                except Exception:
                    pass
            with open(list_file, "w", encoding="utf-8") as f:
                f.write("0.0.0.0/0\n::/0\n")

        elif mode == "loaded":
            for bf in (backup_file, alt_backup):
                if os.path.exists(bf):
                    try:
                        shutil.copyfile(bf, list_file)
                        break
                    except Exception:
                        pass

    # --- Active Fakes (.bin files) ---
    def get_file_hash(self, path):
        if not os.path.exists(path):
            return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def list_available_fakes(self):
        """Returns list of dicts: [{'name': '...', 'path': '...', 'hash': '...'}]"""
        fakes = []
        if not os.path.exists(self.bin_dir):
            return fakes

        for p in glob.glob(os.path.join(self.bin_dir, "*.bin")):
            name = os.path.basename(p)
            if not name.startswith("ACTIVE_"):
                fakes.append({
                    "name": name,
                    "path": p,
                    "hash": self.get_file_hash(p)
                })
        fakes.sort(key=lambda x: x["name"])
        return fakes

    def get_current_fakes_info(self):
        fakes = self.list_available_fakes()
        hash_to_name = {f["hash"]: f["name"] for f in fakes if f["hash"]}

        discord_active_path = os.path.join(self.bin_dir, "ACTIVE_DISCORD_UDP.bin")
        game_active_path = os.path.join(self.bin_dir, "ACTIVE_GAME_UDP.bin")

        discord_hash = self.get_file_hash(discord_active_path)
        game_hash = self.get_file_hash(game_active_path)

        return {
            "discord": hash_to_name.get(discord_hash, "Неизвестный / Custom"),
            "game": hash_to_name.get(game_hash, "Неизвестный / Custom")
        }

    def list_fake_bins(self):
        fakes = self.list_available_fakes()
        return [f["name"] for f in fakes]

    def get_current_fakes(self):
        return self.get_current_fakes_info()

    def set_active_fake(self, fake_type, fake_filename):
        """fake_type: 'discord' or 'game'"""
        target_name = "ACTIVE_DISCORD_UDP.bin" if fake_type == "discord" else "ACTIVE_GAME_UDP.bin"
        target_path = os.path.join(self.bin_dir, target_name)
        source_path = os.path.join(self.bin_dir, fake_filename)

        if os.path.exists(source_path):
            try:
                shutil.copyfile(source_path, target_path)
                return True
            except Exception:
                return False
        return False

    def set_fake_bin(self, fake_type, fake_filename):
        ok = self.set_active_fake(fake_type, fake_filename)
        if ok:
            return True, f"Фейк {fake_type} успешно применен: {fake_filename}"
        return False, f"Не удалось скопировать {fake_filename}"

    # --- User Lists Read/Write ---
    def read_user_list(self, filename):
        path = os.path.join(self.lists_dir, filename)
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def save_user_list(self, filename, content):
        path = os.path.join(self.lists_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Файл {filename} сохранен."
        except Exception as e:
            return False, f"Ошибка сохранения {filename}: {e}"

    def write_user_list(self, filename, content):
        ok, _ = self.save_user_list(filename, content)
        return ok

    def is_domain_in_list(self, filename, domain):
        """Checks if a domain is already listed in user list."""
        if not domain:
            return False
        d = domain.strip().lower()
        content = self.read_user_list(filename)
        for line in content.splitlines():
            line_str = line.strip().lower()
            if line_str and not line_str.startswith("#") and line_str == d:
                return True
        return False

    def add_domain_to_list(self, filename, domain):
        """Adds domain to user list if not present. Returns (ok, already_exists, msg)."""
        if not domain:
            return False, False, "Пустой адрес домена"
        d = domain.strip().lower()
        content = self.read_user_list(filename)
        for line in content.splitlines():
            line_str = line.strip().lower()
            if line_str and not line_str.startswith("#") and line_str == d:
                return True, True, f"Домен {d} уже есть в списке"

        if content and not content.endswith("\n"):
            content += "\n"
        content += f"{d}\n"
        ok, msg = self.save_user_list(filename, content)
        if ok:
            return True, False, f"Домен {d} успешно добавлен в {filename}"
        return False, False, msg

