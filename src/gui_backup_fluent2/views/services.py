import customtkinter as ctk
import threading
from tkinter import messagebox
from ...core.services_mgr import ServicesManager
from ..animator import UIAnimator
from ..design_system import (
    RADIUS_CARD, RADIUS_BTN, RADIUS_CHECKBOX,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_SUCCESS, COLOR_SUCCESS_HOVER,
    COLOR_BG_WINDOW, COLOR_BG_CARD, COLOR_BORDER_CARD, COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_WHITE, AppFont
)

class ServicesView(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color=COLOR_BG_WINDOW)
        self.app = app_controller
        self.services_mgr = ServicesManager(self.app.config.get("zapret_dir"))

        self.grid_columnconfigure(0, weight=1)
        
        # UI State
        self.checkboxes = {}
        self.enabled_set = self.services_mgr.get_enabled_services()
        
        self.create_header()
        self.create_catalog()

    def create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame, text="🌍 Разблокировка сервисов (через Hosts)", 
            font=AppFont.title(), text_color=COLOR_TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")

        desc = ctk.CTkLabel(
            header_frame, 
            text="Разблокирует Gemini, ChatGPT, Copilot и соцсети без VPN.\nЗаписи привязываются к зарубежным IP в системном файле hosts.",
            font=AppFont.body(), text_color=COLOR_TEXT_SECONDARY, justify="left", wraplength=450
        )
        desc.grid(row=1, column=0, sticky="w", pady=(4, 8))

        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=6)

        self.btn_apply = ctk.CTkButton(
            btn_frame, text="💾 Сохранить и применить", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(), fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.apply_changes
        )
        self.btn_apply.pack(side="left", padx=(0, 10))
        UIAnimator.attach_smooth_hover(self.btn_apply, normal_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)

        self.btn_update = ctk.CTkButton(
            btn_frame, text="🔄 Обновить базу IP", height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.update_database
        )
        self.btn_update.pack(side="left")
        UIAnimator.attach_smooth_hover(self.btn_update, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def create_catalog(self):
        catalog = self.services_mgr.get_all_categories()
        service_map = self.services_mgr.get_service_mapping()

        row_idx = 1
        for cat_name, srv_list in catalog.items():
            valid_services = [s for s in srv_list if s in service_map]
            if not valid_services:
                continue

            # Category Inset Card
            card = ctk.CTkFrame(
                self, corner_radius=RADIUS_CARD, fg_color=COLOR_BG_CARD,
                border_width=1, border_color=COLOR_BORDER_CARD
            )
            card.grid(row=row_idx, column=0, padx=15, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            row_idx += 1

            # Category Header Frame
            cat_header = ctk.CTkFrame(card, fg_color="transparent")
            cat_header.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
            cat_header.grid_columnconfigure(0, weight=1)

            cat_icons = {
                "Искусственный интеллект": "🤖",
                "Соцсети": "💬",
                "Музыка": "🎵",
                "Торренты": "🧲",
                "Игры и Стриминг": "🎮",
                "Работа": "💼"
            }
            icon = cat_icons.get(cat_name, "📦")

            cat_lbl = ctk.CTkLabel(
                cat_header, text=f"{icon} {cat_name}",
                font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
            )
            cat_lbl.grid(row=0, column=0, sticky="w")

            # Quick Select/Deselect All button
            btn_toggle_cat = ctk.CTkButton(
                cat_header, text="Выбрать все", width=84, height=24, corner_radius=6,
                font=AppFont.small_bold(),
                fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
                text_color=COLOR_PRIMARY
            )
            btn_toggle_cat.grid(row=0, column=1, sticky="e")

            # Checkboxes container (2 Columns Grid)
            cb_frame = ctk.CTkFrame(card, fg_color="transparent")
            cb_frame.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
            cb_frame.grid_columnconfigure(0, weight=1)
            cb_frame.grid_columnconfigure(1, weight=1)

            cat_vars = []
            r, c = 0, 0
            for srv in valid_services:
                domain_count = len(service_map[srv])
                display_name = srv.capitalize()
                
                var = ctk.BooleanVar(value=(srv in self.enabled_set))
                self.checkboxes[srv] = var
                cat_vars.append(var)

                cb = ctk.CTkCheckBox(
                    cb_frame, text=f"{display_name} ({domain_count} доменов)",
                    variable=var, font=AppFont.body(),
                    checkbox_width=16, checkbox_height=16, corner_radius=RADIUS_CHECKBOX,
                    border_color=("#C7C7CC", "#48484A"),
                    text_color=COLOR_TEXT_PRIMARY,
                    fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, checkmark_color=COLOR_TEXT_WHITE
                )
                cb.grid(row=r, column=c, padx=(0, 10), pady=4, sticky="w")
                
                c += 1
                if c > 1:  # 2 columns max
                    c = 0
                    r += 1

            def make_toggle_handler(variables, button):
                def handler():
                    all_checked = all(v.get() for v in variables)
                    new_val = not all_checked
                    for v in variables:
                        v.set(new_val)
                    button.configure(text="Снять все" if new_val else "Выбрать все")
                return handler

            all_init_checked = all(v.get() for v in cat_vars)
            btn_toggle_cat.configure(
                text="Снять все" if all_init_checked else "Выбрать все",
                command=make_toggle_handler(cat_vars, btn_toggle_cat)
            )

    def apply_changes(self):
        selected = [srv for srv, var in self.checkboxes.items() if var.get()]
        ok, msg = self.services_mgr.apply_services(selected)
        if ok:
            messagebox.showinfo("Успех", msg)
        else:
            messagebox.showerror("Ошибка", msg)

    def update_database(self):
        self.btn_update.configure(state="disabled", text="Скачивание...")
        
        def worker():
            ok, msg = self.services_mgr.update_database()
            self.app.root.after(0, lambda: self._on_update_done(ok, msg))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_done(self, ok, msg):
        self.btn_update.configure(state="normal", text="🔄 Обновить базу IP")
        if ok:
            messagebox.showinfo("Обновлено", msg)
            self.enabled_set = self.services_mgr.get_enabled_services()
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget != self.winfo_children()[0]:
                    widget.destroy()
            self.create_catalog()
        else:
            messagebox.showerror("Ошибка", msg)
