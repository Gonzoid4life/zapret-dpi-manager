import customtkinter as ctk
import threading
import time
import os
import sys

from ..core.config import Config
from ..core.strategy import StrategyManager
from ..core.process_mgr import ProcessManager
from ..core.lists_mgr import ListsManager
from ..core.network_test import NetworkTester
from ..core.updater import Updater
from ..core.diagnostics import Diagnostics
from ..core.tray_mgr import TrayManager
from ..core.traffic_meter import TrafficMeter
from ..core.failover_mgr import FailoverManager
from ..core.logger import logger
from ..core.session_stats import session_stats
from ..core.game_detector import GameDetector

from .views.dashboard import DashboardView
from .views.lists import ListsView
from .views.services import ServicesView
from .views.tools import ToolsView
from .widgets import IOSOptionMenu
from .design_system import (
    APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH, RADIUS_NAV, RADIUS_PILL,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_BG_SIDEBAR, COLOR_BG_WINDOW, COLOR_BG_CARD, COLOR_BORDER_CARD,
    COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER,
    COLOR_SUCCESS, COLOR_SUCCESS_TINT, COLOR_SUCCESS_BORDER, COLOR_BORDER_DIVIDER,
    COLOR_DANGER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_WHITE, AppFont
)

class ZapretApp:
    def __init__(self, root, zapret_dir=None):
        self.root = root
        self.root.title(f"Zapret DPI Manager v{APP_VERSION}")
        
        # Center Window on Screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(WINDOW_WIDTH, max(720, screen_w - 40))
        win_h = min(WINDOW_HEIGHT, max(680, screen_h - 80))
        x = max(0, int((screen_w - win_w) / 2))
        y = max(0, int((screen_h - win_h) / 2))
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.resizable(False, False)

        # Initialize Config
        self.config = Config(zapret_dir)
        saved_theme = self.config.get("theme", "dark")
        if saved_theme not in ["dark", "light", "system"]:
            saved_theme = "dark"
            self.config.set("theme", "dark")

        # Set Appearance & Theme
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")

        # Base Asset Directory
        self.asset_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        # Set Window Icon
        try:
            icon_ico = os.path.join(self.asset_dir, "assets", "icon.ico")
            if not os.path.exists(icon_ico):
                icon_ico = os.path.join(self.asset_dir, "icon.ico")
            if os.path.exists(icon_ico):
                self.root.iconbitmap(icon_ico)
        except Exception:
            pass

        # Initialize Backend Components
        base_dir = self.config.get("zapret_dir")
        self.strategy_mgr = StrategyManager(base_dir)
        self.process_mgr = ProcessManager(base_dir)
        self.lists_mgr = ListsManager(base_dir)
        self.tester = NetworkTester()
        self.updater = Updater(base_dir)
        self.diagnostics = Diagnostics(base_dir)
        self.game_detector = GameDetector(base_dir)

        # Log & Session state
        self.is_log_open = False
        self.log_count = 0
        logger.subscribe(self._on_log_event)

        # Initialize System Tray
        self.tray_mgr = TrayManager(self)
        self.tray_mgr.start()

        # Initialize Traffic Meter & Failover Watchdog
        self.traffic_meter = TrafficMeter()
        self.failover_mgr = FailoverManager(self)
        self.failover_mgr.start()

        # Configure Grid Layout
        self.root.grid_columnconfigure(0, weight=0, minsize=220)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.current_view_key = None

        # Create Navigation Sidebar and Content Container
        self.create_sidebar()
        self.create_content_area()

        # Start background status polling
        self.running_poll = True
        self.poll_thread = threading.Thread(target=self._status_poll_worker, daemon=True)
        self.poll_thread.start()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Check launch minimized
        if "--minimized" in sys.argv or self.config.get("start_minimized", False):
            self.root.after(100, self.root.withdraw)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=COLOR_BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)  # Lock sidebar width statically
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(6, weight=1)

        # App Logo & Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=15, pady=(20, 15), sticky="ew")

        lbl_logo = ctk.CTkLabel(logo_frame, text="🛡️ Zapret DPI", font=AppFont.title())
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(logo_frame, text=f"Manager v{APP_VERSION} (Win11)", font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY)
        lbl_sub.pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "⚡ Главная"),
            ("lists", "📑 Списки и Фейки"),
            ("services", "🌍 Каталог сервисов"),
            ("tools", "🛠️ Инструменты")
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=label, height=42, corner_radius=RADIUS_NAV,
                font=AppFont.nav(),
                anchor="w", fg_color="transparent",
                text_color=COLOR_TEXT_PRIMARY,
                hover_color=("#EAEAEF", "#222226"),
                command=lambda k=key: self.select_view(k)
            )
            btn.grid(row=idx, column=0, padx=10, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Live Status Pill in Sidebar (Compact status indicator)
        self.sidebar_status_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=("#F2F2F7", "#1E1E24"),
            corner_radius=RADIUS_PILL,
            border_width=1,
            border_color=COLOR_BORDER_DIVIDER,
            height=32
        )
        self.sidebar_status_frame.grid(row=5, column=0, padx=12, pady=(12, 4), sticky="ew")
        self.sidebar_status_frame.pack_propagate(False)

        self.lbl_sidebar_status = ctk.CTkLabel(
            self.sidebar_status_frame,
            text="○ ЗАЩИТА ОТКЛ",
            font=AppFont.small_bold(),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_sidebar_status.pack(expand=True)

        # Theme Switcher Box
        theme_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        theme_frame.grid(row=6, column=0, padx=12, pady=(15, 5), sticky="sew")

        lbl_theme = ctk.CTkLabel(theme_frame, text="🎨 Тема интерфейса:", font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY)
        lbl_theme.pack(anchor="w", padx=2, pady=(0, 4))

        saved_theme = self.config.get("theme", "dark")
        theme_map_display = {"dark": "🌙 Тёмная", "light": "☀️ Светлая", "system": "💻 Системная"}
        self.theme_map_rev = {"🌙 Тёмная": "dark", "☀️ Светлая": "light", "💻 Системная": "system"}

        self.opt_theme = IOSOptionMenu(
            theme_frame, values=["🌙 Тёмная", "☀️ Светлая", "💻 Системная"],
            height=30, font=AppFont.sub(),
            fg_color=("#EBEBF0", "#222226"),
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            button_text_color=COLOR_TEXT_WHITE,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.on_theme_changed
        )
        self.opt_theme.set(theme_map_display.get(saved_theme, "🌙 Тёмная"))
        self.opt_theme.pack(fill="x")

        # Footer Version Label
        ver = self.updater.get_local_version()
        self.lbl_version = ctk.CTkLabel(
            self.sidebar, text=f"v{ver} • Zapret Manager v{APP_VERSION}",
            font=AppFont.small(), text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_version.grid(row=7, column=0, padx=15, pady=(5, 12), sticky="s")

    def refresh_version_label(self):
        ver = self.updater.get_local_version()
        if hasattr(self, 'lbl_version'):
            self.lbl_version.configure(text=f"v{ver} • Zapret Manager v{APP_VERSION}")

    def on_theme_changed(self, val):
        mode = self.theme_map_rev.get(val, "dark")
        self.config.set("theme", mode)
        ctk.set_appearance_mode(mode)
        current_mode = ctk.get_appearance_mode()
        for view in getattr(self, "views", {}).values():
            try:
                view._set_appearance_mode(current_mode)
            except Exception:
                pass
            if hasattr(view, 'on_theme_changed'):
                try:
                    view.on_theme_changed()
                except Exception:
                    pass

    def create_content_area(self):
        self.content_container = ctk.CTkFrame(self.root, fg_color=COLOR_BG_WINDOW)
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)  # Views take dynamic vertical space
        self.content_container.grid_rowconfigure(1, weight=0)  # Bottom status bar
        self.content_container.grid_rowconfigure(2, weight=0)  # Log drawer (when visible)

        # Holder for Views
        self.views_holder = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.views_holder.grid(row=0, column=0, sticky="nsew")
        self.views_holder.grid_columnconfigure(0, weight=1)
        self.views_holder.grid_rowconfigure(0, weight=1)

        # Initialize Views inside views_holder
        self.dashboard = DashboardView(self.views_holder, self)
        self.lists = ListsView(self.views_holder, self)
        self.services = ServicesView(self.views_holder, self)
        self.tools = ToolsView(self.views_holder, self)

        self.views = {
            "dashboard": self.dashboard,
            "lists": self.lists,
            "services": self.services,
            "tools": self.tools
        }

        # Place all views into grid once so they stay pre-mapped in memory
        for v in self.views.values():
            v.grid(row=0, column=0, sticky="nsew")

        # Bottom Status Bar with Live Log Button
        self.bottom_bar = ctk.CTkFrame(self.content_container, fg_color="transparent", height=28)
        self.bottom_bar.grid(row=1, column=0, sticky="ew", padx=4, pady=(4, 0))
        self.bottom_bar.grid_columnconfigure(0, weight=1)
        self.bottom_bar.grid_columnconfigure(1, weight=0)

        self.lbl_bottom_status = ctk.CTkLabel(
            self.bottom_bar,
            text="🛡️ Zapret DPI Manager готов к работе",
            font=AppFont.small(),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_bottom_status.grid(row=0, column=0, sticky="w")

        self.btn_toggle_log = ctk.CTkButton(
            self.bottom_bar,
            text="📜 Журнал (0) ▴",
            height=24,
            width=115,
            font=AppFont.small_bold(),
            fg_color=COLOR_BG_CONTROL,
            hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=6,
            command=self.toggle_log_drawer
        )
        self.btn_toggle_log.grid(row=0, column=1, sticky="e")

        # Live Console Drawer (Hidden by default)
        self.log_drawer = ctk.CTkFrame(
            self.content_container,
            corner_radius=10,
            fg_color=COLOR_BG_CARD,
            border_width=1,
            border_color=COLOR_BORDER_CARD,
            height=160
        )
        self.log_drawer.grid_columnconfigure(0, weight=1)
        self.log_drawer.grid_rowconfigure(1, weight=1)

        # Log Header
        log_header = ctk.CTkFrame(self.log_drawer, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=10, pady=(6, 4), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        lbl_log_title = ctk.CTkLabel(
            log_header,
            text="📜 Журнал событий и диагностика ядра",
            font=AppFont.sub_bold(),
            text_color=COLOR_TEXT_PRIMARY
        )
        lbl_log_title.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(log_header, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        btn_copy = ctk.CTkButton(
            btn_box, text="📋 Копировать", width=85, height=22,
            font=AppFont.small(), corner_radius=6,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY, command=self.copy_log
        )
        btn_copy.pack(side="left", padx=(0, 6))

        btn_clear = ctk.CTkButton(
            btn_box, text="🧹 Очистить", width=75, height=22,
            font=AppFont.small(), corner_radius=6,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY, command=self.clear_log
        )
        btn_clear.pack(side="left", padx=(0, 6))

        btn_close = ctk.CTkButton(
            btn_box, text="✖", width=24, height=22,
            font=AppFont.small_bold(), corner_radius=6,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY, command=self.toggle_log_drawer
        )
        btn_close.pack(side="left")

        # Textbox for logs
        self.txt_log = ctk.CTkTextbox(
            self.log_drawer,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=("#F8F8FA", "#141417"),
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            height=110,
            wrap="none"
        )
        self.txt_log.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nsew")
        self.txt_log.configure(state="disabled")

        # Show Dashboard initially
        self.select_view("dashboard")

    def toggle_log_drawer(self):
        self.is_log_open = not self.is_log_open
        arrow = "▾" if self.is_log_open else "▴"
        self.btn_toggle_log.configure(text=f"📜 Журнал ({self.log_count}) {arrow}")
        if self.is_log_open:
            self.log_drawer.grid(row=2, column=0, sticky="ew", padx=4, pady=(4, 0))
        else:
            self.log_drawer.grid_remove()

    def _on_log_event(self, entry):
        if hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, lambda e=entry: self._append_log_entry_ui(e))
            except Exception:
                pass

    def _append_log_entry_ui(self, entry):
        if not hasattr(self, 'txt_log'):
            return
        if entry is None:
            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            self.txt_log.configure(state="disabled")
            self.log_count = 0
            self.btn_toggle_log.configure(text="📜 Журнал (0) ▴")
            return

        self.log_count += 1
        arrow = "▾" if self.is_log_open else "▴"
        self.btn_toggle_log.configure(text=f"📜 Журнал ({self.log_count}) {arrow}")

        line = f"[{entry['time']}] [{entry['level']}] [{entry['category']}] {entry['message']}\n"
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", line)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

        lvl = entry.get("level")
        if lvl == "ERROR":
            self.lbl_bottom_status.configure(text=f"⚠️ {entry['category']}: {entry['message'][:65]}", text_color=COLOR_DANGER)
        elif lvl == "SUCCESS":
            self.lbl_bottom_status.configure(text=f"✅ {entry['category']}: {entry['message'][:65]}", text_color=COLOR_SUCCESS)

    def copy_log(self):
        full_text = logger.get_full_text()
        self.root.clipboard_clear()
        self.root.clipboard_append(full_text)
        self.lbl_bottom_status.configure(text="✅ Лог событий скопирован в буфер обмена!", text_color=COLOR_SUCCESS)
        self.root.after(3000, lambda: self.lbl_bottom_status.configure(text="🛡️ Zapret DPI Manager готов к работе", text_color=COLOR_TEXT_SECONDARY))

    def clear_log(self):
        logger.clear()

    def select_view(self, key):
        if key in self.views:
            # Map the selected view and unmap all others to prevent Tkinter overlap lag
            for v_key, view in self.views.items():
                if v_key == key:
                    view.grid(row=0, column=0, sticky="nsew")
                    if hasattr(view, 'on_show'):
                        view.on_show()
                else:
                    if hasattr(view, 'on_hide'):
                        view.on_hide()
                    view.grid_remove()

            self.current_view_key = key

            # Update button highlights without changing font metrics
            for k, btn in self.nav_buttons.items():
                if k == key:
                    btn.configure(
                        fg_color=COLOR_PRIMARY,
                        text_color=COLOR_TEXT_WHITE,
                        hover_color=COLOR_PRIMARY_HOVER
                    )
                else:
                    btn.configure(
                        fg_color="transparent",
                        text_color=COLOR_TEXT_PRIMARY,
                        hover_color=("#EAEAEF", "#222226")
                    )

    def is_running(self):
        return self.process_mgr.is_winws_running() or self.process_mgr.get_service_status() == "RUNNING"

    def start_zapret(self, strategy_name=None):
        if threading.current_thread() is threading.main_thread():
            threading.Thread(target=self._start_zapret_worker, args=(strategy_name,), daemon=True).start()
        else:
            self._start_zapret_worker(strategy_name)

    def _start_zapret_worker(self, strategy_name=None):
        strat = strategy_name or self.config.get("active_strategy", "general.bat")
        mode = self.config.get("run_mode", "service")
        autostart = self.config.get("autostart", True)
        logger.info("SCM", f"Запуск обхода блокировок: {strat} ({mode})")

        if mode == "service":
            ok = self.process_mgr.start_as_service(strat, autostart=autostart)
        else:
            ok = self.process_mgr.start_as_process(strat)

        if ok:
            logger.success("SCM", f"Ядро Zapret успешно активно (стратегия: {strat})")
            session_stats.start()
        else:
            logger.error("SCM", f"Не удалось запустить Zapret ({strat})")

        if self.root:
            self.root.after(0, self.refresh_status_all)

    def stop_zapret(self):
        if threading.current_thread() is threading.main_thread():
            threading.Thread(target=self._stop_zapret_worker, daemon=True).start()
        else:
            self._stop_zapret_worker()

    def _stop_zapret_worker(self):
        logger.info("SCM", "Остановка сетевого фильтра и служб...")
        self.process_mgr.stop_all()
        session_stats.stop()
        logger.info("SCM", "Ядро Zapret и драйвер WinDivert остановлены")
        if self.root:
            self.root.after(0, self.refresh_status_all)

    def restart_zapret(self, strategy_name=None):
        if threading.current_thread() is threading.main_thread():
            threading.Thread(target=self._restart_zapret_worker, args=(strategy_name,), daemon=True).start()
        else:
            self._restart_zapret_worker(strategy_name)

    def _restart_zapret_worker(self, strategy_name=None):
        logger.info("SCM", "Перезапуск сетевого фильтра...")
        self.process_mgr.stop_all()
        session_stats.stop()
        time.sleep(0.3)
        strat = strategy_name or self.config.get("active_strategy", "general.bat")
        mode = self.config.get("run_mode", "service")
        autostart = self.config.get("autostart", True)

        if mode == "service":
            ok = self.process_mgr.start_as_service(strat, autostart=autostart)
        else:
            ok = self.process_mgr.start_as_process(strat)

        if ok:
            logger.success("SCM", f"Перезапуск завершён: стратегия {strat} активна")
            session_stats.start()
        else:
            logger.error("SCM", "Ошибка при перезапуске")

        if self.root:
            self.root.after(0, self.refresh_status_all)

    def update_sidebar_status(self, running):
        if not hasattr(self, 'lbl_sidebar_status'):
            return
        if running:
            self.sidebar_status_frame.configure(
                fg_color=COLOR_SUCCESS_TINT,
                border_color=COLOR_SUCCESS_BORDER
            )
            self.lbl_sidebar_status.configure(
                text="● ЗАЩИТА ВКЛ",
                text_color=COLOR_SUCCESS
            )
        else:
            self.sidebar_status_frame.configure(
                fg_color=("#F2F2F7", "#1E1E24"),
                border_color=COLOR_BORDER_DIVIDER
            )
            self.lbl_sidebar_status.configure(
                text="○ ЗАЩИТА ОТКЛ",
                text_color=COLOR_TEXT_SECONDARY
            )

    def refresh_status_all(self):
        running = self.is_running()
        self.dashboard.update_status(running)
        self.update_sidebar_status(running)
        if hasattr(self, 'tray_mgr') and self.tray_mgr:
            self.tray_mgr.update_icon(rebuild_menu=True)

    def _status_poll_worker(self):
        last_running = None
        last_strat = None
        last_game_state = False
        while self.running_poll:
            try:
                running = self.is_running()
                self.root.after(0, lambda r=running: self.dashboard.update_status(r))
                self.root.after(0, lambda r=running: self.update_sidebar_status(r))

                # 1. Update Session Stats
                if running:
                    if not session_stats.is_active:
                        session_stats.start()
                    session_stats.update()
                else:
                    if session_stats.is_active:
                        session_stats.stop()

                uptime_str = session_stats.get_uptime_formatted()
                traffic_str = session_stats.get_traffic_formatted()
                peak_str = session_stats.get_peak_formatted()
                if hasattr(self, 'dashboard'):
                    self.root.after(0, lambda u=uptime_str, t=traffic_str, p=peak_str: self.dashboard.update_session_stats(u, t, p))

                # 2. Smart Game Mode Detection
                if self.config.get("smart_game_mode", True) and hasattr(self, 'game_detector'):
                    is_game, game_name, exe_name = self.game_detector.scan_for_active_game()
                    if is_game:
                        self.game_detector.apply_game_mode_protection(True)
                        if not last_game_state:
                            logger.info("GAME", f"Обнаружена игра: {game_name} ({exe_name}) — защита пинга активна")
                            last_game_state = True
                        if hasattr(self, 'dashboard'):
                            self.root.after(0, lambda g=game_name: self.dashboard.set_game_badge(True, g))
                    else:
                        if last_game_state:
                            logger.info("GAME", "Игра завершена — стандартный режим обхода")
                            last_game_state = False
                        if hasattr(self, 'dashboard'):
                            self.root.after(0, lambda: self.dashboard.set_game_badge(False, None))

                speed_str = "0 B/s"
                if hasattr(self, 'traffic_meter') and hasattr(self, 'dashboard'):
                    _, _, speed_str = self.traffic_meter.get_speed()
                    self.root.after(0, lambda s=speed_str: self.dashboard.update_traffic_speed(s))

                if hasattr(self, 'tray_mgr') and self.tray_mgr and self.tray_mgr.icon:
                    strat = self.config.get("active_strategy", "general.bat")
                    clean_strat = strat[:-4] if strat.endswith(".bat") else strat
                    st = "В сети" if running else "Остановлен"
                    tooltip = f"🛡️ Zapret: {st} | {clean_strat} | ⚡ {speed_str}"
                    rebuild = (running != last_running) or (strat != last_strat)
                    self.tray_mgr.update_icon(
                        status="running" if running else "stopped",
                        tooltip_text=tooltip,
                        rebuild_menu=rebuild
                    )
                    last_running = running
                    last_strat = strat
            except Exception:
                pass
            time.sleep(1.8)

    def clean_exit(self):
        self.running_poll = False
        if hasattr(self, 'failover_mgr') and self.failover_mgr:
            try:
                self.failover_mgr.stop()
            except Exception:
                pass
        if hasattr(self, 'tray_mgr') and self.tray_mgr and self.tray_mgr.icon:
            try:
                self.tray_mgr.icon.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def on_closing(self):
        if self.config.get("minimize_to_tray", True):
            self.root.withdraw()
        else:
            self.clean_exit()
