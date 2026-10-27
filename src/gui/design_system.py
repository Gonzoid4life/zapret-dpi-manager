"""
Zapret Manager - Centralized Design System & Style Tokens (Fluent 2 Minimalist)
Single source of truth for all colors, dimensions, corner radii, and typography across the app.
"""
import customtkinter as ctk
import os
import sys

# ==========================================
# 0. APP VERSION
# ==========================================
APP_VERSION = "0.1.33"

def get_smart_strategy_name(raw_name: str) -> str:
    """Formats strategy filenames into clean, readable and concise display titles."""
    if not raw_name:
        return ""
    clean = raw_name[:-4] if raw_name.lower().endswith(".bat") else raw_name
    clean = clean.strip()
    if clean.lower() == "general":
        return "Базовая (general)"
    if clean.lower().startswith("general (") and clean.endswith(")"):
        return clean[9:-1].strip()
    elif clean.lower().startswith("general "):
        return clean[8:].strip()
    elif clean.lower().startswith("general_"):
        return clean[8:].strip()
    return clean

# ==========================================
# 1. WINDOW & LAYOUT DIMENSIONS
# ==========================================
WINDOW_WIDTH = 790
WINDOW_HEIGHT = 860
SIDEBAR_WIDTH = 210

# ==========================================
# 2. CORNER RADII (Fluent 2 Metric - Refined & Crisp)
# ==========================================
RADIUS_CARD = 10        # Clean inset cards
RADIUS_TILE = 8         # Strategy tiles
RADIUS_POPUP = 8        # Dropdown popups
RADIUS_BTN = 6          # Action buttons
RADIUS_NAV = 6          # Sidebar menu items
RADIUS_SEGMENT = 6      # Segmented control pills
RADIUS_SWITCH = 10      # Toggle switches
RADIUS_PILL = 4         # Status badges & tags
RADIUS_CHECKBOX = 4     # Checkboxes

# ==========================================
# 3. COLOR PALETTES (Fluent 2 Minimalist: Light Mode, Dark Mode)
# ==========================================

# Core Accent Colors (Fluent Blue & Refined Semantic Tones)
COLOR_PRIMARY = ("#0067C0", "#388BFD")          # Fluent 2 Windows 11 Blue
COLOR_PRIMARY_HOVER = ("#005FB8", "#2979E6")
COLOR_PRIMARY_TINT = ("#EBF3FB", "#17263C")     # Subtle selection tint
COLOR_PRIMARY_BORDER = ("#CCE4F7", "#223E63")

COLOR_SUCCESS = ("#107C10", "#2EA043")          # Refined Fluent Emerald
COLOR_SUCCESS_HOVER = ("#0E6B0E", "#278939")
COLOR_SUCCESS_TINT = ("#EDF6ED", "#162D20")     # Soft emerald tint
COLOR_SUCCESS_BORDER = ("#CBE7CB", "#234C31")

COLOR_DANGER = ("#C42B1C", "#F85149")           # Fluent Coral Crimson
COLOR_DANGER_HOVER = ("#A82315", "#E0433C")
COLOR_DANGER_TINT = ("#FDF0EE", "#381B1D")
COLOR_DANGER_BORDER = ("#F7C9C5", "#5C2B2E")

COLOR_WARNING = ("#9D5D00", "#F0883E")          # Warm Ochre Amber
COLOR_WARNING_HOVER = ("#824D00", "#D9772F")
COLOR_WARNING_TINT = ("#FFF8ED", "#342214")
COLOR_WARNING_BORDER = ("#FCE5BD", "#54371F")

# Backgrounds (Fluent Mica / Zinc Layering)
COLOR_BG_WINDOW = ("#F9F9FB", "#18181B")        # Soft neutral canvas
COLOR_BG_SIDEBAR = ("#F1F1F5", "#131315")       # Refined hierarchical sidebar
COLOR_BG_CARD = ("#FFFFFF", "#202024")          # Elevated clean card surface
COLOR_BG_CARD_SUB = ("#F4F4F8", "#27272D")      # Inset subsection containers
COLOR_BORDER_CARD = ("#E5E5EB", "#2D2D35")      # Hairline 1px subtle border
COLOR_BORDER_SUB = ("#EBEBEF", "#34343E")       # Sub-box divider border
COLOR_BORDER_DIVIDER = ("#EDEDF2", "#282830")   # Minimalist hairline divider

