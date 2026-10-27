import customtkinter as ctk
from .animator import UIAnimator
from .design_system import (
    RADIUS_SEGMENT, RADIUS_BTN,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_TINT,
    COLOR_BG_CONTROL, COLOR_BG_CONTROL_HOVER, COLOR_BG_CARD,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_WHITE, AppFont
)

class IOSAnimatedButton(ctk.CTkButton):
    """
    Apple iOS style button with smooth RGB color crossfade on hover and gentle click dimming.
    """
    def __init__(self, *args, animate_hover=True, **kwargs):
        super().__init__(*args, **kwargs)
        if animate_hover:
            UIAnimator.attach_smooth_hover(self)

class IOSSegmentedButton(ctk.CTkSegmentedButton):
    def __init__(self, *args, selected_text_color=COLOR_TEXT_WHITE, unselected_text_color=COLOR_TEXT_PRIMARY, **kwargs):
        self._custom_selected_text_color = selected_text_color
        self._custom_unselected_text_color = unselected_text_color
        if "width" in kwargs:
            kwargs.setdefault("dynamic_resizing", False)
        kwargs.setdefault("border_width", 0)
        kwargs.setdefault("corner_radius", RADIUS_SEGMENT)
        kwargs.setdefault("selected_color", COLOR_PRIMARY)
        kwargs.setdefault("selected_hover_color", COLOR_PRIMARY_HOVER)
        kwargs.setdefault("unselected_color", COLOR_BG_CONTROL)
        kwargs.setdefault("unselected_hover_color", COLOR_BG_CONTROL_HOVER)
        kwargs.setdefault("fg_color", COLOR_BG_CONTROL)
        super().__init__(*args, **kwargs)

    def _select_button_by_value(self, value: str):
        super()._select_button_by_value(value)
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(text_color=self._custom_selected_text_color)

    def _unselect_button_by_value(self, value: str):
        super()._unselect_button_by_value(value)
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(text_color=self._custom_unselected_text_color)

    def _create_button_grid(self):
        super()._create_button_grid()
        num_buttons = len(self._buttons_dict)
        if num_buttons > 0:
            for i in range(num_buttons):
                self.grid_columnconfigure(i, weight=1, uniform="seg_col")
        for val, btn in self._buttons_dict.items():
            if val == self._current_value:
                btn.configure(text_color=self._custom_selected_text_color)
            else:
                btn.configure(text_color=self._custom_unselected_text_color)

    def set(self, value: str, *args, **kwargs):
        super().set(value, *args, **kwargs)
        for val, btn in self._buttons_dict.items():
            if val == value:
                btn.configure(text_color=self._custom_selected_text_color)
            else:
                btn.configure(text_color=self._custom_unselected_text_color)

