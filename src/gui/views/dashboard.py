import os
import sys
import customtkinter as ctk
import threading
import time
import datetime
from PIL import Image
from ..widgets import IOSSegmentedButton, IOSOptionMenu
from ..animator import UIAnimator
from ..design_system import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_TINT,
    COLOR_SUCCESS, COLOR_SUCCESS_TINT, COLOR_SUCCESS_BORDER,
    COLOR_DANGER, COLOR_DANGER_HOVER,
    COLOR_WARNING, COLOR_WARNING_TINT,
    COLOR_BG_WINDOW, COLOR_BG_CARD, COLOR_BG_CARD_SUB, COLOR_BORDER_CARD, COLOR_BORDER_DIVIDER,
    COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_WHITE,
    COLOR_RANK_GOLD, COLOR_RANK_SILVER, COLOR_RANK_BRONZE,
    RADIUS_CARD, RADIUS_TILE, RADIUS_BTN, RADIUS_PILL,
    FONT_FAMILY_TITLE, AppFont, get_smart_strategy_name
)

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color=COLOR_BG_WINDOW)
        self.app = app_controller
        self.is_busy = False
        self.show_all_strategies = False

        # Load badge icons
        base_asset_dir = getattr(self.app, 'asset_dir', getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        yt_p = os.path.join(base_asset_dir, "assets", "yt.png") if os.path.exists(os.path.join(base_asset_dir, "assets", "yt.png")) else os.path.join(base_asset_dir, "yt.png")
        dc_p = os.path.join(base_asset_dir, "assets", "dc.png") if os.path.exists(os.path.join(base_asset_dir, "assets", "dc.png")) else os.path.join(base_asset_dir, "dc.png")
        web_p = os.path.join(base_asset_dir, "assets", "web.png") if os.path.exists(os.path.join(base_asset_dir, "assets", "web.png")) else os.path.join(base_asset_dir, "web.png")

        self.img_yt = None
        self.img_dc = None
        self.img_web = None
        try:
            if os.path.exists(yt_p):
                self.img_yt = ctk.CTkImage(Image.open(yt_p), size=(13, 13))
            if os.path.exists(dc_p):
                self.img_dc = ctk.CTkImage(Image.open(dc_p), size=(13, 13))
            if os.path.exists(web_p):
                self.img_web = ctk.CTkImage(Image.open(web_p), size=(13, 13))
        except Exception:
            pass

        self.grid_columnconfigure(0, weight=1)
        self.last_status_state = None
        self.create_status_card()
        self.create_autotune_card()
        self.create_strategy_card()
        self.create_toggles_card()

    def create_status_card(self):
        # Modern Hero Status Card (Fluent 2 / Apple iOS 17 style)
        self.card_status = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        self.card_status.grid(row=0, column=0, padx=(16, 20), pady=(15, 10), sticky="ew")
        self.card_status.grid_columnconfigure(0, weight=1)
        self.card_status.grid_columnconfigure(1, weight=0)

        # Left Column: Status Pill, Title, Subtitle, Speedmeter
        left_col = ctk.CTkFrame(self.card_status, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=(18, 10), pady=14, sticky="nsew")
        left_col.grid_columnconfigure(0, weight=1)

        # Top Meta Row: Status Pill Badge + Live Speed Badge
        meta_row = ctk.CTkFrame(left_col, fg_color="transparent")
        meta_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.status_pill = ctk.CTkLabel(
            meta_row, text="○  Остановлен",
            font=AppFont.small_bold(),
            fg_color=COLOR_BG_CONTROL,
            text_color=COLOR_TEXT_SECONDARY,
            corner_radius=10,
            height=22,
            padx=10
        )
        self.status_pill.pack(side="left")

        self.lbl_speed = ctk.CTkLabel(
            meta_row, text="",
            font=AppFont.small_bold(),
            text_color=COLOR_SUCCESS,
            anchor="w"
        )
        self.lbl_speed.pack(side="left", padx=(10, 0))

        self.lbl_stat_game = ctk.CTkLabel(
            meta_row, text="",
            font=AppFont.small_bold(), fg_color=COLOR_WARNING_TINT,
            corner_radius=RADIUS_PILL, padx=8, pady=2, text_color=COLOR_WARNING
        )

        # Main Title
        self.status_title = ctk.CTkLabel(
            left_col, text="Zapret остановлен",
            font=AppFont.title(),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w"
        )
        self.status_title.grid(row=1, column=0, sticky="w", pady=(0, 2))

        # Subtitle
        self.status_sub = ctk.CTkLabel(
            left_col, text="Нажмите «Запустить» для включения обхода блокировок",
            font=AppFont.sub(),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        )
        self.status_sub.grid(row=2, column=0, sticky="w")

        # Right Column: Action Buttons
        btn_frame = ctk.CTkFrame(self.card_status, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=(6, 16), pady=14, sticky="e")

        self.btn_toggle = ctk.CTkButton(
            btn_frame, text="Запустить", height=38, width=130,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, corner_radius=RADIUS_BTN,
            text_color=COLOR_TEXT_WHITE,
            command=self.on_toggle_click
        )
        self.btn_toggle.pack(side="left", padx=(0, 8))
        UIAnimator.attach_smooth_hover(self.btn_toggle, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        self.btn_restart = ctk.CTkButton(
            btn_frame, text="↻", width=38, height=38,
            font=ctk.CTkFont(family=FONT_FAMILY_TITLE, size=16, weight="bold"),
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY, corner_radius=RADIUS_BTN,
            command=self.on_restart_click
        )
        self.btn_restart.pack(side="left")
        UIAnimator.attach_smooth_hover(self.btn_restart, normal_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER)

# Session micro-stats removed at user request

    
    def create_autotune_card(self):
        self.is_tuning = False
        self.stop_tuning_flag = False
        self.card_autotune = ctk.CTkFrame(
            self, corner_radius=14, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        self.card_autotune.grid(row=1, column=0, padx=(16, 20), pady=(0, 10), sticky="ew")
        self.card_autotune.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(self.card_autotune, text="Автоподбор стратегии", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")
        
        lbl_sub = ctk.CTkLabel(self.card_autotune, text="Автоматический прогон всех стратегий для поиска самой быстрой и стабильной.", font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY)
        lbl_sub.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="w")

        ctrl_frame = ctk.CTkFrame(self.card_autotune, fg_color="transparent")
        ctrl_frame.grid(row=2, column=0, padx=16, pady=4, sticky="ew")
        
        self.mode_var = ctk.StringVar(value="quick")
        self.seg_mode = IOSSegmentedButton(
            ctrl_frame, values=["Быстрый", "Полный"],
            height=30, command=lambda v: self.mode_var.set("full" if "Полный" in v else "quick")
        )
        self.seg_mode.set("Быстрый")
        self.seg_mode.pack(side="left")

        self.btn_autotune = ctk.CTkButton(
            ctrl_frame, text="Подобрать (22)", width=135, height=32,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, corner_radius=10,
            command=self.toggle_autotune
        )
        self.btn_autotune.pack(side="right")
        UIAnimator.attach_smooth_hover(self.btn_autotune, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        self.progress_bar = ctk.CTkProgressBar(self.card_autotune, height=6, corner_radius=3, progress_color=COLOR_PRIMARY, fg_color=COLOR_BG_CONTROL)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, padx=16, pady=(8, 8), sticky="ew")

        init_prog = "⚡ Первый запуск на этом ПК: запустите тест для поиска лучшей стратегии" if getattr(self.app.config, "is_new_pc", False) else "Готов к проверке"
        self.lbl_progress = ctk.CTkLabel(self.card_autotune, text=init_prog, font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, anchor="w")
        self.lbl_progress.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="w")
        
    def toggle_autotune(self):
        if self.is_tuning:
            self.stop_tuning_flag = True
            self.btn_autotune.configure(text="Остановка...", state="disabled")
            self.app.process_mgr.stop_strategy_after_test()
        else:
            self.is_tuning = True
            self.stop_tuning_flag = False
            self.btn_autotune.configure(text="■ Остановить", fg_color=("#FF3B30", "#FF453A"), hover_color=("#E02B20", "#E03830"), state="normal")
            threading.Thread(target=self._autotune_worker, daemon=True).start()

    def _autotune_worker(self):
        was_running = self.app.is_running()
        initial_strategy = self.app.config.get("active_strategy", "general.bat")
        strategies_to_test = self.app.strategy_mgr.list_strategies()
        
        try:
            self.app.process_mgr.set_ipset_mode("any")
            self.app.process_mgr.stop_all()

            total = len(strategies_to_test)
            mode = self.mode_var.get()
            all_targets = self.app.config.get("test_targets", [])
            if mode == "quick":
                test_targets = [t for t in all_targets if t.get("category") in ["youtube", "discord"]]
            else:
                test_targets = all_targets

            tested_results = []

            for idx, strat in enumerate(strategies_to_test):
                if self.stop_tuning_flag:
                    break

                s_name = strat["name"]
                progress_pct = idx / total
                self.app.root.after(0, lambda p=progress_pct: self.progress_bar.set(p))
                self.app.root.after(0, lambda i=idx, t=total, n=s_name: self.lbl_progress.configure(
                    text=f"[{i+1}/{t}] Тестирование «{n}»..."
                ))

                ok = self.app.process_mgr.start_strategy_for_test(s_name)
                if not ok:
                    continue

                time.sleep(3.5)
                results = self.app.tester.test_all_targets(test_targets, max_workers=6)
                score, stars, avg_lat = self.app.tester.calculate_strategy_score(results)
                passed_count = sum(1 for r in results if r.get("success"))

                # 3-state category grading (ok / partial / fail) for Top-3 status badges
                yt_res = [r for r in results if r.get("category") == "youtube"]
                dc_res = [r for r in results if r.get("category") == "discord"]
                web_res = [r for r in results if r.get("category") == "general"]

                yt_video = any(r.get("success") for r in yt_res if "Redirect" in r.get("name", "") or "Video" in r.get("name", ""))
                yt_web = any(r.get("success") for r in yt_res if "Web" in r.get("name", "") or "Short" in r.get("name", ""))
                yt_total_ok = sum(1 for r in yt_res if r.get("success"))

                if yt_video and yt_web:
                    yt_state = "ok"
                elif yt_total_ok > 0:
                    yt_state = "partial"
                else:
                    yt_state = "fail"

                dc_main = any(r.get("success") for r in dc_res if "Main" in r.get("name", ""))
                dc_gateway = any(r.get("success") for r in dc_res if "Gateway" in r.get("name", "") or "CDN" in r.get("name", ""))
                dc_total_ok = sum(1 for r in dc_res if r.get("success"))

                if dc_main and dc_gateway:
                    dc_state = "ok"
                elif dc_total_ok > 0:
                    dc_state = "partial"
                else:
                    dc_state = "fail"

                web_total_ok = sum(1 for r in web_res if r.get("success"))
                if web_total_ok >= len(web_res) - 1 and len(web_res) > 0:
                    web_state = "ok"
                elif web_total_ok > 0:
                    web_state = "partial"
                else:
                    web_state = "fail"

                entry = {
                    "name": s_name,
                    "score": score,
                    "stars": stars,
                    "avg_latency": avg_lat,
                    "yt_state": yt_state,
                    "dc_state": dc_state,
                    "web_state": web_state,
                    "passed_count": passed_count,
                    "total_targets": len(results),
                    "results": results
                }
                tested_results.append(entry)

                self.app.process_mgr.stop_strategy_after_test()
                time.sleep(0.3)

            if tested_results and not self.stop_tuning_flag:
                now_str = datetime.datetime.now().strftime("%d.%m.%Y в %H:%M")
                
                # Merge logic
                merged_results = tested_results.copy()
                merged_results.sort(
                    key=lambda x: (
                        x.get("score", 0), 
                        x.get("passed_count", 0), 
                        -x.get("avg_latency", 0) if x.get("avg_latency", 0) > 0 else -99999
                    ), 
                    reverse=True
                )

                # Save dictionary structure for quick lookup in get_top_3
                ratings_dict = {r["name"]: r for r in merged_results}

                best_strategy = merged_results[0]["name"] if merged_results else initial_strategy

                self.app.config.set("active_strategy", best_strategy)
                self.app.config.set("strategy_ratings", ratings_dict)
                self.app.config.set("last_autotune_time", now_str)
                self.app.config.set("last_autotune_results", merged_results)

                self.app.root.after(0, lambda: self.lbl_progress.configure(text="Тестирование завершено! Лучшая стратегия применена."))
                self.app.root.after(0, lambda: self.progress_bar.set(1.0))
                self.app.root.after(0, lambda b=best_strategy: self.strategy_var.set(b))
                self.app.root.after(0, self.refresh_strategy_dropdown)
            else:
                self.app.root.after(0, lambda: self.lbl_progress.configure(text="Тестирование отменено."))
                self.app.root.after(0, self.refresh_strategy_dropdown)

        except Exception as e:
            self.app.root.after(0, lambda err=e: self.lbl_progress.configure(text=f"Ошибка: {err}"))
        finally:
            self.is_tuning = False
            self.app.root.after(0, lambda: self.btn_autotune.configure(text="Подобрать (22)", fg_color=("#007AFF", "#0A84FF"), hover_color=("#0062CC", "#0070E0"), state="normal"))

            orig_ipset = self.app.config.get("ipset_mode", "loaded")
            self.app.process_mgr.set_ipset_mode(orig_ipset)

            target_to_run = self.app.config.get("active_strategy", initial_strategy)
            if was_running:
                self.app.start_zapret(target_to_run)

    def create_strategy_card(self):
        # iOS 16 Inset Grouped Card
        self.card_strategy = ctk.CTkFrame(
            self, corner_radius=14, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        self.card_strategy.grid(row=2, column=0, padx=(16, 20), pady=(0, 10), sticky="ew")
        self.card_strategy.grid_columnconfigure(0, weight=1)

        # Header with toggle
        header_frame = ctk.CTkFrame(self.card_strategy, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(header_frame, text="Активная стратегия", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.pack(side="left")

        last_time = self.app.config.get("last_autotune_time", "")
        sub_text = f"Тест от {last_time}" if last_time else "Тест еще не проводился"
        self.lbl_strategy_sub = ctk.CTkLabel(
            header_frame, text=sub_text,
            font=AppFont.sub_bold() if last_time else AppFont.sub(),
            text_color=COLOR_PRIMARY if last_time else COLOR_TEXT_SECONDARY
        )
        self.lbl_strategy_sub.pack(side="left", padx=(10, 0))

# All strategies row is always visible without toggle button

        self.strategy_var = ctk.StringVar(value=self.app.config.get("active_strategy", ""))
        strategies = self.app.strategy_mgr.list_strategies()
        self.strategy_names = [s["name"] for s in strategies]
        if not self.strategy_names:
            self.strategy_names = ["general.bat"]

        # 1. Top 3 Rounded Strategy Tiles Grid
        self.top3_container = ctk.CTkFrame(self.card_strategy, fg_color="transparent")
        self.top3_container.grid(row=1, column=0, padx=12, pady=(4, 6), sticky="ew")

        # 2. All Strategies Dropdown (Windows Explorer Natural Sort Order)
        self.dropdown_container = ctk.CTkFrame(self.card_strategy, fg_color="transparent")
        self.dropdown_container.grid(row=2, column=0, padx=16, pady=(2, 6), sticky="ew")
        self.dropdown_container.grid_columnconfigure(0, weight=1)

        display_values = self._build_strategy_display_list()
        self.strategy_map = dict(zip(display_values, self.strategy_names_filtered))
        self.reverse_strategy_map = dict(zip(self.strategy_names_filtered, display_values))

        current_strat = self.strategy_var.get()
        if current_strat and current_strat in self.reverse_strategy_map:
            current_display = self.reverse_strategy_map[current_strat]
        else:
            current_display = "Выберите стратегию..."

        lbl_all = ctk.CTkLabel(
            self.dropdown_container, text="Выбор из всех пресетов:",
            font=AppFont.sub_bold(), text_color=COLOR_TEXT_SECONDARY, anchor="w"
        )
        lbl_all.grid(row=0, column=0, padx=2, pady=(0, 3), sticky="w")

        self.strategy_dropdown = IOSOptionMenu(
            self.dropdown_container, values=display_values, height=36,
            font=AppFont.body_bold(),
            fg_color=COLOR_BG_CONTROL,
            command=self.on_strategy_selected,
            dropdown_font=AppFont.body()
        )
        self.strategy_dropdown.set(current_display)
        self.strategy_dropdown.grid(row=1, column=0, sticky="ew")

        # Visible by default
        self.show_all_strategies = True

        # Render Top 3 Tiles
        self._render_top3_tiles()

        # Description label
        self.lbl_desc = ctk.CTkLabel(
            self.card_strategy, text="Основная универсальная стратегия",
            font=AppFont.body(), text_color=COLOR_TEXT_SECONDARY, anchor="w"
        )
        self.lbl_desc.grid(row=3, column=0, padx=16, pady=(4, 14), sticky="w")
        
        self.update_metrics_and_description(self.strategy_var.get())

    def _get_top_3_strategies(self):
        ratings = self.app.config.get("strategy_ratings", {})
        
        def get_score_key(s_name):
            rate_info = ratings.get(s_name)
            if isinstance(rate_info, dict):
                score = rate_info.get("score", 0)
                lat = rate_info.get("avg_latency", 0)
                return score, -lat if lat > 0 else -99999
            elif isinstance(rate_info, (int, float)):
                return rate_info, 0
            return -1, -99999

        sorted_by_rating = sorted(self.strategy_names, key=get_score_key, reverse=True)
        return sorted_by_rating[:3]

    def _render_top3_tiles(self):
        for w in self.top3_container.winfo_children():
            w.destroy()

        top3 = self._get_top_3_strategies()
        ratings = self.app.config.get("strategy_ratings", {})
        active_strat = self.strategy_var.get()
        has_tested = any(isinstance(v, dict) and v.get("score", 0) > 0 for v in ratings.values())

        ranks = [("#1", COLOR_RANK_GOLD), ("#2", COLOR_RANK_SILVER), ("#3", COLOR_RANK_BRONZE)]

        self.top3_container.grid_columnconfigure(0, weight=1)
        self.top3_container.grid_columnconfigure(1, weight=1)
        self.top3_container.grid_columnconfigure(2, weight=1)

        for col, s_name in enumerate(top3):
            is_active = bool(active_strat and s_name == active_strat)
            rate_info = ratings.get(s_name, {})
            lat = rate_info.get("avg_latency", 0) if isinstance(rate_info, dict) else 0

            if has_tested:
                rank_label, rank_color = ranks[col] if col < len(ranks) else (f"#{col+1}", "#8E8E93")
            else:
                rank_label, rank_color = ("Пресет", "#8E8E93")

            clean_name = get_smart_strategy_name(s_name)

            # Active vs inactive card styling
            bg_col = ("#EDF5FF", "#18283B") if is_active else ("#F6F6F9", "#232327")
            border_col = COLOR_PRIMARY if is_active else ("#E8E8EE", "#2E2E34")
            border_w = 2 if is_active else 1

            tile = ctk.CTkFrame(
                self.top3_container, corner_radius=RADIUS_TILE,
                fg_color=bg_col, border_width=border_w, border_color=border_col,
                cursor="hand2"
            )
            tile.grid(row=0, column=col, padx=4, pady=3, sticky="nsew")
            tile.grid_columnconfigure(0, weight=1)

            # Top row: Rank badge + Latency
            hdr = ctk.CTkFrame(tile, fg_color="transparent")
            hdr.pack(fill="x", padx=8, pady=(8, 2))

            lbl_rank = ctk.CTkLabel(
                hdr, text=rank_label, font=AppFont.sub_bold(),
                text_color=rank_color
            )
            lbl_rank.pack(side="left")

            lat_str = f"{int(lat)} ms" if (has_tested and lat > 0) else "-- ms"
            lbl_lat = ctk.CTkLabel(
                hdr, text=lat_str, font=AppFont.small_bold(),
                text_color=COLOR_SUCCESS if (has_tested and lat > 0) else COLOR_TEXT_SECONDARY
            )
            lbl_lat.pack(side="right")

            # Strategy name (Bold)
            lbl_name = ctk.CTkLabel(
                tile, text=clean_name, font=AppFont.body_bold(),
                text_color=COLOR_TEXT_PRIMARY, wraplength=140
            )
            lbl_name.pack(padx=6, pady=(1, 3))

            # Service mini indicators (iOS Brand Badges with Status Zone)
            badge_row = ctk.CTkFrame(tile, fg_color="transparent")
            badge_row.pack(padx=6, pady=(0, 7))

            def get_pill_style(state):
                if state == "ok":
                    return ("#E3F9E5", "#142E1B"), ("#1B7C37", "#34D399"), " ●"
                elif state == "partial":
                    return ("#FFF4E5", "#32230D"), ("#B76E00", "#FBBF24"), " ▲"
                elif state == "fail":
                    return ("#FEE8E7", "#341718"), ("#C92A2A", "#FF6B6B"), " ✕"
                else:
                    return ("#EBEBF0", "#222226"), ("#8E8E93", "#8E8E93"), " ○"

            default_service_state = "ok" if has_tested else "none"
            yt_state = rate_info.get("yt_state", default_service_state)
            dc_state = rate_info.get("dc_state", default_service_state)
            web_state = rate_info.get("web_state", default_service_state)

            yt_bg, yt_col, yt_sym = get_pill_style(yt_state)
            dc_bg, dc_col, dc_sym = get_pill_style(dc_state)
            web_bg, web_col, web_sym = get_pill_style(web_state)

            lbl_yt = ctk.CTkLabel(
                badge_row, text=yt_sym, font=AppFont.small_bold(),
                image=self.img_yt, compound="left",
                text_color=yt_col, fg_color=yt_bg, corner_radius=4, height=18, padx=3
            )
            lbl_yt.pack(side="left", padx=1)

            lbl_dc = ctk.CTkLabel(
                badge_row, text=dc_sym, font=AppFont.small_bold(),
                image=self.img_dc, compound="left",
                text_color=dc_col, fg_color=dc_bg, corner_radius=4, height=18, padx=1
            )
            lbl_dc.pack(side="left", padx=1)

            lbl_web = ctk.CTkLabel(
                badge_row, text=web_sym, font=AppFont.small_bold(),
                image=self.img_web, compound="left",
                text_color=web_col, fg_color=web_bg, corner_radius=4, height=18, padx=1
            )
            lbl_web.pack(side="left", padx=1)

            if is_active:
                lbl_chk = ctk.CTkLabel(badge_row, text=" ●", font=AppFont.sub_bold(), text_color=COLOR_PRIMARY)
                lbl_chk.pack(side="left", padx=1)

            # Click binding for the entire tile and children
            def make_click_cb(strat_name_target):
                return lambda e: self.select_strategy(strat_name_target)

            tile.bind("<Button-1>", make_click_cb(s_name))
            for child in [hdr, lbl_rank, lbl_lat, lbl_name, badge_row, lbl_yt, lbl_dc, lbl_web]:
                child.bind("<Button-1>", make_click_cb(s_name))

            UIAnimator.attach_smooth_hover(
                tile,
                normal_color=bg_col,
                hover_color=("#E2EDF9", "#22374E") if is_active else ("#EAEAEF", "#2B2B30")
            )

        # Smart Focus: If active strategy is NOT in Top 3, highlight the dropdown container
        active_in_top3 = any((s == active_strat) for s in top3)
        if not active_in_top3 and active_strat:
            self.dropdown_container.configure(border_width=0) # Ensure container has no border
            self.strategy_dropdown.configure(border_color=("#007AFF", "#0A84FF"), border_width=2)
        else:
            self.dropdown_container.configure(border_width=0)
            self.strategy_dropdown.configure(border_width=0)


    def toggle_strategy_list_mode(self):
        self.show_all_strategies = True
        if hasattr(self, 'dropdown_container'):
            self.dropdown_container.grid()

    def _build_strategy_display_list(self):
        ratings = self.app.config.get("strategy_ratings", {})

        def get_sort_key(s_name):
            rate_info = ratings.get(s_name)
            if not rate_info:
                return (1, 9999, s_name)
            if isinstance(rate_info, dict):
                score = rate_info.get("score", 0)
                lat = rate_info.get("avg_latency", 9999)
                if score > 0:
                    return (0, -score, lat if lat > 0 else 9999)
            return (1, 9999, s_name)

        sorted_strats = sorted(self.strategy_names, key=get_sort_key)
        self.strategy_names_filtered = sorted_strats
        display_list = []

        rank_counter = 1
        for name in sorted_strats:
            rate_info = ratings.get(name)
            clean_name = get_smart_strategy_name(name)
            if rate_info and isinstance(rate_info, dict) and rate_info.get("score", 0) > 0:
                lat = int(rate_info.get("avg_latency", 0))
                lat_str = f"  •  ⚡ {lat} ms" if lat > 0 else ""
                
                passed = rate_info.get("passed_count", 0)
                tot = rate_info.get("total_targets", 12)
                if passed == 0 and rate_info.get("score", 0) > 0:
                    passed = min(tot, max(1, rate_info.get("score", 0) // 3))
                score_str = f"  •  {passed}/{tot}" if passed > 0 else ""

                if rank_counter == 1:
                    prefix = "#1  "
                elif rank_counter == 2:
                    prefix = "#2  "
                elif rank_counter == 3:
                    prefix = "#3  "
                else:
                    prefix = f"   #{rank_counter}  "
                disp = f"{prefix}{clean_name}{lat_str}{score_str}"
                rank_counter += 1
            else:
                disp = f"   ▫️  {clean_name}"
            display_list.append(disp)

        return display_list

    def refresh_strategy_dropdown(self):
        display_values = self._build_strategy_display_list()
        self.strategy_map = dict(zip(display_values, self.strategy_names_filtered))
        self.reverse_strategy_map = dict(zip(self.strategy_names_filtered, display_values))
        self.strategy_dropdown.configure(values=display_values)
        current_strat = self.strategy_var.get()
        if current_strat and current_strat in self.reverse_strategy_map:
            current_display = self.reverse_strategy_map[current_strat]
        else:
            current_display = "Выберите стратегию..."
        self.strategy_dropdown.set(current_display)
        self._render_top3_tiles()
        self.update_metrics_and_description(current_strat)

        if hasattr(self, 'lbl_strategy_sub'):
            last_time = self.app.config.get("last_autotune_time", "")
            sub_text = f"Тест от {last_time}" if last_time else "Тест еще не проводился"
            self.lbl_strategy_sub.configure(
                text=sub_text,
                font=AppFont.sub_bold() if last_time else AppFont.sub(),
                text_color=COLOR_PRIMARY if last_time else COLOR_TEXT_SECONDARY
            )

    def select_strategy(self, strategy_name):
        actual_name = self.strategy_map.get(strategy_name, strategy_name)
        self.strategy_var.set(actual_name)
        self.app.config.set("active_strategy", actual_name)
        
        current_display = self.reverse_strategy_map.get(actual_name, actual_name)
        self.strategy_dropdown.set(current_display)
        self._render_top3_tiles()
        self.update_metrics_and_description(actual_name)

        if self.app.is_running():
            self.on_restart_click()

    def _create_ios_switch(self, parent, command):
        # Authentic Apple iOS 16 Toggle Switch
        return ctk.CTkSwitch(
            parent, text="", command=command,
            width=46, height=24, switch_width=44, switch_height=22, corner_radius=12,
            progress_color=("#34C759", "#30D158"),  # Signature Apple iOS Green
            fg_color=("#D1D1D6", "#39393D"),        # Apple System Gray 4 for crisp contrast against white
            button_color=("#E5E5EA", "#FFFFFF"),    # iOS physical button depth (visible against white)
            button_hover_color=("#D1D1D6", "#E5E5EA")
        )

    def _create_hairline(self, parent, row):
        line = ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER_DIVIDER)
        line.grid(row=row, column=0, columnspan=2, padx=16, pady=2, sticky="ew")
        return line

    def create_toggles_card(self):
        # 1. Network Engine Settings Card
        self.card_engine = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        self.card_engine.grid(row=3, column=0, padx=(16, 20), pady=(0, 10), sticky="ew")
        self.card_engine.grid_columnconfigure(0, weight=1, minsize=160)
        self.card_engine.grid_columnconfigure(1, weight=0)
        self.card_toggles = self.card_engine  # Backward compatibility alias

        header_eng = ctk.CTkLabel(
            self.card_engine, text="⚡ Параметры сетевого ядра",
            font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
        )
        header_eng.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 6), sticky="w")

        # 1.1 Mode Switcher
        lbl_mode = ctk.CTkLabel(
            self.card_engine, text="Режим работы:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_mode.grid(row=1, column=0, padx=16, pady=6, sticky="w")

        current_mode = self.app.config.get("run_mode", "service")
        mode_display = "Служба" if current_mode == "service" else "Процесс"
        self.mode_segmented = IOSSegmentedButton(
            self.card_engine, values=["Служба", "Процесс"],
            command=self.on_mode_change, height=30, width=240
        )
        self.mode_segmented.set(mode_display)
        self.mode_segmented.grid(row=1, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_engine, 2)

        # 1.2 IPSet Filter
        lbl_ipset = ctk.CTkLabel(
            self.card_engine, text="Фильтр IPSet:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_ipset.grid(row=3, column=0, padx=16, pady=6, sticky="w")

        current_ipset = self.app.lists_mgr.get_ipset_mode()
        ipset_map_display = {"loaded": "Списки", "any": "Все IP", "none": "Выкл"}
        self.ipset_segmented = IOSSegmentedButton(
            self.card_engine, values=["Списки", "Все IP", "Выкл"],
            command=self.on_ipset_change, height=30, width=240
        )
        self.ipset_segmented.set(ipset_map_display.get(current_ipset, "Списки"))
        self.ipset_segmented.grid(row=3, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_engine, 4)

        # 1.3 Game Filter Mode
        lbl_game = ctk.CTkLabel(
            self.card_engine, text="Игровой UDP:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_game.grid(row=5, column=0, padx=16, pady=(6, 12), sticky="w")

        current_game = self.app.lists_mgr.get_game_filter_mode()
        game_map_display = {"disabled": "Выкл", "all": "TCP+UDP", "tcp": "TCP", "udp": "UDP"}
        self.game_segmented = IOSSegmentedButton(
            self.card_engine, values=["Выкл", "TCP+UDP", "TCP", "UDP"],
            command=self.on_game_filter_change, height=30, width=240, font=AppFont.small_bold()
        )
        self.game_segmented.set(game_map_display.get(current_game, "Выкл"))
        self.game_segmented.grid(row=5, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_engine, 6)

        # 1.4 Smart Game Mode Switch (Auto-detect online games and isolate UDP)
        lbl_smart_game = ctk.CTkLabel(
            self.card_engine, text="Умный игровой режим:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_smart_game.grid(row=7, column=0, padx=16, pady=(6, 12), sticky="w")

        self.sw_smart_game = self._create_ios_switch(self.card_engine, self.on_smart_game_toggle)
        if self.app.config.get("smart_game_mode", True):
            self.sw_smart_game.select()
        else:
            self.sw_smart_game.deselect()
        self.sw_smart_game.grid(row=7, column=1, padx=16, pady=(6, 12), sticky="e")

        # 2. System Integration Settings Card
        self.card_system = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        self.card_system.grid(row=4, column=0, padx=(16, 20), pady=(0, 16), sticky="ew")
        self.card_system.grid_columnconfigure(0, weight=1, minsize=160)
        self.card_system.grid_columnconfigure(1, weight=0)

        header_sys = ctk.CTkLabel(
            self.card_system, text="Системная интеграция",
            font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
        )
        header_sys.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 6), sticky="w")

        # 2.1 Autostart Switch
        lbl_auto = ctk.CTkLabel(
            self.card_system, text="Автозапуск Windows:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_auto.grid(row=1, column=0, padx=16, pady=6, sticky="w")

        self.sw_autostart = self._create_ios_switch(self.card_system, self.on_autostart_toggle)
        if self.app.config.get("autostart", False):
            self.sw_autostart.select()
        else:
            self.sw_autostart.deselect()
        self.sw_autostart.grid(row=1, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_system, 2)

        # 2.2 Tray Minimization Switch
        lbl_tray = ctk.CTkLabel(
            self.card_system, text="Сворачивать в трей:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_tray.grid(row=3, column=0, padx=16, pady=6, sticky="w")

        self.sw_tray = self._create_ios_switch(self.card_system, self.on_tray_toggle)
        if self.app.config.get("minimize_to_tray", True):
            self.sw_tray.select()
        else:
            self.sw_tray.deselect()
        self.sw_tray.grid(row=3, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_system, 4)

        # 2.3 Start Minimized Switch
        lbl_start_min = ctk.CTkLabel(
            self.card_system, text="Запуск свернутым:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_start_min.grid(row=5, column=0, padx=16, pady=6, sticky="w")

        self.sw_start_min = self._create_ios_switch(self.card_system, self.on_start_min_toggle)
        if self.app.config.get("start_minimized", False):
            self.sw_start_min.select()
        else:
            self.sw_start_min.deselect()
        self.sw_start_min.grid(row=5, column=1, padx=16, pady=6, sticky="e")

        self._create_hairline(self.card_system, 6)

        # 2.4 Auto-Failover Switch
        lbl_failover = ctk.CTkLabel(
            self.card_system, text="Авто-переключение при сбое:",
            font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_failover.grid(row=7, column=0, padx=16, pady=(6, 12), sticky="w")

        self.sw_failover = self._create_ios_switch(self.card_system, self.on_failover_toggle)
        if self.app.config.get("auto_failover", True):
            self.sw_failover.select()
        else:
            self.sw_failover.deselect()
        self.sw_failover.grid(row=7, column=1, padx=16, pady=(6, 12), sticky="e")

    def on_failover_toggle(self):
        enabled = self.sw_failover.get() == 1
        self.app.config.set("auto_failover", enabled)

    def update_metrics_and_description(self, strategy_name):
        self.update_description(strategy_name)

    def update_description(self, strategy_name):
        if not strategy_name:
            self.lbl_desc.configure(text="Стратегия еще не выбрана. Рекомендуется запустить автоподбор для вашего провайдера.")
            return
        strategies = self.app.strategy_mgr.list_strategies()
        for s in strategies:
            if s["name"] == strategy_name:
                self.lbl_desc.configure(text=s["description"])
                return
        self.lbl_desc.configure(text="Пользовательский пресет")

    def on_strategy_selected(self, display_val):
        actual_name = self.strategy_map.get(display_val, display_val)
        if not actual_name or actual_name == "Выберите стратегию...":
            return
        self.strategy_var.set(actual_name)
        self.app.config.set("active_strategy", actual_name)
        self.update_metrics_and_description(actual_name)
        self._render_top3_tiles()

        if self.app.is_running():
            self.on_restart_click()

    def on_mode_change(self, val):
        mode = "service" if val == "Служба" else "process"
        self.app.config.set("run_mode", mode)
        if self.app.is_running():
            self.on_restart_click()

    def on_autostart_toggle(self):
        enabled = self.sw_autostart.get() == 1
        self.app.config.set("autostart", enabled)
        start_min = self.app.config.get("start_minimized", False)
        from ...core.autostart_mgr import AutostartManager
        AutostartManager.set_autostart(enabled, start_min)
        mode = self.app.config.get("run_mode", "service")
        self.app.process_mgr.set_autostart(enabled, self.strategy_var.get(), mode)

    def on_tray_toggle(self):
        enabled = self.sw_tray.get() == 1
        self.app.config.set("minimize_to_tray", enabled)

    def on_start_min_toggle(self):
        enabled = self.sw_start_min.get() == 1
        self.app.config.set("start_minimized", enabled)
        if self.app.config.get("autostart", True):
            from ...core.autostart_mgr import AutostartManager
            AutostartManager.set_autostart(True, enabled)

    def refresh_mode_switches(self):
        try:
            current_game = self.app.lists_mgr.get_game_filter_mode()
            game_map_display = {"disabled": "Выкл", "all": "TCP+UDP", "tcp": "TCP", "udp": "UDP"}
            if hasattr(self, 'game_segmented'):
                self.game_segmented.set(game_map_display.get(current_game, "Выкл"))

            current_ipset = self.app.lists_mgr.get_ipset_mode()
            ipset_map_display = {"loaded": "Списки", "any": "Все IP", "none": "Выкл"}
            if hasattr(self, 'ipset_segmented'):
                self.ipset_segmented.set(ipset_map_display.get(current_ipset, "Списки"))

            if hasattr(self, 'sw_autostart'):
                if self.app.config.get("autostart", True):
                    self.sw_autostart.select()
                else:
                    self.sw_autostart.deselect()
            if hasattr(self, 'sw_tray'):
                if self.app.config.get("minimize_to_tray", True):
                    self.sw_tray.select()
                else:
                    self.sw_tray.deselect()
        except Exception:
            pass

    def on_game_filter_change(self, val):
        rev_map = {"Выкл": "disabled", "TCP+UDP": "all", "TCP": "tcp", "UDP": "udp"}
        mode = rev_map.get(val, "disabled")
        self.app.lists_mgr.set_game_filter_mode(mode)
        if self.app.is_running():
            self.on_restart_click()

    def on_ipset_change(self, val):
        rev_map = {"Списки": "loaded", "Все IP": "any", "Выкл": "none"}
        mode = rev_map.get(val, "loaded")
        self.app.lists_mgr.set_ipset_mode(mode)
        if self.app.is_running():
            self.on_restart_click()

    def on_toggle_click(self):
        if self.is_busy:
            return

        self.is_busy = True
        is_currently_running = self.app.is_running()

        if is_currently_running:
            self.is_busy = True
            self.status_pill.configure(text="Остановка...", fg_color=COLOR_WARNING_TINT, text_color=COLOR_WARNING)
            self.status_title.configure(text="Остановка Zapret...")
            self.status_sub.configure(text="Выгрузка WinDivert и очистка сетевых правил...")
            self.btn_toggle.configure(text="Остановка...", fg_color=COLOR_DANGER, state="disabled")
            self.btn_restart.configure(state="disabled")

            def stop_worker():
                self.app.stop_zapret()
                self.app.root.after(0, self._finish_busy_state)

            threading.Thread(target=stop_worker, daemon=True).start()

        else:
            strat = self.strategy_var.get()
            if not strat or strat not in self.strategy_names:
                from tkinter import messagebox
                res = messagebox.askyesno(
                    "Стратегия не выбрана",
                    "Стратегия обхода еще не выбрана для данного компьютера.\n\n"
                    "Запустить автоматический подбор стратегии (Автоподбор) прямо сейчас?\n\n"
                    "• «Да» — протестировать и выбрать оптимальный пресет для вашего провайдера\n"
                    "• «Нет» — применить стандартную базовую стратегию (general.bat)"
                )
                if res:
                    self.is_busy = False
                    self.toggle_autotune()
                    return
                else:
                    self.select_strategy("general.bat")

            self.is_busy = True
            self.status_pill.configure(text="Запуск...", fg_color=COLOR_PRIMARY_TINT, text_color=COLOR_PRIMARY)
            self.status_title.configure(text="Запуск Zapret...")
            self.status_sub.configure(text="Инициализация WinDivert и применение стратегии...")
            self.btn_toggle.configure(text="Запуск...", fg_color=COLOR_PRIMARY, state="disabled")
            self.btn_restart.configure(state="disabled")

            def start_worker():
                self.app.start_zapret(self.strategy_var.get())
                self.app.root.after(0, self._finish_busy_state)

            threading.Thread(target=start_worker, daemon=True).start()

    def _finish_busy_state(self):
        self.is_busy = False
        self.update_status(self.app.is_running(), force=True)

    def on_restart_click(self):
        if self.is_busy:
            return

        self.is_busy = True
        self.status_pill.configure(text="Перезапуск...", fg_color=COLOR_WARNING_TINT, text_color=COLOR_WARNING)
        self.status_title.configure(text="Перезапуск...")
        self.btn_toggle.configure(state="disabled")
        self.btn_restart.configure(state="disabled")

        def restart_worker():
            self.app.restart_zapret(self.strategy_var.get())
            self.app.root.after(0, self._finish_busy_state)

        threading.Thread(target=restart_worker, daemon=True).start()

    def update_status(self, is_running, force=False):
        if self.is_busy:
            return

        if not force and getattr(self, 'last_status_state', None) == is_running:
            return

        self.last_status_state = is_running

        if is_running:
            self.status_pill.configure(
                text="●  Активен",
                fg_color=COLOR_SUCCESS_TINT,
                text_color=COLOR_SUCCESS
            )
            self.status_title.configure(text="Обход блокировок включен", text_color=COLOR_TEXT_PRIMARY)
            clean_s = get_smart_strategy_name(self.strategy_var.get())
            self.status_sub.configure(
                text=f"Пресет: {clean_s}  •  Служба WinDivert активна",
                text_color=COLOR_SUCCESS
            )
            self.card_status.configure(
                border_color=COLOR_SUCCESS_BORDER,
                fg_color=COLOR_SUCCESS_TINT
            )
            self.btn_toggle.configure(
                text="Остановить",
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DANGER_HOVER,
                text_color=COLOR_TEXT_WHITE,
                state="normal"
            )
            UIAnimator.attach_smooth_hover(self.btn_toggle, normal_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER)
            self.btn_restart.configure(state="normal")
        else:
            self.status_pill.configure(
                text="○  Остановлен",
                fg_color=COLOR_BG_CONTROL,
                text_color=COLOR_TEXT_SECONDARY
            )
            self.status_title.configure(text="Zapret остановлен", text_color=COLOR_TEXT_PRIMARY)
            self.status_sub.configure(
                text="Нажмите «Запустить» для включения обхода блокировок",
                text_color=COLOR_TEXT_SECONDARY
            )
            self.card_status.configure(
                border_color=COLOR_BORDER_CARD,
                fg_color=COLOR_BG_CARD
            )
            self.btn_toggle.configure(
                text="Запустить",
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                text_color=COLOR_TEXT_WHITE,
                state="normal"
            )
            UIAnimator.attach_smooth_hover(self.btn_toggle, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)
            self.btn_restart.configure(state="normal")
            if hasattr(self, 'lbl_speed'):
                self.lbl_speed.configure(text="")

    def update_traffic_speed(self, speed_str):
        if hasattr(self, 'lbl_speed'):
            if self.app.is_running() and speed_str and speed_str != "⚡ 0 КБ/с":
                self.lbl_speed.configure(text=f"•  {speed_str}")
            else:
                self.lbl_speed.configure(text="")

    def on_theme_changed(self):
        """Immediately re-renders dynamic widgets and Top 3 tiles with the new theme."""
        self._render_top3_tiles()
        self.update_status(self.app.is_running(), force=True)

    def update_session_stats(self, uptime_str, traffic_str, peak_str):
        pass

    def set_game_badge(self, is_active, game_name):
        if not hasattr(self, 'lbl_stat_game'):
            return
        if is_active and game_name:
            self.lbl_stat_game.configure(text=f"Игра: {game_name}")
            if not self.lbl_stat_game.winfo_ismapped():
                self.lbl_stat_game.pack(side="left", padx=(10, 0))
        else:
            if self.lbl_stat_game.winfo_ismapped():
                self.lbl_stat_game.pack_forget()

    def on_smart_game_toggle(self):
        val = bool(self.sw_smart_game.get())
        self.app.config.set("smart_game_mode", val)
        if not val:
            self.set_game_badge(False, None)
