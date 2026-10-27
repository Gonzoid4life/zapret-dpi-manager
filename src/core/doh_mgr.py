import sys
import subprocess
from .logger import logger

class DohManager:
    @staticmethod
    def is_windows_11():
        try:
            return sys.platform == "win32" and sys.getwindowsversion().build >= 22000
        except Exception:
            return False

    @classmethod
    def get_doh_status(cls):
        """
        Returns a dict: {'supported': bool, 'enabled': bool, 'provider': str}
        """
        supported = cls.is_windows_11()
        if not supported:
            return {"supported": False, "enabled": False, "provider": "Не поддерживается (требуется Windows 11)"}

        try:
            ps_cmd = (
                "$iface = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1; "
                "if ($iface) { "
                "  $dns = Get-DnsClientServerAddress -InterfaceIndex $iface.ifIndex -AddressFamily IPv4; "
                "  if ($dns.ServerAddresses) { $dns.ServerAddresses -join ',' } else { 'DHCP' } "
                "} else { 'NONE' }"
            )
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                text=True, stderr=subprocess.DEVNULL, errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            ).strip()

            if "1.1.1.1" in out:
                return {"supported": True, "enabled": True, "provider": "Cloudflare DoH (1.1.1.1)"}
            elif "8.8.8.8" in out:
                return {"supported": True, "enabled": True, "provider": "Google DoH (8.8.8.8)"}
            elif "9.9.9.9" in out:
                return {"supported": True, "enabled": True, "provider": "Quad9 DoH (9.9.9.9)"}
            elif out == "DHCP":
                return {"supported": True, "enabled": False, "provider": "DHCP (Автоматически)"}
            else:
                return {"supported": True, "enabled": False, "provider": f"Пользовательский ({out})"}
        except Exception as e:
            return {"supported": True, "enabled": False, "provider": f"Ошибка: {e}"}

    @classmethod
    def apply_doh(cls, provider_key="cloudflare"):
        """
        Configures secure DNS-over-HTTPS on Windows 11.
        provider_key: 'cloudflare' | 'google' | 'quad9' | 'dhcp'
        """
        provider_map = {
            "cloudflare": {
                "name": "Cloudflare DoH",
                "ips": '("1.1.1.1", "1.0.0.1")',
                "primary": "1.1.1.1",
                "secondary": "1.0.0.1",
                "template": "https://cloudflare-dns.com/dns-query"
            },
            "google": {
                "name": "Google DoH",
                "ips": '("8.8.8.8", "8.8.4.4")',
                "primary": "8.8.8.8",
                "secondary": "8.8.4.4",
                "template": "https://dns.google/dns-query"
            },
            "quad9": {
                "name": "Quad9 DoH",
                "ips": '("9.9.9.9", "149.112.112.112")',
                "primary": "9.9.9.9",
                "secondary": "149.112.112.112",
                "template": "https://dns.quad9.net/dns-query"
            }
        }

        try:
            if provider_key in provider_map:
                cfg = provider_map[provider_key]
                ps_script = (
                    f"$iface = Get-NetAdapter | Where-Object {{$_.Status -eq 'Up'}} | Select-Object -First 1; "
                    f"if ($iface) {{ "
                    f"  Set-DnsClientServerAddress -InterfaceIndex $iface.ifIndex -ServerAddresses {cfg['ips']}; "
                    f"  try {{ Set-DnsClientDohServerAddress -ServerAddress '{cfg['primary']}' -AutoUpgrade $true -AllowFallbackToUdp $true }} catch {{}}; "
                    f"  try {{ Set-DnsClientDohServerAddress -ServerAddress '{cfg['secondary']}' -AutoUpgrade $true -AllowFallbackToUdp $true }} catch {{}}; "
                    f"  netsh dns add encryption interface=$iface.Name ip={cfg['primary']} dohurl=\"{cfg['template']}\" autoupgrade=yes 2>$null; "
                    f"  netsh dns add encryption interface=$iface.Name ip={cfg['secondary']} dohurl=\"{cfg['template']}\" autoupgrade=yes 2>$null; "
                    f"}}"
                )
                logger.info("DOH", f"Применение профиля шифрованного DNS: {cfg['name']}")
            else:
                # Reset to DHCP
                ps_script = (
                    "$iface = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1; "
                    "if ($iface) { "
                    "  Set-DnsClientServerAddress -InterfaceIndex $iface.ifIndex -ResetServerAddresses; "
                    "}"
                )
                logger.info("DOH", "Сброс DNS на автоматический режим (DHCP)")

            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Flush DNS cache
            subprocess.run(
                ["ipconfig", "/flushdns"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if res.returncode == 0:
                logger.success("DOH", f"Настройки DNS успешно обновлены ({provider_key})")
                return True, "Настройки DNS успешно применены, кэш очищен"
            else:
                err = res.stderr.strip() or res.stdout.strip()
                logger.warn("DOH", f"Предупреждение при настройке DoH: {err}")
                return True, f"DNS обновлен (с предупреждением: {err[:80]})"
        except Exception as e:
            logger.error("DOH", f"Ошибка изменения DNS: {e}")
            return False, f"Ошибка: {e}"
