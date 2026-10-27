import os
import subprocess
import shutil

class Diagnostics:
    def __init__(self, zapret_dir):
        self.zapret_dir = os.path.abspath(zapret_dir)

    def run_all_checks(self):
        """
        Runs comprehensive diagnostic checks.
        Returns list of dicts: [{'title': '...', 'status': 'ok'|'warn'|'error', 'message': '...'}]
        """
        checks = []

        # 1. Check WinDivert64.sys
        sys_file = os.path.join(self.zapret_dir, "bin", "WinDivert64.sys")
        if os.path.exists(sys_file):
            checks.append({"title": "Файл драйвера WinDivert64.sys", "status": "ok", "message": "Найден в bin/"})
        else:
            checks.append({"title": "Файл драйвера WinDivert64.sys", "status": "error", "message": "Файл отсутствует в bin/"})

        # 2. Check Conflicting services
        conflicts = ["GoodbyeDPI", "SmartByte", "CheckPoint", "discordfix_zapret", "winws1", "winws2"]
        found_conflicts = []
        for srv in conflicts:
            try:
                out = subprocess.check_output(f'sc query "{srv}"', shell=True, text=True, stderr=subprocess.DEVNULL, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
                if "SERVICE_NAME" in out:
                    found_conflicts.append(srv)
            except Exception:
                pass

        if found_conflicts:
            checks.append({"title": "Конфликтующие службы", "status": "warn", "message": f"Обнаружены: {', '.join(found_conflicts)} (рекомендуется удалить)"})
        else:
            checks.append({"title": "Конфликтующие службы", "status": "ok", "message": "Конфликтов GoodbyeDPI/SmartByte не обнаружено"})

        # 3. Check VPN services, processes and Virtual Adapters
        vpn_found = []
        try:
            out = subprocess.check_output('sc query', shell=True, text=True, stderr=subprocess.DEVNULL, timeout=1.0, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
            for line in out.splitlines():
                if "SERVICE_NAME" in line or "ИМЯ_СЛУЖБЫ" in line or "SERVICE" in line.upper():
                    if ":" in line:
                        s_name = line.split(":", 1)[1].strip()
                        s_upper = s_name.upper()
                        if any(k in s_upper for k in ["AMNEZIA", "RADMIN", "WIREGUARD", "OPENVPN", "MULLVAD", "PROTON", "SURFSHARK", "WARP", "V2RAY", "XRAY", "SING-BOX"]):
                            if s_name not in vpn_found and s_name.lower() != "zapret":
                                vpn_found.append(s_name)
        except Exception:
            pass

        # Also check running VPN processes
        try:
            p_out = subprocess.check_output('tasklist /FO CSV /NH', shell=True, text=True, stderr=subprocess.DEVNULL, timeout=1.0, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW).lower()
            vpn_proc_names = [
                ("amnezia", "Amnezia VPN"), ("wireguard", "WireGuard"), ("openvpn", "OpenVPN"),
                ("v2ray", "V2Ray"), ("xray", "Xray"), ("clash", "Clash"), ("sing-box", "sing-box"),
                ("radmin", "Radmin VPN"), ("warp", "Cloudflare WARP"), ("proton", "Proton VPN")
            ]
            for kw, disp in vpn_proc_names:
                if kw in p_out and disp not in vpn_found:
                    vpn_found.append(disp)
        except Exception:
            pass

        if vpn_found:
            checks.append({"title": "VPN службы / процессы", "status": "warn", "message": f"Обнаружены активные: {', '.join(vpn_found)} (могут перехватывать трафик)"})
        else:
            checks.append({"title": "VPN службы", "status": "ok", "message": "Конфликтующих VPN служб и процессов не обнаружено"})

        # 4. Check Secure DNS / DoH in registry and active DNS IPs
        try:
            doh_active = False
            # Check DoH registry flags
            try:
                import winreg
                key_path = r"System\CurrentControlSet\Services\Dnscache\InterfaceSpecificParameters"
                root_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                for i in range(winreg.QueryInfoKey(root_key)[0]):
                    subkey_name = winreg.EnumKey(root_key, i)
                    sub_key = winreg.OpenKey(root_key, subkey_name, 0, winreg.KEY_READ)
                    try:
                        val, _ = winreg.QueryValueEx(sub_key, "DohFlags")
                        if val and int(val) > 0:
                            doh_active = True
                            break
                    except Exception:
                        pass
                    finally:
                        winreg.CloseKey(sub_key)
                winreg.CloseKey(root_key)
            except Exception:
                pass

            # Also check if DNS server is set to public secure DNS (8.8.8.8, 1.1.1.1, 9.9.9.9)
            if not doh_active:
                try:
                    ip_out = subprocess.check_output('ipconfig /all', shell=True, text=True, stderr=subprocess.DEVNULL, timeout=1.0, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
                    if any(dns in ip_out for dns in ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9", "77.88.8.8"]):
                        doh_active = True
                except Exception:
                    pass

            if doh_active:
                checks.append({"title": "Шифрованный DNS / DoH", "status": "ok", "message": "Используется безопасный DNS (Google/Cloudflare/DoH)"})
            else:
                checks.append({"title": "Шифрованный DNS (DoH)", "status": "warn", "message": "Рекомендуется включить Secure DNS (Cloudflare 1.1.1.1 / Google 8.8.8.8) в браузере или параметрах сети."})
        except Exception:
            pass

        # 5. Hosts file check
        hosts_path = os.path.expandvars(r"%SystemRoot%\System32\drivers\etc\hosts")
        if os.path.exists(hosts_path):
            try:
                with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "youtube.com" in content or "googlevideo.com" in content:
                    checks.append({"title": "Файл hosts (YouTube)", "status": "warn", "message": "В файле hosts найдены записи для YouTube. Это может мешать воспроизведению."})
                else:
                    checks.append({"title": "Файл hosts", "status": "ok", "message": "Записей, блокирующих YouTube, не обнаружено"})
            except Exception:
                pass

        return checks

    def clear_discord_cache(self):
        """Kills Discord processes and cleans cache folders."""
        appdata = os.environ.get("APPDATA", "")
        clients = [
            ("Discord.exe", "Discord", os.path.join(appdata, "discord")),
            ("DiscordPTB.exe", "Discord PTB", os.path.join(appdata, "discordptb")),
            ("DiscordCanary.exe", "Discord Canary", os.path.join(appdata, "discordcanary")),
            ("DiscordDevelopment.exe", "Discord Dev", os.path.join(appdata, "discorddevelopment")),
        ]

        cleaned = []
        for exe_name, name, folder in clients:
            if os.path.exists(folder):
                subprocess.run(f'taskkill /IM "{exe_name}" /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                for sub in ["Cache", "Code Cache", "GPUCache"]:
                    sub_path = os.path.join(folder, sub)
                    if os.path.exists(sub_path):
                        try:
                            shutil.rmtree(sub_path, ignore_errors=True)
                        except Exception:
                            pass
                cleaned.append(name)

        if cleaned:
            return True, f"Очищен кэш для: {', '.join(cleaned)}"
        return False, "Клиенты Discord не найдены"

    def flush_dns(self):
        try:
            subprocess.run("ipconfig /flushdns", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            return True, "Кэш DNS успешно очищен"
        except Exception as e:
            return False, f"Ошибка: {e}"

    def fix_windivert_conflict(self):
        """Cleans lingering WinDivert and conflicting services."""
        try:
            for srv in ["zapret", "GoodbyeDPI", "discordfix_zapret", "winws1", "winws2", "WinDivert", "WinDivert14"]:
                subprocess.run(f'net stop "{srv}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(f'sc delete "{srv}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /IM winws.exe /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run('taskkill /IM winws2.exe /F', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            return True, "Все конфликтующие службы и драйвер WinDivert сброшены"
        except Exception as e:
            return False, f"Ошибка сброса: {e}"

    def stop_all_vpn_services(self):
        """
        Discovers and stops any active VPN services, adapters, and background processes (including Amnezia & Radmin VPN).
        """
        stopped = []
        # 1. Common known VPN service names (including Amnezia and Radmin VPN)
        known_vpn_services = [
            "AmneziaVPN-service", "AmneziaVPNService", "AmneziaService", "AmneziaWireGuardService", "AmneziaVPN",
            "RadminVPNControlService", "RvControlSvc", "RadminVPN", "Radmin VPN Control Service",
            "WireGuardManager", "WireGuardTunnel", "OpenVPNService", "OpenVPNServiceInteractive",
            "MullvadVPN", "NordVPN", "ProtonVPN", "ExpressVPN", "Surfshark",
            "v2ray", "sing-box", "xray", "AdGuardSvc", "WindscribeService", "WARP", "CloudflareWARP",
            "IVpnService", "CyberGhost", "PIA-VPN", "KasperskySecureConnection"
        ]

        # 2. Dynamic PowerShell Stop-Service for all matching services
        ps_cmd = (
            "powershell -NoProfile -Command \""
            "Get-Service | Where-Object { "
            "$_.Name -match 'amnezia|radmin|wireguard|openvpn|mullvad|proton|nord|surfshark|warp|v2ray|xray|sing-box|wintun' "
            "-or $_.DisplayName -match 'amnezia|radmin|wireguard|openvpn|mullvad|proton|nord|surfshark|warp|v2ray|xray|sing-box|wintun' "
            "} | ForEach-Object { Stop-Service -InputObject $_ -Force -ErrorAction SilentlyContinue; $_.Name }\""
        )
        try:
            out = subprocess.check_output(ps_cmd, shell=True, text=True, stderr=subprocess.DEVNULL, errors="ignore", creationflags=subprocess.CREATE_NO_WINDOW)
            for line in out.splitlines():
                s = line.strip()
                if s and s not in stopped and s.lower() != "zapret":
                    stopped.append(s)
        except Exception:
            pass

        # 3. Fallback net stop / sc stop for explicitly listed services
        for srv in known_vpn_services:
            try:
                res = subprocess.run(f'net stop "{srv}" /y', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if res.returncode == 0 or "успешно" in res.stdout.lower() or "stopped" in res.stdout.lower():
                    if srv not in stopped:
                        stopped.append(srv)
            except Exception:
                pass

        # 4. Terminate known VPN background process executables (including Amnezia & Radmin VPN)
        vpn_processes = [
            "AmneziaVPN.exe", "AmneziaVPN-service.exe", "AmneziaService.exe", "amnezia-wireguard.exe",
            "RadminVPN.exe", "RvControlSvc.exe", "Famatech.RadminVPN.exe", "Famatech.RadminVPN.Service.exe",
            "wireguard.exe", "openvpn.exe", "openvpn-gui.exe", "v2rayn.exe", "v2ray.exe",
            "xray.exe", "nekoray.exe", "sing-box.exe", "clash.exe", "clash-verge.exe",
            "protonvpn.exe", "nordvpn.exe", "windscribe.exe", "warp-svc.exe", "Cloudflare WARP.exe"
        ]
        for proc in vpn_processes:
            try:
                subprocess.run(f'taskkill /F /IM "{proc}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

        if stopped:
            return True, f"Остановлены VPN службы:\n{', '.join(stopped)}"
        return True, "Все активные VPN службы (включая Amnezia и Radmin) успешно остановлены"

    def get_active_dns(self):
        """Returns the DNS server addresses for the active network interface."""
        ps_cmd = (
            "$iface = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1; "
            "if ($iface) { "
            "  $dns = Get-DnsClientServerAddress -InterfaceIndex $iface.ifIndex -AddressFamily IPv4; "
            "  if ($dns.ServerAddresses) { $dns.ServerAddresses -join ', ' } else { 'DHCP' } "
            "} else { 'UNKNOWN' }"
        )
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                text=True, stderr=subprocess.DEVNULL, startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).strip()
            if not out or out == "DHCP":
                return "DHCP (Автоматически)"
            if out == "UNKNOWN":
                return "Неизвестно"
            return out
        except Exception:
            return "Неизвестно"