class IOSOptionMenu(ctk.CTkFrame):
    def __init__(self, master, values=None, command=None, height=36, font=None, dropdown_font=None,
                 fg_color=None, text_color=None, button_color=None, button_hover_color=None,
                 dropdown_fg_color=None, dropdown_hover_color=None, dropdown_text_color=None,
                 corner_radius=RADIUS_BTN, width=140, **kwargs):
        
        bg = fg_color or COLOR_BG_CONTROL
        kwargs.pop("button_text_color", None)
        kwargs.pop("dynamic_resizing", None)
        super().__init__(master, fg_color=bg, corner_radius=corner_radius, height=height, width=width, **kwargs)
        
        self._values = list(values) if values else []
        self._command = command
        self._current_value = self._values[0] if self._values else ""
        self._popup = None
        self._font = font or AppFont.body_bold()
        self._dropdown_font = dropdown_font or AppFont.body()
        self._dropdown_fg = dropdown_fg_color or COLOR_BG_CARD
        self._dropdown_hover = dropdown_hover_color or COLOR_BG_CONTROL
        self._dropdown_text = dropdown_text_color or COLOR_TEXT_PRIMARY
        if button_color is not None:
            self._btn_color = button_color
            self._btn_hover = button_hover_color or COLOR_PRIMARY_HOVER
            self._btn_text_color = kwargs.pop("button_text_color", "#FFFFFF")
        else:
            self._btn_color = "transparent"
            self._btn_hover = button_hover_color or ("#D1D1D6", "#3A3A3C")
            self._btn_text_color = COLOR_PRIMARY
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        
        self._label = ctk.CTkLabel(
            self, text=self._current_value, font=self._font,
            text_color=text_color or COLOR_TEXT_PRIMARY, anchor="w"
        )
        self._label.grid(row=0, column=0, padx=(14, 4), pady=4, sticky="ew")
        
        btn_h = max(24, height - 8)
        self._btn_arrow = ctk.CTkButton(
            self, text="▾", width=30, height=btn_h, corner_radius=corner_radius-2,
            fg_color=self._btn_color, hover_color=self._btn_hover,
            text_color=self._btn_text_color, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.toggle_dropdown
        )
        self._btn_arrow.grid(row=0, column=1, padx=(0, 4), pady=4, sticky="e")
        
        self.bind("<Button-1>", lambda e: self.toggle_dropdown())
        self._label.bind("<Button-1>", lambda e: self.toggle_dropdown())

    def get(self):
        return self._current_value

    def set(self, value):
        self._current_value = str(value)
        self._label.configure(text=self._current_value)

    def cget(self, attr):
        if attr == "values":
            return list(self._values)
        if attr in ("value", "current_value"):
            return self._current_value
        return super().cget(attr)

    def configure(self, **kwargs):
        if "values" in kwargs:
            self._values = list(kwargs.pop("values"))
            if self._current_value not in self._values and self._values:
                self.set(self._values[0])
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "text_color" in kwargs:
            self._label.configure(text_color=kwargs.pop("text_color"))
        super().configure(**kwargs)

    def toggle_dropdown(self):
        if self._popup and self._popup.winfo_exists():
            self.close_dropdown()
        else:
            self.open_dropdown()

    def open_dropdown(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()

        self._btn_arrow.configure(text="▴")
        self.update_idletasks()
        
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 3
        w = max(self.winfo_width(), 200)
        
        item_height = 32
        calc_height = min(len(self._values) * (item_height + 4) + 16, 280)
        
        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.geometry(f"{w}x{calc_height}+{x}+{y}")

        border_frame = ctk.CTkFrame(
            self._popup, corner_radius=12,
            fg_color=self._dropdown_fg,
            border_width=1, border_color=COLOR_PRIMARY
        )
        border_frame.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(
            border_frame, corner_radius=10,
            fg_color="transparent"
        )
        scroll.pack(fill="both", expand=True, padx=3, pady=3)
        scroll.grid_columnconfigure(0, weight=1)

        for val in self._values:
            is_sel = (val == self._current_value)
            row_btn = ctk.CTkButton(
                scroll, text=f"  {val}", anchor="w", height=item_height, corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold" if is_sel else "normal"),
                fg_color=COLOR_PRIMARY_TINT if is_sel else "transparent",
                text_color=COLOR_PRIMARY if is_sel else COLOR_TEXT_PRIMARY,
                hover_color=self._dropdown_hover,
                command=lambda v=val: self._on_item_click(v)
            )
            row_btn.pack(fill="x", padx=2, pady=2)

        top_win = self.winfo_toplevel()

        def _on_global_click(event):
            if not (self._popup and self._popup.winfo_exists()):
                return
            try:
                px, py = self._popup.winfo_rootx(), self._popup.winfo_rooty()
                pw, ph = self._popup.winfo_width(), self._popup.winfo_height()
                if not (px <= event.x_root <= px + pw and py <= event.y_root <= py + ph):
                    bx, by = self.winfo_rootx(), self.winfo_rooty()
                    bw, bh = self.winfo_width(), self.winfo_height()
                    if not (bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh):
                        self.close_dropdown()
            except Exception:
                self.close_dropdown()

        def _on_scroll(event):
            if self._popup and self._popup.winfo_exists():
                self.close_dropdown()

        def _on_window_move(event):
            if self._popup and self._popup.winfo_exists() and event.widget == top_win:
                self.close_dropdown()

        if not hasattr(self, '_listeners_initialized'):
            self._listeners_initialized = True
            top_win.bind("<Button-1>", _on_global_click, add="+")
            top_win.bind("<MouseWheel>", _on_scroll, add="+")
            top_win.bind("<Configure>", _on_window_move, add="+")

    def _on_item_click(self, value):
        self.set(value)
        self.close_dropdown()
        if self._command:
            self._command(value)

    def close_dropdown(self):
        self._btn_arrow.configure(text="▾")
        if self._popup:
            try:
                if self._popup.winfo_exists():
                    self._popup.destroy()
            except Exception:
                pass
            self._popup = None
