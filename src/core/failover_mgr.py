import threading
import urllib.request
import urllib.error

class FailoverManager:
    def __init__(self, app_controller):
        self.app = app_controller
        self.running = False
        self._thread = None
        self._stop_event = threading.Event()
        self.consecutive_failures = 0
        self.max_failures = 2
        self.check_interval_seconds = 180  # 3 minutes
        self.last_failed_target = "YouTube / Discord"

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watchdog_worker, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        self._stop_event.set()

    def is_target_healthy(self, url, timeout=4.0):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=timeout):
                return True
        except urllib.error.HTTPError:
            # Any HTTP status code from server means TLS/TCP handshake succeeded and DPI didn't block it!
            return True
        except Exception:
            return False

    def check_health(self):
        yt_ok = self.is_target_healthy("https://www.youtube.com", timeout=3.5)
        if not yt_ok:
            yt_ok = self.is_target_healthy("https://redirector.googlevideo.com", timeout=3.5)
        dc_ok = self.is_target_healthy("https://gateway.discord.gg", timeout=3.5)

        if not yt_ok and not dc_ok:
            self.last_failed_target = "YouTube и Discord"
            return False
        elif not yt_ok:
            self.last_failed_target = "YouTube"
            return False
        elif not dc_ok:
            self.last_failed_target = "Discord"
            return False

        return True

    def _watchdog_worker(self):
        while self.running:
            if self._stop_event.wait(self.check_interval_seconds):
                break

            if not self.running:
                break

            # Only check when Zapret is actually running and auto_failover is enabled
            if not self.app.is_running():
                self.consecutive_failures = 0
                continue

            if not self.app.config.get("auto_failover", True):
                self.consecutive_failures = 0
                continue

            healthy = self.check_health()
            if healthy:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1

                if self.consecutive_failures >= self.max_failures:
                    self.consecutive_failures = 0
                    self._trigger_failover()

    def _trigger_failover(self):
        ratings = self.app.config.get("strategy_ratings", {})
        active_strat = self.app.config.get("active_strategy", "general.bat")

        # Get sorted strategies by score
        def get_score(s_name):
            r = ratings.get(s_name)
            if isinstance(r, dict):
                return r.get("score", 0)
            return 0

        all_strats = [s["name"] for s in self.app.strategy_mgr.list_strategies()]
        sorted_strats = sorted(all_strats, key=get_score, reverse=True)

        if not sorted_strats:
            return

        # Pick next strategy in ranking
        next_strat = None
        for s in sorted_strats:
            if s != active_strat:
                next_strat = s
                break

        if not next_strat:
            return

        def _worker():
            self.app.config.set("active_strategy", next_strat)

            def _update_ui():
                if hasattr(self.app, "dashboard"):
                    self.app.dashboard.strategy_var.set(next_strat)
                    self.app.dashboard.refresh_strategy_dropdown()

            if self.app and self.app.root:
                self.app.root.after(0, _update_ui)

            # Perform restart in BACKGROUND worker thread so GUI never freezes!
            self.app.restart_zapret(next_strat)

            # Send notification via tray icon if available
            try:
                if hasattr(self.app, "tray_mgr") and self.app.tray_mgr and self.app.tray_mgr.icon:
                    clean_name = next_strat[:-4] if next_strat.lower().endswith(".bat") else next_strat
                    failed_label = getattr(self, 'last_failed_target', 'Целевой сервис')
                    self.app.tray_mgr.icon.notify(
                        title="⚡ Zapret: Авто-переключение",
                        message=f"{failed_label} перестал отвечать. Пресет автоматически изменен на: {clean_name}"
                    )
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()
