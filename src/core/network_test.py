import time
import os
import subprocess
import concurrent.futures
import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetworkTester:
    def __init__(self, timeout=5.0):
        self.timeout = timeout
        self.curl_exe = self._find_curl()

    def _find_curl(self):
        system_curl = os.path.expandvars(r"%SystemRoot%\System32\curl.exe")
        if os.path.exists(system_curl):
            return system_curl
        try:
            res = subprocess.run(["where", "curl"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                return res.stdout.strip().splitlines()[0]
        except Exception:
            pass
        return None

    def test_single_target(self, target):
        """
        Tests target using system curl.exe (matching Flowseal test zapret.ps1 logic)
        or fallback to requests.
        """
        name = target.get("name", "Unknown")
        url = target.get("url", "")
        category = target.get("category", "general")

        if self.curl_exe:
            return self._test_with_curl(name, url, category)
        else:
            return self._test_with_requests(name, url, category)

    def _test_with_curl(self, name, url, category):
        start_time = time.time()
        try:
            # Match Flowseal's curl test: -I -s -m <timeout> -w "%{http_code} %{time_total}"
            cmd = [
                self.curl_exe,
                "-I", "-s",
                "-m", str(int(self.timeout)),
                "-w", "%{http_code} %{time_total}",
                "-o", "NUL",
                "--ssl-no-revoke",
                "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                url
            ]

            proc = subprocess.run(
                cmd, capture_output=True, text=True, 
                timeout=self.timeout + 1.5, errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = proc.stdout.strip()
            elapsed = int((time.time() - start_time) * 1000)

            # Parse http_code and time
            m = re.search(r'(\d{3})\s+([\d\.]+)', output)
            if m:
                code = int(m.group(1))
                time_sec = float(m.group(2))
                latency = int(time_sec * 1000)
                success = code in [200, 204, 301, 302, 303, 307, 308, 400, 401, 403, 404, 405, 429, 500, 502, 503]
                return {
                    "name": name, "url": url, "category": category,
                    "success": success, "status_code": code, "latency_ms": latency,
                    "error": None if success else f"HTTP {code}"
                }

            # Exit codes analysis
            if proc.returncode == 0 and output:
                return {
                    "name": name, "url": url, "category": category,
                    "success": True, "status_code": 200, "latency_ms": elapsed, "error": None
                }
            elif proc.returncode == 28:
                return {
                    "name": name, "url": url, "category": category,
                    "success": False, "status_code": 0, "latency_ms": elapsed, "error": "Таймаут (блокировка)"
                }
            elif proc.returncode == 35 or proc.returncode == 60:
                return {
                    "name": name, "url": url, "category": category,
                    "success": False, "status_code": 0, "latency_ms": elapsed, "error": "SSL/TLS ошибка"
                }
            else:
                return {
                    "name": name, "url": url, "category": category,
                    "success": False, "status_code": 0, "latency_ms": elapsed, "error": "Сброс подключения (RST)"
                }

        except subprocess.TimeoutExpired:
            return {
                "name": name, "url": url, "category": category,
                "success": False, "status_code": 0, "latency_ms": int(self.timeout * 1000), "error": "Таймаут"
            }
        except Exception as e:
            return {
                "name": name, "url": url, "category": category,
                "success": False, "status_code": 0, "latency_ms": 0, "error": str(e)[:30]
            }

    def _test_with_requests(self, name, url, category):
        start_time = time.time()
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        try:
            resp = session.head(url, timeout=self.timeout, verify=False, allow_redirects=True)
            latency = int((time.time() - start_time) * 1000)
            success = resp.status_code in [200, 204, 301, 302, 303, 307, 308, 400, 401, 403, 404, 405, 429, 500, 502, 503]
            return {
                "name": name, "url": url, "category": category,
                "success": success, "status_code": resp.status_code, "latency_ms": latency,
                "error": None if success else f"HTTP {resp.status_code}"
            }
        except Exception:
            latency = int((time.time() - start_time) * 1000)
            return {
                "name": name, "url": url, "category": category,
                "success": False, "status_code": 0, "latency_ms": latency, "error": "Ошибка подключения"
            }

    def test_all_targets(self, targets, max_workers=6):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {executor.submit(self.test_single_target, t): t for t in targets}
            for future in concurrent.futures.as_completed(future_to_target):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    t = future_to_target[future]
                    results.append({
                        "name": t.get("name"), "url": t.get("url"), "category": t.get("category", "general"),
                        "success": False, "status_code": 0, "latency_ms": 0, "error": str(e)
                    })
        return results

    def calculate_strategy_score(self, test_results):
        if not test_results:
            return 0, 1, 0

        score = 0
        latencies = []
        yt_web_ok = False
        yt_video_ok = False
        dc_main_ok = False

        for res in test_results:
            name = res.get("name", "")
            cat = res.get("category", "general")
            success = res.get("success", False)
            lat = res.get("latency_ms", 0)

            if success and lat > 0:
                latencies.append(lat)

            if cat == "youtube":
                if "Web" in name and success:
                    yt_web_ok = True
                    score += 40
                elif "Video" in name and success:
                    yt_video_ok = True
                    score += 20
                elif success:
                    score += 5
            elif cat == "discord":
                if "Main" in name and success:
                    dc_main_ok = True
                    score += 20
                elif success:
                    score += 5
            else:
                if success:
                    score += 5

        # Speed bonus only if at least YouTube or Discord works
        avg_lat = int(sum(latencies) / len(latencies)) if latencies else 0
        if (yt_web_ok or yt_video_ok or dc_main_ok) and latencies:
            if avg_lat < 200:
                score += 10
            elif avg_lat < 400:
                score += 5

        stars = 5 if score >= 80 else (3 if score >= 50 else 1)
        return score, stars, avg_lat
