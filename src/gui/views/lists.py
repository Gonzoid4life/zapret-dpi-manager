import customtkinter as ctk
import os
import re
import threading
import queue
import tkinter as tk
from tkinter import messagebox
from ..widgets import IOSSegmentedButton, IOSOptionMenu
from ..animator import UIAnimator
from ...core.preset_lists import PresetListsManager
from ...core.logger import logger
from ..design_system import (
    RADIUS_CARD, RADIUS_BTN,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_SUCCESS, COLOR_SUCCESS_HOVER,
    COLOR_DANGER, COLOR_DANGER_HOVER, COLOR_WARNING, COLOR_BG_WINDOW, COLOR_BG_CARD, COLOR_BORDER_CARD, COLOR_BORDER_SUB,
    COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_WHITE, AppFont, CURSOR_TEXT
)

class ListsView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color=COLOR_BG_WINDOW)
        self.app = app_controller

        self.list_filenames = [
            "list-general-user.txt",
            "list-exclude-user.txt",
            "ipset-exclude-user.txt"
        ]
        self.base_tab_titles = [
            "Обход",
            "Исключения",
            "IP-исключения"
        ]
        self.tab_to_file = dict(zip(self.base_tab_titles, self.list_filenames))
        self.file_to_tab = dict(zip(self.list_filenames, self.base_tab_titles))
        self.current_selected_file = self.list_filenames[0]
        self.list_buffers = {}

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Fakes card
        self.grid_rowconfigure(1, weight=1)  # Editor card

        self.create_fakes_card()
        self.create_lists_editor_card()

    def create_fakes_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=14, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=0, column=0, padx=15, pady=(10, 8), sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(card, text="Активные фейк-пакеты (Fake UDP)", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 4), sticky="w")

        lbl_fakes_desc = ctk.CTkLabel(
            card,
            text="💡 Фейк-пакеты (Fake UDP/TLS) отправляются перед основным запросом, сбивая фильтры ТСПУ (DPI). "
                 "Если в Discord заикается голос или возникают сбои — смените активный фейк и нажмите «Применить фейки».",
            font=AppFont.sub(),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=450,
            justify="left",
            anchor="w"
        )
        lbl_fakes_desc.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="ew")

        # Fakes selectors
        self.fake_names = self.app.lists_mgr.list_fake_bins()
        if not self.fake_names:
            self.fake_names = ["(файлы .bin не найдены)"]

        current_fakes = self.app.lists_mgr.get_current_fakes()

        # 1. Discord UDP Fake
        lbl_discord = ctk.CTkLabel(card, text="Discord Voice UDP Fake:", font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY)
        lbl_discord.grid(row=2, column=0, padx=16, pady=4, sticky="w")

        self.opt_discord_fake = IOSOptionMenu(
            card, values=self.fake_names, height=32, fg_color=COLOR_BG_CONTROL
        )
        if current_fakes["discord"] in self.fake_names:
            self.opt_discord_fake.set(current_fakes["discord"])
        self.opt_discord_fake.grid(row=2, column=1, padx=16, pady=4, sticky="ew")

        # 2. Game UDP Fake
        lbl_game = ctk.CTkLabel(card, text="Game Filter UDP Fake:", font=AppFont.body(), text_color=COLOR_TEXT_PRIMARY)
        lbl_game.grid(row=3, column=0, padx=16, pady=4, sticky="w")

        self.opt_game_fake = IOSOptionMenu(
            card, values=self.fake_names, height=32, fg_color=COLOR_BG_CONTROL
        )
        if current_fakes["game"] in self.fake_names:
            self.opt_game_fake.set(current_fakes["game"])
        self.opt_game_fake.grid(row=3, column=1, padx=16, pady=4, sticky="ew")

        # Apply button (iOS Blue)
        btn_apply_fakes = ctk.CTkButton(
            card, text="Применить фейки", height=32, width=160,
            font=AppFont.body_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.on_apply_fakes
        )
        btn_apply_fakes.grid(row=4, column=1, padx=16, pady=(8, 14), sticky="e")
        UIAnimator.attach_smooth_hover(btn_apply_fakes, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def create_lists_editor_card(self):
        card = ctk.CTkFrame(
            self, corner_radius=14, fg_color=COLOR_BG_CARD,
            border_width=1, border_color=COLOR_BORDER_CARD
        )
        card.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(4, weight=1)  # Textbox takes all dynamic vertical space

        # Header bar
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        header = ctk.CTkLabel(header_frame, text="Редактор списков", font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY)
        header.grid(row=0, column=0, sticky="w")

        btn_open_folder = ctk.CTkButton(
            header_frame, text="Папка lists", width=95, height=28, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(),
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.open_lists_folder
        )
        btn_open_folder.grid(row=0, column=1, sticky="e")
        UIAnimator.attach_smooth_hover(btn_open_folder, normal_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER)

        # Load file buffers
        for fname in self.list_filenames:
            self.list_buffers[fname] = self.app.lists_mgr.read_user_list(fname)

        # Tabs Bar with Dynamic Counters (iOS Segmented Picker)
        self.tab_titles_with_counts = self._compute_tab_titles()
        self.seg_tabs = IOSSegmentedButton(
            card, values=self.tab_titles_with_counts, height=32,
            font=AppFont.sub_bold(),
            command=self.on_tab_switched
        )
        self.seg_tabs.set(self.tab_titles_with_counts[0])
        self.seg_tabs.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="ew")

        # File purpose hint label
        self.file_descriptions = {
            "list-general-user.txt": "list-general-user.txt  •  Сайты для обхода блокировок (YouTube, Discord и др.)",
            "list-exclude-user.txt": "list-exclude-user.txt  •  Исключения (прямое соединение без обработки)",
            "ipset-exclude-user.txt": "ipset-exclude-user.txt  •  IP-адреса и подсети для прямого соединения"
        }

        self.lbl_file_desc = ctk.CTkLabel(
            card, text=self.file_descriptions.get(self.current_selected_file, ""),
            font=AppFont.sub_bold(),
            text_color=COLOR_PRIMARY,
            anchor="w"
        )
        self.lbl_file_desc.grid(row=2, column=0, padx=18, pady=(0, 6), sticky="w")

        # Action Toolbar (Search + Pinger + Presets + Quick Add)
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.grid(row=3, column=0, padx=16, pady=(0, 6), sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        toolbar.grid_columnconfigure(1, weight=0)
        toolbar.grid_columnconfigure(2, weight=0)
        toolbar.grid_columnconfigure(3, weight=0)

        # Search Entry (iOS Search Bar)
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Поиск домена...", height=32,
            font=AppFont.body(), corner_radius=10,
            fg_color=COLOR_BG_CONTROL, border_width=0,
            text_color=COLOR_TEXT_PRIMARY
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", self.on_search_text)
        try:
            self.search_entry._entry.configure(cursor=CURSOR_TEXT)
        except Exception:
            pass

        # Mass Pinger Button (⚡ Пинг сайтов)
        self.btn_mass_ping = ctk.CTkButton(
            toolbar, text="Пинг сайтов", height=32, width=110,
            font=AppFont.sub_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.show_mass_pinger_dialog
        )
        self.btn_mass_ping.grid(row=0, column=1, sticky="e", padx=(0, 6))
        UIAnimator.attach_smooth_hover(self.btn_mass_ping, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # Community Presets Button (📥 Базы)
        self.btn_community_presets = ctk.CTkButton(
            toolbar, text="Базы", height=32, width=80,
            font=AppFont.sub_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.show_community_presets_dialog
        )
        self.btn_community_presets.grid(row=0, column=2, sticky="e", padx=(0, 6))
        UIAnimator.attach_smooth_hover(self.btn_community_presets, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

        # Quick Add Button (iOS Green)
        btn_quick_add = ctk.CTkButton(
            toolbar, text="Добавить", height=32, width=95,
            font=AppFont.sub_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.show_quick_add_dialog
        )
        btn_quick_add.grid(row=0, column=3, sticky="e")
        UIAnimator.attach_smooth_hover(btn_quick_add, normal_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)

        # Unified Scalable Textbox (iOS Inset Text Editor)
        self.txt_editor = ctk.CTkTextbox(
            card, font=AppFont.mono(11),
            corner_radius=RADIUS_CARD, undo=True,
            fg_color=("#F8F8FA", "#141417"),
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1, border_color=COLOR_BORDER_CARD,
            cursor=CURSOR_TEXT
        )
        self.txt_editor.grid(row=4, column=0, padx=16, pady=2, sticky="nsew")

        # Insert content for first tab
        first_file = self.list_filenames[0]
        self.txt_editor.insert("1.0", self.list_buffers.get(first_file, ""))

        # Setup Complete Clipboard & Shortcut Support
        self.setup_textbox_clipboard(self.txt_editor)

        # Bottom Bar with Hint & Floating Save Button
        bottom_frame = ctk.CTkFrame(card, fg_color="transparent")
        bottom_frame.grid(row=5, column=0, padx=16, pady=(8, 14), sticky="ew")

        self.lbl_count = ctk.CTkLabel(
            bottom_frame, text=self._get_current_count_str(),
            font=AppFont.sub_bold(), text_color=COLOR_PRIMARY
        )
        self.lbl_count.pack(side="left")

        btn_save = ctk.CTkButton(
            bottom_frame, text="Сохранить списки", height=34, width=170,
            font=AppFont.body_bold(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE,
            command=self.save_list_contents
        )
        btn_save.pack(side="right")
        UIAnimator.attach_smooth_hover(btn_save, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def _compute_tab_titles(self):
        titles = []
        for base, fname in zip(self.base_tab_titles, self.list_filenames):
            content = self.list_buffers.get(fname, "")
            lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
            count = len(lines)
            titles.append(f"{base} ({count})")
        return titles

    def _get_current_count_str(self):
        content = self.list_buffers.get(self.current_selected_file, "")
        lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
        return f"Активных записей: {len(lines)}"

    def refresh_tab_titles(self):
        self.tab_titles_with_counts = self._compute_tab_titles()
        self.seg_tabs.configure(values=self.tab_titles_with_counts)
        cur_idx = self.list_filenames.index(self.current_selected_file)
        self.seg_tabs.set(self.tab_titles_with_counts[cur_idx])
        self.lbl_count.configure(text=self._get_current_count_str())
        if hasattr(self, 'lbl_file_desc'):
            self.lbl_file_desc.configure(text=self.file_descriptions.get(self.current_selected_file, ""))

    def load_list_contents(self):
        """Reloads all lists from disk into memory buffers and updates the UI editor."""
        for fname in self.list_filenames:
            self.list_buffers[fname] = self.app.lists_mgr.read_user_list(fname)
        content = self.list_buffers.get(self.current_selected_file, "")
        if hasattr(self, 'txt_editor'):
            self.txt_editor.delete("1.0", "end")
            self.txt_editor.insert("1.0", content)
        self.refresh_tab_titles()
        if hasattr(self, 'on_search_text'):
            self.on_search_text()

    def on_search_text(self, event=None):
        query = self.search_entry.get().strip().lower()
        tk_text = getattr(self.txt_editor, "_textbox", None) or self.txt_editor
        tk_text.tag_remove("search_highlight", "1.0", "end")

        if not query:
            return

        # Configure highlight tag
        tk_text.tag_config("search_highlight", background="#FFCC00", foreground="black")

        start_pos = "1.0"
        first_match = None
        while True:
            pos = tk_text.search(query, start_pos, nocase=True, stopindex="end")
            if not pos:
                break
            if not first_match:
                first_match = pos
            end_pos = f"{pos}+{len(query)}c"
            tk_text.tag_add("search_highlight", pos, end_pos)
            start_pos = end_pos

        if first_match:
            tk_text.see(first_match)

    def show_quick_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Быстрое добавление домена")
        dialog.geometry("480x240")
        dialog.resizable(False, False)
        dialog.transient(self.app.root)
        dialog.grab_set()

        lbl_title = ctk.CTkLabel(
            dialog, text="Добавить сайт в список разблокировки",
            font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_title.pack(padx=20, pady=(20, 4), anchor="w")

        lbl_sub = ctk.CTkLabel(
            dialog, text="Вставьте домен или любую ссылку (ссылка будет автоматически очищена):",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY
        )
        lbl_sub.pack(padx=20, pady=(0, 10), anchor="w")

        entry_url = ctk.CTkEntry(
            dialog, placeholder_text="https://example.com/watch?v=... или notion.so",
            height=36, font=AppFont.body(), corner_radius=RADIUS_BTN,
            fg_color=COLOR_BG_CONTROL, border_width=1, border_color=COLOR_BORDER_SUB,
            text_color=COLOR_TEXT_PRIMARY
        )
        try:
            entry_url._entry.configure(cursor=CURSOR_TEXT)
        except Exception:
            pass
        entry_url.pack(padx=20, pady=5, fill="x")
        entry_url.focus_set()

        lbl_status = ctk.CTkLabel(dialog, text="", font=AppFont.sub())
        lbl_status.pack(padx=20, pady=2, anchor="w")

        def _do_add():
            raw = entry_url.get().strip()
            if not raw:
                lbl_status.configure(text="Введите ссылку или домен!", text_color=COLOR_DANGER)
                return

            # Clean URL
            clean = raw
            clean = re.sub(r'^[a-zA-Z]+://', '', clean)
            clean = clean.split('/')[0].split('?')[0].split('#')[0].split(':')[0]
            if clean.startswith("www."):
                clean = clean[4:]
            clean = clean.lower().strip()

            if not clean or "." not in clean:
                lbl_status.configure(text="Некорректный адрес домена!", text_color=COLOR_DANGER)
                return

            # Read current content
            current_content = self.txt_editor.get("1.0", "end-1c")
            existing_lines = [l.strip().lower() for l in current_content.splitlines()]

            if clean in existing_lines:
                lbl_status.configure(text=f"Домен «{clean}» уже есть в списке!", text_color=COLOR_WARNING)
                return

            # Append domain to editor
            if current_content and not current_content.endswith("\n"):
                self.txt_editor.insert("end", "\n")
            self.txt_editor.insert("end", f"{clean}\n")
            
            # Update buffer
            self.list_buffers[self.current_selected_file] = self.txt_editor.get("1.0", "end-1c")
            self.refresh_tab_titles()

            # Auto-save
            self.app.lists_mgr.save_user_list(self.current_selected_file, self.list_buffers[self.current_selected_file])
            if self.app.is_running():
                self.app.restart_zapret()

            dialog.destroy()
            messagebox.showinfo("Успешно", f"Домен «{clean}» добавлен в список и применен!")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(padx=20, pady=(10, 15), fill="x")

        btn_cancel = ctk.CTkButton(
            btn_row, text="Отмена", width=100, height=32, corner_radius=RADIUS_BTN,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER, text_color=COLOR_TEXT_PRIMARY,
            command=dialog.destroy
        )
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_submit = ctk.CTkButton(
            btn_row, text="Добавить и применить", width=180, height=32, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, text_color=COLOR_TEXT_WHITE,
            command=_do_add
        )
        btn_submit.pack(side="right")
        entry_url.bind("<Return>", lambda e: _do_add())

    def show_community_presets_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Быстрый импорт готовых баз сообщества")
        dialog.geometry("540x520")
        dialog.resizable(False, False)
        dialog.transient(self.app.root)
        dialog.grab_set()

        lbl_title = ctk.CTkLabel(
            dialog, text="Готовые базы доменов сообщества",
            font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_title.pack(padx=20, pady=(16, 4), anchor="w")

        lbl_sub = ctk.CTkLabel(
            dialog, text="Выберите категории сайтов для безопасного добавления в список обхода.\nДубликаты будут автоматически пропущены, существующие записи сохранены.",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, justify="left"
        )
        lbl_sub.pack(padx=20, pady=(0, 10), anchor="w")

        categories = PresetListsManager.get_categories()
        checkbox_vars = {}

        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color=COLOR_BG_CARD, corner_radius=10, height=270)
        scroll_frame.pack(padx=20, pady=4, fill="both", expand=True)

        for cat in categories:
            ck_var = ctk.BooleanVar(value=True if cat["id"] in ("youtube_boost", "discord_voice") else False)
            checkbox_vars[cat["id"]] = ck_var

            item_card = ctk.CTkFrame(scroll_frame, fg_color=COLOR_BG_CONTROL, corner_radius=8)
            item_card.pack(fill="x", padx=4, pady=4)
            item_card.grid_columnconfigure(0, weight=1)

            cb = ctk.CTkCheckBox(
                item_card, text=f"{cat['name']} ({cat['count']} доменов)",
                variable=ck_var, font=AppFont.body_bold(),
                text_color=COLOR_TEXT_PRIMARY, fg_color=COLOR_PRIMARY,
                checkbox_height=20, checkbox_width=20, corner_radius=6
            )
            cb.pack(padx=12, pady=(8, 2), anchor="w")

            desc_lbl = ctk.CTkLabel(
                item_card, text=cat["desc"],
                font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY,
                anchor="w", justify="left"
            )
            desc_lbl.pack(padx=12, pady=(0, 8), anchor="w")

        lbl_status = ctk.CTkLabel(dialog, text="", font=AppFont.sub())
        lbl_status.pack(padx=20, pady=2, anchor="w")

        def _do_import():
            selected = [cid for cid, v in checkbox_vars.items() if v.get()]
            if not selected:
                lbl_status.configure(text="Выберите хотя бы одну категорию!", text_color=COLOR_WARNING)
                return

            base_dir = self.app.lists_mgr.zapret_dir if hasattr(self.app, "lists_mgr") else self.app.config.get("zapret_dir")
            added, skipped = PresetListsManager.import_presets_to_general_user(selected, base_dir)

            # Reload lists into buffers & editor
            self.load_list_contents()
            self.refresh_tab_titles()

            if self.app.is_running():
                self.app.restart_zapret()

            dialog.destroy()
            messagebox.showinfo(
                "Импорт завершен",
                f"Базы сообщества успешно импортированы!\n\n"
                f"• Добавлено новых доменов: {added}\n"
                f"• Пропущено существующих (дубликатов): {skipped}\n\n"
                f"Списки сохранены и правила обновлены."
            )

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(padx=20, pady=(10, 16), fill="x")

        btn_cancel = ctk.CTkButton(
            btn_row, text="Отмена", width=100, height=34, corner_radius=RADIUS_BTN,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER, text_color=COLOR_TEXT_PRIMARY,
            command=dialog.destroy
        )
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_submit = ctk.CTkButton(
            btn_row, text="Импортировать выбранные", width=220, height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(),
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_WHITE,
            command=_do_import
        )
        btn_submit.pack(side="right")
        UIAnimator.attach_smooth_hover(btn_submit, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def show_mass_pinger_dialog(self):
        # Extract domains from current file
        content = self.txt_editor.get("1.0", "end-1c")
        raw_lines = [l.strip() for l in content.splitlines()]
        domains = []
        for l in raw_lines:
            if not l or l.startswith("#"):
                continue
            d = l.split()[0].lower()
            d = re.sub(r'^[a-zA-Z]+://', '', d).split('/')[0].split(':')[0]
            if d.startswith("www."):
                d = d[4:]
            if d and "." in d and d not in domains:
                domains.append(d)

        if not domains:
            messagebox.showinfo("Пакетная проверка", f"В текущем файле ({self.current_selected_file}) нет доменов для проверки!")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Пакетная проверка доступности сайтов")
        dialog.geometry("600x560")
        dialog.minsize(540, 480)
        dialog.transient(self.app.root)
        dialog.grab_set()

        lbl_title = ctk.CTkLabel(
            dialog, text="Пакетная проверка доступности сайтов",
            font=AppFont.card_title(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_title.pack(padx=20, pady=(16, 2), anchor="w")

        lbl_sub = ctk.CTkLabel(
            dialog,
            text=f"Проверка ответа через HTTP/HTTPS для списка «{self.current_selected_file}» ({len(domains)} сайтов).\n"
                 "Зеленый статус означает, что сервер отвечает и обход DPI работает штатно.",
            font=AppFont.sub(), text_color=COLOR_TEXT_SECONDARY, justify="left"
        )
        lbl_sub.pack(padx=20, pady=(0, 8), anchor="w")

        # Top progress bar and summary counter
        prog_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        prog_frame.pack(padx=20, pady=(0, 8), fill="x")

        progress_bar = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4)
        progress_bar.set(0.0)
        progress_bar.pack(fill="x", pady=(2, 6))

        lbl_progress_status = ctk.CTkLabel(
            prog_frame, text=f"Готово к проверке • 0 / {len(domains)}",
            font=AppFont.sub_bold(), text_color=COLOR_TEXT_PRIMARY
        )
        lbl_progress_status.pack(anchor="w")

        # Scrollable container for site rows
        scroll_results = ctk.CTkScrollableFrame(dialog, fg_color=COLOR_BG_CARD, corner_radius=10, height=280)
        scroll_results.pack(padx=20, pady=4, fill="both", expand=True)

        # Pre-populate site cards
        domain_widgets = {}
        for dom in domains:
            row = ctk.CTkFrame(scroll_results, fg_color=COLOR_BG_CONTROL, corner_radius=6, height=28)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(0, weight=1)

            lbl_d = ctk.CTkLabel(
                row, text=dom, font=ctk.CTkFont(family="Consolas", size=11),
                text_color=COLOR_TEXT_PRIMARY, anchor="w"
            )
            lbl_d.grid(row=0, column=0, padx=10, pady=3, sticky="w")

            lbl_s = ctk.CTkLabel(
                row, text="Ожидание", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color=COLOR_TEXT_SECONDARY, anchor="e"
            )
            lbl_s.grid(row=0, column=1, padx=10, pady=3, sticky="e")
            domain_widgets[dom] = (row, lbl_s)

        # Bottom buttons frame
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(padx=20, pady=(10, 16), fill="x")

        btn_close = ctk.CTkButton(
            btn_row, text="Закрыть", width=90, height=34, corner_radius=RADIUS_BTN,
            fg_color=COLOR_BG_CONTROL, hover_color=COLOR_BG_CONTROL_HOVER, text_color=COLOR_TEXT_PRIMARY,
            command=dialog.destroy
        )
        btn_close.pack(side="right", padx=(8, 0))

        failed_domains = set()

        def _remove_failed_domains():
            if not failed_domains:
                return
            confirm = messagebox.askyesno(
                "Удаление неработающих",
                f"Удалить {len(failed_domains)} неработающих доменов из «{self.current_selected_file}»?\n\n"
                "Сайты, которые не ответили на запросы, будут безопасно убраны из списка."
            )
            if not confirm:
                return

            cur_text = self.txt_editor.get("1.0", "end-1c")
            new_lines = []
            for line in cur_text.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    clean = stripped.split()[0].lower()
                    clean = re.sub(r'^[a-zA-Z]+://', '', clean).split('/')[0].split(':')[0]
                    if clean.startswith("www."):
                        clean = clean[4:]
                    if clean in failed_domains:
                        continue
                new_lines.append(line)

            new_content = "\n".join(new_lines)
            self.txt_editor.delete("1.0", "end")
            self.txt_editor.insert("1.0", new_content)
            self.list_buffers[self.current_selected_file] = new_content
            self.app.lists_mgr.save_user_list(self.current_selected_file, new_content)
            self.refresh_tab_titles()

            if self.app.is_running():
                self.app.restart_zapret()

            btn_remove_dead.configure(state="disabled", text="Удалено")
            messagebox.showinfo("Очистка завершена", f"Успешно удалено {len(failed_domains)} недоступных доменов.")

        btn_remove_dead = ctk.CTkButton(
            btn_row, text="Удалить неработающие (0)", width=200, height=34, corner_radius=RADIUS_BTN,
            font=AppFont.sub_bold(), fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
            text_color=COLOR_TEXT_WHITE, state="disabled", command=_remove_failed_domains
        )
        btn_remove_dead.pack(side="right", padx=(8, 0))

        def _run_ping_worker():
            btn_start.configure(state="disabled", text="Проверка...")
            failed_domains.clear()
            btn_remove_dead.configure(state="disabled", text="Удалить неработающие (0)")

            q = queue.Queue()
            for d in domains:
                q.put(d)

            total = len(domains)
            completed_lock = threading.Lock()
            completed_count = 0
            ok_count = 0

            def worker_thread():
                nonlocal completed_count, ok_count
                import urllib.request, urllib.error, time
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                while not q.empty():
                    try:
                        d = q.get_nowait()
                    except queue.Empty:
                        break

                    url = f"https://{d}"
                    start_t = time.time()
                    is_ok = False
                    status_text = ""
                    lat = 0

                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=3.5) as resp:
                            lat = int((time.time() - start_t) * 1000)
                            status_text = f"🟢 HTTP {resp.status} ({lat} ms)"
                            is_ok = True
                    except urllib.error.HTTPError as e:
                        lat = int((time.time() - start_t) * 1000)
                        status_text = f"🟢 HTTP {e.code} ({lat} ms)"
                        is_ok = True
                    except Exception:
                        try:
                            # Fallback http
                            url_http = f"http://{d}"
                            req = urllib.request.Request(url_http, headers=headers)
                            with urllib.request.urlopen(req, timeout=3.0) as resp:
                                lat = int((time.time() - start_t) * 1000)
                                status_text = f"🟢 HTTP {resp.status} ({lat} ms)"
                                is_ok = True
                        except urllib.error.HTTPError as e:
                            lat = int((time.time() - start_t) * 1000)
                            status_text = f"🟢 HTTP {e.code} ({lat} ms)"
                            is_ok = True
                        except Exception:
                            status_text = "🔴 Таймаут / Блок"
                            is_ok = False

                    with completed_lock:
                        completed_count += 1
                        if is_ok:
                            ok_count += 1
                        else:
                            failed_domains.add(d)

                        cur_comp = completed_count
                        cur_ok = ok_count
                        cur_fail = len(failed_domains)

                    def update_ui(dom=d, ok=is_ok, st=status_text, comp=cur_comp, ok_cnt=cur_ok, fail_cnt=cur_fail):
                        if not dialog.winfo_exists():
                            return
                        if dom in domain_widgets:
                            _, lbl = domain_widgets[dom]
                            lbl.configure(text=st, text_color=COLOR_SUCCESS if ok else COLOR_DANGER)

                        progress = comp / total if total > 0 else 1.0
                        progress_bar.set(progress)
                        lbl_progress_status.configure(
                            text=f"Проверено: {comp} / {total}  (🟢 Доступно: {ok_cnt}  |  🔴 Заблокировано: {fail_cnt})"
                        )

                        if comp == total:
                            btn_start.configure(state="normal", text="Повторить")
                            if fail_cnt > 0:
                                btn_remove_dead.configure(
                                    state="normal", text=f"Удалить неработающие ({fail_cnt})"
                                )
                                logger.warn("PINGER", f"Пакетная проверка: {ok_cnt} доступно, {fail_cnt} заблокировано/недоступно")
                            else:
                                logger.success("PINGER", f"Пакетная проверка завершена: все {total} сайтов доступны")

                    if self.app and self.app.root:
                        self.app.root.after(0, update_ui)

                    q.task_done()

            # Start 6 worker threads
            num_workers = min(6, total)
            for _ in range(num_workers):
                t = threading.Thread(target=worker_thread, daemon=True)
                t.start()

        btn_start = ctk.CTkButton(
            btn_row, text="Запустить проверку", width=170, height=34, corner_radius=RADIUS_BTN,
            font=AppFont.body_bold(), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_WHITE, command=_run_ping_worker
        )
        btn_start.pack(side="left")
        UIAnimator.attach_smooth_hover(btn_start, normal_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)

    def setup_textbox_clipboard(self, ctk_textbox):
        tk_text = getattr(ctk_textbox, "_textbox", None) or ctk_textbox

        def copy_selection(event=None):
            try:
                text = tk_text.get("sel.first", "sel.last")
                self.clipboard_clear()
                self.clipboard_append(text)
            except tk.TclError:
                pass
            return "break"

        def paste_selection(event=None):
            try:
                text = self.clipboard_get()
                try:
                    tk_text.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                tk_text.insert("insert", text)
                self.refresh_tab_titles()
            except tk.TclError:
                pass
            return "break"

        def cut_selection(event=None):
            try:
                text = tk_text.get("sel.first", "sel.last")
                self.clipboard_clear()
                self.clipboard_append(text)
                tk_text.delete("sel.first", "sel.last")
                self.refresh_tab_titles()
            except tk.TclError:
                pass
            return "break"

        def select_all(event=None):
            tk_text.tag_add("sel", "1.0", "end")
            return "break"

        def undo_action(event=None):
            try:
                tk_text.edit_undo()
                self.refresh_tab_titles()
            except tk.TclError:
                pass
            return "break"

        def on_ctrl_key(event):
            code = event.keycode
            if code == 67:   # C / С
                return copy_selection()
            elif code == 86: # V / М
                return paste_selection()
            elif code == 88: # X / Ч
                return cut_selection()
            elif code == 65: # A / Ф
                return select_all()
            elif code == 90: # Z / Я
                return undo_action()

        tk_text.bind("<Control-KeyPress>", on_ctrl_key)
        tk_text.bind("<Control-c>", copy_selection)
        tk_text.bind("<Control-C>", copy_selection)
        tk_text.bind("<Control-v>", paste_selection)
        tk_text.bind("<Control-V>", paste_selection)
        tk_text.bind("<Control-x>", cut_selection)
        tk_text.bind("<Control-X>", cut_selection)
        tk_text.bind("<Control-a>", select_all)
        tk_text.bind("<Control-A>", select_all)
        tk_text.bind("<Control-z>", undo_action)
        tk_text.bind("<Control-Z>", undo_action)

        # Context Menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Копировать (Ctrl+C)", command=copy_selection)
        menu.add_command(label="Вставить (Ctrl+V)", command=paste_selection)
        menu.add_command(label="Вырезать (Ctrl+X)", command=cut_selection)
        menu.add_separator()
        menu.add_command(label="Выделить всё (Ctrl+A)", command=select_all)
        menu.add_command(label="Отменить (Ctrl+Z)", command=undo_action)

        def show_popup(event):
            menu.tk_popup(event.x_root, event.y_root)

        tk_text.bind("<Button-3>", show_popup)

    def on_tab_switched(self, selected_title):
        self.list_buffers[self.current_selected_file] = self.txt_editor.get("1.0", "end-1c")

        idx = 0
        for i, t in enumerate(self.tab_titles_with_counts):
            if t == selected_title:
                idx = i
                break
        
        self.current_selected_file = self.list_filenames[idx]
        content = self.list_buffers.get(self.current_selected_file, "")
        self.txt_editor.delete("1.0", "end")
        self.txt_editor.insert("1.0", content)
        self.refresh_tab_titles()
        self.on_search_text()

    def save_list_contents(self):
        self.list_buffers[self.current_selected_file] = self.txt_editor.get("1.0", "end-1c")

        saved_count = 0
        for fname, content in self.list_buffers.items():
            ok, msg = self.app.lists_mgr.save_user_list(fname, content)
            if ok:
                saved_count += 1

        self.refresh_tab_titles()

        if saved_count == len(self.list_buffers):
            messagebox.showinfo("Сохранение", "Все пользовательские списки успешно сохранены!")
            if self.app.is_running():
                self.app.restart_zapret()
        else:
            messagebox.showwarning("Сохранение", "Некоторые списки не удалось сохранить.")

    def on_apply_fakes(self):
        d_fake = self.opt_discord_fake.get()
        g_fake = self.opt_game_fake.get()

        ok1, msg1 = self.app.lists_mgr.set_fake_bin("discord", d_fake)
        ok2, msg2 = self.app.lists_mgr.set_fake_bin("game", g_fake)

        if ok1 and ok2:
            messagebox.showinfo("Фейк-пакеты", f"Фейк-пакеты успешно применены:\n• Discord: {d_fake}\n• Game: {g_fake}")
            if self.app.is_running():
                self.app.restart_zapret()
        else:
            messagebox.showerror("Ошибка", f"{msg1}\n{msg2}")

    def open_lists_folder(self):
        folder = os.path.join(self.app.config.get("zapret_dir"), "lists")
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showerror("Ошибка", "Папка lists не найдена.")