# Controls & Secondary Buttons
COLOR_BG_CONTROL = ("#EAEAEF", "#2A2A32")
COLOR_BG_CONTROL_HOVER = ("#DFDFE5", "#33333D")
COLOR_BG_TILE_HOVER = ("#F3F3F7", "#282830")

# Switches (Fluent 2 Minimalist Style)
COLOR_SWITCH_PROGRESS = ("#107C10", "#2EA043")
COLOR_SWITCH_BG = ("#D6D6DD", "#383842")
COLOR_SWITCH_KNOB = ("#FFFFFF", "#FFFFFF")
COLOR_SWITCH_KNOB_HOVER = ("#F4F4F7", "#EDEDF0")

# Typography Colors (Crisp, High-Legibility)
COLOR_TEXT_PRIMARY = ("#18181B", "#F4F4F6")     # Smooth crisp contrast
COLOR_TEXT_SECONDARY = ("#5E5E68", "#9E9EA8")   # Clean readable muted text
COLOR_TEXT_MUTED = ("#8C8C96", "#686873")
COLOR_TEXT_WHITE = "#FFFFFF"

# Rank Medals (Subtle Fluent metallic)
COLOR_RANK_GOLD = ("#B8860B", "#F1C40F")
COLOR_RANK_SILVER = ("#7F8C8D", "#BDC3C7")
COLOR_RANK_BRONZE = ("#A0522D", "#E67E22")

# ==========================================
# 4. TYPOGRAPHY (Segoe UI Variable & Cascadia Code)
# ==========================================
def _get_font_family(preferred_list, fallback: str = "Segoe UI") -> str:
    """Safely detects installed fonts, falling back gracefully if Tk root isn't up yet."""
    try:
        import tkinter.font as tkfont
        fams = tkfont.families()
        for font_name in preferred_list:
            if font_name in fams:
                return font_name
    except Exception:
        pass
    return preferred_list[0] if preferred_list else fallback

FONT_FAMILY_TITLE = _get_font_family(["Segoe UI Variable Display", "Segoe UI", "Arial"])
FONT_FAMILY_TEXT = _get_font_family(["Segoe UI Variable Text", "Segoe UI", "Arial"])
FONT_FAMILY_SMALL = _get_font_family(["Segoe UI Variable Small", "Segoe UI Variable Text", "Segoe UI"])
FONT_FAMILY_MONO = _get_font_family(["Cascadia Code", "Cascadia Mono", "Consolas", "Courier New"])

class AppFont:
    @staticmethod
    def title():
        return ctk.CTkFont(family=FONT_FAMILY_TITLE, size=18, weight="bold")

    @staticmethod
    def card_title():
        return ctk.CTkFont(family=FONT_FAMILY_TITLE, size=14, weight="bold")

    @staticmethod
    def nav():
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=13, weight="normal")

    @staticmethod
    def nav_active():
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=13, weight="bold")

    @staticmethod
    def body(weight="normal"):
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=12, weight=weight)

    @staticmethod
    def body_bold():
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=12, weight="bold")

    @staticmethod
    def sub(weight="normal"):
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=11, weight=weight)

    @staticmethod
    def sub_bold():
        return ctk.CTkFont(family=FONT_FAMILY_TEXT, size=11, weight="bold")

    @staticmethod
    def small(weight="normal"):
        return ctk.CTkFont(family=FONT_FAMILY_SMALL, size=10, weight=weight)

    @staticmethod
    def small_bold():
        return ctk.CTkFont(family=FONT_FAMILY_SMALL, size=10, weight="bold")

    @staticmethod
    def mono(size=10, weight="normal"):
        return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size, weight=weight)

    @staticmethod
    def mono_bold(size=10):
        return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size, weight="bold")

# ==========================================
# 5. CURSORS (High-Visibility Inverted Text Cursor)
# ==========================================
def get_text_cursor() -> str:
    """Returns high-visibility inverted/white text cursor for dark and light modes on Windows."""
    if sys.platform == "win32":
        # 1. Bundled in assets directory
        base_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        bundled_cur = os.path.join(base_dir, "assets", "beam_i.cur")
        if os.path.exists(bundled_cur):
            return "@" + bundled_cur.replace(os.sep, "/")
        # 2. Windows system cursors folder
        sys_root = os.environ.get("SystemRoot", "C:/Windows")
        for name in ("beam_i.cur", "beam_il.cur", "libeam.cur"):
            cur_file = os.path.join(sys_root, "Cursors", name)
            if os.path.exists(cur_file):
                return "@" + cur_file.replace(os.sep, "/")
    return "arrow"


CURSOR_TEXT = get_text_cursor()
