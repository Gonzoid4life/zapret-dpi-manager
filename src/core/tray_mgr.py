import os
import sys
import threading
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item, Menu

class TrayManager:
    def __init__(self, app_controller):
        self.app = app_controller
        self.icon = None
        self.is_running = False
        self._thread = None
        self.base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    def create_status_image(self, status="running"):
        # Create a crisp 64x64 icon featuring a bold stylized "Z"
        size = (64, 64)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Normalize status boolean vs string
        if status is True or status == "running":
            # Active (ON): Vibrant Cyber Green shield & badge with crisp Z
            bg_color = (18, 32, 22, 240)       # Deep dark emerald
            border_color = (0, 230, 118, 255)   # Glowing Neon Green #00E676
            z_color = (0, 230, 118, 255)        # Bright Neon Green
        elif status in ("warning", "reconnecting", "degraded"):
            # Warning / Reconnecting: Glowing Amber Gold
            bg_color = (36, 28, 12, 240)       # Deep dark amber
            border_color = (255, 179, 0, 255)   # Glowing Gold #FFB300
            z_color = (255, 179, 0, 255)        # Bright Amber
        else:
            # Stopped (OFF): Dark Crimson shield & badge with Red Z
            bg_color = (32, 18, 18, 240)       # Deep dark crimson
            border_color = (235, 17, 35, 255)   # Bright Red #EB1123
            z_color = (235, 17, 35, 255)        # Bright Red

        # Rounded badge container
        draw.rounded_rectangle([3, 3, 61, 61], radius=14, fill=bg_color, outline=border_color, width=3)

        # Sharp Geometric "Z" Polygon
        z_polygon = [
            (16, 16), (48, 16), (48, 24),
            (28, 40), (48, 40), (48, 48),
            (16, 48), (16, 40), (36, 24),
            (16, 24)
        ]
        draw.polygon(z_polygon, fill=z_color)

        return img

    def build_menu(self):
        is_active = self.app.is_running()
        active_strat = self.app.config.get("active_strategy", "general.bat")
        
        status_text = f"🛡️ Zapret: {'Работает' if is_active else 'Остановлен'}"
        strat_text = f"Пресет: {active_strat}"

        # Build dynamic strategy list matching Dashboard (Top 3 + current)
        ratings = self.app.config.get("strategy_ratings", {})

        def get_sort_key(s_name):
            rate_info = ratings.get(s_name)
            if not rate_info:
                return (-1, -99999)
            if isinstance(rate_info, dict):
                score = rate_info.get("score", 0)
                lat = rate_info.get("avg_latency", 0)
            else:
                score = int(rate_info * 100) if rate_info <= 1.0 else int(rate_info)
                lat = 0
            return (score, -lat if lat > 0 else -99999)

        all_strats = [s["name"] for s in self.app.strategy_mgr.list_strategies()]
        sorted_strats = sorted(all_strats, key=get_sort_key, reverse=True)

        top_strats = sorted_strats[:3]
        if active_strat in all_strats and active_strat not in top_strats:
            top_strats.append(active_strat)

        def make_switch_cb(strat_name):
            return lambda icon, item: self._on_switch_strategy(strat_name)

        def format_label(name, rank_idx=None):
            is_cur = (name == active_strat)
            rate_info = ratings.get(name)
            lat = 0
            if isinstance(rate_info, dict):
                lat = int(rate_info.get("avg_latency", 0))

            if rank_idx == 0 and get_sort_key(name)[0] > 0:
                prefix = "🥇 #1  "
            elif rank_idx == 1 and get_sort_key(name)[0] > 0:
                prefix = "🥈 #2  "
            elif rank_idx == 2 and get_sort_key(name)[0] > 0:
                prefix = "🥉 #3  "
            else:
                prefix = ""

            lat_str = f"  •  ⚡ {lat} ms" if lat > 0 else ""
            check = "✔ " if is_cur else "   "
            return f"{check}{prefix}{name}{lat_str}"

        # Top 3 items
        strat_items = []
        for idx, s_name in enumerate(top_strats):
            label = format_label(s_name, rank_idx=idx if s_name in sorted_strats[:3] else None)
            strat_items.append(item(label, make_switch_cb(s_name)))

        # Submenu with all remaining strategies
        all_items = []
        for s_name in sorted_strats:
            label = format_label(s_name)
            all_items.append(item(label, make_switch_cb(s_name)))

        if len(sorted_strats) > 3:
            strat_items.append(Menu.SEPARATOR)
            strat_items.append(item("Все стратегии ▾", Menu(*all_items)))

        menu_items = [
            item(status_text, None, enabled=False),
            item(strat_text, None, enabled=False),
        ]

        if hasattr(self.app, 'traffic_meter') and self.app.traffic_meter:
            try:
                _, _, speed_str = self.app.traffic_meter.get_speed()
                menu_items.append(item(f"⚡ Трафик: {speed_str}", None, enabled=False))
            except Exception:
                pass

        menu_items.extend([
            Menu.SEPARATOR,
            item("Показать окно", self.show_window, default=True),
        ])

        if is_active:
            menu_items.append(item("⏹ Остановить Zapret", self._on_stop))
            menu_items.append(item("↻ Перезапустить", self._on_restart))
        else:
            menu_items.append(item("▶ Запустить Zapret", self._on_start))

        # Quick Switch Top 1 shortcut if not already selected
        if sorted_strats and active_strat != sorted_strats[0]:
            top1 = sorted_strats[0]
            clean_top1 = top1[:-4] if top1.endswith(".bat") else top1
            menu_items.append(item(f"🥇 Переключить на топ-1 ({clean_top1})", make_switch_cb(top1)))

        menu_items.extend([
            Menu.SEPARATOR,
            item("⚡ Сменить стратегию", Menu(*strat_items)),
            Menu.SEPARATOR,
            item("❌ Выход", self._on_exit)
        ])

        return Menu(*menu_items)

    def start(self):
        if self.icon is not None:
            return
        
        is_active = self.app.is_running()
        strat = self.app.config.get("active_strategy", "general.bat")
        img = self.create_status_image("running" if is_active else "stopped")
        init_title = f"🛡️ Zapret: {'Работает' if is_active else 'Остановлен'} | {strat}"
        self.icon = pystray.Icon("ZapretDpiManager", img, init_title, menu=self.build_menu())
        
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def update_icon(self, status=None, tooltip_text=None, rebuild_menu=False):
        if self.icon:
            try:
                if status is None:
                    status = "running" if self.app.is_running() else "stopped"
                self.icon.icon = self.create_status_image(status)
                if tooltip_text:
                    self.icon.title = str(tooltip_text)[:120]
                else:
                    strat = self.app.config.get("active_strategy", "general.bat")
                    clean_strat = strat[:-4] if strat.endswith(".bat") else strat
                    st = "Работает" if self.app.is_running() else "Остановлен"
                    self.icon.title = f"🛡️ Zapret: {st} | {clean_strat}"
                if rebuild_menu:
                    self.icon.menu = self.build_menu()
            except Exception:
                pass

    def show_window(self, icon=None, item=None):
        def _do():
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.root.focus_force()
        self.app.root.after(0, _do)

    def hide_window(self):
        self.app.root.withdraw()

    def _on_start(self, icon=None, item=None):
        self.app.root.after(0, lambda: self.app.start_zapret())
        self.app.root.after(800, lambda: self.update_icon(rebuild_menu=True))

    def _on_stop(self, icon=None, item=None):
        self.app.root.after(0, lambda: self.app.stop_zapret())
        self.app.root.after(800, lambda: self.update_icon(rebuild_menu=True))

    def _on_restart(self, icon=None, item=None):
        self.app.root.after(0, lambda: self.app.restart_zapret())
        self.app.root.after(800, lambda: self.update_icon(rebuild_menu=True))

    def _on_switch_strategy(self, strategy_name):
        def _do():
            self.app.config.set("active_strategy", strategy_name)
            self.app.dashboard.strategy_var.set(strategy_name)
            self.app.dashboard.refresh_strategy_dropdown()
            if self.app.is_running():
                self.app.restart_zapret(strategy_name)
            self.update_icon(rebuild_menu=True)
        self.app.root.after(0, _do)

    def _on_exit(self, icon=None, item=None):
        self.app.root.after(0, self.app.clean_exit)
