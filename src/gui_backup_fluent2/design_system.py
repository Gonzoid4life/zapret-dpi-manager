"""
Zapret Manager - Centralized Design System & Style Tokens (Apple iOS 16 Style)
Single source of truth for all colors, dimensions, corner radii, and fonts across the app.
"""
import customtkinter as ctk

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
WINDOW_WIDTH = 760
WINDOW_HEIGHT = 860
SIDEBAR_WIDTH = 220

# ==========================================
# 2. CORNER RADII (Apple iOS 17 / Fluent 2 Metric)
# ==========================================
RADIUS_CARD = 14        # Inset grouped cards
RADIUS_TILE = 12        # Top-3 strategy tiles
RADIUS_POPUP = 12       # Dropdown popups
RADIUS_BTN = 10         # Action buttons
RADIUS_NAV = 10         # Sidebar menu items
RADIUS_SEGMENT = 8      # Segmented control pills
RADIUS_SWITCH = 12      # Toggle switches
RADIUS_PILL = 6         # Status badges & tags
RADIUS_CHECKBOX = 4     # Checkboxes

# ==========================================
# 3. COLOR PALETTES (Light Mode, Dark Mode)
# ==========================================

# Core Accent Colors
COLOR_PRIMARY = ("#007AFF", "#0A84FF")          # Apple / Fluent Electric Blue
COLOR_PRIMARY_HOVER = ("#0062CC", "#0070E0")
COLOR_PRIMARY_TINT = ("#EBF3FE", "#16253B")     # Soft blue selection tint
COLOR_PRIMARY_BORDER = ("#B8D7FF", "#1D3B60")

COLOR_SUCCESS = ("#34C759", "#30D158")          # Vibrant Neon Emerald
COLOR_SUCCESS_HOVER = ("#248A3D", "#28B84D")
COLOR_SUCCESS_TINT = ("#EAF9ED", "#122A1C")     # Soft glowing emerald tint
COLOR_SUCCESS_BORDER = ("#BEECCD", "#1E4F2D")

COLOR_DANGER = ("#FF3B30", "#FF453A")           # iOS Crimson Red
COLOR_DANGER_HOVER = ("#D70015", "#E03830")
COLOR_DANGER_TINT = ("#FEE8E7", "#321618")
COLOR_DANGER_BORDER = ("#FFCCD0", "#521F22")

COLOR_WARNING = ("#FF9500", "#FF9F0A")          # Warm Amber Orange
COLOR_WARNING_HOVER = ("#D07A00", "#E08B00")
COLOR_WARNING_TINT = ("#FFF4E5", "#30220F")
COLOR_WARNING_BORDER = ("#FFE2BE", "#503612")

# Backgrounds
COLOR_BG_WINDOW = ("#F4F4F8", "#0F0F12")        # Rich obsidian dark, clean slate light
COLOR_BG_SIDEBAR = ("#FFFFFF", "#141418")       # High-contrast clean sidebar
COLOR_BG_CARD = ("#FFFFFF", "#1B1B20")          # Elevated inset card surface
COLOR_BG_CARD_SUB = ("#F6F6FA", "#222228")      # Inset subsection containers
COLOR_BORDER_CARD = ("#E4E4EB", "#292932")      # Hairline 1px border
COLOR_BORDER_SUB = ("#ECECF2", "#31313C")       # Sub-box divider border
COLOR_BORDER_DIVIDER = ("#EAEAEF", "#24242C")   # Clean list hairline divider

# Controls & Secondary Buttons
COLOR_BG_CONTROL = ("#EBEBF0", "#25252C")
COLOR_BG_CONTROL_HOVER = ("#DFDFE6", "#303038")
COLOR_BG_TILE_HOVER = ("#F0F0F5", "#262630")

# Switches (iOS 17 Style)
COLOR_SWITCH_PROGRESS = ("#34C759", "#30D158")
COLOR_SWITCH_BG = ("#D1D1D6", "#36363E")
COLOR_SWITCH_KNOB = ("#FFFFFF", "#FFFFFF")
COLOR_SWITCH_KNOB_HOVER = ("#F0F0F3", "#E5E5EA")

# Typography Colors
COLOR_TEXT_PRIMARY = ("#161618", "#F5F5F7")     # Crisp high contrast
COLOR_TEXT_SECONDARY = ("#6C6C74", "#92929A")   # Clear readable muted text
COLOR_TEXT_MUTED = ("#8E8E96", "#64646C")
COLOR_TEXT_WHITE = "#FFFFFF"

# Rank Medals
COLOR_RANK_GOLD = ("#D4AF37", "#FFD700")
COLOR_RANK_SILVER = ("#A0A0A0", "#C0C0C0")
COLOR_RANK_BRONZE = ("#CD7F32", "#E59866")

# ==========================================
# 4. TYPOGRAPHY (Windows 11 Segoe UI Variable with Fallback)
# ==========================================
def _get_font_family(preferred: str, fallback: str = "Segoe UI") -> str:
    try:
        import tkinter.font as tkfont
        fams = tkfont.families()
        if preferred in fams:
            return preferred
    except Exception:
        pass
    return fallback

FONT_FAMILY_TITLE = _get_font_family("Segoe UI Variable Display", "Segoe UI")
FONT_FAMILY_TEXT = _get_font_family("Segoe UI Variable Text", "Segoe UI")
FONT_FAMILY_SMALL = _get_font_family("Segoe UI Variable Small", "Segoe UI")

class AppFont:
    @staticmethod
    def title():
        return ctk.CTkFont(family=FONT_FAMILY_TITLE, size=18, weight="bold")

    @staticmethod
    def card_title():
        return ctk.CTkFont(family=FONT_FAMILY_TITLE, size=15, weight="bold")

    @staticmethod
    def nav():
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
