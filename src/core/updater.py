import os
import requests
import zipfile
import shutil
import tempfile
import re
import subprocess
import time

FLOWSEAL_REPO = "Flowseal/zapret-discord-youtube"
IPSET_URL = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/ipset-service.txt"
HOSTS_URL = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/hosts"
GITHUB_API_RELEASES = f"https://api.github.com/repos/{FLOWSEAL_REPO}/releases/latest"

class Updater:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)
        self.lists_dir = os.path.join(self.zapret_dir, "lists")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ZapretManager-Win11/1.0"
        })

    def get_local_version(self):
        """
        Dynamically reads version from service.bat or version.txt or folder name.
        Completely independent of folder naming conventions.
        """
        # 1. Try reading from service.bat
        service_bat = os.path.join(self.zapret_dir, "service.bat")
        if os.path.exists(service_bat):
            try:
                with open(service_bat, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "LOCAL_VERSION=" in line:
                            m = re.search(r'LOCAL_VERSION=([0-9\.]+)', line)
                            if m:
                                return m.group(1)
            except Exception:
                pass

        # 2. Check for version.txt if created by a release
        ver_file = os.path.join(self.zapret_dir, "version.txt")
        if os.path.exists(ver_file):
            try:
                with open(ver_file, "r", encoding="utf-8", errors="ignore") as f:
                    v = f.read().strip().lstrip("v")
                    if v:
                        return v
            except Exception:
                pass

        # 3. Try parsing version from directory name if present
        folder_name = os.path.basename(self.zapret_dir)
        m = re.search(r'([0-9]+\.[0-9]+(?:\.[0-9]+)?)', folder_name)
        if m:
            return m.group(1)

        return "1.0.0"

    def check_latest_release(self):
        """
        Returns dict: {'latest_version': '...', 'has_update': bool, 'download_url': '...', 'body': '...', 'error': str}
        """
        local_ver = self.get_local_version()
        try:
            resp = self.session.get(GITHUB_API_RELEASES, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "").lstrip("v")
                assets = data.get("assets", [])
                zip_url = None
                for asset in assets:
                    name = asset.get("name", "").lower()
                    if name.endswith(".zip"):
                        zip_url = asset.get("browser_download_url")
                        break
                if not zip_url:
                    zip_url = data.get("zipball_url")

                has_update = (tag != local_ver) and (tag != "")
                return {
                    "local_version": local_ver,
                    "latest_version": tag or local_ver,
                    "has_update": has_update,
                    "download_url": zip_url,
                    "body": data.get("body", ""),
                    "error": None
                }
            else:
                return {
                    "local_version": local_ver,
                    "latest_version": local_ver,
                    "has_update": False,
                    "download_url": None,
                    "body": "",
                    "error": f"HTTP {resp.status_code}"
                }
        except Exception as e:
            return {
                "local_version": local_ver,
                "latest_version": local_ver,
                "has_update": False,
                "download_url": None,
                "body": "",
                "error": str(e)
            }

    def download_and_install_update(self, download_url, latest_ver, progress_callback=None):
        """
        Downloads release zip, preserves and smart-merges user lists, replaces binaries and scripts.
        """
        if not download_url:
            return False, "Ссылка для скачивания обновления не найдена"

        temp_dir = tempfile.mkdtemp(prefix="zapret_update_")
        zip_path = os.path.join(temp_dir, "update.zip")

        try:
            # 1. Download Release Zip
            if progress_callback:
                progress_callback("Скачивание обновления с GitHub (0%)...")

            resp = self.session.get(download_url, stream=True, timeout=30)
            if resp.status_code != 200:
                return False, f"Ошибка загрузки: HTTP {resp.status_code}"

            total_len = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_len > 0 and progress_callback:
                            percent = int((downloaded / total_len) * 100)
                            progress_callback(f"Скачивание обновления ({percent}%)...")

            # 2. Extract Zip
            if progress_callback:
                progress_callback("Распаковка файлов...")

            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # Find root of zapret files in extracted directory
            source_root = extract_dir
            for root, dirs, files in os.walk(extract_dir):
                if "service.bat" in files or "general.bat" in files:
                    source_root = root
                    break

            # 3. Backup and Prepare User Lists for Smart Merge
            user_list_files = ["list-general-user.txt", "list-exclude-user.txt", "ipset-exclude-user.txt"]
            user_backups = {}
            for fname in user_list_files:
                fpath = os.path.join(self.lists_dir, fname)
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        user_backups[fname] = f.read()

            # 4. Release all process/driver locks before installing binaries
            if progress_callback:
                progress_callback("Освобождение системных ресурсов и процессов...")
            self.release_file_locks()

            if progress_callback:
                progress_callback("Установка новых бинарников и скриптов...")

            for item in os.listdir(source_root):
                s = os.path.join(source_root, item)
                d = os.path.join(self.zapret_dir, item)
                
                # Skip overwriting ZapretManager.exe itself and personal user configs
                if item.lower() in ["zapretmanager.exe", "manager_config.json", "zapret_manager_config.json"]:
                    continue

                if os.path.isdir(s):
                    if item.lower() == "lists":
                        # Handle lists directory carefully: preserve user lists & custom fakes
                        os.makedirs(d, exist_ok=True)
                        protected_list_items = [
                            "list-general-user.txt", "list-exclude-user.txt", "ipset-exclude-user.txt",
                            "active_discord.bin", "active_game.bin", "active_discord_udp.bin", "active_game_udp.bin"
                        ]
                        for list_item in os.listdir(s):
                            ls = os.path.join(s, list_item)
                            ld = os.path.join(d, list_item)
                            if list_item.lower() in user_list_files:
                                continue  # Handled in smart merge step
                            if list_item.lower() in [x.lower() for x in protected_list_items] and os.path.exists(ld):
                                continue  # Preserve existing user custom fakes
                            if os.path.isfile(ls):
                                self._safe_copy_file(ls, ld)
                            elif os.path.isdir(ls):
                                self._safe_copy_tree(ls, ld, protected_files=protected_list_items)
                    elif item.lower() == "bin":
                        # Preserve existing active fake binaries
                        os.makedirs(d, exist_ok=True)
                        protected_bins = ["active_discord_udp.bin", "active_game_udp.bin", "active_discord.bin", "active_game.bin"]
                        for bin_item in os.listdir(s):
                            bs = os.path.join(s, bin_item)
                            bd = os.path.join(d, bin_item)
                            if bin_item.lower() in [x.lower() for x in protected_bins] and os.path.exists(bd):
                                continue  # Do not overwrite active fakes chosen by user
                            if os.path.isfile(bs):
                                self._safe_copy_file(bs, bd)
                            elif os.path.isdir(bs):
                                self._safe_copy_tree(bs, bd, protected_files=protected_bins)
                    else:
                        self._safe_copy_tree(s, d)
                else:
                    self._safe_copy_file(s, d)

            # 5. Smart Merge User Lists with New Author Additions
            for fname in user_list_files:
                original_user_content = user_backups.get(fname, "")
                new_author_path = os.path.join(source_root, "lists", fname)
                target_user_path = os.path.join(self.lists_dir, fname)

                if os.path.exists(new_author_path) and original_user_content:
                    with open(new_author_path, "r", encoding="utf-8", errors="ignore") as f:
                        new_author_content = f.read()

                    merged = self._merge_list_content(original_user_content, new_author_content, latest_ver)
                    with open(target_user_path, "w", encoding="utf-8") as f:
                        f.write(merged)
                elif original_user_content:
                    with open(target_user_path, "w", encoding="utf-8") as f:
                        f.write(original_user_content)

            # Write version.txt to persist updated version tag
            try:
                with open(os.path.join(self.zapret_dir, "version.txt"), "w", encoding="utf-8") as vf:
                    vf.write(f"v{latest_ver}\n")
            except Exception:
                pass

            if progress_callback:
                progress_callback("Обновление успешно завершено!")

            return True, f"Zapret успешно обновлен до версии v{latest_ver}!"

        except Exception as e:
            return False, f"Ошибка при установке обновления: {str(e)}"
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def release_file_locks(self):
        """
        Forcefully terminates winws processes and stops zapret/windivert services,
        ensuring Windows kernel and background processes release file locks before replacement.
        """
        # 1. Kill winws processes immediately so socket & pipe handles are released
        try:
            subprocess.run(["taskkill", "/IM", "winws.exe", "/F", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.5, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["taskkill", "/IM", "winws2.exe", "/F", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.5, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        # 2. Stop zapret service
        try:
            subprocess.run(["net", "stop", "zapret"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=6.0, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["sc", "delete", "zapret"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3.0, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        # 3. Stop WinDivert drivers
        for drv in ["WinDivert", "WinDivert14"]:
            try:
                subprocess.run(["net", "stop", drv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4.0, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["sc", "delete", drv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

        time.sleep(0.5)

    def _safe_copy_file(self, src, dst, max_retries=6, delay=0.4):
        """
        Robustly copies src to dst on Windows with retry logic and sharing violation handling.
        Prevents [WinError 32] (Sharing Violation) and [WinError 5] (Access Denied).
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                shutil.copy2(src, dst)
                return True
            except (PermissionError, OSError) as e:
                last_error = e
                if attempt == 2:
                    self.release_file_locks()
                time.sleep(delay)

        # Retry strategy: try renaming locked destination before overwriting
        temp_old = dst + f".old_{int(time.time())}"
        try:
            if os.path.exists(temp_old):
                try:
                    os.remove(temp_old)
                except Exception:
                    pass
            os.rename(dst, temp_old)
            shutil.copy2(src, dst)
            try:
                os.remove(temp_old)
            except Exception:
                pass
            return True
        except Exception:
            pass

        # Driver / system file safety:
        # If dst is a kernel driver / dll (e.g. WinDivert64.sys) locked by the OS kernel,
        # but already exists in the local directory, keep existing rather than crashing entire update!
        fname = os.path.basename(dst).lower()
        if fname in ["windivert64.sys", "windivert32.sys", "windivert.dll"] and os.path.exists(dst):
            return True

        # If existing file has identical size, accept keeping it
        if os.path.exists(dst):
            try:
                if os.path.getsize(src) == os.path.getsize(dst):
                    return True
            except Exception:
                pass

        if last_error:
            raise last_error
        return False

    def _safe_copy_tree(self, src_dir, dst_dir, protected_files=None):
        """Recursively copies src_dir into dst_dir using _safe_copy_file."""
        os.makedirs(dst_dir, exist_ok=True)
        protected = set(f.lower() for f in (protected_files or []))
        for item in os.listdir(src_dir):
            if item.lower() in protected:
                continue
            s = os.path.join(src_dir, item)
            d = os.path.join(dst_dir, item)
            if os.path.isdir(s):
                self._safe_copy_tree(s, d, protected_files)
            else:
                self._safe_copy_file(s, d)

    def _merge_list_content(self, user_content, new_author_content, version_tag):
        """
        Preserves all user lines, and if author added any brand new domains,
        appends them at the bottom under an explicit version header.
        """
        user_lines_clean = set(
            line.strip().lower() for line in user_content.splitlines() 
            if line.strip() and not line.strip().startswith("#")
        )

        new_entries = []
        for line in new_author_content.splitlines():
            clean = line.strip()
            if clean and not clean.startswith("#"):
                if clean.lower() not in user_lines_clean:
                    new_entries.append(clean)

        if not new_entries:
            return user_content

        # Append new entries with clear tag
        separator = f"\n\n# ==========================================\n# [Добавлено из обновления Zapret v{version_tag}]\n# ==========================================\n"
        return user_content.rstrip() + separator + "\n".join(new_entries) + "\n"

    def update_ipset_list(self):
        """Downloads and compares updated ipset-service.txt to lists/ipset-all.txt"""
        os.makedirs(self.lists_dir, exist_ok=True)
        target_path = os.path.join(self.lists_dir, "ipset-all.txt")
        try:
            resp = None
            mirrors = [
                IPSET_URL,
                "https://ghproxy.net/" + IPSET_URL,
                "https://gh-proxy.com/" + IPSET_URL
            ]
            for mirror in mirrors:
                try:
                    r = self.session.get(mirror, timeout=10)
                    if r.status_code == 200 and len(r.text) > 50:
                        resp = r
                        break
                except Exception:
                    continue
                    
            if not resp:
                return False, "Ошибка загрузки: недоступен GitHub и его зеркала", False
                
            old_lines = set()
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    old_lines = set(l.strip() for l in f if l.strip() and not l.strip().startswith("#"))

            new_lines = set(l.strip() for l in resp.text.splitlines() if l.strip() and not l.strip().startswith("#"))

            if old_lines and old_lines == new_lines:
                return True, "Обновления не требуются (установлен актуальный список IPSet)", False

            diff_count = len(new_lines - old_lines)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(resp.text)

            if diff_count > 0:
                msg = f"Обновлено: добавлено {diff_count} новых адресов (всего {len(new_lines)})"
            else:
                msg = f"База IPSet синхронизирована (всего {len(new_lines)} адресов)"
            return True, msg, True

        except Exception as e:
            return False, f"Ошибка загрузки: {e}", False

    update_ipset_database = update_ipset_list

    def update_hosts_file(self):
        """Downloads hosts from repository and compares/updates Discord routing in system hosts."""
        hosts_path = os.path.expandvars(r"%SystemRoot%\System32\drivers\etc\hosts")
        try:
            resp = None
            mirrors = [
                HOSTS_URL,
                "https://ghproxy.net/" + HOSTS_URL,
                "https://gh-proxy.com/" + HOSTS_URL
            ]
            for mirror in mirrors:
                try:
                    r = self.session.get(mirror, timeout=10)
                    if r.status_code == 200:
                        resp = r
                        break
                except Exception:
                    continue
                    
            if not resp:
                return False, "Ошибка загрузки: недоступен GitHub и его зеркала", False

            repo_content = resp.text.strip()
            if not repo_content:
                return False, "Файл hosts в репозитории пуст", False

            existing_content = ""
            if os.path.exists(hosts_path):
                with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                    existing_content = f.read()

            start_marker = "# === ZAPRET DISCORD HOSTS START ==="
            end_marker = "# === ZAPRET DISCORD HOSTS END ==="
            zapret_block = f"\n{start_marker}\n{repo_content}\n{end_marker}\n"

            # Check if identical block is already in hosts
            if start_marker in existing_content and end_marker in existing_content:
                pattern = re.compile(rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
                match = pattern.search(existing_content)
                if match and match.group(0).strip() == f"{start_marker}\n{repo_content}\n{end_marker}".strip():
                    return True, "Обновления не требуются (маршруты Hosts Discord актуальны)", False
                new_content = pattern.sub(zapret_block.strip(), existing_content)
            else:
                new_content = existing_content.rstrip() + "\n" + zapret_block

            with open(hosts_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            try:
                import subprocess
                subprocess.run("ipconfig /flushdns", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

            return True, "Маршруты Hosts Discord успешно обновлены до актуальной версии!", True
        except PermissionError:
            return False, "Недостаточно прав для записи в C:\\Windows\\System32\\drivers\\etc\\hosts. Запустите от имени Администратора.", False
        except Exception as e:
            return False, f"Ошибка обновления hosts: {e}", False
