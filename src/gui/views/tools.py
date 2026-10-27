import os
import subprocess
import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog
from ..widgets import IOSOptionMenu
from ..animator import UIAnimator
from ..design_system import (
    RADIUS_CARD, RADIUS_BTN,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_SUCCESS, COLOR_SUCCESS_HOVER,
    COLOR_DANGER, COLOR_DANGER_HOVER, COLOR_WARNING, COLOR_WARNING_HOVER, COLOR_BG_WINDOW,
    COLOR_BG_CARD, COLOR_BG_CARD_SUB, COLOR_BORDER_CARD, COLOR_BORDER_SUB, COLOR_BORDER_DIVIDER,
    COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_WHITE, AppFont, CURSOR_TEXT
)
from ...core.stream_benchmark import StreamBenchmark
from ...core.doh_mgr import DohManager

class ToolsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color=COLOR_BG_WINDOW)
        self.app = app_controller

        self.grid_columnconfigure(0, weight=1)
        self.create_updates_card()
        self.create_dns_card()
        self.create_stream_speed_card()
        self.create_site_tester_card()
        self.create_backup_card()
        self.create_diagnostics_card()

    def create_updates_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(card, text="Обновления и базы данных", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 5), sticky="w")

        # Version Info
        local_ver = self.app.updater.get_local_version()
        self.lbl_ver_info = ctk.CTkLabel(
            card, text=f"Установленная версия сборки: v{local_ver}",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_ver_info.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")

        # Buttons Row 1: IPSet update & Hosts update
        self.btn_update_ipset = ctk.CTkButton(
            card, text="Обновить IPSet", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(), fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.run_update_ipset
        )
        self.btn_update_ipset.grid(row=2, column=0, padx=(16, 5), pady=6, sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_update_ipset, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        self.btn_update_hosts = ctk.CTkButton(
            card, text="Обновить Hosts", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(), fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.run_update_hosts
        )
        self.btn_update_hosts.grid(row=2, column=1, padx=(5, 16), pady=6, sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_update_hosts, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # Button Row 2: Check for Zapret Updates (iOS Blue)
        self.btn_check_release = ctk.CTkButton(
            card, text="Проверить обновления сборки", height=36,
            font=AppFont.body_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.run_check_release
        )
        self.btn_check_release.grid(row=3, column=0, columnspan=2, padx=16, pady=(8, 14), sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_check_release, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)


    def create_dns_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=1, column=0, padx=15, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        header = ctk.CTkLabel(card, text="Безопасный DNS (Защита от подмены)", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="w")

        is_win11 = DohManager.is_windows_11()
        desc_text = (
            "Чистые защищенные DNS предотвращают перехват адресов и DNS-спуфинг. "
            + ("Поддерживается нативный зашифрованный DoH (DNS-over-HTTPS) Windows 11." if is_win11 else "")
        )
        desc = ctk.CTkLabel(
            card, text=desc_text,
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, wraplength=440, justify="left"
        )
        desc.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        if is_win11:
            self.dns_options = [
                "Автоматически (DHCP)",
                "Cloudflare DoH (Зашифрованный)",
                "Google DoH (Зашифрованный)",
                "Quad9 DoH (Зашифрованный)",
                "Cloudflare (1.1.1.1 - UDP)",
                "Google Public (8.8.8.8 - UDP)",
                "Quad9 Secure (9.9.9.9 - UDP)"
            ]
        else:
            self.dns_options = [
                "Автоматически (DHCP)",
                "Cloudflare (1.1.1.1)",
                "Google Public (8.8.8.8)",
                "Quad9 Secure (9.9.9.9)"
            ]

        self.opt_dns = IOSOptionMenu(
            card, values=self.dns_options, height=34,
            font=AppFont.body()
        )
        self.opt_dns.set(self.dns_options[0])
        self.opt_dns.grid(row=2, column=0, padx=(16, 6), pady=(4, 14), sticky="ew")

        btn_set_dns = ctk.CTkButton(
            card, text="Применить", height=34, width=110, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.on_apply_dns
        )
        btn_set_dns.grid(row=2, column=1, padx=(6, 16), pady=(4, 14), sticky="e")
        UIAnimator.attach_smooth_hover(btn_set_dns, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # DNS Status Capsule Badge
        self.dns_badge = ctk.CTkFrame(card, corner_radius=8, fg_color=COLOR_BG_CARD_SUB, border_width=1, border_color=COLOR_BORDER_SUB)
        self.dns_badge.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="ew")
        self.dns_badge.grid_columnconfigure(1, weight=1)

        self.dns_badge_dot = ctk.CTkLabel(
            self.dns_badge, text="🌐", font=ctk.CTkFont(family="Segoe UI", size=13),
            width=24
        )
        self.dns_badge_dot.grid(row=0, column=0, padx=(10, 4), pady=6)

        self.lbl_current_dns = ctk.CTkLabel(
            self.dns_badge, text="Текущий DNS: Загрузка...",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        )
        self.lbl_current_dns.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="w")
        self.update_current_dns()

    def update_current_dns(self):
        if not hasattr(self, 'lbl_current_dns'):
            return
        def fetch():
            try:
                doh = DohManager.get_doh_status()
                if doh.get("enabled"):
                    dot = "🔒"
                    disp_text = f"Текущий DNS:  {doh.get('provider')}  •  DoH Защищен"
                    text_color = COLOR_SUCCESS
                else:
                    dns = self.app.diagnostics.get_active_dns()
                    if not (self.app and self.app.root):
                        return
                    is_custom = dns not in ["DHCP (Автоматически)", "Неизвестно"]
                    dot = "🟢" if is_custom else "🌐"
                    disp_text = f"Текущий DNS:  {dns}"
                    text_color = COLOR_PRIMARY if is_custom else COLOR_TEXT_SECONDARY

                if self.app and self.app.root:
                    self.app.root.after(0, lambda: [
                        self.dns_badge_dot.configure(text=dot),
                        self.lbl_current_dns.configure(text=disp_text, text_color=text_color)
                    ])
            except Exception:
                pass
        threading.Thread(target=fetch, daemon=True).start()

    def create_stream_speed_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(
            card, text="Тест скорости YouTube (4K) и Discord Voice",
            font=AppFont.card_title(),
            text_color=COLOR_TEXT_PRIMARY
        )
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="w")

        desc = ctk.CTkLabel(
            card,
            text="Многопоточный замер реальной скорости YouTube CDN и проверка задержки / UDP Discord Voice.",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, wraplength=440, justify="left"
        )
        desc.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        # Inset results frame with two columns: YouTube and Discord
        res_container = ctk.CTkFrame(card, fg_color=COLOR_BG_CARD_SUB, corner_radius=10, border_width=1, border_color=COLOR_BORDER_SUB)
        res_container.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")
        res_container.grid_columnconfigure(0, weight=1)
        res_container.grid_columnconfigure(1, weight=1)

        # Col 0: YouTube
        yt_box = ctk.CTkFrame(res_container, fg_color="transparent")
        yt_box.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        lbl_yt_title = ctk.CTkLabel(yt_box, text="Потоки YouTube", font=AppFont.body_bold(), text_color=COLOR_TEXT_PRIMARY, anchor="w")
        lbl_yt_title.pack(anchor="w", fill="x")

        self.lbl_yt_speed = ctk.CTkLabel(
            yt_box, text="Скорость: —",
            font=AppFont.body_bold(),
            text_color=COLOR_PRIMARY,
            anchor="w"
        )
        self.lbl_yt_speed.pack(anchor="w", fill="x", pady=(2, 0))

        self.lbl_yt_quality = ctk.CTkLabel(
            yt_box, text="Качество: нажмите «Запустить тест»",
            font=AppFont.sub(),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=210,
            justify="left",
            anchor="w"
        )
        self.lbl_yt_quality.pack(anchor="w", fill="x")

        # Col 1: Discord Voice
        dc_box = ctk.CTkFrame(res_container, fg_color="transparent")
        dc_box.grid(row=0, column=1, padx=12, pady=10, sticky="ew")

        lbl_dc_title = ctk.CTkLabel(dc_box, text="Discord Voice & RTC", font=AppFont.body_bold(), text_color=COLOR_TEXT_PRIMARY, anchor="w")
        lbl_dc_title.pack(anchor="w", fill="x")

        self.lbl_dc_lat = ctk.CTkLabel(
            dc_box, text="Пинг: —",
            font=AppFont.body_bold(),
            text_color=("#5865F2", "#7289DA"),
            anchor="w"
        )
        self.lbl_dc_lat.pack(anchor="w", fill="x", pady=(2, 0))

        self.lbl_dc_status = ctk.CTkLabel(
            dc_box, text="Статус: готов к проверке",
            font=AppFont.sub(),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=210,
            justify="left",
            anchor="w"
        )
        self.lbl_dc_status.pack(anchor="w", fill="x")

        # Test trigger button
        self.btn_run_stream_test = ctk.CTkButton(
            card, text="Запустить тест скорости", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_run_stream_test
        )
        self.btn_run_stream_test.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_run_stream_test, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def create_site_tester_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=3, column=0, padx=15, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        header = ctk.CTkLabel(card, text="Проверка доступности сайтов (DPI-тестер)", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="w")

        desc = ctk.CTkLabel(
            card, text="Введите адрес сайта, чтобы проверить доступность через Zapret и добавить в список в 1 клик.",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, wraplength=440, justify="left"
        )
        desc.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        # Input + Test Button row
        self.entry_test_site = ctk.CTkEntry(
            card, placeholder_text="Например: rutracker.org или notion.so",
            height=34, font=AppFont.body(),
            fg_color=COLOR_BG_CONTROL, border_width=1, border_color=COLOR_BORDER_SUB, corner_radius=RADIUS_BTN,
            text_color=COLOR_TEXT_PRIMARY
        )
        try:
            self.entry_test_site._entry.configure(cursor=CURSOR_TEXT)
        except Exception:
            pass
        self.entry_test_site.grid(row=2, column=0, padx=(16, 6), pady=(4, 8), sticky="ew")
        self.entry_test_site.bind("<Return>", lambda e: self.on_run_site_test())

        self.btn_run_test = ctk.CTkButton(
            card, text="Проверить", height=34, width=110, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.on_run_site_test
        )
        self.btn_run_test.grid(row=2, column=1, padx=(6, 16), pady=(4, 8), sticky="e")
        UIAnimator.attach_smooth_hover(self.btn_run_test, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # Inset Container for Result & 1-Click Action Buttons
        self.site_test_badge = ctk.CTkFrame(
            card, corner_radius=10, fg_color=COLOR_BG_CARD_SUB,
            border_width=1, border_color=COLOR_BORDER_SUB
        )
        self.site_test_badge.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="ew")
        self.site_test_badge.grid_columnconfigure(0, weight=1)
        self.site_test_badge.grid_columnconfigure(1, weight=1)

        # Status Label
        self.lbl_site_test_res = ctk.CTkLabel(
            self.site_test_badge, text="Введите домен для проверки доступности или добавления в списки",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY,
            anchor="w", wraplength=440, justify="left"
        )
        self.lbl_site_test_res.grid(row=0, column=0, columnspan=2, padx=12, pady=(8, 6), sticky="w")

        # Hairline divider
        divider = ctk.CTkFrame(self.site_test_badge, height=1, fg_color=COLOR_BORDER_DIVIDER)
        divider.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        # Quick Add Action Buttons (Always accessible in 1 click!)
        self.btn_add_to_bypass = ctk.CTkButton(
            self.site_test_badge, text="В список обхода", height=30, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(),
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.on_add_domain_to_bypass
        )
        self.btn_add_to_bypass.grid(row=2, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_add_to_bypass, normal_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)

        self.btn_add_to_exclude = ctk.CTkButton(
            self.site_test_badge, text="В исключения", height=30, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(),
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.on_add_domain_to_exclude
        )
        self.btn_add_to_exclude.grid(row=2, column=1, padx=(5, 10), pady=(0, 10), sticky="ew")
        UIAnimator.attach_smooth_hover(self.btn_add_to_exclude, normal_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER)

        self.current_tested_domain = None

    def create_backup_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=4, column=0, padx=15, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(card, text="Резервное копирование (.zip)", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="w")

        desc = ctk.CTkLabel(
            card, text="Экспорт списков, настроек и параметров в zip-архив для переноса или бэкапа.",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, wraplength=440, justify="left"
        )
        desc.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="w")

        btn_export = ctk.CTkButton(
            card, text="Экспорт (.zip)", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_export_backup
        )
        btn_export.grid(row=2, column=0, padx=(16, 5), pady=(4, 6), sticky="ew")
        UIAnimator.attach_smooth_hover(btn_export, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        btn_import = ctk.CTkButton(
            card, text="Импорт (.zip)", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_import_backup
        )
        btn_import.grid(row=2, column=1, padx=(5, 16), pady=(4, 6), sticky="ew")
        UIAnimator.attach_smooth_hover(btn_import, normal_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)

        btn_clean = ctk.CTkButton(
            card, text="Подготовить к отправке другу", height=32, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(),
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER, text_color=COLOR_TEXT_PRIMARY,
            command=self.on_clean_for_export
        )
        btn_clean.grid(row=3, column=0, columnspan=2, padx=16, pady=(4, 14), sticky="ew")
        UIAnimator.attach_smooth_hover(btn_clean, normal_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER)

    def create_diagnostics_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=5, column=0, padx=15, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(header_frame, text="Диагностика и устранение неполадок", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.pack(side="left")

        btn_refresh_diag = ctk.CTkButton(
            header_frame, text="Диагностика", width=120, height=28, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.run_diagnostics
        )
        btn_refresh_diag.pack(side="right")
        UIAnimator.attach_smooth_hover(btn_refresh_diag, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # Diagnostics results box (iOS Inset Sub-box)
        self.diag_box = ctk.CTkFrame(card, fg_color=COLOR_BG_CARD_SUB, corner_radius=10, border_width=1, border_color=COLOR_BORDER_SUB)
        self.diag_box.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        self.diag_box.grid_columnconfigure(0, weight=1)

        self.run_diagnostics()

        # Fix action buttons (2x2 grid with semantic iOS colors)
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=2, column=0, padx=16, pady=(8, 14), sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)

        # 1. Discord Cache (Discord Blurple)
        btn_discord_cache = ctk.CTkButton(
            actions_frame, text="Очистить кэш Discord", height=32, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=("#5865F2", "#5865F2"),
            hover_color=("#4752C4", "#4752C4"), text_color=COLOR_TEXT_WHITE,
            command=self.on_clear_discord_cache
        )
        btn_discord_cache.grid(row=0, column=0, padx=(0, 4), pady=3, sticky="ew")
        UIAnimator.attach_smooth_hover(btn_discord_cache, normal_color=("#5865F2", "#5865F2"), hover_color=("#4752C4", "#4752C4"))

        # 2. DNS Flush (iOS Network Blue)
        btn_flush_dns = ctk.CTkButton(
            actions_frame, text="Сбросить кэш DNS", height=32, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_flush_dns
        )
        btn_flush_dns.grid(row=0, column=1, padx=(4, 0), pady=3, sticky="ew")
        UIAnimator.attach_smooth_hover(btn_flush_dns, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # 3. WinDivert Reset (iOS Warning Amber Orange)
        btn_fix_divert = ctk.CTkButton(
            actions_frame, text="Сбросить WinDivert", height=32, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=COLOR_WARNING,
            hover_color=COLOR_WARNING_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_fix_windivert
        )
        btn_fix_divert.grid(row=1, column=0, padx=(0, 4), pady=3, sticky="ew")
        UIAnimator.attach_smooth_hover(btn_fix_divert, normal_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER)

        # 4. Stop Conflicting VPNs (iOS Destructive Red)
        btn_stop_vpn = ctk.CTkButton(
            actions_frame, text="Отключить сторонние VPN", height=32, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER, text_color=COLOR_TEXT_WHITE,
            command=self.on_stop_vpn
        )
        btn_stop_vpn.grid(row=1, column=1, padx=(4, 0), pady=3, sticky="ew")
        UIAnimator.attach_smooth_hover(btn_stop_vpn, normal_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER)

    def on_apply_dns(self):
        choice = self.opt_dns.get()
        if "DoH" in choice:
            key = "cloudflare"
            if "Google" in choice:
                key = "google"
            elif "Quad9" in choice:
                key = "quad9"

            ok, msg = DohManager.apply_doh(key)
            self.update_current_dns()
            if ok:
                messagebox.showinfo("Безопасный DoH DNS", f"Шифрованный системный DNS-over-HTTPS активирован!\n\nПрофиль: {choice}\n{msg}")
            else:
                messagebox.showerror("Ошибка DoH", f"Не удалось настроить DoH:\n{msg}")
            return

        if "Cloudflare" in choice:
            servers = '("1.1.1.1", "1.0.0.1")'
        elif "Google" in choice:
            servers = '("8.8.8.8", "8.8.4.4")'
        elif "Quad9" in choice:
            servers = '("9.9.9.9", "149.112.112.112")'
        else:
            servers = None

        try:
            # Clear any active DoH encryption template if returning to UDP/DHCP
            DohManager.apply_doh("dhcp")

            if servers:
                ps_cmd = f'$iface = Get-NetAdapter | Where-Object {{$_.Status -eq "Up"}} | Select-Object -First 1; Set-DnsClientServerAddress -InterfaceIndex $iface.ifIndex -ServerAddresses {servers}'
                subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )

            self.app.diagnostics.flush_dns()
            self.update_current_dns()
            messagebox.showinfo("DNS", f"DNS-серверы успешно настроены:\n{choice}")
        except Exception as e:
            messagebox.showerror("Ошибка DNS", f"Не удалось изменить DNS: {e}")

    def run_diagnostics(self):
        for widget in self.diag_box.winfo_children():
            widget.destroy()

        checks = self.app.diagnostics.run_all_checks()
        for idx, chk in enumerate(checks):
            card_bg = COLOR_BG_CARD
            border_c = COLOR_BORDER_CARD
            
            row = ctk.CTkFrame(self.diag_box, fg_color=card_bg, corner_radius=8, border_width=1, border_color=border_c)
            row.pack(fill="x", padx=6, pady=3)
            row.grid_columnconfigure(1, weight=1)

            if chk["status"] == "ok":
                icon_text = "✔️"
                icon_color = COLOR_SUCCESS
            elif chk["status"] == "warn":
                icon_text = "⚠️"
                icon_color = COLOR_WARNING
            else:
                icon_text = "❌"
                icon_color = COLOR_DANGER

            lbl_icon = ctk.CTkLabel(
                row, text=icon_text, font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=icon_color, width=28
            )
            lbl_icon.grid(row=0, column=0, padx=(8, 6), pady=6)

            lbl_msg = ctk.CTkLabel(
                row, text=chk["message"], font=AppFont.sub(),
                anchor="w", justify="left", text_color=COLOR_TEXT_PRIMARY,
                wraplength=390
            )
            lbl_msg.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="w")

    def _start_button_spinner(self, btn, text="Загрузка..."):
        original_text = btn.cget("text")
        btn.configure(state="disabled", text=f"⏳ {text}")
        
        def stop(restore_text=None):
            self.app.root.after(0, lambda: btn.configure(
                state="normal", text=restore_text or original_text
            ))
        return stop

    def run_update_ipset(self):
        stop_spinner = self._start_button_spinner(self.btn_update_ipset, "Обновление IPSet...")
        threading.Thread(target=self._update_ipset_worker, args=(stop_spinner,), daemon=True).start()

    def _update_ipset_worker(self, stop_spinner):
        try:
            ok, msg, has_changes = self.app.updater.update_ipset_list()
            if ok:
                messagebox.showinfo("База IPSet", msg)
            else:
                messagebox.showerror("Ошибка обновления IPSet", msg)
        except Exception as e:
            messagebox.showerror("Ошибка обновления IPSet", f"Произошла ошибка: {e}")
        finally:
            stop_spinner("Обновить IPSet")

    def run_update_hosts(self):
        stop_spinner = self._start_button_spinner(self.btn_update_hosts, "Обновление Hosts...")
        threading.Thread(target=self._update_hosts_worker, args=(stop_spinner,), daemon=True).start()

    def _update_hosts_worker(self, stop_spinner):
        try:
            ok, msg, has_changes = self.app.updater.update_hosts_file()
            if ok:
                messagebox.showinfo("Маршруты Hosts (Discord)", msg)
            else:
                messagebox.showerror("Ошибка обновления Hosts", msg)
        except Exception as e:
            messagebox.showerror("Ошибка обновления Hosts", f"Произошла ошибка: {e}")
        finally:
            stop_spinner("Обновить Hosts")

    def run_check_release(self):
        stop_spinner = self._start_button_spinner(self.btn_check_release, "Проверка релизов на GitHub...")
        threading.Thread(target=self._check_release_worker, args=(stop_spinner,), daemon=True).start()

    def _check_release_worker(self, stop_spinner):
        try:
            info = self.app.updater.check_latest_release()
            local_v = info["local_version"]
            latest_v = info["latest_version"]

            if info["has_update"]:
                msg = (
                    f"Найдена новая версия Zapret: v{latest_v} (текущая: v{local_v}).\n\n"
                    "Желаете скачать и установить обновление автоматически прямо сейчас?\n\n"
                    "• Все ваши персональные списки сайтов будут полностью сохранены.\n"
                    "• Новые домены от автора будут аккуратно добавлены с пометкой версии."
                )
                if messagebox.askyesno("Доступно обновление", msg):
                    was_running = self.app.is_running()
                    self.app.process_mgr.stop_all()
                    if self.app.root:
                        self.app.root.after(0, self.app.refresh_status_all)

                    def progress_cb(text):
                        self.app.root.after(0, lambda: self.btn_check_release.configure(text=f"⏳ {text}"))

                    ok, update_msg = self.app.updater.download_and_install_update(
                        info["download_url"], latest_v, progress_callback=progress_cb
                    )

                    if ok:
                        new_v = self.app.updater.get_local_version()
                        self.lbl_ver_info.configure(text=f"Установленная версия сборки: v{new_v}")
                        self.app.refresh_version_label()
                        self.app.lists.load_list_contents()
                        if was_running:
                            self.app.start_zapret()
                        messagebox.showinfo("Обновление завершено", f"{update_msg}\nВсе списки успешно сохранены и применены.")
                    else:
                        if was_running:
                            self.app.start_zapret()
                        messagebox.showerror("Ошибка обновления", update_msg)
            elif info.get("error"):
                messagebox.showwarning("Проверка обновлений", f"Не удалось проверить обновления: {info['error']}")
            else:
                messagebox.showinfo("Обновления не требуются", f"У вас уже установлена актуальная версия сборки (v{local_v}).")
        finally:
            stop_spinner("Проверить обновления сборки")

    def on_clear_discord_cache(self):
        ok, msg = self.app.diagnostics.clear_discord_cache()
        if ok:
            messagebox.showinfo("Очистка кэша", msg)
        else:
            messagebox.showwarning("Discord", msg)

    def on_flush_dns(self):
        ok, msg = self.app.diagnostics.flush_dns()
        messagebox.showinfo("DNS", msg)

    def on_fix_windivert(self):
        ok, msg = self.app.diagnostics.fix_windivert_conflict()
        self.run_diagnostics()
        self.app.refresh_status_all()
        messagebox.showinfo("WinDivert", msg)

    def on_stop_vpn(self):
        ok, msg = self.app.diagnostics.stop_all_vpn_services()
        self.run_diagnostics()
        messagebox.showinfo("VPN Службы", msg)

    def _extract_clean_domain(self, raw: str) -> str:
        if not raw:
            return ""
        import re
        clean = re.sub(r'^[a-zA-Z]+://', '', raw.strip())
        clean = clean.split('/')[0].split('?')[0].split('#')[0].split(':')[0].strip().lower()
        if clean.startswith("www."):
            clean = clean[4:]
        if not clean or "." not in clean or len(clean) < 3 or " " in clean:
            return ""
        return clean

    def on_run_site_test(self):
        raw = self.entry_test_site.get().strip()
        clean = self._extract_clean_domain(raw)
        if not clean:
            self.lbl_site_test_res.configure(
                text="Некорректный адрес домена (например: rutracker.org или notion.so)",
                text_color=COLOR_DANGER
            )
            return

        self.current_tested_domain = clean
        self.btn_run_test.configure(state="disabled", text="Тест...")
        self.lbl_site_test_res.configure(
            text=f"Проверка соединения с {clean}...",
            text_color=COLOR_PRIMARY
        )

        in_bypass = self.app.lists_mgr.is_domain_in_list("list-general-user.txt", clean)
        in_exclude = self.app.lists_mgr.is_domain_in_list("list-exclude-user.txt", clean)

        def worker():
            import urllib.request, urllib.error, time
            url = f"https://{clean}"
            start_t = time.time()
            list_tag = " • [В списке обхода ✔]" if in_bypass else (" • [В исключениях 🚫]" if in_exclude else "")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=4.5) as resp:
                    lat = int((time.time() - start_t) * 1000)
                    msg = f"🟢 Доступен ({resp.status} OK • Пинг: {lat} ms){list_tag} — Обход работает"
                    color = COLOR_SUCCESS
            except urllib.error.HTTPError as e:
                lat = int((time.time() - start_t) * 1000)
                if e.code in (401, 403, 404, 405):
                    msg = f"🟢 Сайт ответил ({e.code} • Пинг: {lat} ms){list_tag} — Связь есть"
                    color = COLOR_SUCCESS
                else:
                    msg = f"⚪ Ошибка сервера сайта (HTTP {e.code}){list_tag}"
                    color = COLOR_TEXT_SECONDARY
            except Exception:
                msg = f"🔴 Блокируется по DPI (таймаут/сброс){list_tag}. Добавьте в список обхода!"
                color = COLOR_DANGER

            def finish():
                self.btn_run_test.configure(state="normal", text="Проверить")
                self.lbl_site_test_res.configure(text=msg, text_color=color)

            if self.app and self.app.root:
                self.app.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def on_add_domain_to_bypass(self):
        self._add_domain_to_target_list("list-general-user.txt", "список обхода", is_bypass=True)

    def on_add_domain_to_exclude(self):
        self._add_domain_to_target_list("list-exclude-user.txt", "список исключений", is_bypass=False)

    def on_add_tested_domain_to_bypass(self):
        self.on_add_domain_to_bypass()

    def _add_domain_to_target_list(self, list_filename, list_display_name, is_bypass=True):
        raw = self.entry_test_site.get().strip()
        dom = self._extract_clean_domain(raw)
        if not dom:
            self.lbl_site_test_res.configure(
                text="Введите домен сайта в поле выше (например: rutracker.org)",
                text_color=COLOR_WARNING
            )
            return

        ok, already_exists, msg = self.app.lists_mgr.add_domain_to_list(list_filename, dom)
        target_btn = self.btn_add_to_bypass if is_bypass else self.btn_add_to_exclude

        if already_exists:
            self.lbl_site_test_res.configure(
                text=f"ℹ️ Домен {dom} уже присутствует в {list_display_name}",
                text_color=COLOR_WARNING
            )
            return

        if not ok:
            self.lbl_site_test_res.configure(
                text=f"Ошибка: {msg}",
                text_color=COLOR_DANGER
            )
            return

        # Refresh lists view tab if loaded
        if hasattr(self.app, "lists") and hasattr(self.app.lists, "load_list_contents"):
            try:
                self.app.lists.load_list_contents()
            except Exception:
                pass

        # Flush DNS cache
        if hasattr(self.app, "diagnostics"):
            try:
                self.app.diagnostics.flush_dns()
            except Exception:
                pass

        # Smooth restart of Zapret if running so changes apply instantly
        reloaded_str = ""
        if self.app.is_running():
            try:
                self.app.restart_zapret()
                reloaded_str = " • Фильтр перезапущен"
            except Exception:
                pass

        self.lbl_site_test_res.configure(
            text=f"Домен {dom} добавлен в {list_display_name}{reloaded_str}!",
            text_color=COLOR_SUCCESS
        )

        orig_text = "В список обхода" if is_bypass else "В исключения"
        target_btn.configure(text="Добавлен", state="disabled")
        self.after(2500, lambda: target_btn.configure(text=orig_text, state="normal"))

    def on_run_stream_test(self):
        self.btn_run_stream_test.configure(state="disabled", text="⏳ Тестирование потоков YouTube (CDN)...")
        self.lbl_yt_speed.configure(text="⚡ Загрузка блоков...", text_color=COLOR_PRIMARY)
        self.lbl_yt_quality.configure(text="Замер пропускной способности...", text_color=COLOR_TEXT_SECONDARY)
        self.lbl_dc_lat.configure(text="⏱️ Ожидание очереди...", text_color=COLOR_TEXT_SECONDARY)
        self.lbl_dc_status.configure(text="Готовится RTC/UDP опрос...", text_color=COLOR_TEXT_SECONDARY)

        def worker():
            yt_res = StreamBenchmark.test_youtube_streaming(timeout=5.5)

            def update_yt():
                self.btn_run_stream_test.configure(text="Проверка Discord RTC...")
                if yt_res.get("success"):
                    spd = yt_res.get("speed_mbps", 0.0)
                    ql = yt_res.get("quality_label", "")
                    color = yt_res.get("badge_color", COLOR_SUCCESS)
                    self.lbl_yt_speed.configure(text=f"⚡ {spd} Мбит/с  [{ql}]", text_color=color)
                    self.lbl_yt_quality.configure(text=yt_res.get("quality_desc", ""), text_color=color)
                else:
                    self.lbl_yt_speed.configure(text="Блокировка / Ошибка", text_color=COLOR_DANGER)
                    self.lbl_yt_quality.configure(text="Потоки YouTube не отвечают", text_color=COLOR_DANGER)

            if self.app and self.app.root:
                self.app.root.after(0, update_yt)

            dc_res = StreamBenchmark.test_discord_voice()

            def update_dc():
                if dc_res.get("success"):
                    lat = dc_res.get("latency_ms", 0)
                    loss = dc_res.get("packet_loss", "")
                    color = dc_res.get("badge_color", COLOR_SUCCESS)
                    self.lbl_dc_lat.configure(text=f"⏱️ {lat} ms  ({loss})", text_color=color)
                    self.lbl_dc_status.configure(text=dc_res.get("voice_status", ""), text_color=color)
                else:
                    self.lbl_dc_lat.configure(text="Недоступен", text_color=COLOR_DANGER)
                    self.lbl_dc_status.configure(text="RTC / UDP блокируются", text_color=COLOR_DANGER)

                self.btn_run_stream_test.configure(state="normal", text="Повторить тест скорости")

            if self.app and self.app.root:
                self.app.root.after(0, update_dc)

        threading.Thread(target=worker, daemon=True).start()

    def on_export_backup(self):
        import datetime, json, zipfile
        base_dir = self.app.lists_mgr.zapret_dir if hasattr(self.app, "lists_mgr") else self.app.config.get("zapret_dir")
        if not base_dir or not os.path.exists(base_dir):
            messagebox.showerror("Ошибка", "Каталог Zapret не найден.")
            return

        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = filedialog.asksaveasfilename(
            title="Экспорт резервной копии профиля",
            defaultextension=".zip",
            initialfile=f"Zapret_Profile_Backup_{date_str}.zip",
            filetypes=[("ZIP Archive", "*.zip"), ("All Files", "*.*")]
        )
        if not dest_path:
            return

        files_to_pack = [
            "manager_config.json",
            os.path.join("lists", "list-general-user.txt"),
            os.path.join("lists", "list-exclude-user.txt"),
            os.path.join("lists", "ipset-exclude-user.txt"),
            os.path.join("lists", "ipset-all-user.txt"),
            os.path.join("lists", "list-discord-user.txt"),
            os.path.join("lists", "list-google-user.txt"),
            os.path.join("lists", "active_discord.bin"),
            os.path.join("lists", "active_game.bin"),
            os.path.join("utils", "game_filter.enabled"),
        ]

        packed_files = []
        try:
            with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for rel in files_to_pack:
                    full = os.path.join(base_dir, rel)
                    if os.path.exists(full):
                        arc_name = rel.replace("\\", "/")
                        zf.write(full, arcname=arc_name)
                        packed_files.append(arc_name)

                manifest = {
                    "app": "ZapretManager",
                    "created_at": datetime.datetime.now().isoformat(),
                    "version": self.app.updater.get_local_version() if hasattr(self.app, "updater") else "1.10.1",
                    "active_strategy": self.app.config.get("active_strategy", "general.bat"),
                    "files": packed_files
                }
                zf.writestr("backup_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

            messagebox.showinfo(
                "Резервная копия создана",
                f"✅ Экспорт успешно завершен!\n\nФайл: {os.path.basename(dest_path)}\n"
                f"Сохранено элементов: {len(packed_files)} (конфигурация, списки, фейки)."
            )
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось создать архив:\n{e}")

    def on_import_backup(self):
        import zipfile
        base_dir = self.app.lists_mgr.zapret_dir if hasattr(self.app, "lists_mgr") else self.app.config.get("zapret_dir")
        if not base_dir or not os.path.exists(base_dir):
            messagebox.showerror("Ошибка", "Каталог Zapret не найден.")
            return

        src_path = filedialog.askopenfilename(
            title="Импорт резервной копии профиля",
            filetypes=[("ZIP Archive", "*.zip"), ("All Files", "*.*")]
        )
        if not src_path:
            return

        if not zipfile.is_zipfile(src_path):
            messagebox.showerror("Ошибка", "Выбранный файл не является корректным ZIP-архивом.")
            return

        confirm = messagebox.askyesno(
            "Восстановление профиля",
            "Вы уверены, что хотите восстановить списки и настройки из резервной копии?\n\n"
            "Текущие пользовательские списки и конфигурация будут заменены файлами из архива."
        )
        if not confirm:
            return

        was_running = self.app.is_running()
        if was_running:
            self.app.stop_zapret()

        restored_count = 0
        try:
            with zipfile.ZipFile(src_path, "r") as zf:
                infolist = zf.infolist()
                for member in infolist:
                    name = member.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name or ":" in name:
                        continue
                    if member.is_dir():
                        continue
                    if name == "manager_config.json" or name.startswith("lists/") or name.startswith("utils/"):
                        target_file = os.path.join(base_dir, os.path.normpath(name))
                        target_dir = os.path.dirname(target_file)
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir, exist_ok=True)
                        with open(target_file, "wb") as f_out:
                            f_out.write(zf.read(member))
                        restored_count += 1

            self.app.config.load()
            if hasattr(self.app, "lists"):
                self.app.lists.load_list_contents()
            if hasattr(self.app, "dashboard"):
                self.app.dashboard.refresh_strategy_dropdown()
                if hasattr(self.app.dashboard, "refresh_mode_switches"):
                    self.app.dashboard.refresh_mode_switches()

            if was_running:
                self.app.start_zapret()

            messagebox.showinfo(
                "Восстановление завершено",
                f"✅ Профиль успешно восстановлен!\n\nВосстановлено файлов: {restored_count}.\n"
                f"Списки и конфигурация обновлены."
            )
        except Exception as e:
            if was_running:
                self.app.start_zapret()
            messagebox.showerror("Ошибка восстановления", f"Не удалось распаковать архив:\n{e}")

    def on_clean_for_export(self):
        res = messagebox.askyesno(
            "Подготовка к отправке другу",
            "Очистить историю тестирования и сбросить выбор активной стратегии?\n\n"
            "Это действие:\n"
            "• Очистит результаты и время последнего теста\n"
            "• Очистит рейтинги и задержки вашего провайдера\n"
            "• Сбросит активную стратегию (чтобы у друга не запускался ваш пресет)\n"
            "• Сохранит ваши списки сайтов и настройки оформления\n\n"
            "После этого вы сможете заархивировать папку и отправить другу."
        )
        if res:
            self.app.config.clean_for_export()
            if hasattr(self.app, "dashboard"):
                self.app.dashboard.strategy_var.set("")
                self.app.dashboard.refresh_strategy_dropdown()
            messagebox.showinfo(
                "Готово",
                "✅ Данные тестирования очищены, выбор стратегии сброшен!\n\n"
                "Папка готова к архивации и передаче другому пользователю."
            )


