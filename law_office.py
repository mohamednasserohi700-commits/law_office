"""
=============================================================
  إدارة مكتب المحاماة الذكي
  برمجة: محمد ناصر عبدالله
  شركة: System Makers
  الإصدار: 2.0 - 2026
=============================================================
  يتطلب: pip install customtkinter pillow cryptography
  التفعيل: ملف السريالات المحلي أو مفتاح الجهاز (من إعدادات المطور).
=============================================================
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import customtkinter as ctk
import sqlite3
import hashlib
import os
import sys
import json
import math
import csv
import html
import shutil
import tempfile
import webbrowser
from datetime import datetime, date, timedelta
from pathlib import Path
import threading
import platform
import secrets
import base64
import mimetypes

try:
    from cryptography.fernet import Fernet

    _HAS_FERNET = True
except ImportError:
    Fernet = None  # type: ignore
    _HAS_FERNET = False

try:
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except ImportError:
    Image = ImageDraw = ImageTk = None  # type: ignore
    _HAS_PIL = False

# ─── الثوابت والألوان ────────────────────────────────────────
APP_NAME    = "إدارة مكتب المحاماة الذكي"
APP_VERSION = "2.0 - 2026"
APP_AUTHOR  = "محمد ناصر عبدالله"
APP_COMPANY = "System Makers"
SUBSCRIPTION_SUPPORT_PHONE = "01103763082"
# سطر علوي في شاشة تسجيل الدخول
LOGIN_SCREEN_TAGLINE = "سيستم ادارة مكتب المحاماه الشامل من شركة System Makers"
# بطاقة الدخول (ثيم داكن + هيدر بحري وكيرف سفلي كالمرجع)
LOGIN_CARD_NAVY = "#1a2f4a"
LOGIN_CARD_BLACK = "#000000"
LOGIN_SUBTITLE_BLUE = "#8ec5e8"
LOGIN_ENTRY_BG = "#2a3348"
LOGIN_ENTRY_BORDER = "#3d4f70"
LOGIN_ENTRY_TEXT = "#f0f2f8"
LOGIN_ENTRY_PH = "#8899b8"
LOGIN_CURVE_STRIP_H = 52
# ثيم فاتح لشاشة الدخول
LOGIN_LIGHT_OUTER_BG = "#d8e0f0"
LOGIN_LIGHT_HEADER_PANEL = "#e8edf7"
LOGIN_LIGHT_HEADER_ACCENT = "#3d5a80"
LOGIN_LIGHT_BODY = "#ffffff"
LOGIN_LIGHT_SUBTITLE = "#3d6db0"
LOGIN_LIGHT_TAGLINE = "#3a4a60"
LOGIN_LIGHT_ENTRY_BG = "#ffffff"
LOGIN_LIGHT_ENTRY_BORDER = "#b8c4dc"
LOGIN_LIGHT_ENTRY_TEXT = "#1a1a2e"
LOGIN_LIGHT_ENTRY_PH = "#8899b8"
LOGIN_LIGHT_FOOTER = "#6a7a9a"
DB_FILENAME = "law_office.db"
# قاعدة منفصلة لملفات الوثائق (صور/ملفات كبيرة) بجانب القاعدة الرئيسية: law_office.documents.db
DOCUMENTS_DB_FILENAME_SUFFIX = ".documents.db"
CONFIG_FILENAME = "law_office_config.json"
# صورة خلفية شاشة الدخول (اختياري): ضع أحد هذه الأسماء بجانب البرنامج أو داخل مجلد assets
LOGIN_BG_FILENAMES = (
    "login_background.png",
    "login_bg.png",
    "mizan_background.png",
)

# ─── تفعيل عبر ملف سريالات محلي (يُدار من صفحة المطور فقط) ───
SERIAL_POOL_FILENAME = "law_office_serial_pool.json"
SERIAL_USED_FILENAME = "law_office_serial_used.json"
# بادئة ملف السريالات المشفّر (Fernet) — القراءة تدعم أيضاً JSON النصّي القديم
_SERIAL_FILE_ENC_PREFIX = b"LAWOFFICE_SERIAL_ENC_V1\n"

# حساب مطور النظام (لا يظهر في قائمة المستخدمين إلا لمطور آخر). غيّر كلمة المرور بعد أول دخول.
DEV_MASTER_USERNAME = "administrator"
DEV_MASTER_DEFAULT_PASSWORD = "3000330210"

# عرض أدوار الصلاحية بالعربية (المفتاح الداخلي في قاعدة البيانات يبقى إنجليزياً للتوافق).
ROLE_LABEL_AR = {
    "dev_master": "مطور عام",
    "admin": "مدير النظام",
    "superfiser": "سوبر فايزر",
    "user": "مستخدم",
    "trial": "تجريبي",
}


def _ui_font(size: int = 13, weight: str = "normal"):
    """خط يُقلّل مشاكل العربية في حقول Tk/CustomTkinter (خصوصاً ويندوز)."""
    if platform.system() == "Windows":
        return ("Segoe UI", size, weight)
    return ("Arial", size, weight)

COLORS_DARK = {
    "bg":          "#0D0F14",
    "bg2":         "#141720",
    "bg3":         "#1C2030",
    "panel":       "#1A1D2E",
    "panel2":      "#20243A",
    "gold":        "#C9A84C",
    "gold_light":  "#E8C97A",
    "gold_dark":   "#9A7A2E",
    "text":        "#E8E8F0",
    "text2":       "#A0A8C0",
    "text3":       "#6070A0",
    "accent":      "#4A90D9",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#2A2E45",
    "hover":       "#242840",
    "white":       "#FFFFFF",
}

COLORS_LIGHT = {
    "bg":          "#F0F4FA",
    "bg2":         "#E4EAF6",
    "bg3":         "#D5DDEF",
    "panel":       "#FFFFFF",
    "panel2":      "#F5F7FF",
    "gold":        "#B8860B",
    "gold_light":  "#8B6508",
    "gold_dark":   "#6A4D06",
    "text":        "#1A1A2E",
    "text2":       "#3A3A5C",
    "text3":       "#6A6A8C",
    "accent":      "#2570C9",
    "green":       "#1A9E50",
    "red":         "#C0392B",
    "orange":      "#D48000",
    "purple":      "#7B3F9E",
    "border":      "#C0C8E0",
    "hover":       "#DDE4F4",
    "white":       "#FFFFFF",
}

COLORS_LIGHT_MINT = {
    "bg":          "#EEF9F4",
    "bg2":         "#E2F4EC",
    "bg3":         "#D2EBDD",
    "panel":       "#FFFFFF",
    "panel2":      "#F3FBF7",
    "gold":        "#1F9D7A",
    "gold_light":  "#17785D",
    "gold_dark":   "#12654E",
    "text":        "#10261D",
    "text2":       "#2E4D3F",
    "text3":       "#5B7A6B",
    "accent":      "#2A7EC7",
    "green":       "#1FA35D",
    "red":         "#C0392B",
    "orange":      "#D48000",
    "purple":      "#7B3F9E",
    "border":      "#BFDCCE",
    "hover":       "#DCEFE5",
    "white":       "#FFFFFF",
}

COLORS_LIGHT_SKY = {
    "bg":          "#EEF5FF",
    "bg2":         "#E4EEFB",
    "bg3":         "#D6E3F5",
    "panel":       "#FFFFFF",
    "panel2":      "#F5F9FF",
    "gold":        "#2D77CC",
    "gold_light":  "#215B9E",
    "gold_dark":   "#1A4B84",
    "text":        "#11213D",
    "text2":       "#334C73",
    "text3":       "#6A7FA3",
    "accent":      "#1CA3A3",
    "green":       "#1A9E50",
    "red":         "#C0392B",
    "orange":      "#CC7A00",
    "purple":      "#6E53BF",
    "border":      "#C0D0EB",
    "hover":       "#DFE8F8",
    "white":       "#FFFFFF",
}

COLORS_LIGHT_ROSE = {
    "bg":          "#FFF1F6",
    "bg2":         "#FBE7EF",
    "bg3":         "#F4D7E3",
    "panel":       "#FFFFFF",
    "panel2":      "#FFF7FA",
    "gold":        "#B44A78",
    "gold_light":  "#8D365C",
    "gold_dark":   "#732A4B",
    "text":        "#321426",
    "text2":       "#654055",
    "text3":       "#967087",
    "accent":      "#3B82C4",
    "green":       "#1B9B55",
    "red":         "#C0392B",
    "orange":      "#C77700",
    "purple":      "#7C4FB3",
    "border":      "#E7C6D6",
    "hover":       "#F1DCE6",
    "white":       "#FFFFFF",
}

COLORS_ROYAL_BLUE = {
    "bg":          "#050A1A",
    "bg2":         "#091228",
    "bg3":         "#0E1C3A",
    "panel":       "#0A1530",
    "panel2":      "#0F1E42",
    "gold":        "#4A9EFF",
    "gold_light":  "#82C0FF",
    "gold_dark":   "#1A6ACC",
    "text":        "#E0EEFF",
    "text2":       "#90BBEE",
    "text3":       "#4A80BB",
    "accent":      "#00CFFF",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#1A3060",
    "hover":       "#142A5A",
    "white":       "#FFFFFF",
}

COLORS_EMERALD = {
    "bg":          "#030F0A",
    "bg2":         "#071A0F",
    "bg3":         "#0C2A1A",
    "panel":       "#09201A",
    "panel2":      "#0E2E20",
    "gold":        "#2ECC71",
    "gold_light":  "#55EE95",
    "gold_dark":   "#1A9950",
    "text":        "#D0F5E0",
    "text2":       "#80CCA0",
    "text3":       "#3A8A60",
    "accent":      "#00FFB0",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#1A4A30",
    "hover":       "#0F3025",
    "white":       "#FFFFFF",
}

COLORS_PURPLE = {
    "bg":          "#0A0514",
    "bg2":         "#130A22",
    "bg3":         "#1E1035",
    "panel":       "#160C2C",
    "panel2":      "#1E1240",
    "gold":        "#BB86FC",
    "gold_light":  "#D4ADFF",
    "gold_dark":   "#8A4FCC",
    "text":        "#EDE0FF",
    "text2":       "#B090D0",
    "text3":       "#7050A0",
    "accent":      "#CF6679",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#3A1A60",
    "hover":       "#2A1050",
    "white":       "#FFFFFF",
}

COLORS_CRIMSON = {
    "bg":          "#130505",
    "bg2":         "#1E0808",
    "bg3":         "#2E0E0E",
    "panel":       "#260808",
    "panel2":      "#320C0C",
    "gold":        "#FF5252",
    "gold_light":  "#FF8080",
    "gold_dark":   "#CC2020",
    "text":        "#FFE0E0",
    "text2":       "#CC9090",
    "text3":       "#995050",
    "accent":      "#FF9800",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#4A1010",
    "hover":       "#3A0808",
    "white":       "#FFFFFF",
}

COLORS_GOLD_PREMIUM = {
    "bg":          "#0E0A00",
    "bg2":         "#1A1200",
    "bg3":         "#261A00",
    "panel":       "#201500",
    "panel2":      "#2E1E00",
    "gold":        "#FFD700",
    "gold_light":  "#FFE766",
    "gold_dark":   "#CC9A00",
    "text":        "#FFF8E0",
    "text2":       "#DDB860",
    "text3":       "#AA8030",
    "accent":      "#FF9800",
    "green":       "#2ECC71",
    "red":         "#E74C3C",
    "orange":      "#F39C12",
    "purple":      "#9B59B6",
    "border":      "#4A3500",
    "hover":       "#382500",
    "white":       "#FFFFFF",
}

# ─── ثيمات زاهية (فاضحة) ────────────────────────────────────
COLORS_NEON_PINK = {
    "bg":          "#16000C",
    "bg2":         "#220012",
    "bg3":         "#32001B",
    "panel":       "#240014",
    "panel2":      "#3A0020",
    "gold":        "#FF4FD8",
    "gold_light":  "#FFB3F0",
    "gold_dark":   "#D100A8",
    "text":        "#FFF0FA",
    "text2":       "#FFBDEB",
    "text3":       "#C98AB4",
    "accent":      "#00E5FF",
    "green":       "#00FF85",
    "red":         "#FF3B6B",
    "orange":      "#FFB000",
    "purple":      "#C77DFF",
    "border":      "#5A0034",
    "hover":       "#3B0022",
    "white":       "#FFFFFF",
}

COLORS_NEON_LIME = {
    "bg":          "#071200",
    "bg2":         "#0B1A00",
    "bg3":         "#102400",
    "panel":       "#0A1F00",
    "panel2":      "#123000",
    "gold":        "#B6FF00",
    "gold_light":  "#E7FF9A",
    "gold_dark":   "#6EA800",
    "text":        "#F4FFE3",
    "text2":       "#CFEFA8",
    "text3":       "#84B85A",
    "accent":      "#00A3FF",
    "green":       "#00FF85",
    "red":         "#FF355E",
    "orange":      "#FFB300",
    "purple":      "#B47CFF",
    "border":      "#294700",
    "hover":       "#152B00",
    "white":       "#FFFFFF",
}

COLORS_CYAN_POP = {
    "bg":          "#001014",
    "bg2":         "#001A22",
    "bg3":         "#002634",
    "panel":       "#001D28",
    "panel2":      "#002E40",
    "gold":        "#00E5FF",
    "gold_light":  "#B7F8FF",
    "gold_dark":   "#00A2B5",
    "text":        "#E9FCFF",
    "text2":       "#A9E9F2",
    "text3":       "#62A7B4",
    "accent":      "#FFB300",
    "green":       "#00FF85",
    "red":         "#FF3D71",
    "orange":      "#FF7A00",
    "purple":      "#C77DFF",
    "border":      "#0B3A45",
    "hover":       "#06222A",
    "white":       "#FFFFFF",
}

# ─── ثيم نيون "تقليدي" (مظهر قوي) ───────────────────────────────
# ملاحظة: هذا الثيم جديد ومختلف عن (neon_pink / neon_lime / cyan_pop)
COLORS_NEON_TRADITIONAL_DARK = {
    "bg":          "#070A13",
    "bg2":         "#0D1120",
    "bg3":         "#121A33",
    "panel":       "#0B1230",
    "panel2":      "#101C3C",
    "gold":        "#FFD166",
    "gold_light":  "#FFF1B8",
    "gold_dark":   "#D6A33A",
    "text":        "#F3F6FF",
    "text2":       "#B9C4E5",
    "text3":       "#6D7AAE",
    "accent":      "#4EEAFF",
    "green":       "#34FF9C",
    "red":         "#FF4D6D",
    "orange":      "#FF8A3D",
    "purple":      "#A78BFA",
    "border":      "#2A345A",
    "hover":       "#151E3B",
    "white":       "#FFFFFF",
}

COLORS_NEON_TRADITIONAL_LIGHT = {
    "bg":          "#F6FAFF",
    "bg2":         "#ECF2FF",
    "bg3":         "#DDE7FF",
    "panel":       "#FFFFFF",
    "panel2":      "#F2F6FF",
    "gold":        "#8B5CF6",
    "gold_light":  "#D8B4FE",
    "gold_dark":   "#6D28D9",
    "text":        "#0F172A",
    "text2":       "#334155",
    "text3":       "#64748B",
    "accent":      "#0891FF",
    "green":       "#10B981",
    "red":         "#E11D48",
    "orange":      "#F97316",
    "purple":      "#7C3AED",
    "border":      "#D6E2FF",
    "hover":       "#E6EEFF",
    "white":       "#FFFFFF",
}

COLORS_SUNSET = {
    "bg":          "#140800",
    "bg2":         "#1E0C00",
    "bg3":         "#2A1200",
    "panel":       "#201000",
    "panel2":      "#331800",
    "gold":        "#FF7A00",
    "gold_light":  "#FFD2A3",
    "gold_dark":   "#C95500",
    "text":        "#FFF2E6",
    "text2":       "#FFC9A2",
    "text3":       "#C38D67",
    "accent":      "#FF2FB3",
    "green":       "#00FF85",
    "red":         "#FF355E",
    "orange":      "#FFB300",
    "purple":      "#8A5CFF",
    "border":      "#5A2A00",
    "hover":       "#321600",
    "white":       "#FFFFFF",
}

ALL_THEMES = {
    "dark":         ("🌙 داكن كلاسيكي",       COLORS_DARK),
    "light":        ("☀️ فاتح",               COLORS_LIGHT),
    "light_mint":   ("🌿 فاتح نعناعي",        COLORS_LIGHT_MINT),
    "light_sky":    ("🩵 فاتح سماوي",         COLORS_LIGHT_SKY),
    "light_rose":   ("🌸 فاتح وردي",          COLORS_LIGHT_ROSE),
    "royal_blue":   ("💙 أزرق ملكي",          COLORS_ROYAL_BLUE),
    "emerald":      ("💚 أخضر زمردي",          COLORS_EMERALD),
    "purple":       ("💜 بنفسجي",              COLORS_PURPLE),
    "crimson":      ("❤️ أحمر داكن",          COLORS_CRIMSON),
    "gold_premium": ("✨ ذهبي فاخر",           COLORS_GOLD_PREMIUM),
    "neon_pink":    ("💗 نيون وردي",           COLORS_NEON_PINK),
    "neon_lime":    ("💚 نيون ليموني",         COLORS_NEON_LIME),
    "cyan_pop":     ("🩵 سماوي صادم",          COLORS_CYAN_POP),
    "neon_traditional":        ("🛡️ نيون نحاسي تقليدي",           COLORS_NEON_TRADITIONAL_DARK),
    "light_neon_traditional": ("🛡️ نيون نحاسي تقليدي (فاتح)",    COLORS_NEON_TRADITIONAL_LIGHT),
    "sunset":       ("🧡 غروب فاقع",           COLORS_SUNSET),
}

COLORS = dict(COLORS_LIGHT)
CURRENT_THEME = "light"

def apply_theme(theme: str):
    global COLORS, CURRENT_THEME, _STYLE_INITIALIZED
    CURRENT_THEME = theme
    theme_data = ALL_THEMES.get(theme)
    if theme_data:
        src = theme_data[1]
    else:
        src = COLORS_DARK
    for k, v in src.items():
        COLORS[k] = v
    _STYLE_INITIALIZED = False  # إعادة تهيئة Style عند تغيير الثيم
    # أي ثيم يبدأ بـ light_ أو الثيم light يعمل بوضع فاتح
    ctk.set_appearance_mode("light" if theme == "light" or theme.startswith("light_") else "dark")

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def _apply_display_scaling_for_monitor() -> None:
    """مواءمة حجم عناصر CustomTkinter مع نسبة تكبير الشاشة في ويندوز (مثل 125% أو 150%)."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        dpi = int(ctypes.windll.user32.GetDpiForSystem())
        scale = dpi / 96.0
        if 1.05 <= scale <= 2.5:
            ctk.set_widget_scaling(scale)
    except Exception:
        pass


_apply_display_scaling_for_monitor()


def _ellipsis_text(s: str, max_chars: int = 40, *, middle: bool = False) -> str:
    """اختصار نص طويل للعرض في الجداول دون كسر التخطيط."""
    t = (s or "").strip()
    if len(t) <= max_chars:
        return t
    if middle and max_chars > 8:
        a = max_chars // 2 - 1
        b = max_chars - a - 1
        return t[:a] + "…" + t[-b:]
    return t[: max_chars - 1] + "…"


def center_window(win, w, h):
    """توسيط أي نافذة في منتصف الشاشة"""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def _set_iconbitmap_safe(win: tk.Misc, abs_ico: str) -> bool:
    try:
        win.iconbitmap(abs_ico)
        return True
    except Exception:
        return False


def apply_window_icon(win: tk.Misc, base_dir: str) -> None:
    """
    أيقونة النافذة وشريط المهام: law_office.ico أو law_office.png بجانب البرنامج.
    مع نوافذ CustomTkinter الفرعية يُفضَّل تعيين الأيقونة أيضاً على النافذة الجذر (master).
    """
    def _log_icon_debug(msg: str) -> None:
        try:
            log_path = Path(base_dir) / "law_office_icon_debug.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")
        except Exception:
            pass

    def _apply_ico_to_win_and_root(abs_ico: str) -> None:
        _set_iconbitmap_safe(win, abs_ico)
        try:
            m = getattr(win, "master", None)
            if m is not None and m is not win and hasattr(m, "iconbitmap"):
                _set_iconbitmap_safe(m, abs_ico)
        except Exception:
            pass

    def _schedule_icon_retry(abs_ico: str) -> None:
        def _retry() -> None:
            _apply_ico_to_win_and_root(abs_ico)

        try:
            win.after(1, _retry)
            win.after(200, _retry)
            win.after(800, _retry)
        except Exception:
            pass

    try:
        search_dirs: list[str] = []
        if base_dir:
            search_dirs.append(base_dir)
        try:
            search_dirs.append(os.getcwd())
        except Exception:
            pass
        try:
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            if exe_dir and exe_dir not in search_dirs:
                search_dirs.append(exe_dir)
        except Exception:
            pass

        for d in search_dirs:
            try:
                ico_path = (Path(d) / "law_office.ico").resolve()
            except Exception:
                ico_path = Path(d) / "law_office.ico"
            if ico_path.is_file():
                abs_s = os.path.normpath(str(ico_path))
                try:
                    _apply_ico_to_win_and_root(abs_s)
                    _log_icon_debug(f"Loaded icon from ico: {abs_s}")
                    _schedule_icon_retry(abs_s)
                    return
                except Exception as e:
                    _log_icon_debug(f"iconbitmap failed for {abs_s}: {e}")
                    break

        for d in search_dirs:
            png_path = Path(d) / "law_office.png"
            if png_path.is_file():
                try:
                    img = tk.PhotoImage(file=str(png_path.resolve()))
                    setattr(win, "_window_icon_photo", img)
                    win.iconphoto(True, img)
                    try:
                        m = getattr(win, "master", None)
                        if m is not None and hasattr(m, "iconphoto"):
                            m.iconphoto(True, img)
                    except Exception:
                        pass
                    _log_icon_debug(f"Loaded icon from png: {png_path}")
                    return
                except Exception as e:
                    _log_icon_debug(f"iconphoto failed for {png_path}: {e}")

        _log_icon_debug("No icon files found (expected law_office.ico or law_office.png).")
    except Exception as e:
        _log_icon_debug(f"apply_window_icon fatal error: {e}")


def _find_login_background_path(base_dir: str) -> Path | None:
    if not base_dir:
        return None
    for name in LOGIN_BG_FILENAMES:
        p = Path(base_dir) / name
        if p.exists():
            return p
        p2 = Path(base_dir) / "assets" / name
        if p2.exists():
            return p2
    return None


def _cover_resize_rgb(im: "Image.Image", tw: int, th: int) -> "Image.Image":
    im = im.convert("RGB")
    iw, ih = im.size
    if iw < 1 or ih < 1 or tw < 1 or th < 1:
        return Image.new("RGB", (max(tw, 1), max(th, 1)), (13, 15, 24))
    scale = max(tw / iw, th / ih)
    nw, nh = max(int(iw * scale), 1), max(int(ih * scale), 1)
    try:
        _rz = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    except Exception:
        _rz = Image.LANCZOS  # type: ignore[attr-defined]
    im = im.resize((nw, nh), _rz)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def _default_login_wallpaper(w: int, h: int) -> "Image.Image":
    """خلفية افتراضية: تدرج داكن ورسم مبسّط لميزان العدالة."""
    w, h = max(w, 2), max(h, 2)
    im = Image.new("RGB", (w, h))
    px = im.load()
    c_top = (18, 22, 34)
    c_bot = (28, 48, 82)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * t)
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * t)
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    dr = ImageDraw.Draw(im)
    gold = (140, 118, 72)
    dim = (55, 62, 88)
    cx, cy = w // 2, h // 2
    beam_y = cy - h // 18
    half = min(w, h) // 3
    dr.line([(cx - half, beam_y), (cx + half, beam_y)], fill=gold, width=max(h // 200, 2))
    dr.line([(cx, beam_y - h // 5), (cx, beam_y + h // 12)], fill=gold, width=max(h // 220, 2))
    lw = max(w // 90, 2)
    for sign in (-1, 1):
        ox = cx + sign * half
        rpan = max(h // 14, 28)
        bbox = (ox - rpan, beam_y - 6, ox + rpan, beam_y + rpan + 24)
        dr.arc(bbox, start=200, end=340, fill=dim, width=lw)
        dr.line([(ox, beam_y), (ox, beam_y + rpan // 2)], fill=dim, width=lw)
    overlay = Image.new("RGB", (w, h), (8, 10, 18))
    im = Image.blend(im, overlay, 0.22)
    return im


def render_login_wallpaper(width: int, height: int, base_dir: str) -> "Image.Image":
    width = max(int(width), 2)
    height = max(int(height), 2)
    if not _HAS_PIL or Image is None:
        raise RuntimeError("render_login_wallpaper requires pillow")
    path = _find_login_background_path(base_dir)
    if path and path.exists():
        try:
            user_im = Image.open(path)
            im = _cover_resize_rgb(user_im, width, height)
            dim = Image.new("RGB", (width, height), (10, 12, 22))
            return Image.blend(im, dim, 0.35)
        except Exception:
            pass
    return _default_login_wallpaper(width, height)


# ════════════════════════════════════════════════════════════
#  قاعدة البيانات
# ════════════════════════════════════════════════════════════
def companion_documents_db_path(main_db_path: str) -> str:
    """مسار قاعدة ملفات الوثائق المرتبطة بالقاعدة الرئيسية (نفس المجلد، اسم منفصل)."""
    p = Path(main_db_path)
    return str(p.parent / f"{p.stem}{DOCUMENTS_DB_FILENAME_SUFFIX}")


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # تحسينات الأداء
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")       # أسرع للكتابة
        self.conn.execute("PRAGMA synchronous = NORMAL")     # توازن بين الأمان والسرعة
        self.conn.execute("PRAGMA busy_timeout = 5000")     # انتظار عند قفل SQLite
        self.conn.execute("PRAGMA cache_size = -8000")       # 8MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY")      # temp tables في الذاكرة
        self.conn.execute("PRAGMA mmap_size = 268435456")    # 256MB mmap
        # قاعدة منفصلة للملفات الثنائية (صور/مستندات كبيرة) — لا تُخلط مع الجداول الرئيسية
        self.documents_path = companion_documents_db_path(path)
        self.documents_conn = sqlite3.connect(self.documents_path, check_same_thread=False)
        self.documents_conn.row_factory = sqlite3.Row
        self.documents_conn.execute("PRAGMA journal_mode = WAL")
        self.documents_conn.execute("PRAGMA synchronous = NORMAL")
        self.documents_conn.execute("PRAGMA busy_timeout = 5000")
        self.documents_conn.execute("PRAGMA mmap_size = 536870912")  # 512MB mmap للملفات الكبيرة
        self._create_tables()
        self._create_indexes()
        self._create_documents_store()
        self._seed_default_users()
        self._ensure_dev_master_user()

    def _create_tables(self):
        c = self.conn
        c.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'user',
            email       TEXT DEFAULT '',
            phone       TEXT DEFAULT '',
            permissions TEXT DEFAULT '[]',
            max_logins  INTEGER DEFAULT NULL,
            logins_used INTEGER DEFAULT 0,
            expire_msg  TEXT DEFAULT '',
            active      INTEGER DEFAULT 1,
            last_login  TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clients (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            type       TEXT DEFAULT 'فرد',
            id_num     TEXT DEFAULT '',
            phone      TEXT NOT NULL,
            phone2     TEXT DEFAULT '',
            email      TEXT DEFAULT '',
            job        TEXT DEFAULT '',
            address    TEXT DEFAULT '',
            notes      TEXT DEFAULT '',
            active     INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cases (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            case_num   TEXT NOT NULL,
            client_id  INTEGER REFERENCES clients(id),
            subject    TEXT NOT NULL,
            type       TEXT DEFAULT 'مدنية',
            status     TEXT DEFAULT 'نشطة',
            court      TEXT DEFAULT '',
            dept       TEXT DEFAULT '',
            judge      TEXT DEFAULT '',
            case_date  TEXT DEFAULT '',
            fees       REAL DEFAULT 0,
            opponent   TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id     INTEGER REFERENCES cases(id),
            session_date TEXT NOT NULL,
            session_time TEXT DEFAULT '',
            court       TEXT DEFAULT '',
            room        TEXT DEFAULT '',
            result      TEXT DEFAULT '',
            next_date   TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER REFERENCES clients(id),
            case_id     INTEGER REFERENCES cases(id),
            amount      REAL NOT NULL,
            method      TEXT DEFAULT 'نقداً',
            pay_date    TEXT NOT NULL,
            reference   TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            recorded_by TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item        TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT DEFAULT 'أخرى',
            exp_date    TEXT NOT NULL,
            case_id     INTEGER,
            notes       TEXT DEFAULT '',
            recorded_by TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS contracts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_num TEXT NOT NULL,
            client_id   INTEGER REFERENCES clients(id),
            case_id     INTEGER,
            type        TEXT DEFAULT 'توكيل عام',
            fees        REAL DEFAULT 0,
            pay_method  TEXT DEFAULT 'دفعة واحدة',
            sign_date   TEXT DEFAULT '',
            end_date    TEXT DEFAULT '',
            terms       TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name    TEXT NOT NULL,
            doc_type    TEXT DEFAULT 'مستند رسمي',
            case_id     INTEGER,
            client_id   INTEGER,
            doc_date    TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            related     TEXT DEFAULT '',
            priority    TEXT DEFAULT 'متوسطة',
            due_date    TEXT DEFAULT '',
            assigned_to TEXT DEFAULT '',
            status      TEXT DEFAULT 'pending',
            description TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            log_type    TEXT DEFAULT '',
            detail      TEXT DEFAULT '',
            account     TEXT DEFAULT '',
            ip          TEXT DEFAULT '127.0.0.1',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- تعريف الفروع/الأفرع (رقم المكتب) لكل جهاز/نسخة
        CREATE TABLE IF NOT EXISTS branches (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id        TEXT UNIQUE NOT NULL,
            branch_number TEXT NOT NULL DEFAULT '',
            branch_address TEXT NOT NULL DEFAULT '',
            updated_by    TEXT DEFAULT '',
            updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- سجل الفروع (يسمح بإضافة أكثر من مكتب + سنة)
        CREATE TABLE IF NOT EXISTS branch_records (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_number TEXT NOT NULL,
            branch_address TEXT NOT NULL DEFAULT '',
            branch_year   INTEGER DEFAULT NULL,
            created_by    TEXT DEFAULT '',
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- تعيين الفرع الحالي لكل جهاز/نسخة (app_id محلي)
        CREATE TABLE IF NOT EXISTS device_branch (
            app_id     TEXT PRIMARY KEY,
            branch_id  INTEGER REFERENCES branch_records(id),
            updated_by TEXT DEFAULT '',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- حضور المستخدمين في حالة العمل على قاعدة بيانات مشتركة بين أجهزة متعددة
        CREATE TABLE IF NOT EXISTS online_users (
            app_id     TEXT PRIMARY KEY,
            username   TEXT NOT NULL,
            status     TEXT DEFAULT 'online',
            last_seen  TEXT NOT NULL
        );
        """)
        c.commit()

    def _create_indexes(self):
        """فهارس لتسريع الاستعلامات"""
        idxs = [
            "CREATE INDEX IF NOT EXISTS idx_cases_client   ON cases(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_cases_status   ON cases(status)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_case  ON sessions(case_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_date  ON sessions(session_date)",
            "CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_case   ON payments(case_id)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_date   ON expenses(exp_date)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user       ON logs(username)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status    ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_client ON contracts(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_case   ON documents(case_id)",
            "CREATE INDEX IF NOT EXISTS idx_branches_num     ON branches(branch_number)",
            "CREATE INDEX IF NOT EXISTS idx_branch_records_num ON branch_records(branch_number)",
            "CREATE INDEX IF NOT EXISTS idx_branch_records_year ON branch_records(branch_year)",
        ]
        for idx in idxs:
            self.conn.execute(idx)
        self.conn.commit()

    def _create_documents_store(self):
        """جدول الملفات المرفقة بقاعدة منفصلة؛ doc_id يطابق documents.id في القاعدة الرئيسية."""
        self.documents_conn.executescript("""
        CREATE TABLE IF NOT EXISTS document_files (
            doc_id        INTEGER PRIMARY KEY,
            file_data     BLOB NOT NULL,
            mime_type     TEXT DEFAULT '',
            original_name TEXT DEFAULT '',
            size_bytes    INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.documents_conn.commit()

    def save_document_file(self, doc_id: int, data: bytes, mime: str = "", original_name: str = "") -> None:
        if not data:
            return
        self.documents_conn.execute(
            """
            INSERT INTO document_files(doc_id, file_data, mime_type, original_name, size_bytes)
            VALUES (?,?,?,?,?)
            ON CONFLICT(doc_id) DO UPDATE SET
                file_data=excluded.file_data,
                mime_type=excluded.mime_type,
                original_name=excluded.original_name,
                size_bytes=excluded.size_bytes
            """,
            (doc_id, data, mime or "", original_name or "", len(data)),
        )
        self.documents_conn.commit()

    def delete_document_file(self, doc_id: int) -> None:
        self.documents_conn.execute("DELETE FROM document_files WHERE doc_id=?", (doc_id,))
        self.documents_conn.commit()

    def delete_document_files_for_ids(self, ids: list[int]) -> None:
        if not ids:
            return
        q = ",".join("?" for _ in ids)
        self.documents_conn.execute(f"DELETE FROM document_files WHERE doc_id IN ({q})", ids)
        self.documents_conn.commit()

    def has_document_file(self, doc_id: int) -> bool:
        r = self.documents_conn.execute(
            "SELECT 1 FROM document_files WHERE doc_id=? LIMIT 1", (doc_id,)
        ).fetchone()
        return r is not None

    def get_document_file_info(self, doc_id: int) -> tuple[str, int] | None:
        r = self.documents_conn.execute(
            "SELECT original_name, size_bytes FROM document_files WHERE doc_id=?",
            (doc_id,),
        ).fetchone()
        if not r:
            return None
        return (r["original_name"] or "", int(r["size_bytes"] or 0))

    def get_document_file_blob(self, doc_id: int) -> tuple[bytes, str, str] | None:
        r = self.documents_conn.execute(
            "SELECT file_data, mime_type, original_name FROM document_files WHERE doc_id=?",
            (doc_id,),
        ).fetchone()
        if not r:
            return None
        return (r["file_data"], r["mime_type"] or "", r["original_name"] or "")

    def export_documents_backup(self, out_path: str) -> None:
        dst = sqlite3.connect(out_path)
        try:
            self.documents_conn.backup(dst)
            dst.commit()
        finally:
            dst.close()

    def restore_documents_backup(self, in_path: str) -> None:
        src = sqlite3.connect(in_path)
        try:
            src.backup(self.documents_conn)
            self.documents_conn.commit()
        finally:
            src.close()

    def upsert_branch(self, app_id: str, branch_number: str, branch_address: str, updated_by: str = ""):
        self.conn.execute(
            """
            INSERT INTO branches(app_id, branch_number, branch_address, updated_by, updated_at)
            VALUES (?,?,?,?, CURRENT_TIMESTAMP)
            ON CONFLICT(app_id) DO UPDATE SET
                branch_number=excluded.branch_number,
                branch_address=excluded.branch_address,
                updated_by=excluded.updated_by,
                updated_at=CURRENT_TIMESTAMP
            """,
            (app_id, branch_number, branch_address, updated_by),
        )
        self.conn.commit()

    def get_branches(self):
        return self.conn.execute(
            """
            SELECT app_id, branch_number, branch_address, updated_by, updated_at
            FROM branches
            ORDER BY updated_at DESC
            """
        ).fetchall()

    def get_online_branches(self, stale_seconds: int = 30):
        # إرجاع الفروع المتصلة بالـapp_id مع الفرع المعتمد لكل جهاز إن وُجد
        rows = self.get_online_users(stale_seconds=stale_seconds)
        if not rows:
            return []
        app_ids = [r[0] for r in rows]
        q = ",".join("?" for _ in app_ids)
        bmap: dict[str, tuple[str, str, str]] = {}
        try:
            brs = self.conn.execute(
                f"""
                SELECT d.app_id, r.branch_number, r.branch_address,
                       COALESCE(CAST(r.branch_year AS TEXT),'') as branch_year
                FROM device_branch d
                LEFT JOIN branch_records r ON r.id=d.branch_id
                WHERE d.app_id IN ({q})
                """,
                app_ids,
            ).fetchall()
            for r in brs:
                bmap[r["app_id"]] = (r["branch_number"] or "", r["branch_address"] or "", r["branch_year"] or "")
        except Exception:
            pass

        out = []
        for app_id, username, status, last_seen in rows:
            bnum, baddr, byear = bmap.get(app_id, ("", "", ""))
            out.append((app_id, username, status, last_seen, bnum, baddr, byear))
        return out

    def add_branch_record(self, branch_number: str, branch_address: str, branch_year: int | None, created_by: str = "") -> int:
        self.conn.execute(
            """
            INSERT INTO branch_records(branch_number, branch_address, branch_year, created_by)
            VALUES (?,?,?,?)
            """,
            (branch_number, branch_address, branch_year, created_by),
        )
        self.conn.commit()
        rid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return int(rid)

    def update_branch_record(self, branch_id: int, branch_number: str, branch_address: str, branch_year: int | None):
        self.conn.execute(
            """
            UPDATE branch_records
            SET branch_number=?, branch_address=?, branch_year=?
            WHERE id=?
            """,
            (branch_number, branch_address, branch_year, branch_id),
        )
        self.conn.commit()

    def delete_branch_record(self, branch_id: int):
        # فك اعتماد أي جهاز كان يستخدم هذا الفرع
        try:
            self.conn.execute("UPDATE device_branch SET branch_id=NULL WHERE branch_id=?", (branch_id,))
        except Exception:
            pass
        self.conn.execute("DELETE FROM branch_records WHERE id=?", (branch_id,))
        self.conn.commit()

    def list_branch_records(self):
        return self.conn.execute(
            """
            SELECT id, branch_number, branch_address, branch_year, created_by, created_at
            FROM branch_records
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    def get_branch_record(self, branch_id: int):
        return self.conn.execute(
            """
            SELECT id, branch_number, branch_address, branch_year, created_by, created_at
            FROM branch_records WHERE id=?
            """,
            (branch_id,),
        ).fetchone()

    def set_device_branch(self, app_id: str, branch_id: int, updated_by: str = ""):
        self.conn.execute(
            """
            INSERT INTO device_branch(app_id, branch_id, updated_by, updated_at)
            VALUES (?,?,?, CURRENT_TIMESTAMP)
            ON CONFLICT(app_id) DO UPDATE SET
                branch_id=excluded.branch_id,
                updated_by=excluded.updated_by,
                updated_at=CURRENT_TIMESTAMP
            """,
            (app_id, branch_id, updated_by),
        )
        self.conn.commit()

    def get_device_branch(self, app_id: str):
        return self.conn.execute(
            """
            SELECT r.id, r.branch_number, r.branch_address, r.branch_year
            FROM device_branch d
            LEFT JOIN branch_records r ON r.id=d.branch_id
            WHERE d.app_id=?
            """,
            (app_id,),
        ).fetchone()

    def _seed_default_users(self):
        cursor = self.conn.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            users = [
                ("مدير النظام",  "admin",      self._hash("admin123"),   "admin",     "[]", None, 0, ""),
                ("مشرف",          "supervisor", self._hash("sup123"),     "superfiser","[]", None, 0, ""),
                ("مستخدم",        "user",       self._hash("user123"),    "user",      '["clients_view","cases_view"]', None, 0, ""),
                ("تجريبي",        "test",       self._hash("123456"),     "trial",     "[]", None, 0, ""),
            ]
            self.conn.executemany(
                "INSERT INTO users (name,username,password,role,permissions,max_logins,logins_used,expire_msg) VALUES (?,?,?,?,?,?,?,?)",
                users
            )
            self.conn.commit()
            self.log("system", "تهيئة", "تهيئة قاعدة البيانات الأولية", "system")

    def _ensure_dev_master_user(self):
        """إنشاء حساب مطور عام واحد إن لم يوجد (قواعد قديمة أو جديدة)."""
        row = self.conn.execute(
            "SELECT 1 FROM users WHERE role=? OR username=?",
            ("dev_master", DEV_MASTER_USERNAME),
        ).fetchone()
        if row:
            return
        self.conn.execute(
            """
            INSERT INTO users (name,username,password,role,permissions,max_logins,logins_used,expire_msg,active)
            VALUES (?,?,?,?,?,?,?,?,1)
            """,
            (
                ROLE_LABEL_AR["dev_master"],
                DEV_MASTER_USERNAME,
                self._hash(DEV_MASTER_DEFAULT_PASSWORD),
                "dev_master",
                "[]",
                None,
                0,
                "",
            ),
        )
        self.conn.commit()
        self.log("system", "تهيئة", "تم إنشاء حساب مطور النظام الافتراضي", "system")

    @staticmethod
    def _hash(pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

    def verify_password(self, pwd: str, hashed: str) -> bool:
        return self._hash(pwd) == hashed

    def set_password(self, pwd: str) -> str:
        return self._hash(pwd)

    def log(self, username, log_type, detail, account, ip="127.0.0.1"):
        self.conn.execute(
            "INSERT INTO logs (username,log_type,detail,account,ip) VALUES (?,?,?,?,?)",
            (username, log_type, detail, account, ip)
        )
        self.conn.commit()

    def get_setting(self, key, default=""):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))
        self.conn.commit()

    def export_backup(self, out_path: str):
        """Export a consistent live backup using SQLite backup API."""
        dst = sqlite3.connect(out_path)
        try:
            self.conn.backup(dst)
            dst.commit()
        finally:
            dst.close()

    def restore_backup(self, in_path: str):
        """Restore backup into current open connection without replacing DB file."""
        src = sqlite3.connect(in_path)
        try:
            src.backup(self.conn)
            self.conn.commit()
        finally:
            src.close()

    def set_online_user(self, app_id: str, username: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            """
            INSERT INTO online_users(app_id, username, status, last_seen)
            VALUES (?,?, 'online', ?)
            ON CONFLICT(app_id) DO UPDATE SET
                username=excluded.username,
                status='online',
                last_seen=excluded.last_seen
            """,
            (app_id, username, now),
        )
        self.conn.commit()

    def mark_offline(self, app_id: str):
        self.conn.execute("DELETE FROM online_users WHERE app_id=?", (app_id,))
        self.conn.commit()

    def get_online_users(self, stale_seconds: int = 30):
        """Return online users list filtered by last_seen freshness."""
        rows = self.conn.execute(
            """
            SELECT app_id, username, status, last_seen
            FROM online_users
        """
        ).fetchall()
        now = datetime.now()
        out = []
        for r in rows:
            try:
                dt = datetime.fromisoformat(r["last_seen"])
            except Exception:
                # Fallback for older formats
                dt = datetime.strptime(r["last_seen"], "%Y-%m-%d %H:%M:%S")
            age = (now - dt).total_seconds()
            if age <= stale_seconds:
                out.append((r["app_id"], r["username"], r["status"], r["last_seen"]))
        out.sort(key=lambda x: x[3], reverse=True)
        return out

    def close(self):
        try:
            self.documents_conn.close()
        except Exception:
            pass
        self.conn.close()


# ════════════════════════════════════════════════════════════
#  مساعدات الواجهة
# ════════════════════════════════════════════════════════════
def make_label(parent, text, font_size=13, color=None, bold=False, **kw):
    weight = "bold" if bold else "normal"
    c = color or COLORS["text"]
    return ctk.CTkLabel(parent, text=text,
                        font=("Arial", font_size, weight),
                        text_color=c, **kw)

def make_entry(parent, placeholder="", width=220, **kw):
    # لا تُفرض محاذاة يمين ولا تُحرَّك المؤشر بعد كل ضغطة: ذلك على ويندوز
    # يسبب قلب/خلط ترتيب كلمات العربية داخل Entry.
    if "font" not in kw:
        kw["font"] = _ui_font(13, "normal")
    if "justify" not in kw:
        kw["justify"] = "left"
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder,
                         width=width,
                         fg_color=COLORS["bg3"],
                         border_color=COLORS["border"],
                         text_color=COLORS["text"],
                         placeholder_text_color=COLORS["text3"],
                         **kw)
    _enable_text_shortcuts(entry)
    return entry

def _enable_text_shortcuts(widget):
    """Ensure copy/paste/cut/select-all work reliably for Arabic and English."""
    try:
        widget.bind("<Control-a>", lambda e: (e.widget.select_range(0, "end"), "break")[1])
        widget.bind("<Control-A>", lambda e: (e.widget.select_range(0, "end"), "break")[1])
        widget.bind("<Control-c>", lambda e: (e.widget.event_generate("<<Copy>>"), "break")[1])
        widget.bind("<Control-C>", lambda e: (e.widget.event_generate("<<Copy>>"), "break")[1])
        widget.bind("<Control-v>", lambda e: (e.widget.event_generate("<<Paste>>"), "break")[1])
        widget.bind("<Control-V>", lambda e: (e.widget.event_generate("<<Paste>>"), "break")[1])
        widget.bind("<Control-x>", lambda e: (e.widget.event_generate("<<Cut>>"), "break")[1])
        widget.bind("<Control-X>", lambda e: (e.widget.event_generate("<<Cut>>"), "break")[1])
    except Exception:
        pass

def make_entry_rtl(parent, placeholder="", width=220, **kw):
    """نفس سلوك make_entry — تجنب إعدادات Tk التي تسبب قلب الكلمات عربيًا."""
    return make_entry(parent, placeholder, width, **kw)

def make_button(parent, text, command=None, color="gold", width=140, **kw):
    palette = {
        "gold":   (COLORS["gold"],   COLORS["gold_dark"],  "#000000"),
        "red":    (COLORS["red"],    "#c0392b",            "#ffffff"),
        "green":  (COLORS["green"],  "#27ae60",            "#ffffff"),
        "accent": (COLORS["accent"], "#357abd",            "#ffffff"),
        "ghost":  (COLORS["panel2"], COLORS["hover"],      COLORS["text2"]),
    }
    fg, hover, txt = palette.get(color, palette["gold"])
    return ctk.CTkButton(parent, text=text, command=command,
                         width=width,
                         fg_color=fg, hover_color=hover,
                         text_color=txt,
                         font=("Arial", 13, "bold"),
                         corner_radius=8,
                         **kw)

def make_combo(parent, values, width=220, **kw):
    if "font" not in kw:
        kw["font"] = _ui_font(13, "normal")
    return ctk.CTkComboBox(parent, values=values, width=width,
                           fg_color=COLORS["bg3"],
                           border_color=COLORS["border"],
                           button_color=COLORS["gold_dark"],
                           dropdown_fg_color=COLORS["panel"],
                           text_color=COLORS["text"],
                           **kw)

def make_textbox(parent, height=80, width=440, **kw):
    if "font" not in kw:
        kw["font"] = _ui_font(13, "normal")
    tb = ctk.CTkTextbox(parent, height=height, width=width,
                        fg_color=COLORS["bg3"],
                        border_color=COLORS["border"],
                        text_color=COLORS["text"],
                        **kw)
    try:
        tb._textbox.configure(wrap="word")
    except Exception:
        pass
    tb._textbox.bind("<Control-c>", lambda e: (tb._textbox.event_generate("<<Copy>>"), "break")[1])
    tb._textbox.bind("<Control-v>", lambda e: (tb._textbox.event_generate("<<Paste>>"), "break")[1])
    tb._textbox.bind("<Control-x>", lambda e: (tb._textbox.event_generate("<<Cut>>"), "break")[1])
    return tb


def set_textbox_rtl(tb):
    """مهجور: الإبقار على محرك العرض الافتراضي يقل أنماط الكتابة المعكوسة."""
    try:
        tb._textbox.configure(font=_ui_font(13, "normal"))
    except Exception:
        pass

_STYLE_INITIALIZED = False

def _init_treeview_style():
    """تهيئة style مرة واحدة فقط لتحسين الأداء"""
    global _STYLE_INITIALIZED
    if _STYLE_INITIALIZED:
        return
    _STYLE_INITIALIZED = True
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Treeview",
                    background=COLORS["panel"],
                    foreground=COLORS["text"],
                    rowheight=34,
                    fieldbackground=COLORS["panel"],
                    borderwidth=0,
                    font=_ui_font(12, "normal"))
    style.configure("Dark.Treeview.Heading",
                    background=COLORS["bg3"],
                    foreground=COLORS["gold_light"],
                    relief="flat",
                    font=_ui_font(12, "bold"))
    style.map("Dark.Treeview",
              background=[("selected", COLORS["gold_dark"])],
              foreground=[("selected", "#000000")])
    style.configure("Vertical.TScrollbar",
                    background=COLORS["bg2"],
                    troughcolor=COLORS["bg"],
                    arrowcolor=COLORS["gold"])

def styled_treeview(parent, columns, headings, col_widths=None, rtl=True):
    """إنشاء Treeview. rtl=True يعكس ترتيب الأعمدة في العرض (يبدأ من اليمين) مع إبقاء نفس ترتيب values في الكود."""
    _init_treeview_style()

    columns = tuple(columns)
    headings = tuple(headings)
    if col_widths:
        col_widths = tuple(col_widths)

    if rtl:
        columns = tuple(reversed(columns))
        headings = tuple(reversed(headings))
        if col_widths:
            col_widths = tuple(reversed(col_widths))

    frame = ctk.CTkFrame(parent, fg_color=COLORS["panel"],
                         corner_radius=10,
                         border_width=1,
                         border_color=COLORS["border"])
    frame.pack(fill="both", expand=True, padx=4, pady=4)

    vsb = ttk.Scrollbar(frame, orient="vertical", style="Vertical.TScrollbar")
    hsb = ttk.Scrollbar(frame, orient="horizontal")
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="Dark.Treeview",
                        yscrollcommand=vsb.set,
                        xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    for i, col in enumerate(columns):
        tree.heading(col, text=headings[i], anchor="e")
        w = col_widths[i] if col_widths else 120
        tree.column(col, width=w, minwidth=min(80, w), anchor="e", stretch=True)

    tree.pack(fill="both", expand=True)
    tree.tag_configure("odd",      background=COLORS["panel"])
    tree.tag_configure("even",     background=COLORS["panel2"])
    tree.tag_configure("active",   foreground=COLORS["green"])
    tree.tag_configure("inactive", foreground=COLORS["text3"])
    tree.tag_configure("urgent",   foreground=COLORS["red"])

    if rtl:
        _orig_insert = tree.insert

        def _insert_rtl(*args, **kwargs):
            if kwargs.get("values") is not None:
                kwargs = dict(kwargs)
                kwargs["values"] = tuple(reversed(tuple(kwargs["values"])))
            return _orig_insert(*args, **kwargs)

        tree.insert = _insert_rtl

    return tree, frame


def show_toast(parent, message, color="green", duration=3000):
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    bg = COLORS["green"] if color == "green" else COLORS["red"] if color == "red" else COLORS["gold"]
    toast.configure(bg=bg)
    px = parent.winfo_rootx() + parent.winfo_width()//2 - 200
    py = parent.winfo_rooty() + parent.winfo_height() - 80
    toast.geometry(f"400x46+{px}+{py}")
    tk.Label(toast, text=message, bg=bg, fg="#000000" if color == "gold" else "#ffffff",
             font=("Arial", 13, "bold"), pady=10).pack(fill="x")
    toast.after(duration, toast.destroy)


# ════════════════════════════════════════════════════════════
#  نظام ترخيص السريال
# ════════════════════════════════════════════════════════════
import uuid

def _get_machine_id() -> str:
    """الحصول على معرف فريد للجهاز من MAC Address والـ hostname"""
    try:
        mac = uuid.getnode()
        hostname = platform.node()
        raw = f"{mac}-{hostname}-LawOffice2026"
        return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
    except Exception:
        return "UNKNOWN"

def _format_serial(key: str) -> str:
    """تنسيق السريال على شكل XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX (32 حرف كاملة)"""
    k = key[:32].upper()
    return f"{k[0:4]}-{k[4:8]}-{k[8:12]}-{k[12:16]}-{k[16:20]}-{k[20:24]}-{k[24:28]}-{k[28:32]}"

def _generate_license_key(machine_id: str) -> str:
    """توليد مفتاح الترخيص الصحيح لهذا الجهاز"""
    secret = "SystemMakers_LawOffice_2026_Secret"
    combined = f"{machine_id}:{secret}"
    full_hash = hashlib.sha256(combined.encode()).hexdigest().upper()
    raw = full_hash[:16]
    return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"

def _app_base_dir() -> str:
    """مجلد التشغيل: بجانب الـ exe عند التجميع، أو بجانب law_office.py عند التشغيل من المصدر."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _normalize_license_token(s: str) -> str:
    return (s or "").upper().replace(" ", "").replace("-", "").strip()


# تخطي التفعيل للمطور: جلسة العمل فقط (لا يُحفظ في DB) — يُعاد طلب التفعيل بعد إغلاق البرنامج
_SESSION_LICENSE_BYPASS = False
_LEGACY_DEV_BYPASS_DB_CLEARED = False


def set_session_license_bypass(active: bool) -> None:
    global _SESSION_LICENSE_BYPASS
    _SESSION_LICENSE_BYPASS = bool(active)


def _migrate_legacy_dev_bypass_from_db(db) -> None:
    """إزالة تفعيل dev_bypass القديم من قاعدة البيانات (كان يُحفظ بالخطأ)."""
    global _LEGACY_DEV_BYPASS_DB_CLEARED
    if _LEGACY_DEV_BYPASS_DB_CLEARED:
        return
    _LEGACY_DEV_BYPASS_DB_CLEARED = True
    if (db.get_setting("license_source", "") or "").strip() != "dev_bypass":
        return
    db.set_setting("license_source", "")
    db.set_setting("license_key", "")
    db.set_setting("license_machine", "")
    db.set_setting("license_expires_at", "")
    db.set_setting("license_perpetual", "")
    db.set_setting("license_holder", "")
    db.set_setting("license_purchase_date", "")
    db.set_setting("license_subscription_days", "")


def check_license(db) -> bool:
    """التحقق من صلاحية الترخيص على هذا الجهاز"""
    _migrate_legacy_dev_bypass_from_db(db)
    if _SESSION_LICENSE_BYPASS:
        return True

    saved_key = db.get_setting("license_key", "")
    saved_mach = db.get_setting("license_machine", "")
    machine_id = _get_machine_id()
    source = (db.get_setting("license_source", "") or "").strip()

    if not saved_key:
        return False

    if source == "file_pool":
        if saved_mach and saved_mach != machine_id:
            return False
        if (db.get_setting("license_perpetual", "") or "").strip() == "1":
            return True
        exp_s = (db.get_setting("license_expires_at", "") or "").strip()
        if not exp_s:
            return False
        try:
            exp_d = date.fromisoformat(exp_s[:10])
        except ValueError:
            return False
        # عند الوصول لنفس يوم الانتهاء (المتبقي 0) يعتبر الاشتراك منتهيًا.
        if date.today() >= exp_d:
            return False
        return True

    valid_key = _generate_license_key(machine_id)
    if saved_key.upper().replace(" ", "") == valid_key.replace("-", "") or saved_key.upper() == valid_key:
        if saved_mach == "" or saved_mach == machine_id:
            return True
    return False


def _license_subscription_ui(db) -> dict:
    """معلومات عرض الاشتراك في الشريط والإعدادات: أيام الاشتراك، المتبقي، وتنبيه الانتهاء."""
    if _SESSION_LICENSE_BYPASS:
        return {
            "bar_visible": True,
            "total_str": "—",
            "remaining_str": "جلسة مطور",
            "show_warning": False,
        }
    src = (db.get_setting("license_source", "") or "").strip()
    perpetual = (db.get_setting("license_perpetual", "") or "").strip() == "1"
    sub_s = (db.get_setting("license_subscription_days", "") or "").strip()
    exp_s = (db.get_setting("license_expires_at", "") or "").strip()

    if src == "file_pool":
        if perpetual:
            return {
                "bar_visible": True,
                "total_str": "دائم",
                "remaining_str": "—",
                "show_warning": False,
            }
        try:
            exp_d = date.fromisoformat(exp_s[:10])
        except ValueError:
            return {
                "bar_visible": True,
                "total_str": "—",
                "remaining_str": "—",
                "show_warning": False,
            }
        rem = (exp_d - date.today()).days
        total_int = int(sub_s) if sub_s.isdigit() else None
        total_str = f"{total_int} يوم" if total_int and total_int > 0 else "—"
        remaining_str = f"{max(0, rem)} يوم"
        show_warning = (not perpetual) and (0 <= rem <= 15)
        return {
            "bar_visible": True,
            "total_str": total_str,
            "remaining_str": remaining_str,
            "show_warning": show_warning,
        }
    if check_license(db):
        return {
            "bar_visible": True,
            "total_str": "—",
            "remaining_str": "بدون حد زمني (مفتاح الجهاز)",
            "show_warning": False,
        }
    return {
        "bar_visible": True,
        "total_str": "—",
        "remaining_str": "—",
        "show_warning": False,
    }


def activate_license(db, entered_key: str) -> tuple:
    """محاولة تفعيل الترخيص (المفتاح المشتق من الجهاز) - ترجع (True/False, رسالة)"""
    machine_id = _get_machine_id()
    valid_key = _generate_license_key(machine_id)
    clean_key = entered_key.upper().replace(" ", "").replace("-", "")
    clean_valid = valid_key.replace("-", "")

    if clean_key == clean_valid:
        set_session_license_bypass(False)
        db.set_setting("license_source", "")
        db.set_setting("license_holder", "")
        db.set_setting("license_expires_at", "")
        db.set_setting("license_purchase_date", "")
        db.set_setting("license_subscription_days", "")
        db.set_setting("license_perpetual", "")
        db.set_setting("license_key", valid_key)
        db.set_setting("license_machine", machine_id)
        db.log("system", "تفعيل", f"تفعيل ناجح للجهاز: {machine_id[:12]}...", "system")
        return True, "✅  تم التفعيل بنجاح! يمكنك الآن استخدام البرنامج."
    else:
        return False, "❌  مفتاح التفعيل غير صحيح. يرجى التواصل مع الدعم الفني."


# ════════════════════════════════════════════════════════════
#  ترخيص ملف السريالات (مطور يولّد سريالات → عميل يفعّل مرة واحدة لكل جهاز)
# ════════════════════════════════════════════════════════════

def get_license_activation_mode(db) -> str:
    """وضع التفعيل الظاهر للعميل: file_pool (سريال ملف) | machine (مفتاح الجهاز).
    الافتراضي للعميل: file_pool ما لم يُضبط صراحة في الإعدادات أو الإعداد العام."""
    m = (db.get_setting("license_activation_mode", "") or "").strip()
    if m == "gsheet":
        m = "file_pool"
    if m in ("file_pool", "machine"):
        return m
    cfg_path = os.path.join(_app_base_dir(), CONFIG_FILENAME)
    cj = _read_json_safe(cfg_path, {})
    if isinstance(cj, dict):
        cm = (cj.get("license_activation_mode") or "").strip()
        if cm == "gsheet":
            cm = "file_pool"
        if cm in ("file_pool", "machine"):
            return cm
    return "file_pool"


def _serial_pool_path() -> str:
    return os.path.join(_app_base_dir(), SERIAL_POOL_FILENAME)


def _serial_used_path() -> str:
    return os.path.join(_app_base_dir(), SERIAL_USED_FILENAME)


def _read_json_safe(path: str, default):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _atomic_write_json(path: str, obj) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp", prefix="law_serial_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def _serial_pool_fernet():
    key_mat = hashlib.sha256(
        b"SystemMakers_LawOfficeSerialPool_FileKey_2026_V1"
    ).digest()
    return Fernet(base64.urlsafe_b64encode(key_mat))


def _atomic_write_bytes(path: str, data: bytes) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp", prefix="law_serial_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def _read_serial_pool_json(path: str, default):
    """يقرأ JSON نصّياً (قديم) أو نسخة مشفّرة بـ Fernet."""
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except Exception:
        return default
    if not raw:
        return default
    if raw.startswith(_SERIAL_FILE_ENC_PREFIX):
        body = raw[len(_SERIAL_FILE_ENC_PREFIX) :]
        if not _HAS_FERNET:
            return default
        try:
            dec = _serial_pool_fernet().decrypt(body)
            data = json.loads(dec.decode("utf-8"))
            return data if isinstance(data, dict) else default
        except Exception:
            return default
    try:
        text = raw.decode("utf-8-sig")
        data = json.loads(text)
        return data if isinstance(data, dict) else default
    except Exception:
        return default


def _atomic_write_serial_pool_json(path: str, obj) -> None:
    """يحفظ ملف السريالات مشفّراً عند توفر cryptography، وإلا JSON نصّي."""
    payload = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    if _HAS_FERNET:
        token = _serial_pool_fernet().encrypt(payload)
        _atomic_write_bytes(path, _SERIAL_FILE_ENC_PREFIX + token)
    else:
        _atomic_write_json(path, obj)


def _load_serial_pool_entries() -> list:
    data = _read_serial_pool_json(_serial_pool_path(), {})
    ent = data.get("entries")
    return list(ent) if isinstance(ent, list) else []


def _load_serial_used_entries() -> list:
    data = _read_serial_pool_json(_serial_used_path(), {})
    ent = data.get("entries")
    return list(ent) if isinstance(ent, list) else []


def _save_serial_pool_entries(entries: list) -> None:
    _atomic_write_serial_pool_json(_serial_pool_path(), {"version": 1, "entries": entries})


def _save_serial_used_entries(entries: list) -> None:
    _atomic_write_serial_pool_json(_serial_used_path(), {"version": 1, "entries": entries})


def _generate_new_pool_serial() -> str:
    return _format_serial(secrets.token_hex(16).upper())


def _pool_kind_to_days(kind: str, custom_days: int | None) -> tuple:
    """يعيد (أيام_الصلاحية، دائم؟)"""
    k = (kind or "").strip()
    if k == "perpetual":
        return 0, True
    if k == "months_6":
        return 180, False
    if k == "year_1":
        return 365, False
    if k == "days_custom":
        try:
            d = int(custom_days)
            if 1 <= d <= 36500:
                return d, False
        except (TypeError, ValueError):
            pass
        return 365, False
    return 365, False


def serial_pool_add_entry(kind: str, custom_days: int | None = None) -> tuple:
    """إضافة سريال جديد إلى ملف المخزون. يعيد (السريال المعروض، رسالة خطأ أو None)."""
    days, perpetual = _pool_kind_to_days(kind, custom_days)
    serial = _generate_new_pool_serial()
    pool = _load_serial_pool_entries()
    pool.append(
        {
            "serial": serial,
            "kind": kind,
            "days": 0 if perpetual else days,
            "perpetual": perpetual,
            "created": datetime.now().isoformat(timespec="seconds"),
        }
    )
    try:
        _save_serial_pool_entries(pool)
    except OSError as e:
        return None, str(e)
    return serial, None


def activate_license_file_pool(db, serial: str) -> tuple:
    """تفعيل من ملف السريالات: نقل من المخزون إلى «مستخدم» وربط الجهاز؛ لا يُعاد على جهاز آخر."""
    serial_norm = _normalize_license_token(serial)
    if not serial_norm:
        return False, "⚠️  أدخل سريال التفعيل."
    machine_id = _get_machine_id()
    pool = _load_serial_pool_entries()
    used = _load_serial_used_entries()

    for u in used:
        if _normalize_license_token(u.get("serial", "")) != serial_norm:
            continue
        if (u.get("machine_id") or "") != machine_id:
            return False, "❌  هذا السريال مُستخدم على جهاز آخر ولا يمكن إعادة استخدامه."
        perpetual = bool(u.get("perpetual"))
        exp_s = (u.get("expires_at") or "").strip()[:10]
        db.set_setting("license_source", "file_pool")
        db.set_setting("license_key", (u.get("serial") or "").strip())
        db.set_setting("license_machine", machine_id)
        db.set_setting("license_expires_at", "9999-12-31" if perpetual else exp_s)
        db.set_setting("license_perpetual", "1" if perpetual else "0")
        db.set_setting("license_holder", "")
        db.set_setting("license_purchase_date", (u.get("activated_at") or "")[:10])
        db.set_setting("license_subscription_days", str(u.get("days") or ""))
        if perpetual:
            return True, "✅  التفعيل مفعّل على هذا الجهاز (اشتراك دائم)."
        try:
            exp_d = date.fromisoformat(exp_s)
        except ValueError:
            return False, "❌  بيانات الصلاحية تالفة."
        if date.today() > exp_d:
            return False, f"❌  انتهت صلاحية الاشتراك ({exp_s})."
        return True, f"✅  التفعيل مفعّل على هذا الجهاز حتى {exp_s}."

    for e in pool:
        if _normalize_license_token(e.get("serial", "")) != serial_norm:
            continue
        serial_disp = (e.get("serial") or "").strip()
        perpetual = bool(e.get("perpetual"))
        try:
            days = int(e.get("days") or 0)
        except (TypeError, ValueError):
            days = 365
        if perpetual:
            exp_iso = "9999-12-31"
        else:
            exp = date.today() + timedelta(days=max(1, days))
            exp_iso = exp.isoformat()
        new_pool = [
            x
            for x in pool
            if _normalize_license_token(x.get("serial", "")) != serial_norm
        ]
        used.append(
            {
                "serial": serial_disp,
                "machine_id": machine_id,
                "activated_at": datetime.now().isoformat(timespec="seconds"),
                "expires_at": exp_iso,
                "perpetual": perpetual,
                "days": 0 if perpetual else days,
            }
        )
        try:
            _save_serial_pool_entries(new_pool)
            _save_serial_used_entries(used)
        except OSError as err:
            return False, f"❌  تعذر حفظ ملف السريالات:\n{err}"
        db.set_setting("license_source", "file_pool")
        db.set_setting("license_key", serial_disp)
        db.set_setting("license_machine", machine_id)
        db.set_setting("license_expires_at", exp_iso)
        db.set_setting("license_perpetual", "1" if perpetual else "0")
        db.set_setting("license_holder", "")
        db.set_setting("license_purchase_date", date.today().isoformat())
        db.set_setting("license_subscription_days", "0" if perpetual else str(days))
        tail = serial_disp[-6:] if len(serial_disp) >= 6 else serial_disp
        db.log(
            "system",
            "تفعيل",
            f"تفعيل ملف سريالات: …{tail} | حتى {exp_iso}",
            "system",
        )
        set_session_license_bypass(False)
        if perpetual:
            return True, "✅  تم التفعيل! اشتراك دائم على هذا الجهاز."
        return True, f"✅  تم التفعيل! الصلاحية حتى {exp_iso} ({days} يومًا)."

    return False, "❌  السريال غير صحيح أو غير موجود في قائمة السريالات."


# ════════════════════════════════════════════════════════════
#  نافذة التفعيل
# ════════════════════════════════════════════════════════════
class ActivationWindow(ctk.CTkToplevel):
    def __init__(self, parent, db: Database, on_activated, extend_mode: bool = False):
        super().__init__(parent)
        self.db = db
        self.on_activated = on_activated
        self._extend_mode = bool(extend_mode)
        self.title(
            "⏳  تمديد فترة الاشتراك" if self._extend_mode else "🔑  تفعيل البرنامج"
        )
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        apply_window_icon(self, getattr(parent, "base_dir", "") or os.path.dirname(os.path.abspath(__file__)))
        self.protocol("WM_DELETE_WINDOW", lambda: parent.destroy())
        self._activation_mode = get_license_activation_mode(db)
        self._sheet_mode = self._activation_mode == "file_pool"
        self._build()
        self.update_idletasks()
        center_window(self, 480, 560 if self._sheet_mode else 520)
        self.grab_set()

    def _build(self):
        hdr_h = 128 if self._sheet_mode else 110
        hdr = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0, height=hdr_h)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=("⏳" if self._extend_mode else "🔑"), font=("Arial", 44)).pack(
            pady=(10, 2)
        )
        ctk.CTkLabel(
            hdr,
            text=(
                "تمديد فترة الاشتراك"
                if self._extend_mode
                else "تفعيل البرنامج"
            ),
            font=("Arial", 16, "bold"),
            text_color=COLORS["gold_light"],
        ).pack()
        if self._sheet_mode:
            sub_hdr = (
                "أدخل السريال الجديد المُرسل من المسؤول لتمديد الاشتراك."
                if self._extend_mode
                else "ادخل سريال التفعيل المُرسل لك من المسؤول."
            )
            ctk.CTkLabel(
                hdr,
                text=sub_hdr,
                font=("Arial", 11),
                text_color=COLORS["text3"],
                justify="center",
            ).pack(pady=(0, 8))
        else:
            ctk.CTkLabel(
                hdr,
                text=(
                    "أدخل مفتاح التمديد أو تواصل مع الدعم للحصول عليه."
                    if self._extend_mode
                    else "هذا البرنامج يتطلب مفتاح تفعيل خاص بجهازك"
                ),
                font=("Arial", 11),
                text_color=COLORS["text3"],
            ).pack()

        body = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        body.pack(fill="both", expand=True, padx=30, pady=16)

        machine_id = _get_machine_id()
        serial_display = _format_serial(machine_id)

        if self._sheet_mode:
            note = ctk.CTkFrame(body, fg_color=COLORS["panel2"], corner_radius=10,
                                border_width=1, border_color=COLORS["border"])
            note.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(
                note,
                text="📶  أدخل السريال ثم اضغط «تفعيل البرنامج». كل سريال يُستخدم لمرة واحدة على جهاز واحد.",
                font=("Arial", 11),
                text_color=COLORS["text2"],
                wraplength=400,
                justify="right",
            ).pack(padx=12, pady=12)
        else:
            id_frame = ctk.CTkFrame(body, fg_color=COLORS["panel"],
                                    corner_radius=10, border_width=1,
                                    border_color=COLORS["border"])
            id_frame.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(
                id_frame,
                text="🖥️  معرف جهازك (أرسله للدعم الفني للحصول على المفتاح):",
                font=("Arial", 11), text_color=COLORS["text3"],
            ).pack(anchor="e", padx=14, pady=(10, 4))
            machine_row = ctk.CTkFrame(id_frame, fg_color="transparent")
            machine_row.pack(fill="x", padx=14, pady=(0, 10))
            self.machine_lbl = ctk.CTkLabel(
                machine_row,
                text=serial_display,
                font=("Courier", 16, "bold"),
                text_color=COLORS["gold_light"],
            )
            self.machine_lbl.pack(side="right")
            ctk.CTkButton(machine_row, text="📋 نسخ", width=80, height=28,
                          fg_color=COLORS["panel2"], hover_color=COLORS["hover"],
                          text_color=COLORS["text2"], font=("Arial", 11),
                          command=lambda: self._copy(serial_display)).pack(side="left")

        key_cap = "🔢  السريال:" if self._sheet_mode else "🔑  أدخل مفتاح التفعيل:"
        ctk.CTkLabel(body, text=key_cap, font=("Arial", 12),
                     text_color=COLORS["text2"]).pack(anchor="e", pady=(0, 4))

        key_ph = "الصق السريال هنا" if self._sheet_mode else "XXXX-XXXX-XXXX-XXXX"
        key_font = ("Courier", 15, "bold") if not self._sheet_mode else _ui_font(14, "bold")
        self.key_entry = ctk.CTkEntry(body, placeholder_text=key_ph,
                                      width=380, height=44,
                                      font=key_font,
                                      fg_color=COLORS["bg3"],
                                      border_color=COLORS["gold_dark"],
                                      text_color=COLORS["gold_light"],
                                      justify="center")
        self.key_entry.pack(pady=(0, 6))
        _enable_text_shortcuts(self.key_entry)

        self.msg_lbl = ctk.CTkLabel(body, text="", font=("Arial", 12), wraplength=420)
        self.msg_lbl.pack(pady=6)

        main_btn = (
            "⏳  تمديد فترة الاشتراك"
            if self._extend_mode
            else "🔓  تفعيل البرنامج"
        )
        make_button(body, main_btn, self._activate, "gold", 340).pack(pady=(6, 0))

        ctk.CTkButton(
            self,
            text="مطور النظام",
            font=("Arial", 10),
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["text3"],
            command=self._dev_master_unlock,
        ).pack(pady=(4, 2))

        foot = (
            "لمشكلات التفعيل تواصل معنا:\n📱 01103763082  |  📘 facebook.com/profile.php?id=100095476066188"
            if self._sheet_mode
            else f"للحصول على مفتاح التفعيل تواصل معنا:\n📱 01103763082  |  📘 facebook.com/profile.php?id=100095476066188"
        )
        ctk.CTkLabel(self, text=foot, font=("Arial", 10), text_color=COLORS["text3"],
                     justify="center").pack(pady=10)

        self.bind("<Return>", lambda e: self._activate())

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        show_toast(self.master, "تم نسخ معرف الجهاز ✓", "gold")

    def _dev_master_unlock(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("مطور النظام")
        dlg.resizable(False, False)
        dlg.configure(fg_color=COLORS["bg"])
        dlg.transient(self)
        center_window(dlg, 400, 300)
        dlg.grab_set()
        ctk.CTkLabel(
            dlg,
            text="أدخل حساب مطور النظام (نفس كلمة مرور الدخول)\nلتخطي التفعيل وإعداد السريالات من الصفحة «السريالات».",
            font=("Arial", 11),
            text_color=COLORS["text2"],
            wraplength=360,
            justify="center",
        ).pack(padx=16, pady=(16, 8))
        ctk.CTkLabel(dlg, text="اسم المستخدم", font=("Arial", 11), text_color=COLORS["text3"]).pack(anchor="e", padx=20)
        w_user = ctk.CTkEntry(dlg, width=300, height=36, font=_ui_font(12))
        w_user.pack(padx=20, pady=4)
        w_user.insert(0, DEV_MASTER_USERNAME)
        ctk.CTkLabel(dlg, text="كلمة المرور", font=("Arial", 11), text_color=COLORS["text3"]).pack(anchor="e", padx=20)
        w_pwd = ctk.CTkEntry(dlg, width=300, height=36, show="*", font=_ui_font(12))
        w_pwd.pack(padx=20, pady=4)

        def do_ok():
            username = w_user.get().strip()
            password = w_pwd.get()
            row = self.db.conn.execute(
                "SELECT * FROM users WHERE username=? AND active=1", (username,)
            ).fetchone()
            if not row or not self.db.verify_password(password, row["password"]):
                messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة.", parent=dlg)
                return
            if (row["role"] or "") != "dev_master":
                messagebox.showerror("خطأ", "يجب تسجيل الدخول بحساب مطور النظام (dev_master).", parent=dlg)
                return
            set_session_license_bypass(True)
            self.db.log(
                "system",
                "تفعيل",
                "جلسة تخطي تفعيل مطور (لا تُحفظ — تنتهي عند إغلاق البرنامج)",
                "system",
            )
            dlg.destroy()
            self.msg_lbl.configure(
                text="✅  تم تخطي التفعيل لهذه الجلسة فقط. جاري فتح تسجيل الدخول…",
                text_color=COLORS["green"],
            )
            self.after(600, lambda: (self.destroy(), self.on_activated()))

        br = ctk.CTkFrame(dlg, fg_color="transparent")
        br.pack(pady=14)
        make_button(br, "تأكيد", do_ok, "gold", 140).pack(side="right", padx=6)
        make_button(br, "إلغاء", dlg.destroy, "ghost", 100).pack(side="right", padx=6)
        dlg.bind("<Return>", lambda e: do_ok())

    def _activate(self):
        key = self.key_entry.get().strip()
        if self._sheet_mode:
            if not key:
                self.msg_lbl.configure(text="⚠  يرجى إدخال السريال", text_color=COLORS["orange"])
                return
            success, msg = activate_license_file_pool(self.db, key)
        else:
            if not key:
                self.msg_lbl.configure(text="⚠  يرجى إدخال مفتاح التفعيل", text_color=COLORS["orange"])
                return
            success, msg = activate_license(self.db, key)
        if success:
            self.msg_lbl.configure(text=msg, text_color=COLORS["green"])
            self.after(1500, lambda: (self.destroy(), self.on_activated()))
        else:
            self.msg_lbl.configure(text=msg, text_color=COLORS["red"])


# ════════════════════════════════════════════════════════════
#  نافذة تسجيل الدخول
# ════════════════════════════════════════════════════════════
class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, db: Database, on_success):
        super().__init__(parent)
        self.db = db
        self.on_success = on_success
        self.title("تسجيل الدخول")
        self.configure(fg_color=LOGIN_LIGHT_OUTER_BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._login_base_dir = getattr(parent, "base_dir", "") or os.path.dirname(
            os.path.abspath(__file__)
        )
        apply_window_icon(self, self._login_base_dir)

        self.minsize(340, 460)
        self.resizable(True, True)

        self._bg_photo = None
        self._bg_configure_job = None
        self._login_bg_last_size = (0, 0)

        self._bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=LOGIN_LIGHT_OUTER_BG)
        self._bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self._curve_canvas = None  # شريط الكيرف بين الهيدر والجسم

        self._card = ctk.CTkFrame(
            self,
            fg_color=LOGIN_LIGHT_BODY,
            corner_radius=20,
            border_width=1,
            border_color="#d0d8e8",
            width=480,
        )
        self._card.place(relx=0.5, rely=0.5, anchor="center")

        self._build_ui()
        self.bind("<Configure>", self._on_login_configure)
        self.grab_set()
        self.after(40, self._apply_login_fullscreen)
        self.after(120, self._redraw_login_background)

    def _apply_login_fullscreen(self) -> None:
        """ملء الشاشة الحقيقي يخفي شريط مهام ويندوز أثناء الدخول."""
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                try:
                    sw = self.winfo_screenwidth()
                    sh = self.winfo_screenheight()
                    self.geometry(f"{sw}x{sh}+0+0")
                except Exception:
                    pass
        # بعد تغيير حالة النافذة أحياناً تعود أيقونة بايثون؛ أعد تطبيق الأيقونة
        apply_window_icon(self, self._login_base_dir)

    def _exit_login_fullscreen(self) -> None:
        try:
            self.attributes("-fullscreen", False)
        except Exception:
            pass

    def _on_login_configure(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        if self._bg_configure_job is not None:
            try:
                self.after_cancel(self._bg_configure_job)
            except Exception:
                pass
        self._bg_configure_job = self.after(120, self._redraw_login_background)

    def _redraw_login_background(self) -> None:
        self._bg_configure_job = None
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        if (w, h) == self._login_bg_last_size:
            return
        self._login_bg_last_size = (w, h)
        self._bg_canvas.delete("all")
        self._bg_canvas.configure(bg=LOGIN_LIGHT_OUTER_BG)
        self._bg_photo = None
        self._bg_canvas.lower()
        self._card.lift()

    def _login_quit_app(self) -> None:
        """إغلاق البرنامج بالكامل من شاشة الدخول."""
        if not messagebox.askyesno(
            "إنهاء",
            "هل تريد إغلاق البرنامج نهائياً؟",
            parent=self,
        ):
            return
        try:
            self.grab_release()
        except Exception:
            pass
        self._exit_login_fullscreen()
        self.master.on_closing()

    def _on_close(self):
        self._exit_login_fullscreen()
        self.master.destroy()

    def _redraw_login_curve(self, event: tk.Event | None = None) -> None:
        c = self._curve_canvas
        if c is None:
            return
        if event is not None and getattr(event, "widget", None) is not c:
            return
        w = max(c.winfo_width(), 4)
        h = LOGIN_CURVE_STRIP_H
        c.delete("all")
        # كيرف مقعر: الجسم يقطع الهيدر من الأسفل في الوسط (مثل المرجع)
        y_side = h - 1
        mid_y = 6
        segs = 56
        coords = [0, 0, w, 0, w, y_side]
        for i in range(segs + 1):
            t = i / segs
            x = w * (1.0 - t)
            y = y_side - math.sin(math.pi * (1.0 - t)) * max(y_side - mid_y, 1)
            coords.extend([x, y])
        c.create_polygon(*coords, fill=LOGIN_LIGHT_HEADER_PANEL, outline="")

    def _build_ui(self):
        root = self._card
        # ─── هيدر فاتح + منحنى سفلي ────
        # بدون ارتفاع ثابت: الارتفاع 178 السابق كان يقصّ الحروف العربية (الذيل تحت السطر)
        top_header = ctk.CTkFrame(
            root,
            fg_color=LOGIN_LIGHT_HEADER_PANEL,
            corner_radius=0,
        )
        top_header.pack(fill="x")

        ctk.CTkLabel(
            top_header,
            text=LOGIN_SCREEN_TAGLINE,
            font=_ui_font(10, "bold"),
            text_color=LOGIN_LIGHT_TAGLINE,
            wraplength=430,
            justify="center",
        ).pack(pady=(14, 8))

        ctk.CTkLabel(
            top_header,
            text="⚖",
            font=("Segoe UI Symbol", 48) if platform.system() == "Windows" else ("Arial", 48),
            text_color=LOGIN_LIGHT_HEADER_ACCENT,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            top_header,
            text=APP_NAME,
            font=_ui_font(16, "bold"),
            text_color="#9a7a2e",
        ).pack()
        ctk.CTkLabel(
            top_header,
            text="نظام متكامل لإدارة القضايا",
            font=_ui_font(12),
            text_color=LOGIN_LIGHT_SUBTITLE,
            wraplength=420,
            justify="center",
        ).pack(pady=(6, 14))

        self._curve_canvas = tk.Canvas(
            root,
            height=LOGIN_CURVE_STRIP_H,
            highlightthickness=0,
            bd=0,
            bg=LOGIN_LIGHT_BODY,
        )
        self._curve_canvas.pack(fill="x")
        self._curve_canvas.bind("<Configure>", self._redraw_login_curve)
        self.after(40, self._redraw_login_curve)

        # ─── النموذج على خلفية بيضاء ────
        body = ctk.CTkFrame(root, fg_color=LOGIN_LIGHT_BODY, corner_radius=0)
        body.pack(fill="both", expand=True, padx=28, pady=(6, 14))

        self.error_lbl = ctk.CTkLabel(
            body,
            text="",
            text_color=COLORS["red"],
            font=_ui_font(12),
            fg_color="transparent",
            corner_radius=6,
        )
        self.error_lbl.pack(fill="x", pady=(0, 8))

        make_label(body, "اسم المستخدم", 12, "#4a5568").pack(anchor="w")
        self.user_entry = ctk.CTkEntry(
            body,
            placeholder_text="أدخل اسم المستخدم",
            width=340,
            height=40,
            font=_ui_font(13),
            justify="left",
            fg_color=LOGIN_LIGHT_ENTRY_BG,
            border_color=LOGIN_LIGHT_ENTRY_BORDER,
            text_color=LOGIN_LIGHT_ENTRY_TEXT,
            placeholder_text_color=LOGIN_LIGHT_ENTRY_PH,
            corner_radius=10,
        )
        _enable_text_shortcuts(self.user_entry)
        self.user_entry.pack(pady=(4, 14))

        make_label(body, "كلمة المرور", 12, "#4a5568").pack(anchor="w")
        pass_row = ctk.CTkFrame(body, fg_color="transparent")
        pass_row.pack(fill="x", pady=(4, 16))
        self.pass_entry = ctk.CTkEntry(
            pass_row,
            placeholder_text="أدخل كلمة المرور",
            width=290,
            height=40,
            font=_ui_font(13),
            justify="left",
            show="●",
            fg_color=LOGIN_LIGHT_ENTRY_BG,
            border_color=LOGIN_LIGHT_ENTRY_BORDER,
            text_color=LOGIN_LIGHT_ENTRY_TEXT,
            placeholder_text_color=LOGIN_LIGHT_ENTRY_PH,
            corner_radius=10,
        )
        _enable_text_shortcuts(self.pass_entry)
        self.pass_entry.pack(side="right", fill="x", expand=True)
        self.show_pass_btn = ctk.CTkButton(
            pass_row,
            text="👁",
            width=42,
            height=40,
            command=self._toggle_password_visibility,
            font=_ui_font(14, "bold"),
            fg_color=COLORS["panel2"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text2"],
            corner_radius=10,
        )
        self.show_pass_btn.pack(side="right", padx=(0, 6))

        remember_row = ctk.CTkFrame(body, fg_color="transparent")
        remember_row.pack(fill="x", pady=(0, 8))
        remembered_flag = (self.db.get_setting("remember_last_username", "1") or "1").strip().lower()
        self.remember_var = tk.BooleanVar(value=remembered_flag in ("1", "true", "yes", "on"))
        self.remember_cb = ctk.CTkCheckBox(
            remember_row,
            text="حفظ تذكرني",
            variable=self.remember_var,
            onvalue=True,
            offvalue=False,
            font=_ui_font(12, "bold"),
            text_color="#4a5568",
            fg_color=COLORS["accent"],
            hover_color="#357abd",
            checkmark_color="#ffffff",
        )
        self.remember_cb.pack(side="right")
        self._show_password = False

        if self.remember_var.get():
            last_user = (self.db.get_setting("last_username", "") or "").strip()
            if last_user:
                self.user_entry.delete(0, "end")
                self.user_entry.insert(0, last_user)

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 4))
        ctk.CTkButton(
            btn_row,
            text="إنهاء",
            command=self._login_quit_app,
            width=100,
            height=48,
            font=_ui_font(12, "bold"),
            fg_color=COLORS["red"],
            hover_color="#c0392b",
            text_color="#FFFFFF",
            corner_radius=26,
        ).pack(side="right")
        ctk.CTkButton(
            btn_row,
            text="🔐  تسجيل الدخول",
            command=self._login,
            height=48,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_dark"],
            text_color="#000000",
            font=_ui_font(14, "bold"),
            corner_radius=26,
        ).pack(side="right", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            root,
            text=f"© 2026 {APP_COMPANY}  |  {APP_AUTHOR}",
            font=_ui_font(10),
            text_color=LOGIN_LIGHT_FOOTER,
        ).pack(pady=(0, 14))

        self.bind("<Return>", lambda e: self._login())
        self.user_entry.focus()

    def _toggle_password_visibility(self):
        self._show_password = not self._show_password
        self.pass_entry.configure(show="" if self._show_password else "●")
        self.show_pass_btn.configure(text="🙈" if self._show_password else "👁")

    def _login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not username or not password:
            self.error_lbl.configure(text="⚠  يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        user = self.db.conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()

        if not user or not self.db.verify_password(password, user["password"]):
            self.error_lbl.configure(text="❌  اسم المستخدم أو كلمة المرور غير صحيحة")
            self.db.log(username, "فشل دخول", f"محاولة دخول فاشلة", username)
            return

        if not user["active"]:
            self.error_lbl.configure(text="⛔  هذا الحساب موقوف. تواصل مع المسؤول.")
            return

        # فحص الحساب التجريبي
        if user["role"] == "trial" and user["max_logins"] is not None:
            if user["logins_used"] >= user["max_logins"]:
                msg = user["expire_msg"] or "انتهت صلاحية الحساب التجريبي.\nيرجى التواصل مع المسؤول."
                messagebox.showwarning("انتهاء الصلاحية", msg, parent=self)
                return
            self.db.conn.execute(
                "UPDATE users SET logins_used=logins_used+1 WHERE id=?", (user["id"],)
            )

        now = datetime.now().isoformat()
        self.db.conn.execute(
            "UPDATE users SET last_login=? WHERE id=?", (now, user["id"])
        )
        self.db.conn.commit()
        self.db.log(username, "تسجيل دخول",
                    f"تسجيل دخول ناجح - {user['name']}", username)

        # تذكر آخر اسم مستخدم حسب اختيار المستخدم.
        try:
            if self.remember_var.get():
                self.db.set_setting("remember_last_username", "1")
                self.db.set_setting("last_username", username)
            else:
                self.db.set_setting("remember_last_username", "0")
                self.db.set_setting("last_username", "")
        except Exception:
            pass

        self._exit_login_fullscreen()
        self.destroy()
        self.on_success(dict(user))


# ════════════════════════════════════════════════════════════
#  قاعدة كل صفحة فرعية
# ════════════════════════════════════════════════════════════
class BasePage(ctk.CTkFrame):
    def __init__(self, parent, db: Database, current_user: dict, app):
        super().__init__(parent, fg_color=COLORS["bg2"], corner_radius=0)
        self.db = db
        self.current_user = current_user
        self.app = app

    def refresh(self):
        pass

    def _page_header(self, title: str, subtitle: str = ""):
        hdr = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=10)
        hdr.pack(fill="x", padx=12, pady=(12, 6))
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(side="right", fill="y", padx=16, pady=12)
        try:
            sub_wrap = min(max(self.winfo_screenwidth() - 160, 320), 920)
        except Exception:
            sub_wrap = 720
        ctk.CTkLabel(inner, text=title,
                     font=("Arial", 18, "bold"),
                     text_color=COLORS["gold_light"]).pack(anchor="e", pady=(0, 4))
        if subtitle:
            ctk.CTkLabel(
                inner,
                text=subtitle,
                font=("Arial", 11),
                text_color=COLORS["text3"],
                wraplength=sub_wrap,
                justify="right",
            ).pack(anchor="e")
        return hdr

    def _stat_card(self, parent, icon, value, label, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["panel"],
                            corner_radius=10,
                            border_width=1,
                            border_color=COLORS["border"])
        card.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(card, text=icon,
                     font=("Arial", 26)).pack(pady=(14, 4))
        ctk.CTkLabel(card, text=str(value),
                     font=("Arial", 24, "bold"),
                     text_color=color).pack()
        ctk.CTkLabel(card, text=label,
                     font=("Arial", 11),
                     text_color=COLORS["text3"]).pack(pady=(0, 12))
        return card

    def _confirm_delete(self, msg, callback):
        if messagebox.askyesno("تأكيد الحذف", f"⚠  {msg}\n\nهل أنت متأكد؟", parent=self):
            callback()

    def has_perm(self, perm_key: str) -> bool:
        """التحقق من صلاحية المستخدم الحالي."""
        try:
            role = (self.current_user or {}).get("role", "")
            # الأدوار المميزة (صلاحيات كاملة)
            if role in ("admin", "dev_master", "superfiser"):
                return True
            perms = self.current_user.get("permissions") if self.current_user else None
            if isinstance(perms, str):
                perms = json.loads(perms or "[]")
            if not isinstance(perms, list):
                perms = []
            return perm_key in perms
        except Exception:
            return False

    def require_perm(self, perm_key: str, msg: str = "ليس لديك صلاحية لتنفيذ هذا الإجراء."):
        """اعرض رسالة ومنع الإجراء إن لم تتوفر الصلاحية."""
        if self.has_perm(perm_key):
            return True
        messagebox.showwarning("صلاحيات", msg, parent=self)
        return False

    def _open_print_preview(self, title: str, columns, rows, note: str = ""):
        """إنشاء معاينة طباعة A4 وفتحها في المتصفح."""
        safe_title = html.escape(title)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        col_html = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
        body_rows = []
        for row in rows:
            cells = "".join(f"<td>{html.escape(str(v if v is not None else '-'))}</td>" for v in row)
            body_rows.append(f"<tr>{cells}</tr>")
        rows_html = "\n".join(body_rows) if body_rows else f"<tr><td colspan='{max(1, len(columns))}'>لا توجد بيانات للطباعة</td></tr>"
        note_html = f"<div class='note'>{html.escape(note)}</div>" if note else ""
        doc = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>{safe_title}</title>
  <style>
    @page {{ size: A4; margin: 12mm; }}
    * {{ box-sizing: border-box; }}
    html, body {{ direction: rtl; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; color: #111; text-align: right; }}
    .head {{ margin-bottom: 12px; }}
    .title {{ font-size: 22px; font-weight: 700; }}
    .meta {{ color: #555; font-size: 12px; margin-top: 4px; }}
    .note {{ margin: 10px 0 14px; padding: 8px 10px; background: #f7f7f7; border-right: 4px solid #999; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; direction: rtl; }}
    th, td {{ border: 1px solid #999; padding: 7px 6px; text-align: right; vertical-align: top; }}
    th {{ background: #efefef; font-weight: 700; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    .foot {{ margin-top: 10px; font-size: 12px; color: #444; }}
  </style>
</head>
<body>
  <div class="head">
    <div class="title">{safe_title}</div>
    <div class="meta">{html.escape(APP_NAME)} | تاريخ الطباعة: {html.escape(now)}</div>
  </div>
  {note_html}
  <table>
    <thead><tr>{col_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="foot">عدد السجلات: {len(rows)}</div>
  <script>window.onload = () => window.print();</script>
</body>
</html>"""
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
                tmp.write(doc)
                out_path = tmp.name
            webbrowser.open(Path(out_path).as_uri())
        except Exception as ex:
            messagebox.showerror("خطأ", f"تعذر فتح معاينة الطباعة:\n{ex}", parent=self)

    def _print_treeview(self, tree, title: str, note: str = ""):
        columns = [tree.heading(col).get("text", col) for col in tree["columns"]]
        rows = []
        for item_id in tree.get_children():
            values = tree.item(item_id, "values")
            rows.append(values if isinstance(values, (list, tuple)) else [values])
        # لضمان أن أول عمود يظهر يميناً في الطباعة العربية
        columns = list(reversed(columns))
        rows = [list(reversed(list(r))) for r in rows]
        self._open_print_preview(title, columns, rows, note=note)


# ════════════════════════════════════════════════════════════
#  صفحة الرئيسية
# ════════════════════════════════════════════════════════════
class DashboardPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._stat_labels = {}
        self._build()

    def _build(self):
        self._page_header("🏠  لوحة التحكم", f"مرحباً {self.current_user['name']}")

        # ─── الإحصائيات ────
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=6)

        # استعلام واحد لكل الإحصائيات بدل 6 استعلامات منفصلة
        stats = self.db.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM clients) as clients_c,
                (SELECT COUNT(*) FROM cases WHERE status='نشطة') as cases_c,
                (SELECT COUNT(*) FROM sessions WHERE session_date >= date('now')) as sess_c,
                (SELECT COALESCE(SUM(amount),0) FROM payments) as total_in,
                (SELECT COALESCE(SUM(amount),0) FROM expenses) as total_out,
                (SELECT COUNT(*) FROM tasks WHERE status='pending') as tasks_c
        """).fetchone()

        cards = [
            ("👥", stats[0],                 "إجمالي العملاء",     COLORS["gold"],   "clients"),
            ("📁", stats[1],                 "قضايا نشطة",         COLORS["accent"], "cases"),
            ("🗓", stats[2],                 "جلسات قادمة",        COLORS["purple"], "sessions"),
            ("💰", f"{stats[3]:,.0f}",       "إجمالي الإيرادات",   COLORS["green"],  "income"),
            ("📤", f"{stats[4]:,.0f}",       "إجمالي المصروفات",   COLORS["red"],    "expenses"),
            ("✅", stats[5],                 "مهام معلقة",         COLORS["orange"], "tasks"),
        ]
        self._stat_labels = {}
        for icon, value, label, color, key in cards:
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["panel"],
                                corner_radius=10, border_width=1,
                                border_color=COLORS["border"])
            card.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(card, text=icon, font=("Arial", 26)).pack(pady=(14, 4))
            val_lbl = ctk.CTkLabel(card, text=str(value),
                                   font=("Arial", 24, "bold"), text_color=color)
            val_lbl.pack()
            self._stat_labels[key] = val_lbl
            ctk.CTkLabel(card, text=label, font=("Arial", 11),
                         text_color=COLORS["text3"]).pack(pady=(0, 12))

        # ─── جلسات قادمة (تأخذ كل العرض) ────
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        left = ctk.CTkFrame(mid, fg_color=COLORS["panel"],
                            corner_radius=10, border_width=1,
                            border_color=COLORS["border"])
        left.pack(fill="both", expand=True)
        ctk.CTkLabel(left, text="🗓  الجلسات القادمة",
                     font=("Arial", 14, "bold"),
                     text_color=COLORS["gold_light"]).pack(anchor="w", padx=14, pady=10)

        cols = ("القضية", "التاريخ", "المحكمة", "القاعة")
        widths = (340, 130, 220, 100)
        self._sess_tree, _ = styled_treeview(left, cols, cols, widths)
        self._load_sessions()

    def _load_sessions(self):
        self._sess_tree.delete(*self._sess_tree.get_children())
        rows = self.db.conn.execute("""
            SELECT c.case_num, c.subject, s.session_date, s.court, s.room
            FROM sessions s JOIN cases c ON c.id = s.case_id
            WHERE s.session_date >= date('now')
            ORDER BY s.session_date LIMIT 10
        """).fetchall()
        for i, r in enumerate(rows):
            self._sess_tree.insert("", "end",
                values=(f"{r[0]} - {r[1][:30]}", r[2], r[3], r[4]),
                tags=("odd" if i % 2 == 0 else "even",))

    def _load_logs(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        logs = self.db.conn.execute(
            "SELECT username, detail, created_at FROM logs ORDER BY id DESC LIMIT 20"
        ).fetchall()
        for l in logs:
            dt = l[2][:16] if l[2] else ""
            self._log_box.insert("end", f"[{dt}] {l[0]}  ›  {l[1]}\n")
        self._log_box.configure(state="disabled")

    def refresh(self):
        """تحديث الأرقام فقط بدون إعادة بناء الواجهة"""
        if not self._stat_labels:
            return
        stats = self.db.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM clients),
                (SELECT COUNT(*) FROM cases WHERE status='نشطة'),
                (SELECT COUNT(*) FROM sessions WHERE session_date >= date('now')),
                (SELECT COALESCE(SUM(amount),0) FROM payments),
                (SELECT COALESCE(SUM(amount),0) FROM expenses),
                (SELECT COUNT(*) FROM tasks WHERE status='pending')
        """).fetchone()
        keys = ["clients","cases","sessions","income","expenses","tasks"]
        for i, key in enumerate(keys):
            if key in self._stat_labels:
                val = f"{stats[i]:,.0f}" if key in ("income","expenses") else str(stats[i])
                self._stat_labels[key].configure(text=val)
        self._load_sessions()

    def _load_logs(self):
        pass  # مخفي - غير مستخدم


# ════════════════════════════════════════════════════════════
#  صفحة العملاء
# ════════════════════════════════════════════════════════════
class ClientsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("👥  العملاء", "إدارة بيانات العملاء والموكلين")
        self._btn_add = make_button(hdr, "➕  إضافة عميل", self._open_add,
                                    color="gold", width=160)
        self._btn_add.pack(side="right", padx=14, pady=14)

        # شريط البحث
        bar = ctk.CTkFrame(self, fg_color=COLORS["panel"],
                           corner_radius=8, height=48)
        bar.pack(fill="x", padx=12, pady=(0, 6))
        bar.pack_propagate(False)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_data())
        e = ctk.CTkEntry(bar, textvariable=self.search_var,
                         placeholder_text="🔍  بحث...",
                         width=280,
                         fg_color=COLORS["bg3"],
                         border_color=COLORS["border"],
                         text_color=COLORS["text"])
        e.pack(side="right", padx=10, pady=8)
        _enable_text_shortcuts(e)

        # الجدول
        cols = ("#", "الاسم", "النوع", "الجوال", "البريد", "العنوان", "القضايا", "المدفوعات", "الحالة")
        widths = (40, 200, 80, 120, 180, 180, 70, 100, 70)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.pack_configure(padx=12, pady=(0, 4))
        self.tree.bind("<Double-1>", self._on_double_click)

        # أزرار الإجراءات
        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_edit = make_button(btn_bar, "✏️  تعديل",  self._open_edit,   "accent", 130)
        self._btn_edit.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف",   self._delete,      "red",   120)
        self._btn_del.pack(side="right", padx=4)
        make_button(btn_bar, "🖨️  طباعة", self._print_report, "ghost", 120).pack(side="left", padx=4)
        make_button(btn_bar, "📊  تصدير",  self._export_csv,  "ghost", 120).pack(side="left",  padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("clients_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("clients_edit"):
            self._btn_edit.configure(state="disabled")
        if not self.has_perm("clients_delete"):
            self._btn_del.configure(state="disabled")

        self._load_data()

    def _load_data(self, *_):
        self.tree.delete(*self.tree.get_children())
        q = f"%{self.search_var.get()}%"
        rows = self.db.conn.execute("""
            SELECT c.id, c.name, c.type, c.phone, c.email, c.address, c.active,
                   (SELECT COUNT(*) FROM cases WHERE client_id=c.id),
                   (SELECT COALESCE(SUM(amount),0) FROM payments WHERE client_id=c.id)
            FROM clients c
            WHERE c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?
            ORDER BY c.id DESC
        """, (q, q, q)).fetchall()

        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            status = "نشط" if r[6] else "موقوف"
            self.tree.insert("", "end",
                             iid=str(r[0]),
                             values=(i+1, r[1], r[2], r[3], r[4] or "-",
                                     r[5] or "-", r[7], f"{r[8]:,.0f}", status),
                             tags=(tag,))

    def _open_add(self):
        if not self.require_perm("clients_add", "ليس لديك صلاحية إضافة عملاء."):
            return
        ClientDialog(self, self.db, None, self.current_user, self._load_data)

    def _open_edit(self):
        if not self.require_perm("clients_edit", "ليس لديك صلاحية تعديل العملاء."):
            return
        sel = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else "")
        if not sel:
            messagebox.showinfo("تنبيه", "اختر عميلاً أولاً", parent=self)
            return
        ClientDialog(self, self.db, int(sel), self.current_user, self._load_data)

    def _on_double_click(self, _):
        self._open_edit()

    def _delete(self):
        if not self.require_perm("clients_delete", "ليس لديك صلاحية حذف العملاء."):
            return
        sel = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else "")
        if not sel:
            messagebox.showinfo("تنبيه", "اختر عميلاً أولاً", parent=self)
            return
        row = self.db.conn.execute("SELECT name FROM clients WHERE id=?", (sel,)).fetchone()
        self._confirm_delete(f"حذف العميل: {row['name']}",
                             lambda: self._do_delete(int(sel)))

    def _do_delete(self, cid):
        # حذف كل ما يرتبط بالعميل أولاً لتفادي فشل قيود foreign keys
        doc_ids = [
            r[0]
            for r in self.db.conn.execute(
                "SELECT id FROM documents WHERE client_id=? OR case_id IN (SELECT id FROM cases WHERE client_id=?)",
                (cid, cid),
            ).fetchall()
        ]
        self.db.delete_document_files_for_ids(doc_ids)
        self.db.conn.execute(
            "DELETE FROM tasks WHERE related IN (SELECT case_num FROM cases WHERE client_id=?)",
            (cid,),
        )
        self.db.conn.execute("DELETE FROM sessions WHERE case_id IN (SELECT id FROM cases WHERE client_id=?)", (cid,))
        self.db.conn.execute("DELETE FROM payments WHERE client_id=? OR case_id IN (SELECT id FROM cases WHERE client_id=?)", (cid, cid))
        self.db.conn.execute("DELETE FROM contracts WHERE client_id=? OR case_id IN (SELECT id FROM cases WHERE client_id=?)", (cid, cid))
        self.db.conn.execute("DELETE FROM documents WHERE client_id=? OR case_id IN (SELECT id FROM cases WHERE client_id=?)", (cid, cid))
        self.db.conn.execute("DELETE FROM expenses WHERE case_id IN (SELECT id FROM cases WHERE client_id=?)", (cid,))
        self.db.conn.execute("DELETE FROM cases WHERE client_id=?", (cid,))
        self.db.conn.execute("DELETE FROM clients WHERE id=?", (cid,))
        self.db.conn.commit()
        self.db.log(self.current_user["username"], "عميل",
                    f"حذف عميل id={cid}", self.current_user["username"])
        self._load_data()
        show_toast(self.app, "تم حذف العميل ✓", "red")
        try:
            self.app.refresh_all_open_pages()
        except Exception:
            pass

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="حفظ ملف CSV"
        )
        if not path:
            return
        rows = self.db.conn.execute("SELECT * FROM clients").fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([d[0] for d in rows[0].description] if rows else [])
            w.writerows(rows)
        show_toast(self.app, "تم التصدير بنجاح ✓", "gold")

    def _print_report(self):
        self._print_treeview(self.tree, "تقرير العملاء", note="تقرير تفصيلي للعملاء الحاليين")

    def refresh(self):
        self._load_data()


class ClientDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, client_id, user, callback):
        super().__init__(parent)
        self.db = db
        self.client_id = client_id
        self.user = user
        self.callback = callback
        self.title("إضافة عميل" if not client_id else "تعديل عميل")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 560, 600)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if client_id:
            self._load_existing()

    def _build(self):
        ctk.CTkLabel(self, text="بيانات العميل",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)

        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"],
                                    corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        sc.grid_columnconfigure((0, 1), weight=1)

        fields = [
            ("الاسم الكامل *",    "name",    0, 0, 2, ""),
            ("نوع العميل",         "type",    1, 0, 1, ["فرد", "شركة", "مؤسسة"]),
            ("رقم الهوية/السجل",  "id_num",  1, 1, 1, ""),
            ("رقم الجوال *",       "phone",   2, 0, 1, ""),
            ("هاتف إضافي",         "phone2",  2, 1, 1, ""),
            ("البريد الإلكتروني",  "email",   3, 0, 1, ""),
            ("المهنة / الجنسية",   "job",     3, 1, 1, ""),
            ("العنوان",            "address", 4, 0, 2, ""),
            ("ملاحظات",            "notes",   5, 0, 2, "text"),
        ]
        self.widgets = {}
        for label, key, row, col, span, extra in fields:
            ctk.CTkLabel(sc, text=label, font=("Arial", 12),
                         text_color=COLORS["text2"]).grid(
                row=row*2, column=col, columnspan=span,
                sticky="w", padx=8, pady=(8, 2))
            if extra == "text":
                w = make_textbox(sc, height=70, width=490)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            elif isinstance(extra, list):
                w = make_combo(sc, extra, width=225)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            else:
                w = make_entry(sc, width=225 if span == 1 else 490)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            self.widgets[key] = w

        # الأزرار
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _get(self, key):
        w = self.widgets[key]
        if isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def _set(self, key, val):
        w = self.widgets[key]
        if isinstance(w, ctk.CTkTextbox):
            w.delete("1.0", "end")
            w.insert("1.0", val or "")
        elif isinstance(w, ctk.CTkComboBox):
            w.set(val or "")
        else:
            w.delete(0, "end")
            w.insert(0, val or "")

    def _load_existing(self):
        r = self.db.conn.execute(
            "SELECT * FROM clients WHERE id=?", (self.client_id,)
        ).fetchone()
        if r:
            for k in self.widgets:
                self._set(k, r[k] if k in r.keys() else "")

    def _save(self):
        name  = self._get("name")
        phone = self._get("phone")
        if not name or not phone:
            messagebox.showerror("خطأ", "الاسم والجوال مطلوبان", parent=self)
            return

        data = {k: self._get(k) for k in self.widgets}
        if self.client_id:
            sets = ", ".join(f"{k}=?" for k in data)
            self.db.conn.execute(
                f"UPDATE clients SET {sets} WHERE id=?",
                list(data.values()) + [self.client_id]
            )
            action = f"تعديل عميل: {name}"
        else:
            cols = ", ".join(data.keys())
            phs  = ", ".join("?" for _ in data)
            self.db.conn.execute(
                f"INSERT INTO clients ({cols}) VALUES ({phs})",
                list(data.values())
            )
            action = f"إضافة عميل جديد: {name}"

        self.db.conn.commit()
        self.db.log(self.user["username"], "عميل", action, self.user["username"])
        show_toast(self.master, f"تم الحفظ: {name} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة القضايا
# ════════════════════════════════════════════════════════════
class CasesPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self.filter_status = "الكل"
        self._build()

    def _build(self):
        hdr = self._page_header("📁  القضايا", "إدارة وتتبع القضايا القانونية")
        self._btn_add = make_button(hdr, "➕  إضافة قضية", self._open_add,
                                    color="gold", width=160)
        self._btn_add.pack(side="right", padx=14, pady=14)

        # فلاتر الحالة
        flt = ctk.CTkFrame(self, fg_color=COLORS["panel"],
                           corner_radius=8, height=44)
        flt.pack(fill="x", padx=12, pady=(0, 6))
        flt.pack_propagate(False)
        for status in ["الكل", "نشطة", "معلقة", "منتهية", "مؤرشفة"]:
            ctk.CTkButton(flt, text=status, width=90, height=30,
                          font=("Arial", 12, "bold"),
                          fg_color=COLORS["gold"] if status == self.filter_status else COLORS["bg3"],
                          hover_color=COLORS["gold_dark"],
                          text_color="#000" if status == self.filter_status else COLORS["text2"],
                          corner_radius=6,
                          command=lambda s=status: self._filter(s)).pack(side="right", padx=4, pady=6)

        # الجدول
        cols = ("#", "رقم القضية", "الموضوع", "العميل", "النوع", "المحكمة", "القاضي", "الحالة", "التاريخ", "الأتعاب")
        widths = (40, 110, 200, 160, 90, 180, 150, 80, 100, 90)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.bind("<Double-1>", lambda _: self._open_edit())

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_edit = make_button(btn_bar, "✏️  تعديل", self._open_edit, "accent", 130)
        self._btn_edit.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف",  self._delete,    "red",   120)
        self._btn_del.pack(side="right", padx=4)
        self._btn_add_session = make_button(btn_bar, "➕  جلسة", self._add_session, "ghost", 140)
        self._btn_add_session.pack(side="left", padx=4)
        make_button(btn_bar, "🖨️  طباعة", self._print_report, "ghost", 120).pack(side="left", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("cases_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("cases_edit"):
            self._btn_edit.configure(state="disabled")
        if not self.has_perm("cases_delete"):
            self._btn_del.configure(state="disabled")
        if not self.has_perm("sessions_add"):
            self._btn_add_session.configure(state="disabled")

        self._load_data()

    def _filter(self, status):
        self.filter_status = status
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _load_data(self):
        self.tree.delete(*self.tree.get_children())
        where = "" if self.filter_status == "الكل" else f"WHERE ca.status='{self.filter_status}'"
        rows = self.db.conn.execute(f"""
            SELECT ca.id, ca.case_num, ca.subject, cl.name,
                   ca.type, ca.court, ca.judge, ca.status,
                   ca.case_date, ca.fees
            FROM cases ca
            LEFT JOIN clients cl ON cl.id = ca.client_id
            {where}
            ORDER BY ca.id DESC
        """).fetchall()

        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            status_color = {"نشطة": "active", "منتهية": "inactive",
                            "معلقة": "urgent"}.get(r[7], tag)
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1], r[2][:35], r[3] or "-",
                                     r[4], r[5], r[6] or "-", r[7],
                                     r[8] or "-", f"{r[9]:,.0f}"),
                             tags=(status_color,))

    def _open_add(self):
        if not self.require_perm("cases_add", "ليس لديك صلاحية إضافة قضايا."):
            return
        CaseDialog(self, self.db, None, self.current_user, self._load_data)

    def _open_edit(self):
        if not self.require_perm("cases_edit", "ليس لديك صلاحية تعديل القضايا."):
            return
        sel = self.tree.selection()[0] if self.tree.selection() else self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر قضية أولاً", parent=self); return
        CaseDialog(self, self.db, int(sel), self.current_user, self._load_data)

    def _delete(self):
        if not self.require_perm("cases_delete", "ليس لديك صلاحية حذف القضايا."):
            return
        sel = self.tree.selection()[0] if self.tree.selection() else self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر قضية أولاً", parent=self); return
        r = self.db.conn.execute("SELECT case_num FROM cases WHERE id=?", (sel,)).fetchone()
        if not r:
            self._load_data()
            messagebox.showinfo(
                "تنبيه",
                "لا توجد هذه القضية في القاعدة (ربما حُذفت مع عميل). تم تحديث القائمة.",
                parent=self,
            )
            return
        self._confirm_delete(f"حذف القضية: {r[0]}",
                             lambda: self._do_delete(int(sel)))

    def _do_delete(self, cid):
        self.db.conn.execute(
            "DELETE FROM tasks WHERE related=(SELECT case_num FROM cases WHERE id=?)",
            (cid,),
        )
        self.db.conn.execute("DELETE FROM sessions WHERE case_id=?", (cid,))
        self.db.conn.execute("DELETE FROM payments WHERE case_id=?", (cid,))
        self.db.conn.execute("DELETE FROM contracts WHERE case_id=?", (cid,))
        doc_ids = [r[0] for r in self.db.conn.execute("SELECT id FROM documents WHERE case_id=?", (cid,)).fetchall()]
        self.db.delete_document_files_for_ids(doc_ids)
        self.db.conn.execute("DELETE FROM documents WHERE case_id=?", (cid,))
        self.db.conn.execute("DELETE FROM expenses WHERE case_id=?", (cid,))
        self.db.conn.execute("DELETE FROM cases WHERE id=?", (cid,))
        self.db.conn.commit()
        self.db.log(self.current_user["username"], "قضية", f"حذف قضية id={cid}",
                    self.current_user["username"])
        self._load_data()
        show_toast(self.app, "تم حذف القضية ✓", "red")

    def _add_session(self):
        if not self.require_perm("sessions_add", "ليس لديك صلاحية إضافة جلسات."):
            return
        sel = self.tree.focus()
        case_id = int(sel) if sel else None
        SessionDialog(self, self.db, case_id, self.current_user, lambda: None)

    def refresh(self):
        self._load_data()

    def _print_report(self):
        self._print_treeview(self.tree, "تقرير القضايا", note=f"حالة الفلترة الحالية: {self.filter_status}")


class CaseDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, case_id, user, callback):
        super().__init__(parent)
        self.db = db
        self.case_id = case_id
        self.user = user
        self.callback = callback
        self.title("إضافة قضية" if not case_id else "تعديل قضية")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 640, 680)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if case_id:
            self._load_existing()

    def _build(self):
        ctk.CTkLabel(self, text="بيانات القضية",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)

        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        sc.grid_columnconfigure((0, 1), weight=1)

        clients = self.db.conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
        client_names = [f"{r[0]} - {r[1]}" for r in clients]
        self.client_map = {f"{r[0]} - {r[1]}": r[0] for r in clients}

        fields = [
            ("رقم القضية *",       "case_num",   0, 0, 1, ""),
            ("العميل *",           "client_sel", 0, 1, 1, client_names),
            ("موضوع القضية *",     "subject",    1, 0, 2, ""),
            ("نوع القضية",         "type",       2, 0, 1,
             ["مدنية","جنائية","تجارية","عمالية","أحوال شخصية","إدارية","عقارية","دولية"]),
            ("الحالة",             "status",     2, 1, 1,
             ["نشطة","معلقة","منتهية","مؤرشفة"]),
            ("المحكمة",            "court",      3, 0, 1, ""),
            ("الدائرة / الشعبة",   "dept",       3, 1, 1, ""),
            ("اسم القاضي",         "judge",      4, 0, 1, ""),
            ("تاريخ الرفع",        "case_date",  4, 1, 1, ""),
            ("أتعاب المحاماة",      "fees",       5, 0, 1, ""),
            ("الطرف الآخر",        "opponent",   5, 1, 1, ""),
            ("وصف القضية",         "description",6, 0, 2, "text"),
        ]
        self.widgets = {}
        for label, key, row, col, span, extra in fields:
            ctk.CTkLabel(sc, text=label, font=("Arial", 12),
                         text_color=COLORS["text2"]).grid(
                row=row*2, column=col, columnspan=span,
                sticky="w", padx=8, pady=(8, 2))
            if extra == "text":
                w = make_textbox(sc, height=80, width=580)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            elif isinstance(extra, list):
                w = make_combo(sc, extra, width=280)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            else:
                w = make_entry(sc, width=280)
                w.grid(row=row*2+1, column=col, columnspan=span,
                       sticky="ew", padx=8, pady=(0, 4))
            self.widgets[key] = w

        if not client_names:
            ctk.CTkLabel(sc, text="⚠ أضف عملاء أولاً",
                         text_color=COLORS["red"],
                         font=("Arial", 12)).grid(row=1, column=1, sticky="w", padx=8)

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _get(self, key):
        w = self.widgets[key]
        if isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def _set(self, key, val):
        w = self.widgets[key]
        if isinstance(w, ctk.CTkTextbox):
            w.delete("1.0", "end"); w.insert("1.0", val or "")
        elif isinstance(w, ctk.CTkComboBox):
            w.set(val or "")
        else:
            w.delete(0, "end"); w.insert(0, val or "")

    def _load_existing(self):
        r = self.db.conn.execute("""
            SELECT ca.*, cl.id||' - '||cl.name as client_sel
            FROM cases ca LEFT JOIN clients cl ON cl.id=ca.client_id
            WHERE ca.id=?
        """, (self.case_id,)).fetchone()
        if r:
            d = dict(r)
            for k in self.widgets:
                self._set(k, d.get(k, ""))

    def _save(self):
        case_num = self._get("case_num")
        subject  = self._get("subject")
        cl_sel   = self._get("client_sel")
        if not case_num or not subject:
            messagebox.showerror("خطأ", "رقم القضية والموضوع مطلوبان", parent=self)
            return
        client_id = self.client_map.get(cl_sel)

        data = {
            "case_num":    case_num,
            "client_id":   client_id,
            "subject":     subject,
            "type":        self._get("type"),
            "status":      self._get("status"),
            "court":       self._get("court"),
            "dept":        self._get("dept"),
            "judge":       self._get("judge"),
            "case_date":   self._get("case_date"),
            "fees":        float(self._get("fees") or 0),
            "opponent":    self._get("opponent"),
            "description": self._get("description"),
        }
        if self.case_id:
            sets = ", ".join(f"{k}=?" for k in data)
            self.db.conn.execute(
                f"UPDATE cases SET {sets} WHERE id=?",
                list(data.values()) + [self.case_id]
            )
            action = f"تعديل قضية: {case_num}"
        else:
            cols = ", ".join(data.keys())
            phs  = ", ".join("?" for _ in data)
            self.db.conn.execute(
                f"INSERT INTO cases ({cols}) VALUES ({phs})",
                list(data.values())
            )
            action = f"إضافة قضية: {case_num}"

        self.db.conn.commit()
        self.db.log(self.user["username"], "قضية", action, self.user["username"])
        show_toast(self.master, f"تم الحفظ: {case_num} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة الجلسات
# ════════════════════════════════════════════════════════════
class SessionsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("🗓  الجلسات", "جدول الجلسات والمواعيد القضائية")
        self._btn_add = make_button(hdr, "➕  إضافة جلسة", self._open_add,
                                    color="gold", width=160)
        self._btn_add.pack(side="right", padx=14, pady=14)

        cols = ("#", "القضية", "التاريخ", "الوقت", "المحكمة", "القاعة", "النتيجة", "الجلسة القادمة", "ملاحظات")
        widths = (40, 230, 110, 70, 160, 70, 160, 120, 160)
        self.tree, _ = styled_treeview(self, cols, cols, widths)

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_del = make_button(btn_bar, "🗑️  حذف", self._delete, "red", 120)
        self._btn_del.pack(side="right", padx=4)
        make_button(btn_bar, "🖨️  طباعة", self._print_report, "ghost", 120).pack(side="left", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("sessions_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("sessions_delete"):
            self._btn_del.configure(state="disabled")

        self._load_data()

    def _load_data(self):
        self.tree.delete(*self.tree.get_children())
        rows = self.db.conn.execute("""
            SELECT s.id, c.case_num||' - '||c.subject,
                   s.session_date, s.session_time, s.court, s.room,
                   s.result, s.next_date, s.notes
            FROM sessions s
            JOIN cases c ON c.id=s.case_id
            ORDER BY s.session_date DESC
        """).fetchall()

        today = date.today().isoformat()
        for i, r in enumerate(rows):
            tag = "active" if r[2] >= today else "inactive"
            if i % 2 == 0 and tag == "inactive":
                tag = "even"
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1][:40], r[2], r[3] or "-",
                                     r[4] or "-", r[5] or "-",
                                     r[6] or "-", r[7] or "-", r[8] or "-"),
                             tags=(tag,))

    def _open_add(self):
        if not self.require_perm("sessions_add", "ليس لديك صلاحية إضافة جلسات."):
            return
        SessionDialog(self, self.db, None, self.current_user, self._load_data)

    def _delete(self):
        if not self.require_perm("sessions_delete", "ليس لديك صلاحية حذف الجلسات."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر جلسة أولاً", parent=self); return
        self._confirm_delete("حذف هذه الجلسة؟",
                             lambda: self._do_delete(int(sel)))

    def _do_delete(self, sid):
        self.db.conn.execute("DELETE FROM sessions WHERE id=?", (sid,))
        self.db.conn.commit()
        self._load_data()
        show_toast(self.app, "تم حذف الجلسة ✓", "red")

    def refresh(self):
        self._load_data()

    def _print_report(self):
        self._print_treeview(self.tree, "تقرير الجلسات", note="يشمل جميع الجلسات المعروضة في الجدول")


class SessionDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, case_id_default, user, callback):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.callback = callback
        self.title("إضافة جلسة")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 520, 520)
        self.resizable(False, False)
        self.grab_set()
        self._build(case_id_default)

    def _build(self, case_id_default):
        ctk.CTkLabel(self, text="بيانات الجلسة",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)

        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        cases = self.db.conn.execute("SELECT id, case_num, subject FROM cases ORDER BY id DESC").fetchall()
        case_options = [f"{r[0]} - {r[1]} | {r[2][:30]}" for r in cases]
        self.case_map = {f"{r[0]} - {r[1]} | {r[2][:30]}": r[0] for r in cases}

        def lbl(t): ctk.CTkLabel(sc, text=t, font=("Arial", 12),
                                  text_color=COLORS["text2"]).pack(anchor="w", padx=4, pady=(8,2))
        def ent(ph=""): e=make_entry(sc, ph, width=460); e.pack(padx=4, pady=(0,4)); return e

        lbl("القضية *")
        self.w_case = make_combo(sc, case_options, width=460)
        self.w_case.pack(padx=4, pady=(0, 4))
        if case_id_default:
            match = next((k for k, v in self.case_map.items() if v == case_id_default), None)
            if match:
                self.w_case.set(match)

        lbl("تاريخ الجلسة * (YYYY-MM-DD)")
        self.w_date = ent()
        self.w_date.insert(0, date.today().isoformat())

        lbl("وقت الجلسة (HH:MM)")
        self.w_time = ent("مثال: 09:00")

        lbl("المحكمة")
        self.w_court = ent()

        lbl("رقم القاعة")
        self.w_room = ent()

        lbl("نتيجة الجلسة")
        self.w_result = ent()

        lbl("موعد الجلسة القادمة")
        self.w_next = ent()

        lbl("ملاحظات")
        self.w_notes = make_textbox(sc, height=60, width=460)
        self.w_notes.pack(padx=4, pady=(0, 4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _save(self):
        case_sel  = self.w_case.get()
        sess_date = self.w_date.get().strip()
        if not case_sel or not sess_date:
            messagebox.showerror("خطأ", "القضية والتاريخ مطلوبان", parent=self); return

        case_id = self.case_map.get(case_sel)
        self.db.conn.execute("""
            INSERT INTO sessions (case_id, session_date, session_time, court, room, result, next_date, notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (case_id, sess_date,
              self.w_time.get().strip(),
              self.w_court.get().strip(),
              self.w_room.get().strip(),
              self.w_result.get().strip(),
              self.w_next.get().strip(),
              self.w_notes.get("1.0", "end").strip()))
        self.db.conn.commit()
        self.db.log(self.user["username"], "قضية",
                    f"إضافة جلسة بتاريخ {sess_date}", self.user["username"])
        show_toast(self.master, "تم إضافة الجلسة ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة الشؤون المالية
# ════════════════════════════════════════════════════════════
class FinancePage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("💰  الشؤون المالية", "المدفوعات والمصروفات والملخص المالي")
        self._btn_add_pay = make_button(hdr, "➕  دفعة جديدة", self._open_pay,
                                        color="green", width=150)
        self._btn_add_pay.pack(side="right", padx=6, pady=14)
        self._btn_add_exp = make_button(hdr, "📤  مصروف", self._open_exp,
                                        color="red", width=130)
        self._btn_add_exp.pack(side="right", padx=2, pady=14)

        # إحصائيات
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=6)
        total_in  = self.db.conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0]
        total_out = self.db.conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        net = total_in - total_out
        self._stat_card(stats, "📥", f"{total_in:,.2f}", "إجمالي الإيرادات", COLORS["green"])
        self._stat_card(stats, "📤", f"{total_out:,.2f}", "إجمالي المصروفات", COLORS["red"])
        self._stat_card(stats, "💹", f"{net:,.2f}",
                        "صافي الربح", COLORS["gold"] if net >= 0 else COLORS["red"])
        self._stat_card(stats, "📊", self.db.conn.execute(
            "SELECT COUNT(*) FROM payments").fetchone()[0],
            "عدد المعاملات", COLORS["accent"])

        # تابز
        tab = ctk.CTkTabview(self, fg_color=COLORS["panel"],
                             segmented_button_fg_color=COLORS["bg3"],
                             segmented_button_selected_color=COLORS["gold"],
                             segmented_button_selected_hover_color=COLORS["gold_dark"],
                             segmented_button_unselected_color=COLORS["bg3"],
                             segmented_button_unselected_hover_color=COLORS["hover"],
                             text_color=COLORS["text"],
                             corner_radius=10)
        tab.pack(fill="both", expand=True, padx=12, pady=6)
        tab.add("المدفوعات")
        tab.add("المصروفات")

        # جدول المدفوعات
        p_cols = ("#", "التاريخ", "العميل", "القضية", "المبلغ", "طريقة الدفع", "المرجع", "المسجل", "ملاحظات")
        p_widths = (40, 110, 170, 130, 90, 110, 100, 100, 140)
        self.pay_tree, _ = styled_treeview(tab.tab("المدفوعات"), p_cols, p_cols, p_widths)

        pbtns = ctk.CTkFrame(tab.tab("المدفوعات"), fg_color="transparent", height=40)
        pbtns.pack(fill="x", padx=4, pady=(0, 4))
        pbtns.pack_propagate(False)
        self._btn_del_pay = make_button(pbtns, "🗑️  حذف", self._del_payment, "red", 120)
        self._btn_del_pay.pack(side="right", padx=4)
        make_button(pbtns, "🖨️  طباعة المدفوعات", self._print_payments, "ghost", 150).pack(side="left", padx=4)

        # جدول المصروفات
        e_cols = ("#", "التاريخ", "البند", "المبلغ", "الفئة", "المسجل", "ملاحظات")
        e_widths = (40, 110, 220, 90, 130, 100, 160)
        self.exp_tree, _ = styled_treeview(tab.tab("المصروفات"), e_cols, e_cols, e_widths)

        ebtns = ctk.CTkFrame(tab.tab("المصروفات"), fg_color="transparent", height=40)
        ebtns.pack(fill="x", padx=4, pady=(0, 4))
        ebtns.pack_propagate(False)
        self._btn_del_exp = make_button(ebtns, "🗑️  حذف", self._del_expense, "red", 120)
        self._btn_del_exp.pack(side="right", padx=4)
        make_button(ebtns, "🖨️  طباعة المصروفات", self._print_expenses, "ghost", 150).pack(side="left", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("finance_add"):
            self._btn_add_pay.configure(state="disabled")
            self._btn_add_exp.configure(state="disabled")
        if not self.has_perm("finance_delete"):
            self._btn_del_pay.configure(state="disabled")
            self._btn_del_exp.configure(state="disabled")

        self._load_payments()
        self._load_expenses()

    def _load_payments(self):
        self.pay_tree.delete(*self.pay_tree.get_children())
        rows = self.db.conn.execute("""
            SELECT p.id, p.pay_date, cl.name, c.case_num,
                   p.amount, p.method, p.reference, p.recorded_by, p.notes
            FROM payments p
            LEFT JOIN clients cl ON cl.id=p.client_id
            LEFT JOIN cases c ON c.id=p.case_id
            ORDER BY p.id DESC
        """).fetchall()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.pay_tree.insert("", "end", iid=str(r[0]),
                                 values=(i+1, r[1], r[2] or "-", r[3] or "-",
                                         f"{r[4]:,.2f}", r[5], r[6] or "-",
                                         r[7], r[8] or "-"),
                                 tags=(tag,))

    def _load_expenses(self):
        self.exp_tree.delete(*self.exp_tree.get_children())
        rows = self.db.conn.execute("""
            SELECT id, exp_date, item, amount, category, recorded_by, notes
            FROM expenses ORDER BY id DESC
        """).fetchall()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.exp_tree.insert("", "end", iid=str(r[0]),
                                 values=(i+1, r[1], r[2],
                                         f"{r[3]:,.2f}", r[4], r[5], r[6] or "-"),
                                 tags=(tag,))

    def _open_pay(self):
        if not self.require_perm("finance_add", "ليس لديك صلاحية تسجيل مدفوعات."):
            return
        PaymentDialog(self, self.db, self.current_user, self.refresh)

    def _open_exp(self):
        if not self.require_perm("finance_add", "ليس لديك صلاحية تسجيل مصروفات."):
            return
        ExpenseDialog(self, self.db, self.current_user, self.refresh)

    def _del_payment(self):
        if not self.require_perm("finance_delete", "ليس لديك صلاحية حذف المعاملات المالية."):
            return
        sel = self.pay_tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر دفعة أولاً", parent=self); return
        self._confirm_delete("حذف هذه الدفعة؟",
                             lambda: [self.db.conn.execute("DELETE FROM payments WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self.refresh()])

    def _del_expense(self):
        if not self.require_perm("finance_delete", "ليس لديك صلاحية حذف المعاملات المالية."):
            return
        sel = self.exp_tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مصروفاً أولاً", parent=self); return
        self._confirm_delete("حذف هذا المصروف؟",
                             lambda: [self.db.conn.execute("DELETE FROM expenses WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self.refresh()])

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _print_payments(self):
        self._print_treeview(self.pay_tree, "تقرير المدفوعات", note="تقرير حركة الإيرادات")

    def _print_expenses(self):
        self._print_treeview(self.exp_tree, "تقرير المصروفات", note="تقرير حركة المصروفات")


class PaymentDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, user, callback):
        super().__init__(parent)
        self.db = db; self.user = user; self.callback = callback
        self.title("تسجيل دفعة جديدة")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 520, 560)
        self.resizable(False, False)
        self.grab_set()
        self.cl_map = {}
        self.cs_map = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="💰  تسجيل دفعة",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        clients = self.db.conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
        cl_opts = [f"{r[0]} - {r[1]}" for r in clients]
        self.cl_map = {f"{r[0]} - {r[1]}": r[0] for r in clients}

        def lbl(t): ctk.CTkLabel(sc, text=t, font=("Arial", 12),
                                  text_color=COLORS["text2"]).pack(anchor="e", padx=4, pady=(8,2))
        lbl("العميل *")
        self.w_cl = make_combo(sc, cl_opts if cl_opts else ["— لا يوجد عملاء —"], width=450)
        self.w_cl.pack(padx=4, pady=(0,4))
        self.w_cl.configure(command=lambda _=None: self._on_client_change())

        lbl("القضية (اختياري — أتعاب هذه القضية فقط)")
        self.w_cs = make_combo(sc, ["-- بدون قضية --"], width=450)
        self.w_cs.pack(padx=4, pady=(0,4))
        self.w_cs.configure(command=lambda _=None: self._update_fees_hint())

        self.w_fees_info = ctk.CTkLabel(
            sc,
            text="—",
            font=("Arial", 11, "bold"),
            text_color=COLORS["gold_light"],
            anchor="e",
            justify="right",
            wraplength=430,
        )
        self.w_fees_info.pack(fill="x", padx=4, pady=(4, 8))

        lbl("المبلغ *")
        self.w_amount = make_entry(sc, "المبلغ", 450); self.w_amount.pack(padx=4, pady=(0,4))
        lbl("طريقة الدفع")
        self.w_method = make_combo(sc, ["نقداً","تحويل بنكي","شيك","بطاقة ائتمان","أخرى"], 450)
        self.w_method.pack(padx=4, pady=(0,4))
        lbl("التاريخ *")
        self.w_date = make_entry(sc, "YYYY-MM-DD", 450)
        self.w_date.insert(0, date.today().isoformat()); self.w_date.pack(padx=4, pady=(0,4))
        lbl("رقم الإيصال / المرجع")
        self.w_ref = make_entry(sc, "", 450); self.w_ref.pack(padx=4, pady=(0,4))
        lbl("ملاحظات")
        self.w_notes = make_textbox(sc, height=60, width=450); self.w_notes.pack(padx=4, pady=(0,4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  تسجيل", self._save, "green", 140).pack(side="right", padx=4)

        if cl_opts:
            self._on_client_change()

    def _on_client_change(self):
        """تحديث قائمة قضايا العميل فقط + ملخص الأتعاب."""
        cid = self.cl_map.get(self.w_cl.get())
        if not cid:
            self.w_cs.configure(values=["-- بدون قضية --"])
            self.w_cs.set("-- بدون قضية --")
            self.cs_map = {}
            self._update_fees_hint()
            return
        rows = self.db.conn.execute(
            "SELECT id, case_num FROM cases WHERE client_id=? ORDER BY id DESC",
            (cid,),
        ).fetchall()
        opts = ["-- بدون قضية --"] + [f"{r[0]} - {r[1]}" for r in rows]
        self.cs_map = {f"{r[0]} - {r[1]}": r[0] for r in rows}
        self.w_cs.configure(values=opts)
        self.w_cs.set(opts[0])
        self._update_fees_hint()

    def _fees_snapshot(self, client_id: int, case_id):
        """إرجاع (إجمالي الأتعاب المعتمدة، المدفوع سابقاً، المتبقي)."""
        if case_id:
            row = self.db.conn.execute(
                "SELECT COALESCE(fees,0) AS f FROM cases WHERE id=? AND client_id=?",
                (case_id, client_id),
            ).fetchone()
            total = float(row["f"]) if row else 0.0
            paid = float(
                self.db.conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM payments WHERE case_id=?",
                    (case_id,),
                ).fetchone()[0]
            )
        else:
            total = float(
                self.db.conn.execute(
                    "SELECT COALESCE(SUM(fees),0) FROM cases WHERE client_id=?",
                    (client_id,),
                ).fetchone()[0]
            )
            paid = float(
                self.db.conn.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM payments WHERE client_id=?",
                    (client_id,),
                ).fetchone()[0]
            )
        rem = max(0.0, total - paid)
        return total, paid, rem

    def _update_fees_hint(self):
        cid = self.cl_map.get(self.w_cl.get())
        if not cid:
            self.w_fees_info.configure(text="اختر العميل لعرض الأتعاب والمتبقي.")
            return
        sel = self.w_cs.get()
        case_id = self.cs_map.get(sel) if sel and sel != "-- بدون قضية --" else None
        total, paid, rem = self._fees_snapshot(cid, case_id)
        if case_id:
            scope = "لهذه القضية"
        else:
            scope = "لجميع قضايا العميل (مجموع الأتعاب)"
        if total <= 0:
            self.w_fees_info.configure(
                text=f"{scope}: لا توجد أتعاب مسجّلة في القضايا لهذا النطاق — لن يُفرض حد أقصى للدفعة."
            )
        else:
            self.w_fees_info.configure(
                text=(
                    f"{scope}\n"
                    f"إجمالي الأتعاب المطلوبة: {total:,.2f}  |  المدفوع سابقاً: {paid:,.2f}  |  "
                    f"المتبقي المسموح دفعه: {rem:,.2f}"
                )
            )

    def _save(self):
        cl = self.cl_map.get(self.w_cl.get())
        amount_str = self.w_amount.get().strip()
        pay_date   = self.w_date.get().strip()
        if not cl or not amount_str or not pay_date:
            messagebox.showerror("خطأ", "العميل والمبلغ والتاريخ مطلوبة", parent=self); return
        try: amount = float(amount_str)
        except Exception:
            messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً", parent=self); return
        if amount <= 0:
            messagebox.showerror("خطأ", "المبلغ يجب أن يكون أكبر من صفر", parent=self); return

        cs_sel = self.w_cs.get()
        case_id = self.cs_map.get(cs_sel) if cs_sel and cs_sel != "-- بدون قضية --" else None
        if case_id:
            ok = self.db.conn.execute(
                "SELECT 1 FROM cases WHERE id=? AND client_id=?",
                (case_id, cl),
            ).fetchone()
            if not ok:
                messagebox.showerror("خطأ", "القضية المختارة لا تنتمي لهذا العميل.", parent=self)
                return

        total, paid, rem = self._fees_snapshot(cl, case_id)
        if total > 0 and amount > rem + 0.005:
            messagebox.showerror(
                "خطأ",
                f"لا يمكن دفع أكثر من المتبقي من الأتعاب.\nالمتبقي المتاح: {rem:,.2f}",
                parent=self,
            )
            return

        client = self.db.conn.execute("SELECT name FROM clients WHERE id=?", (cl,)).fetchone()

        cur = self.db.conn.execute("""
            INSERT INTO payments (client_id, case_id, amount, method, pay_date, reference, notes, recorded_by)
            VALUES (?,?,?,?,?,?,?,?)
        """, (cl, case_id, amount, self.w_method.get(),
              pay_date, self.w_ref.get().strip(),
              self.w_notes.get("1.0", "end").strip(),
              self.user["username"]))
        payment_id = cur.lastrowid
        case_num = None
        if case_id:
            row_case = self.db.conn.execute("SELECT case_num FROM cases WHERE id=?", (case_id,)).fetchone()
            case_num = row_case[0] if row_case else None
        method = self.w_method.get() or "-"
        reference = self.w_ref.get().strip() or "-"
        notes = self.w_notes.get("1.0", "end").strip() or "-"
        self.db.conn.commit()
        self.db.log(self.user["username"], "مالية",
                    f"تسجيل دفعة {amount:,.2f} من {client[0] if client else ''}",
                    self.user["username"])
        show_toast(self.master, f"تم تسجيل الدفعة: {amount:,.2f} ✓", "green")
        if messagebox.askyesno("طباعة إيصال", "تم تسجيل الدفعة بنجاح.\nهل تريد طباعة إيصال الآن؟", parent=self):
            self._print_receipt({
                "payment_id": payment_id,
                "client_name": client[0] if client else "-",
                "case_num": case_num or "-",
                "amount": f"{amount:,.2f}",
                "method": method,
                "date": pay_date,
                "reference": reference,
                "recorded_by": self.user["username"],
                "notes": notes,
            })
        self.callback()
        self.destroy()

    def _print_receipt(self, data):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        doc = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>إيصال دفعة #{html.escape(str(data.get("payment_id", "")))}</title>
  <style>
    @page {{ size: A4; margin: 15mm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; color: #111; }}
    .box {{ border: 2px solid #222; padding: 14px; }}
    .title {{ font-size: 24px; font-weight: 700; text-align: center; margin-bottom: 10px; }}
    .meta {{ text-align: center; color: #555; margin-bottom: 14px; font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    td {{ border: 1px solid #aaa; padding: 8px 10px; }}
    td.k {{ background: #f2f2f2; width: 30%; font-weight: 700; }}
    .amount {{ font-size: 20px; font-weight: 700; color: #0a7a36; }}
    .foot {{ margin-top: 16px; display: flex; justify-content: space-between; font-size: 13px; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="title">إيصال سداد أتعاب</div>
    <div class="meta">{html.escape(APP_NAME)} | طباعة: {html.escape(now)}</div>
    <table>
      <tr><td class="k">رقم الإيصال</td><td>{html.escape(str(data.get("payment_id", "-")))}</td></tr>
      <tr><td class="k">العميل</td><td>{html.escape(str(data.get("client_name", "-")))}</td></tr>
      <tr><td class="k">القضية</td><td>{html.escape(str(data.get("case_num", "-")))}</td></tr>
      <tr><td class="k">المبلغ</td><td class="amount">{html.escape(str(data.get("amount", "-")))}</td></tr>
      <tr><td class="k">طريقة الدفع</td><td>{html.escape(str(data.get("method", "-")))}</td></tr>
      <tr><td class="k">التاريخ</td><td>{html.escape(str(data.get("date", "-")))}</td></tr>
      <tr><td class="k">المرجع</td><td>{html.escape(str(data.get("reference", "-")))}</td></tr>
      <tr><td class="k">ملاحظات</td><td>{html.escape(str(data.get("notes", "-")))}</td></tr>
    </table>
    <div class="foot">
      <div>المسجل: {html.escape(str(data.get("recorded_by", "-")))}</div>
      <div>التوقيع: _______________</div>
    </div>
  </div>
  <script>window.onload = () => window.print();</script>
</body>
</html>"""
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as tmp:
                tmp.write(doc)
                out_path = tmp.name
            webbrowser.open(Path(out_path).as_uri())
        except Exception as ex:
            messagebox.showerror("خطأ", f"تعذر فتح إيصال الطباعة:\n{ex}", parent=self)


class ExpenseDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, user, callback):
        super().__init__(parent)
        self.db = db; self.user = user; self.callback = callback
        self.title("تسجيل مصروف")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 480, 420)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="📤  تسجيل مصروف",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def lbl(t): ctk.CTkLabel(sc, text=t, font=("Arial", 12),
                                  text_color=COLORS["text2"]).pack(anchor="w", padx=4, pady=(8,2))
        lbl("البند / الوصف *")
        self.w_item = make_entry(sc, "", 430); self.w_item.pack(padx=4, pady=(0,4))
        lbl("المبلغ *")
        self.w_amt = make_entry(sc, "المبلغ", 430); self.w_amt.pack(padx=4, pady=(0,4))
        lbl("الفئة")
        self.w_cat = make_combo(sc, ["إيجار","رواتب","مستلزمات مكتبية","تواصل ونقل","رسوم قضائية","أخرى"], 430)
        self.w_cat.pack(padx=4, pady=(0,4))
        lbl("التاريخ *")
        self.w_date = make_entry(sc, "YYYY-MM-DD", 430)
        self.w_date.insert(0, date.today().isoformat()); self.w_date.pack(padx=4, pady=(0,4))
        lbl("ملاحظات")
        self.w_notes = make_textbox(sc, height=60, width=430); self.w_notes.pack(padx=4, pady=(0,4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  تسجيل", self._save, "red", 140).pack(side="right", padx=4)

    def _save(self):
        item = self.w_item.get().strip()
        amt_str = self.w_amt.get().strip()
        exp_date = self.w_date.get().strip()
        if not item or not amt_str or not exp_date:
            messagebox.showerror("خطأ", "البند والمبلغ والتاريخ مطلوبة", parent=self); return
        try: amount = float(amt_str)
        except: messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً", parent=self); return

        self.db.conn.execute("""
            INSERT INTO expenses (item, amount, category, exp_date, notes, recorded_by)
            VALUES (?,?,?,?,?,?)
        """, (item, amount, self.w_cat.get(), exp_date,
              self.w_notes.get("1.0", "end").strip(),
              self.user["username"]))
        self.db.conn.commit()
        self.db.log(self.user["username"], "مالية",
                    f"تسجيل مصروف: {item} - {amount:,.2f}",
                    self.user["username"])
        show_toast(self.master, f"تم تسجيل المصروف: {amount:,.2f} ✓", "red")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة المهام
# ════════════════════════════════════════════════════════════
class TasksPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("✅  المهام", "متابعة المهام والتذكيرات")
        self._btn_add = make_button(hdr, "➕  مهمة جديدة", self._open_add,
                                    color="gold", width=160)
        self._btn_add.pack(side="right", padx=14, pady=14)

        # فلاتر
        flt = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8, height=44)
        flt.pack(fill="x", padx=12, pady=(0, 6))
        flt.pack_propagate(False)
        self.filter_var = ctk.StringVar(value="الكل")
        for s in ["الكل", "قيد التنفيذ", "منجزة", "متأخرة"]:
            ctk.CTkButton(flt, text=s, width=110, height=30,
                          font=("Arial", 12, "bold"),
                          fg_color=COLORS["bg3"],
                          hover_color=COLORS["gold_dark"],
                          text_color=COLORS["text2"],
                          corner_radius=6,
                          command=lambda v=s: self._filter(v)).pack(side="right", padx=4, pady=6)

        cols = ("#", "المهمة", "المرتبط بـ", "الأولوية", "الاستحقاق", "المكلف", "الحالة")
        widths = (40, 260, 180, 90, 110, 120, 100)
        self.tree, _ = styled_treeview(self, cols, cols, widths)

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_complete = make_button(btn_bar, "✅  إنجاز", self._complete, "green", 120)
        self._btn_complete.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف",  self._delete,   "red",   120)
        self._btn_del.pack(side="right", padx=4)
        make_button(btn_bar, "🖨️  طباعة", self._print_report, "ghost", 120).pack(side="left", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("tasks_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("tasks_edit"):
            self._btn_complete.configure(state="disabled")
        if not self.has_perm("tasks_delete"):
            self._btn_del.configure(state="disabled")

        self._load_data()

    def _filter(self, val):
        self.filter_var.set(val)
        self._load_data()

    def _load_data(self):
        self.tree.delete(*self.tree.get_children())
        today = date.today().isoformat()
        fv = self.filter_var.get()

        where = ""
        if fv == "قيد التنفيذ":
            where = "WHERE status='pending'"
        elif fv == "منجزة":
            where = "WHERE status='done'"
        elif fv == "متأخرة":
            where = f"WHERE status='pending' AND due_date < '{today}'"

        rows = self.db.conn.execute(f"""
            SELECT id, title, related, priority, due_date, assigned_to, status
            FROM tasks {where} ORDER BY
            CASE priority WHEN 'عالية' THEN 1 WHEN 'متوسطة' THEN 2 ELSE 3 END,
            due_date
        """).fetchall()

        for i, r in enumerate(rows):
            is_late  = r[6] == "pending" and r[4] and r[4] < today
            is_done  = r[6] == "done"
            tag = "urgent" if is_late else ("inactive" if is_done else ("odd" if i%2==0 else "even"))
            status_lbl = "منجزة ✅" if is_done else ("متأخرة ⚠" if is_late else "قيد التنفيذ")
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1], r[2] or "-", r[3],
                                     r[4] or "-", r[5], status_lbl),
                             tags=(tag,))

    def _open_add(self):
        if not self.require_perm("tasks_add", "ليس لديك صلاحية إضافة مهام."):
            return
        TaskDialog(self, self.db, self.current_user, self._load_data)

    def _complete(self):
        if not self.require_perm("tasks_edit", "ليس لديك صلاحية تعديل/إنجاز المهام."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مهمة أولاً", parent=self); return
        self.db.conn.execute("UPDATE tasks SET status='done' WHERE id=?", (sel,))
        self.db.conn.commit()
        self._load_data()
        show_toast(self.app, "تم إنجاز المهمة ✓", "green")

    def _delete(self):
        if not self.require_perm("tasks_delete", "ليس لديك صلاحية حذف المهام."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مهمة أولاً", parent=self); return
        self._confirm_delete("حذف هذه المهمة؟",
                             lambda: [self.db.conn.execute("DELETE FROM tasks WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self._load_data()])

    def refresh(self):
        self._load_data()

    def _print_report(self):
        self._print_treeview(self.tree, "تقرير المهام", note=f"فلتر الحالة: {self.filter_var.get()}")


class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, user, callback):
        super().__init__(parent)
        self.db = db; self.user = user; self.callback = callback
        self.title("مهمة جديدة")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 480, 400)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="✅  مهمة جديدة",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def lbl(t): ctk.CTkLabel(sc, text=t, font=("Arial", 12),
                                  text_color=COLORS["text2"]).pack(anchor="w", padx=4, pady=(8,2))
        lbl("عنوان المهمة *")
        self.w_title = make_entry(sc, "", 440); self.w_title.pack(padx=4, pady=(0,4))
        lbl("الأولوية")
        self.w_prio = make_combo(sc, ["عالية","متوسطة","منخفضة"], 440); self.w_prio.pack(padx=4, pady=(0,4))
        lbl("تاريخ الاستحقاق")
        self.w_due = make_entry(sc, "YYYY-MM-DD", 440)
        self.w_due.insert(0, date.today().isoformat()); self.w_due.pack(padx=4, pady=(0,4))
        lbl("المرتبط بـ (قضية / عميل)")
        cases = self.db.conn.execute("SELECT case_num FROM cases ORDER BY id DESC LIMIT 20").fetchall()
        opts = ["-- عام --"] + [r[0] for r in cases]
        self.w_rel = make_combo(sc, opts, 440); self.w_rel.pack(padx=4, pady=(0,4))
        lbl("وصف المهمة")
        self.w_desc = make_textbox(sc, height=80, width=440); self.w_desc.pack(padx=4, pady=(0,4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _save(self):
        title = self.w_title.get().strip()
        if not title:
            messagebox.showerror("خطأ", "عنوان المهمة مطلوب", parent=self); return
        self.db.conn.execute("""
            INSERT INTO tasks (title, priority, due_date, related, description, assigned_to)
            VALUES (?,?,?,?,?,?)
        """, (title, self.w_prio.get(), self.w_due.get().strip(),
              self.w_rel.get(), self.w_desc.get("1.0","end").strip(),
              self.user["username"]))
        self.db.conn.commit()
        self.db.log(self.user["username"], "مهام", f"إضافة مهمة: {title}", self.user["username"])
        show_toast(self.master, f"تم إضافة المهمة: {title} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة العقود
# ════════════════════════════════════════════════════════════
class ContractsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("📜  العقود", "إدارة عقود التوكيل والاتفاقيات")
        self._btn_add = make_button(hdr, "➕  عقد جديد", self._open_add,
                                    color="gold", width=150)
        self._btn_add.pack(side="right", padx=14, pady=14)

        bar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8, height=48)
        bar.pack(fill="x", padx=12, pady=(0, 6))
        bar.pack_propagate(False)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_data())
        e = ctk.CTkEntry(bar, textvariable=self.search_var,
                         placeholder_text="🔍  بحث...", width=280,
                         fg_color=COLORS["bg3"], border_color=COLORS["border"],
                         text_color=COLORS["text"])
        e.pack(side="right", padx=10, pady=8)
        _enable_text_shortcuts(e)

        cols = ("#", "رقم العقد", "العميل", "نوع العقد", "الأتعاب", "طريقة الدفع", "تاريخ التوقيع", "تاريخ الانتهاء")
        widths = (40, 120, 180, 130, 90, 130, 120, 120)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.bind("<Double-1>", lambda _: self._open_edit())

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_edit = make_button(btn_bar, "✏️  تعديل", self._open_edit, "accent", 130)
        self._btn_edit.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف",  self._delete,    "red",   120)
        self._btn_del.pack(side="right", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("contracts_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("contracts_edit"):
            self._btn_edit.configure(state="disabled")
        if not self.has_perm("contracts_delete"):
            self._btn_del.configure(state="disabled")

        self._load_data()

    def _load_data(self, *_):
        self.tree.delete(*self.tree.get_children())
        q = f"%{self.search_var.get()}%"
        rows = self.db.conn.execute("""
            SELECT cn.id, cn.contract_num, cl.name, cn.type,
                   cn.fees, cn.pay_method, cn.sign_date, cn.end_date
            FROM contracts cn
            LEFT JOIN clients cl ON cl.id = cn.client_id
            WHERE cn.contract_num LIKE ? OR cl.name LIKE ? OR cn.type LIKE ?
            ORDER BY cn.id DESC
        """, (q, q, q)).fetchall()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1], r[2] or "-", r[3],
                                     f"{r[4]:,.2f}", r[5], r[6] or "-", r[7] or "-"),
                             tags=(tag,))

    def _open_add(self):
        if not self.require_perm("contracts_add", "ليس لديك صلاحية إضافة عقود."):
            return
        ContractDialog(self, self.db, None, self.current_user, self._load_data)

    def _open_edit(self):
        if not self.require_perm("contracts_edit", "ليس لديك صلاحية تعديل العقود."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر عقداً أولاً", parent=self); return
        ContractDialog(self, self.db, int(sel), self.current_user, self._load_data)

    def _delete(self):
        if not self.require_perm("contracts_delete", "ليس لديك صلاحية حذف العقود."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر عقداً أولاً", parent=self); return
        r = self.db.conn.execute("SELECT contract_num FROM contracts WHERE id=?", (sel,)).fetchone()
        self._confirm_delete(f"حذف العقد: {r[0]}",
                             lambda: [self.db.conn.execute("DELETE FROM contracts WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self._load_data()])

    def refresh(self):
        self._load_data()


class ContractDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, contract_id, user, callback):
        super().__init__(parent)
        self.db = db
        self.contract_id = contract_id
        self.user = user
        self.callback = callback
        self.title("إضافة عقد" if not contract_id else "تعديل عقد")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 580, 620)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if contract_id:
            self._load_existing()

    def _build(self):
        ctk.CTkLabel(self, text="📜  بيانات العقد",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        sc.grid_columnconfigure((0, 1), weight=1)

        clients = self.db.conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
        cl_opts = [f"{r[0]} - {r[1]}" for r in clients]
        self.cl_map = {f"{r[0]} - {r[1]}": r[0] for r in clients}
        cases = self.db.conn.execute("SELECT id, case_num, subject FROM cases ORDER BY id DESC").fetchall()
        cs_opts = ["-- بدون قضية --"] + [f"{r[0]} - {r[1]}" for r in cases]
        self.cs_map = {f"{r[0]} - {r[1]}": r[0] for r in cases}

        def lbl(sc, text, row, col, span=1):
            ctk.CTkLabel(sc, text=text, font=("Arial", 12),
                         text_color=COLORS["text2"]).grid(
                row=row*2, column=col, columnspan=span,
                sticky="e", padx=8, pady=(8, 2))

        lbl(sc, "رقم العقد *", 0, 0)
        self.w_num = make_entry(sc, "", 260)
        self.w_num.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "العميل *", 0, 1)
        self.w_cl = make_combo(sc, cl_opts, 260)
        self.w_cl.grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "نوع العقد", 1, 0)
        self.w_type = make_combo(sc, ["توكيل عام","توكيل خاص","عقد مرافعة","اتفاقية تسوية","عقد استشارات","أخرى"], 260)
        self.w_type.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "القضية المرتبطة", 1, 1)
        self.w_cs = make_combo(sc, cs_opts, 260)
        self.w_cs.grid(row=3, column=1, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "الأتعاب", 2, 0)
        self.w_fees = make_entry(sc, "0.00", 260)
        self.w_fees.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "طريقة الدفع", 2, 1)
        self.w_pay = make_combo(sc, ["دفعة واحدة","دفعات","نسبة من التسوية","أخرى"], 260)
        self.w_pay.grid(row=5, column=1, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "تاريخ التوقيع", 3, 0)
        self.w_sign = make_entry(sc, "YYYY-MM-DD", 260)
        self.w_sign.insert(0, date.today().isoformat())
        self.w_sign.grid(row=7, column=0, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "تاريخ الانتهاء", 3, 1)
        self.w_end = make_entry(sc, "YYYY-MM-DD", 260)
        self.w_end.grid(row=7, column=1, sticky="ew", padx=8, pady=(0, 4))

        lbl(sc, "شروط العقد", 4, 0, 2)
        self.w_terms = make_textbox(sc, height=100, width=520)
        self.w_terms.grid(row=9, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 4))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _get_val(self, w):
        if isinstance(w, ctk.CTkTextbox):
            return w.get("1.0", "end").strip()
        return w.get().strip()

    def _load_existing(self):
        r = self.db.conn.execute("""
            SELECT cn.*, cl.id||' - '||cl.name as cl_sel
            FROM contracts cn LEFT JOIN clients cl ON cl.id=cn.client_id
            WHERE cn.id=?
        """, (self.contract_id,)).fetchone()
        if not r: return
        self.w_num.insert(0, r["contract_num"] or "")
        self.w_cl.set(r["cl_sel"] or "")
        self.w_type.set(r["type"] or "")
        self.w_fees.delete(0, "end"); self.w_fees.insert(0, str(r["fees"] or 0))
        self.w_pay.set(r["pay_method"] or "")
        self.w_sign.delete(0, "end"); self.w_sign.insert(0, r["sign_date"] or "")
        self.w_end.delete(0, "end");  self.w_end.insert(0, r["end_date"] or "")
        self.w_terms.delete("1.0", "end"); self.w_terms.insert("1.0", r["terms"] or "")

    def _save(self):
        num = self._get_val(self.w_num)
        cl_sel = self._get_val(self.w_cl)
        if not num or not cl_sel:
            messagebox.showerror("خطأ", "رقم العقد والعميل مطلوبان", parent=self); return
        try: fees = float(self.w_fees.get().strip() or 0)
        except: fees = 0.0
        cl_id = self.cl_map.get(cl_sel)
        cs_sel = self._get_val(self.w_cs)
        cs_id = self.cs_map.get(cs_sel)
        data = {
            "contract_num": num,
            "client_id":    cl_id,
            "case_id":      cs_id,
            "type":         self._get_val(self.w_type),
            "fees":         fees,
            "pay_method":   self._get_val(self.w_pay),
            "sign_date":    self._get_val(self.w_sign),
            "end_date":     self._get_val(self.w_end),
            "terms":        self._get_val(self.w_terms),
        }
        if self.contract_id:
            sets = ", ".join(f"{k}=?" for k in data)
            self.db.conn.execute(f"UPDATE contracts SET {sets} WHERE id=?",
                                 list(data.values()) + [self.contract_id])
            action = f"تعديل عقد: {num}"
        else:
            cols = ", ".join(data.keys())
            phs  = ", ".join("?" for _ in data)
            self.db.conn.execute(f"INSERT INTO contracts ({cols}) VALUES ({phs})",
                                 list(data.values()))
            action = f"إضافة عقد: {num}"
        self.db.conn.commit()
        self.db.log(self.user["username"], "عقد", action, self.user["username"])
        show_toast(self.master, f"تم الحفظ: {num} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة الوثائق
# ════════════════════════════════════════════════════════════
class DocumentsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self.filter_type = "الكل"
        self._build()

    def _build(self):
        hdr = self._page_header("📂  الوثائق", "إدارة المستندات والوثائق القانونية")
        self._btn_add = make_button(hdr, "➕  إضافة وثيقة", self._open_add,
                                    color="gold", width=160)
        self._btn_add.pack(side="right", padx=14, pady=14)

        bar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8, height=48)
        bar.pack(fill="x", padx=12, pady=(0, 6))
        bar.pack_propagate(False)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_data())
        e = ctk.CTkEntry(bar, textvariable=self.search_var,
                         placeholder_text="🔍  بحث...", width=280,
                         fg_color=COLORS["bg3"], border_color=COLORS["border"],
                         text_color=COLORS["text"])
        e.pack(side="right", padx=10, pady=8)
        _enable_text_shortcuts(e)

        # فلاتر النوع
        flt = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8, height=44)
        flt.pack(fill="x", padx=12, pady=(0, 6))
        flt.pack_propagate(False)
        self._filter_btns = {}
        for t in ["الكل", "مستند رسمي", "حكم قضائي", "عقد", "توكيل", "أخرى"]:
            b = ctk.CTkButton(
                flt, text=t, width=100, height=30,
                font=("Arial", 12, "bold"),
                fg_color=COLORS["gold"] if t == self.filter_type else COLORS["bg3"],
                hover_color=COLORS["gold_dark"],
                text_color="#000" if t == self.filter_type else COLORS["text2"],
                corner_radius=6,
                command=lambda v=t: self._filter(v),
            )
            b.pack(side="right", padx=4, pady=6)
            self._filter_btns[t] = b

        cols = ("#", "اسم الوثيقة", "نوع الوثيقة", "القضية", "العميل", "التاريخ", "ملاحظات")
        widths = (40, 220, 130, 180, 160, 110, 200)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.bind("<Double-1>", lambda _: self._open_edit())

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_edit = make_button(btn_bar, "✏️  تعديل", self._open_edit, "accent", 130)
        self._btn_edit.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف",  self._delete,    "red",   120)
        self._btn_del.pack(side="right", padx=4)

        # تطبيق الصلاحيات
        if not self.has_perm("docs_add"):
            self._btn_add.configure(state="disabled")
        if not self.has_perm("docs_edit"):
            self._btn_edit.configure(state="disabled")
        if not self.has_perm("docs_delete"):
            self._btn_del.configure(state="disabled")

        self._load_data()

    def _filter(self, val):
        self.filter_type = val
        for t, btn in self._filter_btns.items():
            active = t == self.filter_type
            btn.configure(
                fg_color=COLORS["gold"] if active else COLORS["bg3"],
                text_color="#000" if active else COLORS["text2"],
            )
        self._load_data()

    def _load_data(self, *_):
        self.tree.delete(*self.tree.get_children())
        q = f"%{self.search_var.get()}%"
        if self.filter_type == "الكل":
            rows = self.db.conn.execute("""
                SELECT d.id, d.doc_name, d.doc_type,
                       c.case_num, cl.name, d.doc_date, d.notes
                FROM documents d
                LEFT JOIN cases c  ON c.id  = d.case_id
                LEFT JOIN clients cl ON cl.id = d.client_id
                WHERE (d.doc_name LIKE ? OR d.doc_type LIKE ?)
                ORDER BY d.id DESC
            """, (q, q)).fetchall()
        else:
            rows = self.db.conn.execute("""
                SELECT d.id, d.doc_name, d.doc_type,
                       c.case_num, cl.name, d.doc_date, d.notes
                FROM documents d
                LEFT JOIN cases c  ON c.id  = d.case_id
                LEFT JOIN clients cl ON cl.id = d.client_id
                WHERE (d.doc_name LIKE ? OR d.doc_type LIKE ?) AND d.doc_type = ?
                ORDER BY d.id DESC
            """, (q, q, self.filter_type)).fetchall()
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1], r[2], r[3] or "-",
                                     r[4] or "-", r[5] or "-", r[6] or "-"),
                             tags=(tag,))

    def _open_add(self):
        if not self.require_perm("docs_add", "ليس لديك صلاحية إضافة وثائق."):
            return
        DocumentDialog(self, self.db, None, self.current_user, self._load_data)

    def _open_edit(self):
        if not self.require_perm("docs_edit", "ليس لديك صلاحية تعديل الوثائق."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر وثيقة أولاً", parent=self); return
        DocumentDialog(self, self.db, int(sel), self.current_user, self._load_data)

    def _delete(self):
        if not self.require_perm("docs_delete", "ليس لديك صلاحية حذف الوثائق."):
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر وثيقة أولاً", parent=self); return
        r = self.db.conn.execute("SELECT doc_name FROM documents WHERE id=?", (sel,)).fetchone()
        self._confirm_delete(f"حذف الوثيقة: {r[0]}",
                             lambda: [self.db.delete_document_file(int(sel)),
                                      self.db.conn.execute("DELETE FROM documents WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self._load_data()])

    def refresh(self):
        self._load_data()


_MAX_DOCUMENT_BYTES = 80 * 1024 * 1024  # 80MB — الملفات في قاعدة منفصلة


class DocumentDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, doc_id, user, callback):
        super().__init__(parent)
        self.db = db
        self.doc_id = doc_id
        self.user = user
        self.callback = callback
        self._pending_file: bytes | None = None
        self._pending_name = ""
        self._pending_mime = ""
        self._remove_attachment = False
        self.title("إضافة وثيقة" if not doc_id else "تعديل وثيقة")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 540, 640)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if doc_id:
            self._load_existing()

    def _build(self):
        ctk.CTkLabel(self, text="📂  بيانات الوثيقة",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def lbl(t): ctk.CTkLabel(sc, text=t, font=("Arial", 12),
                                  text_color=COLORS["text2"]).pack(anchor="e", padx=4, pady=(8, 2))
        def ent(ph="", w=490): e = make_entry(sc, ph, w); e.pack(padx=4, pady=(0, 4)); return e

        cases   = self.db.conn.execute("SELECT id, case_num, subject FROM cases ORDER BY id DESC").fetchall()
        clients = self.db.conn.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
        cs_opts = ["-- بدون قضية --"] + [f"{r[0]} - {r[1]}" for r in cases]
        cl_opts = ["-- بدون عميل --"] + [f"{r[0]} - {r[1]}" for r in clients]
        self.cs_map = {f"{r[0]} - {r[1]}": r[0] for r in cases}
        self.cl_map = {f"{r[0]} - {r[1]}": r[0] for r in clients}

        lbl("اسم الوثيقة *")
        self.w_name = ent()

        lbl("نوع الوثيقة")
        self.w_type = make_combo(sc, ["مستند رسمي","حكم قضائي","عقد","توكيل","صور شخصية","أخرى"], 490)
        self.w_type.pack(padx=4, pady=(0, 4))

        lbl("القضية المرتبطة")
        self.w_cs = make_combo(sc, cs_opts, 490)
        self.w_cs.pack(padx=4, pady=(0, 4))

        lbl("العميل المرتبط")
        self.w_cl = make_combo(sc, cl_opts, 490)
        self.w_cl.pack(padx=4, pady=(0, 4))

        lbl("تاريخ الوثيقة")
        self.w_date = ent("YYYY-MM-DD")
        self.w_date.delete(0, "end")
        self.w_date.insert(0, date.today().isoformat())

        lbl("ملاحظات")
        self.w_notes = make_textbox(sc, height=80, width=490)
        self.w_notes.pack(padx=4, pady=(0, 4))

        lbl("مرفق (صورة أو ملف) — يُخزَّن في قاعدة مستندات منفصلة")
        att_row = ctk.CTkFrame(sc, fg_color="transparent")
        att_row.pack(fill="x", padx=4, pady=(0, 6))
        make_button(att_row, "📎  إرفاق", self._pick_attachment, "accent", 110).pack(side="right", padx=(4, 0))
        make_button(att_row, "👁  فتح", self._open_attachment, "ghost", 90).pack(side="right", padx=4)
        make_button(att_row, "✖  إزالة", self._remove_attachment_click, "red", 90).pack(side="right", padx=4)
        self._lbl_att = ctk.CTkLabel(
            att_row, text="لا يوجد مرفق", font=("Arial", 11),
            text_color=COLORS["text3"], anchor="e",
        )
        self._lbl_att.pack(side="right", fill="x", expand=True, padx=(8, 0))

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _sync_att_label(self):
        if self._remove_attachment and not self._pending_file:
            self._lbl_att.configure(text="سيتم إزالة المرفق عند الحفظ", text_color=COLORS["orange"])
            return
        if self._pending_file:
            sz = len(self._pending_file)
            self._lbl_att.configure(
                text=f"{self._pending_name or 'مرفق'}  ({sz // 1024} ك.ب تقريباً)",
                text_color=COLORS["text"],
            )
            return
        if self.doc_id and self.db.has_document_file(self.doc_id):
            info = self.db.get_document_file_info(self.doc_id)
            if info:
                nm, sz = info
                self._lbl_att.configure(
                    text=f"{nm or 'مرفق'}  ({sz // 1024} ك.ب تقريباً)",
                    text_color=COLORS["text"],
                )
                return
        self._lbl_att.configure(text="لا يوجد مرفق", text_color=COLORS["text3"])

    def _pick_attachment(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="اختر ملف الوثيقة",
            filetypes=[
                ("مستندات وصور", "*.pdf;*.png;*.jpg;*.jpeg;*.webp;*.tif;*.tiff;*.doc;*.docx"),
                ("الكل", "*.*"),
            ],
        )
        if not path:
            return
        try:
            st = os.stat(path)
            if st.st_size > _MAX_DOCUMENT_BYTES:
                messagebox.showerror(
                    "حجم كبير",
                    f"الحد الأقصى للملف {_MAX_DOCUMENT_BYTES // (1024 * 1024)} م.ب",
                    parent=self,
                )
                return
            with open(path, "rb") as f:
                self._pending_file = f.read()
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر قراءة الملف:\n{e}", parent=self)
            return
        self._pending_name = os.path.basename(path)
        self._pending_mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        self._remove_attachment = False
        self._sync_att_label()

    def _remove_attachment_click(self):
        has_stored = bool(self.doc_id and self.db.has_document_file(self.doc_id))
        if not self._pending_file and not has_stored:
            messagebox.showinfo("تنبيه", "لا يوجد مرفق لإزالته.", parent=self)
            return
        self._pending_file = None
        self._pending_name = ""
        self._pending_mime = ""
        self._remove_attachment = True
        self._sync_att_label()

    def _open_attachment(self):
        if self._pending_file:
            try:
                ext = os.path.splitext(self._pending_name or "file")[1] or ".bin"
                fd, tmp = tempfile.mkstemp(suffix=ext)
                os.close(fd)
                with open(tmp, "wb") as f:
                    f.write(self._pending_file)
                if platform.system() == "Windows":
                    os.startfile(tmp)  # noqa: S606
                else:
                    webbrowser.open(f"file://{tmp}")
            except Exception as e:
                messagebox.showerror("خطأ", str(e), parent=self)
            return
        if not self.doc_id or not self.db.has_document_file(self.doc_id):
            messagebox.showinfo("تنبيه", "لا يوجد مرفق محفوظ.", parent=self)
            return
        got = self.db.get_document_file_blob(self.doc_id)
        if not got:
            messagebox.showinfo("تنبيه", "لا يوجد مرفق محفوظ.", parent=self)
            return
        data, _mime, oname = got
        try:
            ext = os.path.splitext(oname or "file")[1] or ".bin"
            fd, tmp = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            with open(tmp, "wb") as f:
                f.write(data)
            if platform.system() == "Windows":
                os.startfile(tmp)  # noqa: S606
            else:
                webbrowser.open(f"file://{tmp}")
        except Exception as e:
            messagebox.showerror("خطأ", str(e), parent=self)

    def _load_existing(self):
        r = self.db.conn.execute("""
            SELECT d.*, c.case_num, cl.name as cl_name
            FROM documents d
            LEFT JOIN cases c ON c.id=d.case_id
            LEFT JOIN clients cl ON cl.id=d.client_id
            WHERE d.id=?
        """, (self.doc_id,)).fetchone()
        if not r: return
        self.w_name.delete(0, "end"); self.w_name.insert(0, r["doc_name"] or "")
        self.w_type.set(r["doc_type"] or "")
        self.w_date.delete(0, "end"); self.w_date.insert(0, r["doc_date"] or "")
        self.w_notes.delete("1.0", "end"); self.w_notes.insert("1.0", r["notes"] or "")
        if r["case_id"]:
            match = next((k for k, v in self.cs_map.items() if v == r["case_id"]), None)
            if match: self.w_cs.set(match)
        if r["client_id"]:
            match = next((k for k, v in self.cl_map.items() if v == r["client_id"]), None)
            if match: self.w_cl.set(match)
        self._sync_att_label()

    def _save(self):
        name = self.w_name.get().strip()
        if not name:
            messagebox.showerror("خطأ", "اسم الوثيقة مطلوب", parent=self); return
        cs_id = self.cs_map.get(self.w_cs.get())
        cl_id = self.cl_map.get(self.w_cl.get())
        data = {
            "doc_name":  name,
            "doc_type":  self.w_type.get(),
            "case_id":   cs_id,
            "client_id": cl_id,
            "doc_date":  self.w_date.get().strip(),
            "notes":     self.w_notes.get("1.0", "end").strip(),
        }
        try:
            if self.doc_id:
                sets = ", ".join(f"{k}=?" for k in data)
                self.db.conn.execute(f"UPDATE documents SET {sets} WHERE id=?",
                                     list(data.values()) + [self.doc_id])
                action = f"تعديل وثيقة: {name}"
                doc_id = self.doc_id
            else:
                cols = ", ".join(data.keys()); phs = ", ".join("?" for _ in data)
                cur = self.db.conn.execute(f"INSERT INTO documents ({cols}) VALUES ({phs})",
                                           list(data.values()))
                doc_id = int(cur.lastrowid)
                action = f"إضافة وثيقة: {name}"
            self.db.conn.commit()

            if self._remove_attachment and not self._pending_file:
                self.db.delete_document_file(doc_id)
            elif self._pending_file:
                self.db.save_document_file(
                    doc_id,
                    self._pending_file,
                    mime=self._pending_mime,
                    original_name=self._pending_name,
                )
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل الحفظ:\n{e}", parent=self)
            return
        self.db.log(self.user["username"], "وثيقة", action, self.user["username"])
        show_toast(self.master, f"تم الحفظ: {name} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة سجل العمليات
# ════════════════════════════════════════════════════════════
class LogsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        role = (self.current_user or {}).get("role", "")
        if role not in ("dev_master", "admin", "superfiser"):
            messagebox.showwarning("صلاحيات", "هذه الصفحة متاحة للسوبرفايزر والأدمن فقط.", parent=self)
            try:
                self.app._navigate("dashboard")
            except Exception:
                pass
            return
        hdr = self._page_header("📋  سجل العمليات", "جميع العمليات المسجلة في النظام")
        if role in ("dev_master", "admin"):
            make_button(hdr, "🗑️  مسح السجل", self._clear,
                        color="red", width=150).pack(side="right", padx=14, pady=14)

        # بحث وفلتر
        bar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8, height=48)
        bar.pack(fill="x", padx=12, pady=(0, 6))
        bar.pack_propagate(False)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_data())
        e = ctk.CTkEntry(bar, textvariable=self.search_var,
                         placeholder_text="🔍  بحث...", width=280,
                         fg_color=COLORS["bg3"], border_color=COLORS["border"],
                         text_color=COLORS["text"])
        e.pack(side="right", padx=10, pady=8)
        _enable_text_shortcuts(e)

        cols = ("#", "التاريخ والوقت", "المستخدم", "نوع العملية", "التفاصيل", "الحساب", "IP")
        widths = (40, 150, 110, 110, 320, 110, 110)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self._load_data()

    def _load_data(self):
        self.tree.delete(*self.tree.get_children())
        q = f"%{self.search_var.get()}%"
        rows = self.db.conn.execute("""
            SELECT id, created_at, username, log_type, detail, account, ip
            FROM logs
            WHERE username LIKE ? OR detail LIKE ? OR log_type LIKE ?
            ORDER BY id DESC LIMIT 500
        """, (q, q, q)).fetchall()

        type_colors = {"تسجيل دخول":"active", "مالية":"urgent",
                       "قضية":"even", "عميل":"odd", "فشل دخول":"urgent"}
        for i, r in enumerate(rows):
            tag = type_colors.get(r[3], "odd" if i%2==0 else "even")
            dt  = r[1][:16] if r[1] else "-"
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, dt, r[2], r[3], r[4], r[5], r[6]),
                             tags=(tag,))

    def _clear(self):
        role = (self.current_user or {}).get("role", "")
        if role not in ("dev_master", "admin"):
            messagebox.showwarning("صلاحيات", "مسح السجل متاح للأدمن فقط.", parent=self)
            return
        if messagebox.askyesno("تأكيد", "مسح جميع السجلات؟ لا يمكن التراجع.", parent=self):
            self.db.conn.execute("DELETE FROM logs")
            self.db.conn.commit()
            self._load_data()
            show_toast(self.app, "تم مسح السجلات ✓", "gold")

    def refresh(self):
        self._load_data()


# ════════════════════════════════════════════════════════════
#  صفحة المتصلين (تعدد مستخدمين على نفس قاعدة البيانات)
# ════════════════════════════════════════════════════════════
class ConnectedUsersPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self.stale_seconds = 30
        self._build()

    def _build(self):
        hdr = self._page_header("🟢  المتصلون", "آخر نشاط للمستخدمين على قاعدة البيانات المشتركة")
        make_button(hdr, "🔄  تحديث", self._load_data, "ghost", 140).pack(side="left", padx=14, pady=14)

        cols = ("#", "المستخدم", "الحالة", "آخر نشاط", "app_id")
        widths = (40, 200, 100, 170, 240)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.pack_configure(padx=12, pady=(0, 4))
        self._load_data()

    def _load_data(self, *_):
        self.tree.delete(*self.tree.get_children())
        rows = self.db.get_online_users(stale_seconds=self.stale_seconds)
        for i, r in enumerate(rows):
            tag = "active" if r[2] == "online" else "inactive"
            self.tree.insert(
                "",
                "end",
                iid=str(r[0]),
                values=(i + 1, r[1], r[2], r[3], r[0]),
                tags=(tag,),
            )

    def refresh(self):
        self._load_data()


# ════════════════════════════════════════════════════════════
#  صفحة المستخدمين
# ════════════════════════════════════════════════════════════
PERMISSIONS_LIST = [
    ("clients_view",   "عرض العملاء"),
    ("clients_add",    "إضافة عملاء"),
    ("clients_edit",   "تعديل العملاء"),
    ("clients_delete", "حذف العملاء"),
    ("cases_view",     "عرض القضايا"),
    ("cases_add",      "إضافة قضايا"),
    ("cases_edit",     "تعديل القضايا"),
    ("cases_delete",   "حذف القضايا"),
    ("sessions_view",  "عرض الجلسات"),
    ("sessions_add",   "إضافة جلسات"),
    ("sessions_delete","حذف الجلسات"),
    ("finance_view",   "عرض المالية"),
    ("finance_add",    "تسجيل مدفوعات"),
    ("finance_edit",   "تعديل المالية"),
    ("finance_delete", "حذف معاملات مالية"),
    ("tasks_view",     "عرض المهام"),
    ("tasks_add",      "إضافة مهام"),
    ("tasks_edit",     "تعديل/إنجاز مهام"),
    ("tasks_delete",   "حذف المهام"),
    ("contracts_view", "عرض العقود"),
    ("contracts_add",  "إضافة عقود"),
    ("contracts_edit", "تعديل العقود"),
    ("contracts_delete","حذف العقود"),
    ("docs_view",      "عرض الوثائق"),
    ("docs_add",       "رفع وثائق"),
    ("docs_edit",      "تعديل الوثائق"),
    ("docs_delete",    "حذف الوثائق"),
    ("backup_manage",  "النسخ الاحتياطي والاستيراد والتصدير"),
    ("logs_view",      "عرض السجلات"),
    ("reports_view",   "عرض التقارير"),
    ("settings_manage","إدارة الإعدادات"),
]


class UsersPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        hdr = self._page_header("👤  المستخدمون", "إدارة حسابات المستخدمين والصلاحيات")
        self._btn_add = make_button(hdr, "➕  مستخدم جديد", self._open_add,
                                    color="gold", width=170)
        self._btn_add.pack(side="right", padx=14, pady=14)

        cols = ("#", "الاسم", "اسم المستخدم", "الصلاحية", "النوع",
                "حد الدخول", "المتبقي", "الحالة", "آخر دخول")
        widths = (40, 160, 130, 90, 80, 90, 80, 80, 160)
        self.tree, _ = styled_treeview(self, cols, cols, widths)
        self.tree.bind("<Double-1>", lambda _: self._open_edit())

        btn_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        btn_bar.pack(fill="x", padx=12, pady=(0, 8))
        btn_bar.pack_propagate(False)
        self._btn_edit = make_button(btn_bar, "✏️  تعديل", self._open_edit, "accent", 130)
        self._btn_edit.pack(side="right", padx=4)
        self._btn_toggle = make_button(btn_bar, "🔒  إيقاف/تفعيل", self._toggle, "ghost", 150)
        self._btn_toggle.pack(side="right", padx=4)
        self._btn_del = make_button(btn_bar, "🗑️  حذف", self._delete, "red", 120)
        self._btn_del.pack(side="right", padx=4)

        if self.current_user.get("role") == "trial":
            self._btn_add.pack_forget()
            for b in (self._btn_edit, self._btn_toggle, self._btn_del):
                b.configure(state="disabled")

        self._load_data()

    def _open_add(self):
        if self.current_user.get("role") == "trial":
            messagebox.showinfo(
                "تفعيل النسخة",
                "قم بتفعيل النسخة لتمكن من إضافة مستخدمين",
                parent=self,
            )
            return
        UserDialog(self, self.db, None, self.current_user, self._load_data)

    def _load_data(self):
        self.tree.delete(*self.tree.get_children())
        rows = self.db.conn.execute(
            "SELECT id,name,username,role,max_logins,logins_used,active,last_login FROM users ORDER BY id"
        ).fetchall()
        if self.current_user.get("role") != "dev_master":
            rows = [r for r in rows if r["role"] != "dev_master"]
        for i, r in enumerate(rows):
            rem = (r[4] - r[5]) if r[4] is not None else "∞"
            tag = "active" if r[6] else "inactive"
            dt  = r[7][:16] if r[7] else "لم يسجل دخول"
            self.tree.insert("", "end", iid=str(r[0]),
                             values=(i+1, r[1], r[2],
                                     ROLE_LABEL_AR.get(r[3], r[3]),
                                     "تجريبي" if r[3]=="trial" else "دائم",
                                     r[4] if r[4] else "غير محدود", rem,
                                     "نشط" if r[6] else "موقوف", dt),
                             tags=(tag,))

    def _open_edit(self):
        if self.current_user.get("role") == "trial":
            messagebox.showinfo(
                "تنبيه",
                "الحساب التجريبي يعرض قائمة المستخدمين فقط ولا يمكنه التعديل.",
                parent=self,
            )
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مستخدماً أولاً", parent=self); return
        prow = self.db.conn.execute("SELECT role FROM users WHERE id=?", (sel,)).fetchone()
        if prow and prow["role"] == "trial" and self.current_user.get("role") != "dev_master":
            messagebox.showwarning(
                "تنبيه",
                "تعديل الحسابات التجريبية متاح لمطور النظام فقط.",
                parent=self,
            )
            return
        UserDialog(self, self.db, int(sel), self.current_user, self._load_data)

    def _toggle(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مستخدماً أولاً", parent=self); return
        r = self.db.conn.execute(
            "SELECT username, role, active FROM users WHERE id=?", (sel,)
        ).fetchone()
        if r["username"] == "admin":
            messagebox.showwarning("تنبيه", "لا يمكن إيقاف حساب admin", parent=self); return
        if r["username"] == DEV_MASTER_USERNAME:
            messagebox.showwarning("تنبيه", "لا يمكن إيقاف حساب مطور النظام الثابت.", parent=self); return
        if r["role"] == "dev_master" and self.current_user.get("role") != "dev_master":
            messagebox.showwarning("تنبيه", "غير مصرح بإيقاف هذا الحساب.", parent=self); return
        new_active = 0 if r["active"] else 1
        self.db.conn.execute("UPDATE users SET active=? WHERE id=?", (new_active, sel))
        self.db.conn.commit()
        self.db.log(self.current_user["username"], "مستخدم",
                    f"{'تفعيل' if new_active else 'إيقاف'} مستخدم: {r['username']}",
                    self.current_user["username"])
        self._load_data()
        show_toast(self.app, f"تم {'التفعيل' if new_active else 'الإيقاف'} ✓", "gold")

    def _delete(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مستخدماً أولاً", parent=self); return
        r = self.db.conn.execute("SELECT username, role FROM users WHERE id=?", (sel,)).fetchone()
        if r["username"] == "admin":
            messagebox.showwarning("تنبيه", "لا يمكن حذف حساب admin", parent=self); return
        if r["username"] == DEV_MASTER_USERNAME:
            messagebox.showwarning("تنبيه", "لا يمكن حذف حساب مطور النظام الثابت.", parent=self); return
        if r["role"] == "dev_master" and self.current_user.get("role") != "dev_master":
            messagebox.showwarning("تنبيه", "لا يمكن حذف حساب مطور نظام إلا من مطور نظام آخر.", parent=self); return
        self._confirm_delete(f"حذف المستخدم: {r['username']}",
                             lambda: [self.db.conn.execute("DELETE FROM users WHERE id=?", (sel,)),
                                      self.db.conn.commit(), self._load_data()])

    def refresh(self):
        self._load_data()


class UserDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, user_id, current_user, callback):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.current_user = current_user
        self.callback = callback
        self.title("إضافة مستخدم" if not user_id else "تعديل مستخدم")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 620, 700)
        self.resizable(False, False)
        self.grab_set()
        self._role_pairs = []
        self._build()
        if user_id:
            self._load_existing()

    def _build(self):
        ctk.CTkLabel(self, text="بيانات المستخدم",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)

        sc = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg2"], corner_radius=8)
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # ─── البيانات الأساسية ────
        ctk.CTkLabel(sc, text="── البيانات الأساسية ──",
                     font=("Arial", 12, "bold"),
                     text_color=COLORS["gold"]).pack(anchor="w", padx=8, pady=(10, 4))

        row1 = ctk.CTkFrame(sc, fg_color="transparent"); row1.pack(fill="x", padx=4)
        row1.grid_columnconfigure((0,1), weight=1)

        def lbl_entry(parent, text, row, col, placeholder="", is_pass=False):
            ctk.CTkLabel(parent, text=text, font=("Arial", 12),
                         text_color=COLORS["text2"]).grid(row=row*2, column=col, sticky="w", padx=6, pady=(6,2))
            e = make_entry(parent, placeholder, width=260,
                           show="●" if is_pass else "")
            e.grid(row=row*2+1, column=col, sticky="ew", padx=6, pady=(0,4))
            return e

        self.w_name     = lbl_entry(row1, "الاسم الكامل *",    0, 0)
        self.w_username = lbl_entry(row1, "اسم المستخدم *",    0, 1)
        self.w_password = lbl_entry(row1, "كلمة المرور *" if not self.user_id else "كلمة المرور الجديدة (اتركها فارغة للإبقاء)", 1, 0, is_pass=True)
        self.w_email    = lbl_entry(row1, "البريد الإلكتروني", 1, 1)
        self.w_phone    = lbl_entry(row1, "رقم الجوال",         2, 0)

        ctk.CTkLabel(row1, text="الصلاحية (الدور)", font=("Arial", 12),
                     text_color=COLORS["text2"]).grid(row=4, column=1, sticky="w", padx=6, pady=(6,2))
        self.w_role = make_combo(row1, [ROLE_LABEL_AR["user"]], width=260)
        self.w_role.grid(row=5, column=1, sticky="ew", padx=6, pady=(0,4))
        self.w_role.configure(command=self._on_role_change)

        # ─── خيارات التجريبي ────
        self.trial_frame = ctk.CTkFrame(sc, fg_color=COLORS["panel"],
                                        corner_radius=8,
                                        border_width=1,
                                        border_color=COLORS["border"])
        self.trial_frame.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(self.trial_frame, text="⚙️  إعدادات الحساب التجريبي",
                     font=("Arial", 12, "bold"),
                     text_color=COLORS["orange"]).pack(anchor="w", padx=10, pady=(10, 4))

        tf_row = ctk.CTkFrame(self.trial_frame, fg_color="transparent")
        tf_row.pack(fill="x", padx=8)
        tf_row.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(tf_row, text="عدد مرات الدخول المسموحة",
                     font=("Arial", 12), text_color=COLORS["text2"]).grid(
            row=0, column=0, sticky="w", padx=4, pady=(4,2))
        self.w_max_logins = make_entry(tf_row, "مثال: 5", 240)
        self.w_max_logins.grid(row=1, column=0, sticky="ew", padx=4, pady=(0,4))
        self.w_max_logins.insert(0, "5")

        ctk.CTkLabel(tf_row, text="رسالة انتهاء الصلاحية",
                     font=("Arial", 12), text_color=COLORS["text2"]).grid(
            row=0, column=1, sticky="w", padx=4, pady=(4,2))
        self.w_expire_msg = make_entry(tf_row, "الرسالة عند انتهاء عدد الدخولات", 240)
        self.w_expire_msg.grid(row=1, column=1, sticky="ew", padx=4, pady=(0,4))
        self.w_expire_msg.insert(0, "انتهت صلاحية الحساب التجريبي. يرجى التواصل مع المسؤول.")
        self.trial_frame.pack_forget()  # مخفي افتراضياً

        # ─── الصلاحيات اليدوية ────
        ctk.CTkLabel(sc, text="── الصلاحيات اليدوية ──",
                     font=("Arial", 12, "bold"),
                     text_color=COLORS["gold"]).pack(anchor="w", padx=8, pady=(10, 4))

        perm_grid = ctk.CTkFrame(sc, fg_color=COLORS["panel"],
                                  corner_radius=8,
                                  border_width=1,
                                  border_color=COLORS["border"])
        perm_grid.pack(fill="x", padx=4, pady=4)

        self.perm_vars = {}
        cols_count = 3
        for idx, (key, label) in enumerate(PERMISSIONS_LIST):
            var = ctk.BooleanVar()
            self.perm_vars[key] = var
            r, c = divmod(idx, cols_count)
            ctk.CTkCheckBox(perm_grid, text=label, variable=var,
                            text_color=COLORS["text2"],
                            font=("Arial", 11),
                            fg_color=COLORS["gold"],
                            hover_color=COLORS["gold_dark"],
                            border_color=COLORS["border"]).grid(
                row=r, column=c, sticky="w", padx=10, pady=5)

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=10)
        make_button(btn_bar, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btn_bar, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

        self._rebuild_role_combo()
        if not self.user_id:
            self.w_role.set(ROLE_LABEL_AR["user"])
            self._on_role_change(apply_template=True)

    def _rebuild_role_combo(self):
        vr = self.current_user.get("role", "")
        pairs = [
            (ROLE_LABEL_AR["user"], "user"),
            (ROLE_LABEL_AR["superfiser"], "superfiser"),
            (ROLE_LABEL_AR["admin"], "admin"),
        ]
        if vr == "dev_master":
            pairs.append((ROLE_LABEL_AR["trial"], "trial"))
            pairs.append((ROLE_LABEL_AR["dev_master"], "dev_master"))
        self._role_pairs = pairs
        self.w_role.configure(values=[p[0] for p in pairs])

    def _role_key_from_combo(self) -> str:
        lab = (self.w_role.get() or "").strip()
        for lbl, key in self._role_pairs:
            if lbl == lab:
                return key
        return "user"

    def _on_role_change(self, choice=None, apply_template: bool = True):
        key = self._role_key_from_combo()
        if key == "trial":
            self.trial_frame.pack(fill="x", padx=4, pady=6)
        else:
            self.trial_frame.pack_forget()
        # لا تغيّر صلاحيات مستخدم موجود إلا لو اختيار الدور تم بقصد (apply_template=True)
        if not apply_template:
            if key in ("admin", "superfiser", "dev_master") and "backup_manage" in self.perm_vars:
                self.perm_vars["backup_manage"].set(True)
            return

        def set_all(val: bool):
            for _k, v in self.perm_vars.items():
                try:
                    v.set(val)
                except Exception:
                    pass

        def set_only(keys: list[str]):
            ks = set(keys)
            for _k, v in self.perm_vars.items():
                try:
                    v.set(_k in ks)
                except Exception:
                    pass

        if key in ("admin", "superfiser", "dev_master"):
            # الأدمن/السوبر: كل الصلاحيات تلقائياً
            set_all(True)
        elif key == "user":
            # مستخدم: صلاحيات افتراضية (يمكن تعديلها يدوياً)
            set_only(["clients_view", "cases_view", "sessions_view", "docs_view", "tasks_view"])
        elif key == "trial":
            # تجريبي: عرض محدود جداً افتراضياً
            set_only(["clients_view", "cases_view"])

    def _load_existing(self):
        r = self.db.conn.execute("SELECT * FROM users WHERE id=?", (self.user_id,)).fetchone()
        if not r:
            return
        if r["role"] == "dev_master" and self.current_user.get("role") != "dev_master":
            messagebox.showerror(
                "غير مصرح",
                "لا يمكن عرض أو تعديل حساب مطور النظام.",
                parent=self,
            )
            self.destroy()
            return
        self._rebuild_role_combo()
        self.w_name.insert(0, r["name"])
        self.w_username.insert(0, r["username"])
        self.w_email.insert(0, r["email"] or "")
        self.w_phone.insert(0, r["phone"] or "")
        rk = r["role"]
        label = ROLE_LABEL_AR.get(rk, ROLE_LABEL_AR["user"])
        valid_labels = [p[0] for p in self._role_pairs]
        if label not in valid_labels:
            label = ROLE_LABEL_AR["user"]
        self.w_role.set(label)
        # لا تطبق قالب صلاحيات هنا؛ اعرض الصلاحيات المخزنة للمستخدم
        self._on_role_change(apply_template=False)
        if r["max_logins"]:
            self.w_max_logins.delete(0, "end")
            self.w_max_logins.insert(0, str(r["max_logins"]))
        self.w_expire_msg.delete(0, "end")
        self.w_expire_msg.insert(0, r["expire_msg"] or "")

        perms = json.loads(r["permissions"] or "[]")
        for key, var in self.perm_vars.items():
            var.set(key in perms)

        if r["role"] in ("admin", "superfiser", "dev_master"):
            if "backup_manage" in self.perm_vars:
                self.perm_vars["backup_manage"].set(True)

    def _save(self):
        name     = self.w_name.get().strip()
        username = self.w_username.get().strip()
        password = self.w_password.get()
        role     = self._role_key_from_combo()
        viewer   = self.current_user.get("role", "")

        if not name or not username:
            messagebox.showerror("خطأ", "الاسم واسم المستخدم مطلوبان", parent=self); return

        if role in ("trial", "dev_master") and viewer != "dev_master":
            messagebox.showerror(
                "غير مصرح",
                "إنشاء أو تغيير الدور إلى «تجريبي» أو «مطور عام» متاح لمطور النظام فقط.",
                parent=self,
            )
            return

        if not self.user_id and role in ("trial", "dev_master") and viewer != "dev_master":
            messagebox.showerror("غير مصرح", "لا يمكن تنفيذ هذا الإجراء.", parent=self); return

        # التحقق من تكرار اسم المستخدم
        existing = self.db.conn.execute(
            "SELECT id FROM users WHERE username=? AND id!=?",
            (username, self.user_id or 0)
        ).fetchone()
        if existing:
            messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل", parent=self); return

        if self.user_id:
            prev = self.db.conn.execute(
                "SELECT role FROM users WHERE id=?", (self.user_id,)
            ).fetchone()
            if prev:
                if prev["role"] in ("trial", "dev_master") and viewer != "dev_master":
                    messagebox.showerror("غير مصرح", "لا يمكن تعديل دور هذا الحساب.", parent=self)
                    return
                if prev["role"] == "dev_master" and role != "dev_master" and username == DEV_MASTER_USERNAME:
                    messagebox.showwarning(
                        "تنبيه",
                        "لا يُنصح بإزالة دور مطور النظام عن الحساب الثابت dev_system.",
                        parent=self,
                    )

        perms = json.dumps([k for k, v in self.perm_vars.items() if v.get()])
        max_logins = None
        expire_msg = ""
        if role == "trial":
            try:
                max_logins = int(self.w_max_logins.get())
            except Exception:
                max_logins = 5
            expire_msg = self.w_expire_msg.get().strip()

        if self.user_id:
            fields = "name=?, username=?, role=?, email=?, phone=?, permissions=?, max_logins=?, expire_msg=?"
            vals   = [name, username, role,
                      self.w_email.get().strip(), self.w_phone.get().strip(),
                      perms, max_logins, expire_msg]
            if password:
                fields += ", password=?"
                vals.append(self.db.set_password(password))
            vals.append(self.user_id)
            self.db.conn.execute(f"UPDATE users SET {fields} WHERE id=?", vals)
            action = f"تعديل مستخدم: {username}"
        else:
            if not password:
                messagebox.showerror("خطأ", "كلمة المرور مطلوبة للمستخدم الجديد", parent=self); return
            self.db.conn.execute("""
                INSERT INTO users (name, username, password, role, email, phone, permissions, max_logins, expire_msg)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (name, username, self.db.set_password(password), role,
                  self.w_email.get().strip(), self.w_phone.get().strip(),
                  perms, max_logins, expire_msg))
            action = f"إضافة مستخدم: {username} ({role})"

        self.db.conn.commit()
        self.db.log(self.current_user["username"], "مستخدم", action, self.current_user["username"])
        show_toast(self.master, f"تم الحفظ: {name} ✓", "gold")
        self.callback()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة السريالات (مطور النظام فقط)
# ════════════════════════════════════════════════════════════
class SerialLicensesPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        if (self.current_user or {}).get("role") != "dev_master":
            messagebox.showwarning("صلاحيات", "هذه الصفحة متاحة لمطور النظام فقط.", parent=self)
            try:
                self.app._navigate("dashboard")
            except Exception:
                pass
            return

        self._page_header("🔑  إدارة السريالات", "توليد سريالات وضبط وضع التفعيل (ملف السريالات أو مفتاح الجهاز)")

        wrap = ctk.CTkScrollableFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=12, pady=8)

        card = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            card,
            text="وضع التفعيل الظاهر عند العميل",
            font=("Arial", 13, "bold"),
            text_color=COLORS["gold_light"],
        ).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(
            card,
            text="ملف السريالات: دون إنترنت بعد التوزيع؛ مفتاح الجهاز: يُرسل معرّف الجهاز للدعم.",
            font=("Arial", 10),
            text_color=COLORS["text3"],
            wraplength=720,
            justify="right",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        cur = get_license_activation_mode(self.db)
        self.w_activation_mode = make_combo(
            card,
            ["file_pool — ملف السريالات", "machine — مفتاح الجهاز"],
            width=340,
        )
        self.w_activation_mode.pack(padx=14, pady=(0, 10), anchor="w")
        mode_map = {
            "file_pool": "file_pool — ملف السريالات",
            "machine": "machine — مفتاح الجهاز",
        }
        self.w_activation_mode.set(mode_map.get(cur, mode_map["file_pool"]))

        make_button(card, "💾  حفظ وضع التفعيل", self._save_activation_mode, "gold", 220).pack(
            padx=14, pady=(0, 12), anchor="w"
        )

        gen = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                           border_width=1, border_color=COLORS["border"])
        gen.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            gen,
            text="توليد سريال جديد (يُحفظ في الملف بجانب البرنامج)",
            font=("Arial", 13, "bold"),
            text_color=COLORS["gold_light"],
        ).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(
            gen,
            text="⚠️  الملفات law_office_serial_pool.json و law_office_serial_used.json تُنسَخ مع النسخة للعميل. "
            "تُحفظ مشفّرة على القرص (فتح الملف بالمحرر لا يُظهر السريالات كنص). لا تشارك ملف المخزون كاملاً إن أردت حصر السريالات غير المباعة.",
            font=("Arial", 10),
            text_color=COLORS["orange"],
            wraplength=720,
            justify="right",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        row1 = ctk.CTkFrame(gen, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row1, text="مدة الاشتراك:", font=("Arial", 11), text_color=COLORS["text2"]).pack(
            side="right", padx=(8, 0)
        )
        self.w_pool_kind = make_combo(
            row1,
            [
                "months_6 — 6 أشهر",
                "year_1 — سنة",
                "perpetual — دائم",
                "days_custom — أيام يدوي",
            ],
            width=260,
        )
        self.w_pool_kind.set("year_1 — سنة")
        self.w_pool_kind.pack(side="right")

        row2 = ctk.CTkFrame(gen, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(row2, text="عدد الأيام (عند «يدوي»):", font=("Arial", 11), text_color=COLORS["text2"]).pack(
            side="right", padx=(8, 0)
        )
        self.w_custom_days = make_entry(row2, "90", 100)
        self.w_custom_days.pack(side="right")

        make_button(gen, "➕  توليد وإضافة سريال", self._add_serial, "accent", 240).pack(
            padx=14, pady=(4, 8), anchor="w"
        )
        ctk.CTkLabel(
            gen,
            text="آخر سريال مُولّد (حدد النص وانسخ Ctrl+C):",
            font=("Arial", 11),
            text_color=COLORS["text2"],
        ).pack(anchor="e", padx=14, pady=(4, 2))
        self.w_last_serial = ctk.CTkEntry(
            gen,
            width=420,
            height=40,
            font=("Courier", 13, "bold"),
            fg_color=COLORS["bg3"],
            border_color=COLORS["gold_dark"],
            text_color=COLORS["gold_light"],
            justify="center",
        )
        self.w_last_serial.pack(padx=14, pady=(0, 12), fill="x")
        self.w_last_serial.insert(0, "")
        _enable_text_shortcuts(self.w_last_serial)

        paths = ctk.CTkFrame(wrap, fg_color=COLORS["panel2"], corner_radius=8)
        paths.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            paths,
            text=f"المخزون:\n{_serial_pool_path()}\n\nالمستخدم:\n{_serial_used_path()}",
            font=("Courier", 10),
            text_color=COLORS["text3"],
            justify="right",
        ).pack(padx=12, pady=10, anchor="e")

        self.pool_frame = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                                       border_width=1, border_color=COLORS["border"])
        self.pool_frame.pack(fill="both", expand=True, pady=(0, 8))
        ctk.CTkLabel(
            self.pool_frame,
            text="📋  سريالات جاهزة للبيع (لم تُستخدم)",
            font=("Arial", 12, "bold"),
            text_color=COLORS["text2"],
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.used_frame = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                                        border_width=1, border_color=COLORS["border"])
        self.used_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            self.used_frame,
            text="✅  سريالات مُفعّلة (مرتبطة بجهاز)",
            font=("Arial", 12, "bold"),
            text_color=COLORS["text2"],
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self._refresh_lists()

    def _save_activation_mode(self):
        label = self.w_activation_mode.get()
        if "machine" in label:
            m = "machine"
        else:
            m = "file_pool"
        self.db.set_setting("license_activation_mode", m)
        cfg_path = os.path.join(_app_base_dir(), CONFIG_FILENAME)
        cj = _read_json_safe(cfg_path, {})
        if not isinstance(cj, dict):
            cj = {}
        cj["license_activation_mode"] = m
        try:
            _atomic_write_json(cfg_path, cj)
        except OSError:
            pass
        self.db.log(
            self.current_user["username"],
            "إعدادات",
            f"تغيير وضع التفعيل إلى: {m}",
            self.current_user["username"],
        )
        show_toast(self.app, f"تم الحفظ: {m} ✓", "gold")

    def _parse_kind_from_combo(self) -> tuple:
        label = self.w_pool_kind.get()
        if "months_6" in label:
            return "months_6", None
        if "year_1" in label:
            return "year_1", None
        if "perpetual" in label:
            return "perpetual", None
        try:
            d = int(self.w_custom_days.get().strip())
        except Exception:
            d = 90
        return "days_custom", d

    def _add_serial(self):
        kind, cd = self._parse_kind_from_combo()
        serial, err = serial_pool_add_entry(kind, cd)
        if err:
            messagebox.showerror("خطأ", err, parent=self)
            return
        self.w_last_serial.delete(0, "end")
        self.w_last_serial.insert(0, serial)
        try:
            self.w_last_serial.select_range(0, "end")
            self.w_last_serial.focus_set()
        except Exception:
            pass
        show_toast(self.app, "تم توليد السريال — انسخه من المربع أعلاه", "green")
        self.db.log(
            self.current_user["username"],
            "سريالات",
            f"توليد سريال جديد ({kind})",
            self.current_user["username"],
        )
        self._refresh_lists()

    def _strip_frame_children_after_title(self, frame):
        """يحذف كل أبناء الإطار ما عدا أول عنصر (عنوان القسم) لتفادي تراكب قوائم."""
        ch = list(frame.winfo_children())
        for w in ch[1:]:
            try:
                w.destroy()
            except Exception:
                pass

    def _refresh_lists(self):
        self._strip_frame_children_after_title(self.pool_frame)
        self._strip_frame_children_after_title(self.used_frame)

        sp = ctk.CTkScrollableFrame(self.pool_frame, fg_color="transparent")
        sp.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        pool = _load_serial_pool_entries()
        if not pool:
            ctk.CTkLabel(sp, text="— لا توجد سريالات في المخزون —", text_color=COLORS["text3"]).pack(anchor="e", pady=12)
        for e in pool:
            row = ctk.CTkFrame(sp, fg_color=COLORS["bg3"], corner_radius=8)
            row.pack(fill="x", pady=(0, 8))
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=8, pady=8)
            s = (e.get("serial") or "").strip()
            k = e.get("kind", "")
            pr = "دائم" if e.get("perpetual") else f"{e.get('days', '')} يوم"
            ctk.CTkButton(
                inner,
                text="📋 نسخ",
                width=72,
                height=30,
                fg_color=COLORS["panel2"],
                hover_color=COLORS["hover"],
                font=("Arial", 11),
                command=lambda t=s: self._copy_clip(t),
            ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                inner,
                text=f"{s}\n{k}  |  {pr}",
                font=("Courier", 11),
                text_color=COLORS["gold_light"],
                anchor="e",
                justify="right",
            ).pack(side="right", fill="x", expand=True)

        su = ctk.CTkScrollableFrame(self.used_frame, fg_color="transparent")
        su.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        used = _load_serial_used_entries()
        if not used:
            ctk.CTkLabel(su, text="— لا يوجد تفعيل بعد —", text_color=COLORS["text3"]).pack(anchor="e", pady=12)
        for u in reversed(used[-200:]):
            row = ctk.CTkFrame(su, fg_color=COLORS["bg3"], corner_radius=8)
            row.pack(fill="x", pady=(0, 8))
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=8, pady=8)
            s = (u.get("serial") or "").strip()
            mid = (u.get("machine_id") or "")[:16]
            ex = (u.get("expires_at") or "")[:10]
            ctk.CTkLabel(
                inner,
                text=f"{s}\nجهاز: {mid}…  |  حتى {ex}",
                font=("Courier", 10),
                text_color=COLORS["text2"],
                anchor="e",
                justify="right",
            ).pack(fill="x")

    def _copy_clip(self, text: str):
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        show_toast(self.app, "تم النسخ ✓", "gold")

    def refresh(self):
        self._refresh_lists()


# ════════════════════════════════════════════════════════════
#  صفحة الإعدادات
# ════════════════════════════════════════════════════════════
class SettingsPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._settings_resize_after = None
        self._settings_dynamic_labels: list = []
        self._settings_dynamic_entries: list = []
        self._build()

    def _settings_col_wrap_from_width(self, inner_w: int) -> tuple[int, int]:
        """عرض حقول العمود وطول التفاف النصوص من عرض المنطقة الداخلة (عمودان)."""
        w = max(inner_w, 480)
        col = max(260, min(680, (w - 96) // 2))
        wrap = max(220, col - 28)
        return col, wrap

    def _sync_settings_sizes(self) -> None:
        self._settings_resize_after = None
        try:
            self.update_idletasks()
            inner_w = self.winfo_width()
            if inner_w < 120:
                inner_w = max(self.winfo_screenwidth() - 80, 560)
        except Exception:
            inner_w = 1100
        col, wrap = self._settings_col_wrap_from_width(inner_w)
        for lbl in self._settings_dynamic_labels:
            try:
                lbl.configure(wraplength=wrap)
            except Exception:
                pass
        for wdg in self._settings_dynamic_entries:
            try:
                wdg.configure(width=col)
            except Exception:
                pass

    def _on_settings_configure(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        if self._settings_resize_after is not None:
            try:
                self.after_cancel(self._settings_resize_after)
            except Exception:
                pass
        self._settings_resize_after = self.after(120, self._sync_settings_sizes)

    def _build(self):
        role = (self.current_user or {}).get("role", "")
        if role not in ("dev_master", "admin", "superfiser") and not self.has_perm("settings_manage"):
            messagebox.showwarning("صلاحيات", "لا تملك صلاحية الدخول إلى الإعدادات.", parent=self)
            try:
                self.app._navigate("dashboard")
            except Exception:
                pass
            return
        self._page_header("⚙️  الإعدادات", "إعدادات النظام وقاعدة البيانات")

        self.bind("<Configure>", self._on_settings_configure)

        sc = ctk.CTkScrollableFrame(self, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=12, pady=8)
        sc.grid_columnconfigure((0, 1), weight=1)
        for r in range(0, 5):
            sc.grid_rowconfigure(r, weight=0)

        try:
            self.update_idletasks()
            _col0, _wrap0 = self._settings_col_wrap_from_width(self.winfo_width() or self.winfo_screenwidth())
        except Exception:
            _col0, _wrap0 = 400, 360

        def section(parent, title, row, col):
            f = ctk.CTkFrame(parent, fg_color=COLORS["panel"],
                             corner_radius=10,
                             border_width=1,
                             border_color=COLORS["border"])
            f.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(f, text=title, font=("Arial", 14, "bold"),
                         text_color=COLORS["gold_light"]).pack(anchor="w", padx=14, pady=(14,8))
            return f

        # ─── مسار قاعدة البيانات ────
        db_frame = section(sc, "💾  قاعدة البيانات", 0, 0)
        current_path = self.db.path
        lb_db_path = ctk.CTkLabel(
            db_frame,
            text=f"📍 المسار الحالي:\n{current_path}",
            text_color=COLORS["text2"],
            font=("Arial", 11),
            wraplength=_wrap0,
            justify="right",
        )
        lb_db_path.pack(anchor="w", padx=14, pady=(0, 10))
        self._settings_dynamic_labels.append(lb_db_path)
        lb_db_note = ctk.CTkLabel(
            db_frame,
            text="ملاحظة: مشاركة الشبكة قد تسبب بطء/قفلات مع SQLite.\nلأفضل نتيجة: سيرفر قاعدة بيانات أو جهاز مستضيف واحد.",
            text_color=COLORS["text3"],
            font=("Arial", 10, "bold"),
            justify="right",
            wraplength=_wrap0,
        )
        lb_db_note.pack(anchor="w", padx=14, pady=(0, 10))
        self._settings_dynamic_labels.append(lb_db_note)

        ctk.CTkLabel(db_frame, text="اختر مسار جديد لحفظ قاعدة البيانات:",
                     text_color=COLORS["text2"], font=("Arial", 12)).pack(anchor="w", padx=14)
        self.w_db_path = make_entry(db_frame, "المسار الجديد...", _col0)
        self.w_db_path.pack(padx=14, pady=6)
        self.w_db_path.insert(0, str(Path(current_path).parent))
        self._settings_dynamic_entries.append(self.w_db_path)

        ctk.CTkLabel(db_frame, text="اسم ملف قاعدة البيانات:",
                     text_color=COLORS["text2"], font=("Arial", 12)).pack(anchor="w", padx=14)
        self.w_db_name = make_entry(db_frame, DB_FILENAME, _col0)
        self.w_db_name.pack(padx=14, pady=6)
        self.w_db_name.insert(0, Path(current_path).name)
        self._settings_dynamic_entries.append(self.w_db_name)

        btn_row = ctk.CTkFrame(db_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=8)
        make_button(btn_row, "📂  استعراض", self._browse_db, "ghost", 130).pack(side="right", padx=4)
        make_button(btn_row, "↩️  استعادة المسار الافتراضي", self._reset_db_path_default, "ghost", 210).pack(side="right", padx=4)
        make_button(btn_row, "💾  نقل قاعدة البيانات", self._move_db, "gold", 200).pack(side="right", padx=4)

        # ─── الترخيص والتفعيل ────
        lic_frame = section(sc, "🔑  الترخيص والتفعيل", 0, 1)
        machine_id = _get_machine_id()
        is_active = check_license(self.db)
        sub_ui = _license_subscription_ui(self.db)
        warn_lic = sub_ui.get("show_warning")
        warn_txt = (
            "⚠️  البرنامج على وشك انتهاء الاشتراك قم بالتواصل مع المسؤول للتجديد"
            if warn_lic
            else ""
        )
        self._lic_warn_lbl = ctk.CTkLabel(
            lic_frame,
            text=warn_txt,
            font=("Arial", 11, "bold"),
            text_color=COLORS["orange"],
            wraplength=_wrap0,
            justify="right",
        )
        self._lic_warn_lbl.pack(padx=14, pady=(4, 2))
        self._settings_dynamic_labels.append(self._lic_warn_lbl)
        sub_line = (
            f"أيام الاشتراك: {sub_ui['total_str']}  |  المتبقي: {sub_ui['remaining_str']}"
        )
        lb_sub = ctk.CTkLabel(
            lic_frame,
            text=sub_line,
            font=("Arial", 11),
            text_color=COLORS["text2"],
            wraplength=_wrap0,
            justify="right",
        )
        lb_sub.pack(padx=14, pady=(0, 6))
        self._settings_dynamic_labels.append(lb_sub)
        status_color = COLORS["green"] if is_active else COLORS["red"]
        status_text = "✅  البرنامج مُفعَّل على هذا الجهاز" if is_active else "❌  البرنامج غير مُفعَّل"
        ctk.CTkLabel(lic_frame, text=status_text, font=("Arial", 12, "bold"),
                     text_color=status_color).pack(padx=14, pady=(4, 8))
        ctk.CTkLabel(lic_frame, text="معرف الجهاز:", font=("Arial", 11),
                     text_color=COLORS["text3"]).pack(anchor="e", padx=14)
        serial_disp = _format_serial(machine_id)
        id_row = ctk.CTkFrame(lic_frame, fg_color="transparent")
        id_row.pack(fill="x", padx=14, pady=(2, 10))
        ctk.CTkLabel(id_row, text=serial_disp, font=("Courier", 13, "bold"),
                     text_color=COLORS["gold_light"]).pack(side="right")
        ctk.CTkButton(
            id_row,
            text="📋 نسخ",
            width=70,
            height=26,
            fg_color=COLORS["panel2"],
            hover_color=COLORS["hover"],
            text_color=COLORS["text2"],
            font=("Arial", 10),
            command=lambda: (self.clipboard_clear(), self.clipboard_append(serial_disp),
                             show_toast(self.app, "تم النسخ ✓", "gold")),
        ).pack(side="left")
        make_button(
            lic_frame,
            "⏳  تمديد فترة الاشتراك",
            lambda: ActivationWindow(
                self.app,
                self.db,
                lambda: show_toast(self.app, "تم تحديث الاشتراك ✓", "green"),
                extend_mode=True,
            ),
            "gold",
            240,
        ).pack(padx=14, pady=8)

        # ─── بيانات المكتب ────
        off_frame = section(sc, "🏢  بيانات المكتب", 1, 0)
        fields = [
            ("office_name", "اسم المكتب", "مكتب المحاماة"),
            ("lawyer_name", "المحامي المسؤول", "المحامي"),
            ("license_num", "رقم الترخيص المهني", ""),
            ("office_phone", "هاتف المكتب", ""),
            ("office_address", "عنوان المكتب", ""),
        ]
        self.office_widgets = {}
        for key, lbl, default in fields:
            ctk.CTkLabel(off_frame, text=lbl, font=("Arial", 12),
                         text_color=COLORS["text2"]).pack(anchor="w", padx=14, pady=(6, 2))
            e = make_entry_rtl(off_frame, default, _col0)
            e.pack(padx=14, pady=(0, 4))
            e.insert(0, self.db.get_setting(key, default))
            self.office_widgets[key] = e
            self._settings_dynamic_entries.append(e)
        make_button(off_frame, "💾  حفظ بيانات المكتب", self._save_office, "gold", 220).pack(padx=14, pady=12)

        # ─── الثيمات ────
        theme_frame = section(sc, "🎨  ثيمات البرنامج", 2, 0)
        sc.grid_rowconfigure(2, weight=0)
        ctk.CTkLabel(theme_frame, text="اختر مظهر البرنامج المفضل لديك",
                     text_color=COLORS["text2"], font=("Arial", 11)).pack(padx=14, pady=(0,8))

        themes_grid = ctk.CTkFrame(theme_frame, fg_color="transparent")
        themes_grid.pack(fill="x", padx=10, pady=4)

        for i, (tk_key, (tk_name, tk_colors)) in enumerate(ALL_THEMES.items()):
            is_cur = (tk_key == CURRENT_THEME)
            btn_frame = ctk.CTkFrame(themes_grid,
                                     fg_color=tk_colors["panel"],
                                     corner_radius=8,
                                     border_width=2,
                                     border_color=tk_colors["gold"] if is_cur else tk_colors["border"])
            btn_frame.grid(row=i//2, column=i%2, padx=4, pady=4, sticky="ew")
            themes_grid.grid_columnconfigure(0, weight=1)
            themes_grid.grid_columnconfigure(1, weight=1)

            def _pick(k=tk_key):
                self.app._set_theme(k)

            dots = ctk.CTkFrame(btn_frame, fg_color="transparent")
            dots.pack(side="right", padx=8, pady=10)
            for ck in ["gold", "accent", "green"]:
                ctk.CTkFrame(dots, fg_color=tk_colors[ck],
                             width=12, height=12, corner_radius=6).pack(side="right", padx=1)

            ctk.CTkLabel(btn_frame, text=("✅ " if is_cur else "") + tk_name,
                         font=("Arial", 11, "bold"),
                         text_color=tk_colors["gold_light"]).pack(side="right", padx=10, pady=10)
            btn_frame.bind("<Button-1>", lambda e, fn=_pick: fn())

        make_button(theme_frame, "🎨  اختر ثيماً", self.app._open_theme_picker, "gold", 220).pack(padx=14, pady=12)

        # ─── الأمان ────
        sec_frame = section(sc, "🔐  الأمان", 2, 1)
        ctk.CTkLabel(sec_frame, text="مدة انتهاء الجلسة (دقائق)",
                     text_color=COLORS["text2"], font=("Arial", 12)).pack(anchor="w", padx=14, pady=(10,2))
        self.w_timeout = make_entry(sec_frame, "60", _col0)
        self.w_timeout.pack(padx=14, pady=(0,8))
        self.w_timeout.insert(0, self.db.get_setting("session_timeout", "60"))
        self._settings_dynamic_entries.append(self.w_timeout)

        ctk.CTkLabel(sec_frame, text="عدد محاولات الدخول قبل الحجب",
                     text_color=COLORS["text2"], font=("Arial", 12)).pack(anchor="w", padx=14, pady=(0,2))
        self.w_max_attempts = make_entry(sec_frame, "5", _col0)
        self.w_max_attempts.pack(padx=14, pady=(0,8))
        self.w_max_attempts.insert(0, self.db.get_setting("max_attempts", "5"))
        self._settings_dynamic_entries.append(self.w_max_attempts)

        ctk.CTkLabel(sec_frame, text="العملة",
                     text_color=COLORS["text2"], font=("Arial", 12)).pack(anchor="w", padx=14, pady=(0,2))
        self.w_currency = make_combo(sec_frame,
            ["SAR - ريال سعودي","EGP - جنيه مصري","AED - درهم إماراتي","KWD - دينار كويتي","USD - دولار"], _col0)
        self.w_currency.pack(padx=14, pady=(0,8))
        self.w_currency.set(self.db.get_setting("currency", "SAR - ريال سعودي"))
        self._settings_dynamic_entries.append(self.w_currency)

        make_button(sec_frame, "💾  حفظ إعدادات الأمان", self._save_security, "gold", 220).pack(padx=14, pady=12)

        self.after(50, self._sync_settings_sizes)

    def _browse_db(self):
        folder = filedialog.askdirectory(title="اختر مجلد قاعدة البيانات")
        if folder:
            self.w_db_path.delete(0, "end")
            self.w_db_path.insert(0, folder)

    def _move_db(self):
        new_dir  = self.w_db_path.get().strip()
        new_name = self.w_db_name.get().strip() or DB_FILENAME
        if not new_dir:
            messagebox.showerror("خطأ", "أدخل المسار الجديد", parent=self); return

        new_path = os.path.join(new_dir, new_name)
        try:
            os.makedirs(new_dir, exist_ok=True)
            src_path = os.path.normcase(os.path.normpath(self.db.path))
            dst_path = os.path.normcase(os.path.normpath(new_path))
            if src_path == dst_path:
                messagebox.showinfo("تنبيه", "هذا هو نفس مسار قاعدة البيانات الحالية.", parent=self)
                return
            # استخدم SQLite backup API لتفادي مشاكل نسخ الملف وهو مفتوح على ويندوز.
            self.db.export_backup(new_path)
            try:
                self.db.export_documents_backup(companion_documents_db_path(new_path))
            except Exception as e:
                messagebox.showwarning(
                    "تنبيه",
                    f"تم نسخ القاعدة الرئيسية.\nتعذر نسخ قاعدة المستندات المنفصلة:\n{e}",
                    parent=self,
                )
            # حفظ المسار في ملف إعداد خارجي حتى تُفتح نفس القاعدة في كل الأجهزة
            try:
                self.app.set_db_path_config(new_path)
            except Exception:
                pass
            # احتفاظ اختياري داخل القاعدة (للعرض فقط)
            self.db.set_setting("db_path", new_path)
            messagebox.showinfo("نجاح",
                f"تم نسخ قاعدة البيانات إلى:\n{new_path}\n\nأعد تشغيل البرنامج لتطبيق مسار قاعدة البيانات الجديد.",
                parent=self)
            self.db.log(self.current_user["username"], "إعدادات",
                        f"نقل قاعدة البيانات إلى: {new_path}", self.current_user["username"])
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل النقل:\n{e}", parent=self)

    def _reset_db_path_default(self):
        """إرجاع مسار القاعدة للمسار الافتراضي داخل مجلد التشغيل."""
        default_path = os.path.join(self.app.base_dir, DB_FILENAME)
        default_dir = str(Path(default_path).parent)
        default_name = Path(default_path).name
        try:
            self.w_db_path.delete(0, "end")
            self.w_db_path.insert(0, default_dir)
            self.w_db_name.delete(0, "end")
            self.w_db_name.insert(0, default_name)
        except Exception:
            pass
        try:
            self.app.set_db_path_config(default_path)
            self.db.set_setting("db_path", default_path)
            messagebox.showinfo(
                "تمت الاستعادة",
                f"تمت استعادة مسار قاعدة البيانات إلى الافتراضي:\n{default_path}\n\n"
                "إذا كانت قاعدة البيانات الفعلية في مسار آخر، استخدم زر (نقل قاعدة البيانات) أولاً ثم أعد التشغيل.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر استعادة المسار الافتراضي:\n{e}", parent=self)

    def _save_office(self):
        for key, w in self.office_widgets.items():
            self.db.set_setting(key, w.get().strip())
        show_toast(self.app, "تم حفظ بيانات المكتب ✓", "gold")

    def _save_security(self):
        self.db.set_setting("session_timeout", self.w_timeout.get().strip())
        self.db.set_setting("max_attempts", self.w_max_attempts.get().strip())
        self.db.set_setting("currency", self.w_currency.get())
        show_toast(self.app, "تم حفظ إعدادات الأمان ✓", "gold")

    def _show_license_info(self):
        """عرض معلومات الترخيص"""
        machine_id = _get_machine_id()
        serial_disp = _format_serial(machine_id)
        is_active = check_license(self.db)
        status = "✅ مُفعَّل" if is_active else "❌ غير مُفعَّل"
        extra = ""
        if _SESSION_LICENSE_BYPASS:
            extra += "\nوضع جلسة (تخطي مطور): بدون تفعيل محفوظ — يُطلب التفعيل بعد إغلاق البرنامج."
        src = (self.db.get_setting("license_source", "") or "").strip()
        if src == "file_pool":
            if (self.db.get_setting("license_perpetual", "") or "").strip() == "1":
                extra += "\nنوع التفعيل: سريال ملف (دائم)"
            else:
                exp = (self.db.get_setting("license_expires_at", "") or "").strip()
                if exp:
                    extra += f"\nصالح حتى: {exp}"
        foot = (
            "أرسل معرف الجهاز للدعم عند التفعيل بالمفتاح التقليدي."
            if get_license_activation_mode(self.db) == "machine"
            else ""
        )
        msg = f"حالة الترخيص: {status}{extra}\n\nمعرف الجهاز:\n{serial_disp}"
        if foot:
            msg += f"\n\n{foot}"
        messagebox.showinfo("معلومات الترخيص", msg, parent=self)


# ════════════════════════════════════════════════════════════
#  صفحة رقم المكتب / الفرع
# ════════════════════════════════════════════════════════════
class OfficeNumberPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self.stale_seconds = 30
        self._build()

    def _build(self):
        role = (self.current_user or {}).get("role", "")
        if role not in ("dev_master", "admin", "superfiser"):
            messagebox.showwarning("صلاحيات", "هذه الصفحة متاحة للسوبرفايزر والأدمن فقط.", parent=self)
            try:
                self.app._navigate("dashboard")
            except Exception:
                pass
            return

        self._page_header("🏢  رقم المكتب", "تعريف رقم الفرع وعنوانه لهذه النسخة")

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=12, pady=8)
        wrap.grid_columnconfigure((0, 1), weight=1)
        wrap.grid_rowconfigure(0, weight=2)
        wrap.grid_rowconfigure(1, weight=1)

        card = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))

        ctk.CTkLabel(card, text="رقم المكتب / الفرع", font=("Arial", 12),
                     text_color=COLORS["text2"]).pack(anchor="w", padx=14, pady=(14, 2))
        self.w_branch_num = make_entry_rtl(card, "مثال: 1 أو فرع الرياض", 360)
        self.w_branch_num.pack(padx=14, pady=(0, 8))
        # لا نقرأ من settings لأنها مشتركة بين كل الأجهزة
        if getattr(self.app, "app_id", None):
            cur = self.db.get_device_branch(self.app.app_id)
            if cur and cur["branch_number"]:
                self.w_branch_num.insert(0, cur["branch_number"])

        ctk.CTkLabel(card, text="عنوان الفرع", font=("Arial", 12),
                     text_color=COLORS["text2"]).pack(anchor="w", padx=14, pady=(6, 2))
        self.w_branch_addr = make_entry_rtl(card, "العنوان...", 360)
        self.w_branch_addr.pack(padx=14, pady=(0, 12))
        if getattr(self.app, "app_id", None):
            cur = self.db.get_device_branch(self.app.app_id)
            if cur and cur["branch_address"]:
                self.w_branch_addr.insert(0, cur["branch_address"])

        year_row = ctk.CTkFrame(card, fg_color="transparent")
        year_row.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(year_row, text="السنة (اختياري)", font=("Arial", 12),
                     text_color=COLORS["text2"]).pack(side="right", padx=(0, 8))
        self.w_branch_year = make_entry(year_row, str(date.today().year), 110)
        self.w_branch_year.pack(side="right", padx=(6, 10))
        try:
            if getattr(self.app, "app_id", None):
                cur = self.db.get_device_branch(self.app.app_id)
                if cur and cur["branch_year"]:
                    self.w_branch_year.delete(0, "end")
                    self.w_branch_year.insert(0, str(cur["branch_year"]))
        except Exception:
            pass
        # أزرار مصغرة بجانب السنة بدون تمرير خصائص متعارضة.
        make_button(year_row, "➕ إضافة", self._save, "gold", 86, height=30).pack(side="right", padx=3)
        make_button(year_row, "✅ اعتماد", self._use_selected, "accent", 86, height=30).pack(side="right", padx=3)
        make_button(year_row, "✏️ تعديل", self._edit_selected, "accent", 86, height=30).pack(side="right", padx=3)
        make_button(year_row, "🗑️ حذف", self._delete_selected, "red", 78, height=30).pack(side="right", padx=3)

        # صف أزرار كامل (ثابت وبدون أي خصائص قد تسبب تضارب).
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(0, 14))
        make_button(btns, "➕  إضافة مكتب", self._save, "gold", 160).pack(side="right", padx=4)
        make_button(btns, "🔄  تحديث", self.refresh, "ghost", 120).pack(side="right", padx=4)
        make_button(btns, "✅  اعتماد المحدد", self._use_selected, "accent", 170).pack(side="right", padx=4)
        make_button(btns, "✏️  تعديل المحدد", self._edit_selected, "accent", 170).pack(side="right", padx=4)
        make_button(btns, "🗑️  حذف المحدد", self._delete_selected, "red", 150).pack(side="right", padx=4)

        # ─── جدول كل الفروع المسجلة ───
        grid_card = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                                 border_width=1, border_color=COLORS["border"])
        grid_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
        ctk.CTkLabel(grid_card, text="📌  جميع الأفرع المسجلة", font=("Arial", 13, "bold"),
                     text_color=COLORS["gold_light"]).pack(anchor="w", padx=14, pady=(14, 6))
        cols = ("#", "رقم الفرع", "العنوان", "السنة", "تاريخ الإضافة", "المضيف")
        widths = (40, 120, 240, 80, 150, 100)
        self.branches_tree, _ = styled_treeview(grid_card, cols, cols, widths)
        self.branches_tree.pack_configure(padx=12, pady=(0, 12))

        # ─── جدول الأفرع المتصلة الآن ───
        online_card = ctk.CTkFrame(wrap, fg_color=COLORS["panel"], corner_radius=10,
                                   border_width=1, border_color=COLORS["border"])
        online_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 6))
        ctk.CTkLabel(online_card, text="🟢  الأفرع المتصلة الآن", font=("Arial", 13, "bold"),
                     text_color=COLORS["gold_light"]).pack(anchor="w", padx=14, pady=(14, 6))
        ocols = ("#", "المستخدم", "الحالة", "آخر نشاط", "رقم الفرع", "العنوان", "السنة", "app_id")
        owidths = (40, 100, 80, 140, 100, 200, 64, 130)
        self.online_tree, _ = styled_treeview(online_card, ocols, ocols, owidths)
        self.online_tree.pack_configure(padx=12, pady=(0, 12))
        for cn, st in (("#", False), ("المستخدم", False), ("الحالة", False), ("السنة", False), ("app_id", False)):
            try:
                self.online_tree.column(cn, stretch=st)
            except tk.TclError:
                pass
        for cn in ("العنوان", "آخر نشاط", "رقم الفرع"):
            try:
                self.online_tree.column(cn, stretch=True)
            except tk.TclError:
                pass

        self.refresh()

    def _selected_branch_id(self) -> int | None:
        sel = self.branches_tree.focus() or (self.branches_tree.selection()[0] if self.branches_tree.selection() else "")
        if not sel:
            return None
        try:
            return int(sel)
        except Exception:
            return None

    def _save(self):
        role = (self.current_user or {}).get("role", "")
        if role not in ("dev_master", "admin", "superfiser"):
            messagebox.showwarning("صلاحيات", "ليس لديك صلاحية.", parent=self)
            return
        bnum = self.w_branch_num.get().strip()
        baddr = self.w_branch_addr.get().strip()
        byear_raw = (self.w_branch_year.get() or "").strip()
        byear = None
        if byear_raw:
            try:
                byear = int(byear_raw)
            except Exception:
                byear = None

        # حفظ كفرع داخل الجدول وربطه بالـ app_id المحلي
        app_id = getattr(self.app, "app_id", None) or ""
        if not app_id:
            try:
                self.app._start_online_presence()
                app_id = getattr(self.app, "app_id", None) or ""
            except Exception:
                app_id = ""
        if not app_id:
            messagebox.showerror("خطأ", "تعذر إنشاء معرف الجهاز (app_id).", parent=self)
            return

        if not bnum:
            messagebox.showerror("خطأ", "رقم/اسم المكتب مطلوب.", parent=self)
            return
        branch_id = self.db.add_branch_record(bnum, baddr, byear, created_by=self.current_user.get("username", ""))
        self.db.set_device_branch(app_id, branch_id, updated_by=self.current_user.get("username", ""))
        self.db.log(self.current_user["username"], "فرع", f"إضافة/اعتماد فرع: {bnum} - {baddr}", self.current_user["username"])
        self.refresh()
        try:
            self.app.refresh_all_open_pages()
        except Exception:
            pass
        show_toast(self.app, "تم حفظ واعتماد المكتب ✓", "gold")

    def _use_selected(self):
        app_id = getattr(self.app, "app_id", None) or ""
        if not app_id:
            messagebox.showerror("خطأ", "تعذر إنشاء معرف الجهاز (app_id).", parent=self)
            return
        sel = self.branches_tree.focus() or (self.branches_tree.selection()[0] if self.branches_tree.selection() else "")
        if not sel:
            messagebox.showinfo("تنبيه", "اختر مكتباً من الجدول أولاً.", parent=self)
            return
        try:
            branch_id = int(sel)
        except Exception:
            messagebox.showerror("خطأ", "تعذر قراءة المكتب المحدد.", parent=self)
            return
        self.db.set_device_branch(app_id, branch_id, updated_by=self.current_user.get("username", ""))
        cur = self.db.get_device_branch(app_id)
        try:
            if cur:
                self.w_branch_num.delete(0, "end")
                self.w_branch_num.insert(0, cur["branch_number"] or "")
                self.w_branch_addr.delete(0, "end")
                self.w_branch_addr.insert(0, cur["branch_address"] or "")
                self.w_branch_year.delete(0, "end")
                self.w_branch_year.insert(0, str(cur["branch_year"] or ""))
        except Exception:
            pass
        self.refresh()
        try:
            self.app.refresh_all_open_pages()
        except Exception:
            pass
        show_toast(self.app, "تم اعتماد المكتب لهذا الجهاز ✓", "green")

    def _edit_selected(self):
        bid = self._selected_branch_id()
        if not bid:
            messagebox.showinfo("تنبيه", "اختر مكتباً من الجدول أولاً.", parent=self)
            return
        row = self.db.get_branch_record(bid)
        if not row:
            messagebox.showwarning("تنبيه", "لم يتم العثور على هذا المكتب. سيتم تحديث القائمة.", parent=self)
            self.refresh()
            return
        BranchRecordDialog(self, self.db, bid, dict(row), self.current_user, self.refresh)

    def _delete_selected(self):
        bid = self._selected_branch_id()
        if not bid:
            messagebox.showinfo("تنبيه", "اختر مكتباً من الجدول أولاً.", parent=self)
            return
        row = self.db.get_branch_record(bid)
        if not row:
            self.refresh()
            return
        if messagebox.askyesno(
            "تأكيد الحذف",
            f"حذف المكتب: {row['branch_number']} ؟\nسيتم فك اعتماده من أي جهاز كان يستخدمه.",
            parent=self,
        ):
            try:
                self.db.delete_branch_record(bid)
                self.db.log(self.current_user["username"], "فرع", f"حذف فرع id={bid}", self.current_user["username"])
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحذف:\n{e}", parent=self)
                return
            self.refresh()
            try:
                self.app.refresh_all_open_pages()
            except Exception:
                pass
            show_toast(self.app, "تم حذف المكتب ✓", "red")

    def refresh(self):
        try:
            if hasattr(self, "branches_tree"):
                self.branches_tree.delete(*self.branches_tree.get_children())
                rows = self.db.list_branch_records()
                for i, r in enumerate(rows):
                    dt = (r["created_at"] or "")[:16] if "created_at" in r.keys() else ""
                    yr = r["branch_year"] if "branch_year" in r.keys() else ""
                    addr = r["branch_address"] or ""
                    self.branches_tree.insert(
                        "",
                        "end",
                        iid=str(r["id"]),
                        values=(
                            i + 1,
                            r["branch_number"],
                            _ellipsis_text(addr, 48),
                            yr or "-",
                            dt,
                            _ellipsis_text(str(r["created_by"] or ""), 24),
                        ),
                        tags=("odd" if i % 2 == 0 else "even",),
                    )

            if hasattr(self, "online_tree"):
                self.online_tree.delete(*self.online_tree.get_children())
                rows = self.db.get_online_branches(stale_seconds=self.stale_seconds)
                for i, (app_id, username, status, last_seen, bnum, baddr, byear) in enumerate(rows):
                    tag = "active" if status == "online" else ("odd" if i % 2 == 0 else "even")
                    aid = _ellipsis_text(str(app_id or ""), 34, middle=True)
                    self.online_tree.insert(
                        "",
                        "end",
                        iid=f"o_{i}",
                        values=(
                            i + 1,
                            _ellipsis_text(str(username or ""), 28),
                            status,
                            (last_seen or "")[:16],
                            _ellipsis_text(str(bnum or "-"), 20),
                            _ellipsis_text(str(baddr or "-"), 40),
                            byear or "-",
                            aid,
                        ),
                        tags=(tag,),
                    )
        except Exception:
            pass


class BranchRecordDialog(ctk.CTkToplevel):
    def __init__(self, parent, db: Database, branch_id: int, branch_row: dict, user: dict, on_done):
        super().__init__(parent)
        self.db = db
        self.branch_id = branch_id
        self.branch_row = branch_row or {}
        self.user = user or {}
        self.on_done = on_done
        self.title("تعديل مكتب / فرع")
        self.configure(fg_color=COLORS["bg"])
        center_window(self, 520, 360)
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="✏️  تعديل بيانات المكتب", font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=14)
        sc = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=10,
                          border_width=1, border_color=COLORS["border"])
        sc.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def lbl(t):
            ctk.CTkLabel(sc, text=t, font=("Arial", 12), text_color=COLORS["text2"]).pack(anchor="w", padx=14, pady=(10, 2))

        lbl("رقم المكتب / الفرع *")
        self.w_num = make_entry_rtl(sc, "", 420)
        self.w_num.pack(padx=14, pady=(0, 6))
        self.w_num.insert(0, self.branch_row.get("branch_number", "") or "")

        lbl("العنوان")
        self.w_addr = make_entry_rtl(sc, "", 420)
        self.w_addr.pack(padx=14, pady=(0, 6))
        self.w_addr.insert(0, self.branch_row.get("branch_address", "") or "")

        lbl("السنة (اختياري)")
        self.w_year = make_entry(sc, "", 180)
        self.w_year.pack(padx=14, pady=(0, 10), anchor="w")
        by = self.branch_row.get("branch_year", "")
        if by is None:
            by = ""
        self.w_year.insert(0, str(by))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=10)
        make_button(btns, "إلغاء", self.destroy, "ghost", 120).pack(side="right", padx=4)
        make_button(btns, "💾  حفظ", self._save, "gold", 140).pack(side="right", padx=4)

    def _save(self):
        num = (self.w_num.get() or "").strip()
        if not num:
            messagebox.showerror("خطأ", "رقم/اسم المكتب مطلوب.", parent=self)
            return
        addr = (self.w_addr.get() or "").strip()
        yraw = (self.w_year.get() or "").strip()
        y = None
        if yraw:
            try:
                y = int(yraw)
            except Exception:
                y = None
        try:
            self.db.update_branch_record(self.branch_id, num, addr, y)
            self.db.log(self.user.get("username", "system"), "فرع", f"تعديل فرع id={self.branch_id}", self.user.get("username", "system"))
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل الحفظ:\n{e}", parent=self)
            return
        try:
            if callable(self.on_done):
                self.on_done()
        except Exception:
            pass
        self.destroy()


# ════════════════════════════════════════════════════════════
#  صفحة النسخ الاحتياطي والتصدير والاستيراد
# ════════════════════════════════════════════════════════════
class DataBackupPage(BasePage):
    """تصدير واستيراد قاعدة البيانات، ونسخ احتياطي تلقائي بوقت يومي."""

    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        self._page_header(
            "💾  النسخ الاحتياطي والبيانات",
            "تصدير أو استيراد قاعدة البيانات، وجدولة نسخ احتياطي تلقائي يومي في وقت تحدده",
        )

        wrap = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=0)
        wrap.pack(fill="both", expand=True, padx=12, pady=8)

        self.permission_lbl = ctk.CTkLabel(
            wrap,
            text="—",
            text_color=COLORS["text3"],
            font=("Arial", 11, "bold"),
            justify="right",
            wraplength=720,
        )
        self.permission_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=4, pady=4)
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        # ─── تصدير / استيراد ───
        self.io_frame = ctk.CTkFrame(
            row,
            fg_color=COLORS["panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.io_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        ctk.CTkLabel(
            self.io_frame,
            text="📤📥  التصدير والاستيراد",
            font=("Arial", 14, "bold"),
            text_color=COLORS["gold_light"],
        ).pack(anchor="w", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            self.io_frame,
            text="ملف .db كامل لقاعدة البيانات. التصدير ينسخ لحظياً عبر واجهة SQLite؛ الاستيراد يستبدل البيانات الحالية.",
            text_color=COLORS["text2"],
            font=("Arial", 11),
            wraplength=340,
            justify="right",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        self.btn_export = make_button(
            self.io_frame,
            "📤  تصدير قاعدة البيانات",
            self._export_db,
            "accent",
            260,
        )
        self.btn_export.pack(padx=14, pady=6)

        self.btn_import = make_button(
            self.io_frame,
            "📥  استيراد قاعدة البيانات (استعادة)",
            self._import_db,
            "ghost",
            260,
        )
        self.btn_import.pack(padx=14, pady=(6, 16))

        # ─── نسخ تلقائي بوقت محدد ───
        self.auto_frame = ctk.CTkFrame(
            row,
            fg_color=COLORS["panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.auto_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        ctk.CTkLabel(
            self.auto_frame,
            text="⏰  النسخ الاحتياطي التلقائي",
            font=("Arial", 14, "bold"),
            text_color=COLORS["gold_light"],
        ).pack(anchor="w", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            self.auto_frame,
            text="يُنشأ ملف نسخة يومياً عند الوصول إلى الوقت المحدد (البرنامج يعمل في الخلفية).",
            text_color=COLORS["text2"],
            font=("Arial", 11),
            wraplength=340,
            justify="right",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.auto_var = ctk.BooleanVar(value=False)
        self.cb_auto = ctk.CTkCheckBox(
            self.auto_frame,
            text="تفعيل النسخ التلقائي اليومي",
            variable=self.auto_var,
            text_color=COLORS["text2"],
            font=("Arial", 12, "bold"),
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_dark"],
            border_color=COLORS["border"],
        )
        self.cb_auto.pack(anchor="w", padx=14, pady=(2, 8))

        time_row = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        time_row.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(
            time_row,
            text="وقت التنفيذ اليومي (ساعة:دقيقة)",
            text_color=COLORS["text2"],
            font=("Arial", 12),
        ).pack(side="right")
        self.w_auto_time = make_entry(time_row, "23:00", 120)
        self.w_auto_time.pack(side="right", padx=(8, 0))

        ctk.CTkLabel(
            self.auto_frame,
            text="مجلد حفظ النسخ (إن تركت فارغاً يُستخدم مجلد backups بجانب قاعدة البيانات)",
            text_color=COLORS["text2"],
            font=("Arial", 11),
            wraplength=340,
            justify="right",
        ).pack(anchor="w", padx=14, pady=(0, 6))

        dir_row = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        dir_row.pack(fill="x", padx=14, pady=(0, 8))
        self.w_auto_dir = make_entry(dir_row, "", 240)
        self.w_auto_dir.pack(side="right", fill="x", expand=True)
        self.btn_browse_dir = make_button(dir_row, "📂 استعراض", self._browse_auto_dir, "ghost", 100)
        self.btn_browse_dir.pack(side="right", padx=(6, 0))

        self.lbl_auto_state = ctk.CTkLabel(
            self.auto_frame,
            text="—",
            text_color=COLORS["text3"],
            font=("Arial", 11, "bold"),
            justify="right",
            wraplength=340,
        )
        self.lbl_auto_state.pack(anchor="w", padx=14, pady=(4, 14))

        btn_row = ctk.CTkFrame(wrap, fg_color="transparent")
        btn_row.pack(fill="x", padx=6, pady=8)
        self.btn_save = make_button(
            btn_row,
            "💾  حفظ إعدادات النسخ التلقائي",
            self._save_auto_settings,
            "gold",
            300,
        )
        self.btn_save.pack(side="right", padx=10)

        self.refresh()

    def refresh(self):
        can_manage = self.has_perm("backup_manage")
        state = "normal" if can_manage else "disabled"

        self.permission_lbl.configure(
            text="لديك صلاحية إدارة النسخ والاستيراد ✓"
            if can_manage
            else "لا تملك صلاحية النسخ أو الاستيراد.\nيرجى التواصل مع المسؤول."
        )

        try:
            self.btn_export.configure(state=state)
            self.btn_import.configure(state=state)
            self.btn_save.configure(state=state)
            self.cb_auto.configure(state=state)
            self.btn_browse_dir.configure(state=state)
            self.w_auto_time.configure(state=state)
            self.w_auto_dir.configure(state=state)
        except Exception:
            pass

        enabled_raw = self.db.get_setting("auto_export_enabled", "0")
        enabled = str(enabled_raw).strip().lower() in ("1", "true", "yes", "on")
        self.auto_var.set(enabled)

        auto_time = (self.db.get_setting("auto_export_time", "23:00") or "").strip() or "23:00"
        self.w_auto_time.delete(0, "end")
        self.w_auto_time.insert(0, auto_time)

        auto_dir = (self.db.get_setting("auto_export_dir", "") or "").strip()
        if not auto_dir:
            auto_dir = os.path.join(os.path.dirname(self.db.path), "backups")
        self.w_auto_dir.delete(0, "end")
        self.w_auto_dir.insert(0, auto_dir)

        self.lbl_auto_state.configure(text=self._compute_auto_status(enabled, auto_time))

    def _browse_auto_dir(self):
        path = filedialog.askdirectory(title="اختر مجلد حفظ النسخ التلقائية")
        if path:
            self.w_auto_dir.delete(0, "end")
            self.w_auto_dir.insert(0, path)

    def _compute_auto_status(self, enabled: bool, auto_time: str) -> str:
        if not enabled:
            return "النسخ التلقائي معطّل."
        parsed = self.app._parse_hhmm(auto_time)
        if not parsed:
            return "الوقت غير صحيح. استخدم صيغة HH:MM (مثال: 23:00)."
        hh, mm = parsed

        now = datetime.now()
        scheduled_dt = datetime(now.year, now.month, now.day, hh, mm)
        if now >= scheduled_dt:
            scheduled_dt = scheduled_dt + timedelta(days=1)
        next_str = scheduled_dt.strftime("%Y-%m-%d %H:%M")
        last_date = (self.db.get_setting("auto_export_last_run_date", "") or "").strip()
        if last_date:
            return f"مفعّل — آخر نسخة: {last_date} — الموعد القادم تقريباً: {next_str}."
        return f"مفعّل — الموعد القادم تقريباً: {next_str}."

    def _save_auto_settings(self):
        if not self.require_perm("backup_manage", "ليس لديك صلاحية حفظ إعدادات النسخ."):
            return
        enabled = self.auto_var.get()
        auto_time = self.w_auto_time.get().strip()
        auto_dir = self.w_auto_dir.get().strip()
        parsed = self.app._parse_hhmm(auto_time)
        if not parsed:
            messagebox.showerror("خطأ", "الوقت يجب أن يكون بصيغة HH:MM (مثال: 23:00).", parent=self)
            return

        if not auto_dir:
            auto_dir = os.path.join(os.path.dirname(self.db.path), "backups")

        try:
            os.makedirs(auto_dir, exist_ok=True)
            self.db.set_setting("auto_export_dir", auto_dir)
            self.db.set_setting("auto_export_enabled", "1" if enabled else "0")
            self.db.set_setting("auto_export_time", auto_time)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل حفظ الإعدادات:\n{e}", parent=self)
            return

        self.db.log(
            self.current_user["username"],
            "إعدادات",
            "حفظ إعدادات النسخ الاحتياطي التلقائي",
            self.current_user["username"],
        )
        show_toast(self.app, "تم حفظ إعدادات النسخ التلقائي ✓", "gold")
        self.refresh()

    def _export_db(self):
        if not self.require_perm("backup_manage", "ليس لديك صلاحية التصدير."):
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile=f"law_backup_{date.today().isoformat()}.db",
            filetypes=[("Database", "*.db"), ("All", "*.*")],
            title="حفظ ملف التصدير",
        )
        if path:
            self.db.export_backup(path)
            docs_out = companion_documents_db_path(path)
            try:
                self.db.export_documents_backup(docs_out)
            except Exception as e:
                messagebox.showwarning(
                    "تنبيه",
                    f"تم تصدير القاعدة الرئيسية.\nتعذر تصدير قاعدة المستندات:\n{e}",
                    parent=self,
                )
            self.db.log(
                self.current_user["username"],
                "نسخ احتياطي",
                f"تصدير القاعدة: {path} + المستندات: {docs_out}",
                self.current_user["username"],
            )
            show_toast(self.app, "تم التصدير بنجاح ✓", "green")

    def _import_db(self):
        if not self.require_perm("backup_manage", "ليس لديك صلاحية الاستيراد."):
            return
        path = filedialog.askopenfilename(
            filetypes=[("Database", "*.db"), ("All", "*.*")],
            title="اختر ملف قاعدة البيانات للاستيراد",
        )
        if path and messagebox.askyesno(
            "تأكيد الاستيراد",
            "استيراد ملف قاعدة البيانات؟ ستُستبدل جميع البيانات الحالية.\n\nهل تريد المتابعة؟",
            parent=self,
        ):
            try:
                self.db.restore_backup(path)
                docs_in = companion_documents_db_path(path)
                if os.path.isfile(docs_in):
                    try:
                        self.db.restore_documents_backup(docs_in)
                    except Exception as e:
                        messagebox.showwarning(
                            "تنبيه",
                            f"تم استيراد القاعدة الرئيسية.\nتعذر استيراد قاعدة المستندات من:\n{docs_in}\n\n{e}",
                            parent=self,
                        )
                self.db.log(
                    self.current_user["username"],
                    "نسخ احتياطي",
                    f"استيراد القاعدة: {path}" + (f" + مستندات: {docs_in}" if os.path.isfile(docs_in) else ""),
                    self.current_user["username"],
                )
                self.app.reload_ui_after_database_restore()
                messagebox.showinfo("تم الاستيراد", "تم استيراد القاعدة وتحديث الشاشات.", parent=self)
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الاستيراد:\n{e}", parent=self)


# ════════════════════════════════════════════════════════════
#  صفحة حول البرنامج
# ════════════════════════════════════════════════════════════
class AboutPage(BasePage):
    def __init__(self, parent, db, user, app):
        super().__init__(parent, db, user, app)
        self._build()

    def _build(self):
        sc = ctk.CTkScrollableFrame(self, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=40, pady=20)

        # الأيقونة
        ctk.CTkLabel(sc, text="⚖️",
                     font=("Arial", 72)).pack(pady=(20, 8))

        ctk.CTkLabel(sc, text=APP_NAME,
                     font=("Arial", 26, "bold"),
                     text_color=COLORS["gold_light"]).pack()

        try:
            about_wrap = min(max(self.winfo_screenwidth() - 140, 320), 900)
        except Exception:
            about_wrap = 640
        ctk.CTkLabel(
            sc,
            text="نظام متكامل لإدارة القضايا والعملاء والشؤون المالية",
            font=("Arial", 13),
            text_color=COLORS["text3"],
            wraplength=about_wrap,
            justify="center",
        ).pack(pady=(10, 28))

        # بطاقة المعلومات
        card = ctk.CTkFrame(sc, fg_color=COLORS["panel"],
                            corner_radius=14,
                            border_width=1,
                            border_color=COLORS["border"])
        card.pack(fill="x", pady=8)

        info_rows = [
            ("💻", "برمجة وتطوير",    APP_AUTHOR,   None),
            ("🏢", "الشركة المطورة",   APP_COMPANY,  None),
            ("📋", "إصدار البرنامج",   APP_VERSION,  None),
            ("💾", "قاعدة البيانات",   "SQLite - تخزين محلي آمن", None),
            ("🐍", "لغة البرمجة",      "Python 3 + CustomTkinter", None),
        ]

        for icon, label, value, _ in info_rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)

            ctk.CTkFrame(card, fg_color=COLORS["border"],
                         height=1, corner_radius=0).pack(fill="x", padx=20)

            icon_lbl = ctk.CTkFrame(row, fg_color=COLORS["bg3"],
                                    corner_radius=8,
                                    width=44, height=44)
            icon_lbl.pack(side="right", padx=(0, 10))
            icon_lbl.pack_propagate(False)
            ctk.CTkLabel(icon_lbl, text=icon, font=("Arial", 20)).pack(expand=True)

            info_col = ctk.CTkFrame(row, fg_color="transparent")
            info_col.pack(side="right", fill="both", expand=True)
            ctk.CTkLabel(info_col, text=label, font=("Arial", 11),
                         text_color=COLORS["text3"]).pack(anchor="e")
            ctk.CTkLabel(info_col, text=value, font=("Arial", 13, "bold"),
                         text_color=COLORS["text"]).pack(anchor="e")

        # ─── أزرار التواصل ────
        contact_card = ctk.CTkFrame(sc, fg_color=COLORS["panel"],
                                    corner_radius=14,
                                    border_width=1,
                                    border_color=COLORS["border"])
        contact_card.pack(fill="x", pady=8)
        ctk.CTkLabel(contact_card, text="📞  تواصل معنا",
                     font=("Arial", 14, "bold"),
                     text_color=COLORS["gold_light"]).pack(anchor="e", padx=20, pady=(14, 8))

        import webbrowser

        btn_row = ctk.CTkFrame(contact_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(4, 16))

        # زر الفيسبوك
        fb_btn = ctk.CTkButton(
            btn_row,
            text="📘  فتح صفحة الفيسبوك",
            command=lambda: webbrowser.open("https://www.facebook.com/profile.php?id=100095476066188"),
            width=220, height=42,
            font=("Arial", 13, "bold"),
            fg_color="#1877F2",
            hover_color="#1456b8",
            text_color="#FFFFFF",
            corner_radius=10
        )
        fb_btn.pack(side="right", padx=8)

        # زر الهاتف / واتساب
        wa_btn = ctk.CTkButton(
            btn_row,
            text="📱  01103763082  (واتساب)",
            command=lambda: webbrowser.open("https://wa.me/201103763082"),
            width=220, height=42,
            font=("Arial", 13, "bold"),
            fg_color="#25D366",
            hover_color="#1aaa50",
            text_color="#FFFFFF",
            corner_radius=10
        )
        wa_btn.pack(side="right", padx=8)

        # رسالة الخدمات
        svc = ctk.CTkFrame(sc, fg_color=COLORS["panel"],
                           corner_radius=12,
                           border_width=1,
                           border_color=COLORS["gold_dark"])
        svc.pack(fill="x", pady=14)
        ctk.CTkLabel(svc,
                     text="✨  يمكنك طلب برنامجك بنسخة مخصصة حسب رغبتك\nعن أي مؤسسة تمتلكها",
                     font=("Arial", 13),
                     text_color=COLORS["gold_light"],
                     justify="center").pack(pady=16)

        ctk.CTkLabel(sc,
                     text=f"© 2026 {APP_COMPANY}  ·  {APP_AUTHOR}  ·  جميع الحقوق محفوظة",
                     font=("Arial", 11),
                     text_color=COLORS["text3"]).pack(pady=10)


# ════════════════════════════════════════════════════════════
#  التطبيق الرئيسي
# ════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self._apply_initial_geometry_and_minsize()
        self.configure(fg_color=COLORS["bg"])
        self.bind("<Map>", self._on_main_window_map)
        # بعد الظهور: ملء الشاشة الحقيقي (يغطي شريط مهام ويندوز؛ يُلغى عند الإغلاق)
        self.after(10, self._apply_startup_window_mode)

        # تحديد مسار قاعدة البيانات (افتراضي: نفس مجلد البرنامج)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self._set_window_icon()
        # ملف إعدادات ثابت (AppData) حتى لو تم نقل مجلد البرنامج
        roaming = os.environ.get("APPDATA") or ""
        config_dir = os.path.join(roaming, "LawOfficeSmart") if roaming else base_dir
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception:
            config_dir = base_dir
        self.config_path = os.path.join(config_dir, CONFIG_FILENAME)
        # توافق: لو كان فيه ملف إعدادات قديم بجانب البرنامج
        self.legacy_config_path = os.path.join(base_dir, CONFIG_FILENAME)
        self._bad_db_path = None
        self.db_path = self._load_db_path_or_default(os.path.join(base_dir, DB_FILENAME))

        self.db = Database(self.db_path)
        self.current_user = None
        self.pages: dict[str, BasePage] = {}
        self.active_page = None
        # ─── خدمة التصدير التلقائي ────
        self._auto_export_after_id = None
        # ─── حضور المتصلين والتحديث التلقائي ────
        self.app_id: str | None = None
        self._online_after_id = None
        self._auto_refresh_after_id = None
        self._last_db_mtime = None

        self.withdraw()  # إخفاء النافذة الرئيسية حتى يُفعَّل ويسجل الدخول

        self.after(100, self._check_license)

    def _apply_initial_geometry_and_minsize(self) -> None:
        """حجم أولي وحد أدنى يتناسب مع شاشة الجهاز وتباينات الدقة."""
        try:
            self.update_idletasks()
            sw = max(self.winfo_screenwidth(), 320)
            sh = max(self.winfo_screenheight(), 240)
            self.geometry(f"{sw}x{sh}+0+0")
            # لا يتجاوز عرض/ارتفاع الشاشة حتى قبل التكبير
            mw = min(720, max(360, sw - 40))
            mh = min(520, max(280, sh - 56))
            self.minsize(mw, mh)
        except Exception:
            self.geometry("1280x760")
            self.minsize(640, 420)

    def _on_main_window_map(self, event: tk.Event) -> None:
        """عند إظهار النافذة (مثلاً بعد تسجيل الدخول) أعد ملء الشاشة ليتوافق مع الشاشة الحالية."""
        if event.widget is not self:
            return
        if getattr(self, "current_user", None) is None:
            return
        self.after(60, self._apply_startup_window_mode)

    def _apply_startup_window_mode(self) -> None:
        """ملء الشاشة بالكامل حسب حجم الشاشة الحالية؛ يتوافق مع شاشات مختلفة."""
        try:
            self.update_idletasks()
            sw = max(self.winfo_screenwidth(), 320)
            sh = max(self.winfo_screenheight(), 240)
            self.geometry(f"{sw}x{sh}+0+0")
        except Exception:
            pass
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            try:
                self.state("zoomed")
            except Exception:
                try:
                    sw = self.winfo_screenwidth()
                    sh = self.winfo_screenheight()
                    self.geometry(f"{sw}x{sh}+0+0")
                except Exception:
                    pass

    def _exit_fullscreen_safe(self) -> None:
        try:
            self.attributes("-fullscreen", False)
        except Exception:
            pass

    def _set_window_icon(self) -> None:
        """
        أيقونة النافذة وشريط المهام: ضع `law_office.ico` أو `law_office.png` بجانب البرنامج.
        """
        apply_window_icon(self, self.base_dir)

    # ─────────────────────────────────────────────
    # إعدادات خارجية (مسار قاعدة البيانات)
    # ─────────────────────────────────────────────
    def _load_app_config(self) -> dict:
        try:
            # الأول: AppData
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            # ثم الملف القديم بجانب البرنامج (للتوافق)
            if getattr(self, "legacy_config_path", None) and os.path.exists(self.legacy_config_path):
                with open(self.legacy_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _save_app_config(self, data: dict) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_db_path_or_default(self, default_path: str) -> str:
        cfg = self._load_app_config()
        p = (cfg.get("db_path") or "").strip()
        if not p:
            return default_path
        try:
            # تطبيع المسار (يدعم C:/ و C:\ و UNC ومسارات بها متغيرات)
            p2 = os.path.expandvars(os.path.expanduser(p))
            p2 = os.path.normpath(p2)
            # إن كان المسار غير موجود، ارجع للافتراضي لكن لا تتجاهل المشكلة بصمت
            if os.path.exists(p2):
                return p2
            # خزّن آخر مسار فشل للعرض لاحقاً داخل الواجهة
            self._bad_db_path = p2
            return default_path
        except Exception:
            return default_path

    def set_db_path_config(self, new_path: str) -> None:
        cfg = self._load_app_config()
        try:
            p2 = os.path.expandvars(os.path.expanduser(new_path.strip()))
            p2 = os.path.normpath(p2)
        except Exception:
            p2 = new_path
        cfg["db_path"] = p2
        self._save_app_config(cfg)

    def _get_or_create_local_app_id(self) -> str:
        cfg = self._load_app_config()
        app_id = (cfg.get("app_id") or "").strip()
        if app_id:
            return app_id
        app_id = uuid.uuid4().hex
        cfg["app_id"] = app_id
        self._save_app_config(cfg)
        return app_id

    def _check_license(self):
        """فحص الترخيص أولاً قبل عرض تسجيل الدخول"""
        if check_license(self.db):
            self._show_login()
        else:
            ActivationWindow(self, self.db, self._show_login)

    def _show_login(self):
        LoginWindow(self, self.db, self._after_login)

    def _show_subscription_expired_message(self):
        messagebox.showwarning(
            "انتهاء الاشتراك",
            "انتهت مدة الاشتراك.\n"
            "قم بتجديد الاشتراك وتواصل مع المسئول.\n"
            f"ت/{SUBSCRIPTION_SUPPORT_PHONE}",
            parent=self,
        )

    def _require_active_subscription(self, on_activated=None) -> bool:
        """يتحقق من صلاحية الاشتراك؛ عند الانتهاء يمنع الاستخدام ويعرض نافذة التمديد."""
        if check_license(self.db):
            return True
        self._show_subscription_expired_message()
        try:
            ActivationWindow(self, self.db, on_activated or self._show_login)
        except Exception:
            pass
        return False

    def _after_login(self, user: dict):
        self.current_user = user
        if not self._require_active_subscription(on_activated=lambda: self._after_login(user)):
            return
        saved_theme = self.db.get_setting("theme", "light")
        apply_theme(saved_theme)
        self.deiconify()
        # إعادة تعيين الأيقونة بعد deiconify لأن بعض إصدارات ويندوز
        # تكون أيقونة الشريط تعتمد على أول ظهور فعلي للنافذة.
        self._set_window_icon()
        self.after(10, self._apply_startup_window_mode)
        self.after(350, self._apply_startup_window_mode)
        self._build_main_ui()
        # لو مسار DB مضبوط لكنه غير متاح/غير موجود عند التشغيل، ننبّه المستخدم بعد تسجيل الدخول.
        try:
            if getattr(self, "_bad_db_path", None):
                messagebox.showwarning(
                    "تنبيه قاعدة البيانات",
                    "تم العثور على مسار قاعدة بيانات مضبوط لكنه غير متاح، لذلك تم فتح القاعدة الافتراضية.\n\n"
                    f"المسار غير المتاح:\n{self._bad_db_path}\n\n"
                    "افتح الإعدادات واضبط المسار الصحيح (أو تأكد من توفر مسار الشبكة).",
                    parent=self,
                )
        except Exception:
            pass
        self._ensure_auto_export_scheduler()
        self._start_online_presence()
        self._start_db_auto_refresh()

    # ─────────────────────────────────────────────
    # خدمة التصدير التلقائي
    # ─────────────────────────────────────────────
    def _ensure_auto_export_scheduler(self):
        """تشغيل فحص دوري للتصدير التلقائي (مرة واحدة لكل App)."""
        if self._auto_export_after_id is not None:
            return
        self._auto_export_after_id = self.after(30000, self._auto_export_tick)

    def _stop_auto_export_scheduler(self):
        if self._auto_export_after_id is not None:
            try:
                self.after_cancel(self._auto_export_after_id)
            except Exception:
                pass
            self._auto_export_after_id = None

    # ─────────────────────────────────────────────
    # حضور المتصلين (Shared DB)
    # ─────────────────────────────────────────────
    def _start_online_presence(self):
        """Heartbeat لكل نسخة App حتى تظهر كـ 'متصل'."""
        if getattr(self, "_online_after_id", None) is not None:
            return
        try:
            # app_id يجب أن يكون محلي للجهاز (ليس داخل قاعدة البيانات المشتركة)
            self.app_id = self._get_or_create_local_app_id()
            self.db.set_online_user(self.app_id, self.current_user["username"])
        except Exception:
            # لا نوقف البرنامج لو فشل حضور المتصلين
            return
        self._online_after_id = self.after(10000, self._online_presence_tick)

    def _stop_online_presence(self):
        if self._online_after_id is not None:
            try:
                self.after_cancel(self._online_after_id)
            except Exception:
                pass
            self._online_after_id = None
        self._mark_offline_safely()

    def _mark_offline_safely(self):
        try:
            if self.app_id:
                self.db.mark_offline(self.app_id)
        except Exception:
            pass

    def _online_presence_tick(self):
        try:
            if not getattr(self, "current_user", None) or not self.app_id:
                return
            self.db.set_online_user(self.app_id, self.current_user["username"])
        except Exception:
            pass
        finally:
            if getattr(self, "current_user", None):
                self._online_after_id = self.after(10000, self._online_presence_tick)
            else:
                self._online_after_id = None

    # ─────────────────────────────────────────────
    # Auto refresh للصفحة النشطة عند تعديلات مستخدمين آخرين
    # ─────────────────────────────────────────────
    def _start_db_auto_refresh(self):
        if getattr(self, "_auto_refresh_after_id", None) is not None:
            return
        try:
            if os.path.exists(self.db.path):
                self._last_db_mtime = os.path.getmtime(self.db.path)
        except Exception:
            self._last_db_mtime = None
        self._auto_refresh_after_id = self.after(2000, self._db_auto_refresh_tick)

    def _stop_db_auto_refresh(self):
        if self._auto_refresh_after_id is not None:
            try:
                self.after_cancel(self._auto_refresh_after_id)
            except Exception:
                pass
            self._auto_refresh_after_id = None

    def refresh_all_open_pages(self, toast_msg: str | None = None, toast_color: str = "gold"):
        """إعادة تحميل كل الصفحات المفتوحة (بعد حذف عميل، استعادة DB، إلخ)."""
        try:
            if os.path.exists(self.db.path):
                self._last_db_mtime = os.path.getmtime(self.db.path)
        except Exception:
            self._last_db_mtime = None
        self._refresh_branch_status_label()
        for _pid, pg in list(self.pages.items()):
            try:
                if hasattr(pg, "refresh"):
                    pg.refresh()
            except Exception:
                pass
        if toast_msg:
            show_toast(self, toast_msg, toast_color)

    def reload_ui_after_database_restore(self):
        """إعادة تحميل كل الصفحات المفتوحة بعد استعادة قاعدة البيانات (نفس الجلسة)."""
        self.refresh_all_open_pages("تم تحديث البيانات بعد الاستعادة ✓", "green")

    def _should_skip_auto_refresh(self) -> bool:
        """تجنب إعادة بناء الشاشات أثناء الكتابة داخل Entry/Text."""
        try:
            w = self.focus_get()
            if w is None:
                return False
            cname = w.__class__.__name__.lower()
            return ("entry" in cname) or ("textbox" in cname) or ("text" == cname)
        except Exception:
            return False

    def _db_auto_refresh_tick(self):
        try:
            if not getattr(self, "current_user", None):
                self._stop_db_auto_refresh()
                return
            if self._should_skip_auto_refresh():
                return
            if not self.active_page or self.active_page not in self.pages:
                return
            try:
                mtime = os.path.getmtime(self.db.path)
            except Exception:
                mtime = None
            if mtime is not None and self._last_db_mtime is not None and mtime == self._last_db_mtime:
                return
            if mtime is not None:
                self._last_db_mtime = mtime
            self.refresh_all_open_pages()
        except Exception:
            pass
        finally:
            if getattr(self, "current_user", None):
                self._auto_refresh_after_id = self.after(2000, self._db_auto_refresh_tick)
            else:
                self._auto_refresh_after_id = None

    def _parse_hhmm(self, hhmm: str):
        """تحويل 'HH:MM' إلى (hh, mm) أو None."""
        try:
            hh_str, mm_str = (hhmm or "").strip().split(":")
            hh = int(hh_str)
            mm = int(mm_str)
            if 0 <= hh < 24 and 0 <= mm < 60:
                return hh, mm
        except Exception:
            pass
        return None

    def _auto_export_tick(self):
        """يُستدعى دورياً داخل خيط الواجهة (Tkinter)."""
        try:
            # إذا تمت عملية تسجيل خروج/إغلاق، أوقف الخدمة.
            if not getattr(self, "current_user", None):
                self._stop_auto_export_scheduler()
                return

            enabled_raw = self.db.get_setting("auto_export_enabled", "0")
            enabled = str(enabled_raw).strip().lower() in ("1", "true", "yes", "on")
            if not enabled:
                # لا تصدير، لكن استمر في الفحص حتى لو تم تفعيلها لاحقاً.
                return

            parsed = self._parse_hhmm(self.db.get_setting("auto_export_time", "23:00"))
            if not parsed:
                return
            hh, mm = parsed

            now = datetime.now()
            scheduled_dt = datetime(now.year, now.month, now.day, hh, mm)
            if now < scheduled_dt:
                return

            last_date = (self.db.get_setting("auto_export_last_run_date", "") or "").strip()
            today_key = scheduled_dt.date().isoformat()
            if last_date == today_key:
                return  # تم التنفيذ اليوم بالفعل

            out_dir = (self.db.get_setting("auto_export_dir", "") or "").strip()
            if not out_dir:
                out_dir = os.path.join(os.path.dirname(self.db.path), "backups")
            os.makedirs(out_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(out_dir, f"law_backup_{stamp}.db")
            self.db.export_backup(out_path)
            try:
                self.db.export_documents_backup(companion_documents_db_path(out_path))
            except Exception:
                pass

            username = self.current_user["username"]
            self.db.log(username, "نسخ تلقائي", f"تم إنشاء نسخة تلقائية: {out_path}", username)
            # مرة واحدة يومياً غالباً؛ عرض توست لتأكيد للمسؤول.
            show_toast(self, "تم إنشاء نسخة تلقائية ✓", "green")
            self.db.set_setting("auto_export_last_run_date", today_key)
        except Exception as e:
            # أي خطأ في النسخ لا يمنع استمرار الخدمة
            try:
                username = self.current_user["username"] if getattr(self, "current_user", None) else "system"
                self.db.log(username, "نسخ تلقائي - فشل", str(e), username)
            except Exception:
                pass

        finally:
            # أعد جدولة الفحص الدوري
            if getattr(self, "current_user", None):
                self._auto_export_after_id = self.after(30000, self._auto_export_tick)
            else:
                self._auto_export_after_id = None

    def _compute_branch_text(self) -> str:
        branch_text = "🏢 الفرع: غير محدد"
        try:
            if getattr(self, "app_id", None):
                b = self.db.get_device_branch(self.app_id)
                if b and (b["branch_number"] or b["branch_address"]):
                    bn = (b["branch_number"] or "").strip()
                    ba = (b["branch_address"] or "").strip()
                    by = str(b["branch_year"]).strip() if b["branch_year"] else ""
                    parts = [f"🏢 {bn}" if bn else "🏢 فرع"]
                    if ba:
                        parts.append(ba)
                    if by:
                        parts.append(by)
                    branch_text = " | ".join(parts)
        except Exception:
            pass
        return branch_text

    def _refresh_branch_status_label(self):
        try:
            if hasattr(self, "branch_status_lbl") and self.branch_status_lbl:
                self.branch_status_lbl.configure(text=self._compute_branch_text())
        except Exception:
            pass

    def _build_main_ui(self):
        role_labels = dict(ROLE_LABEL_AR)
        role = self.current_user["role"]
        branch_text = self._compute_branch_text()

        # ══════════════════════════════════════════
        # الشريط العلوي — صفّان
        # ══════════════════════════════════════════
        self.toolbar = ctk.CTkFrame(self, fg_color=COLORS["panel"],
                                    corner_radius=0)
        self.toolbar.pack(fill="x", side="top")

        # ── الصف الأول: شعار + معلومات المستخدم + الثيم + اشتراك + الخروج ──
        top_row = ctk.CTkFrame(self.toolbar, fg_color=COLORS["bg3"], corner_radius=0, height=46)
        top_row.pack(fill="x")
        top_row.pack_propagate(False)

        sub_bar = _license_subscription_ui(self.db)
        warn_bar = sub_bar.get("show_warning", False)
        warn_bar_txt = (
            "⚠️  البرنامج على وشك انتهاء الاشتراك قم بالتواصل مع المسؤول للتجديد"
            if warn_bar
            else ""
        )
        sub_bar_line = (
            f"📅  أيام الاشتراك: {sub_bar['total_str']}  |  المتبقي: {sub_bar['remaining_str']}"
        )

        exit_btns = ctk.CTkFrame(top_row, fg_color="transparent")
        exit_btns.pack(side="left", padx=8, pady=6)
        ctk.CTkButton(
            exit_btns,
            text="🚪 خروج",
            command=self._quit_application,
            width=88,
            height=26,
            font=("Arial", 11, "bold"),
            fg_color=COLORS["red"],
            hover_color="#c0392b",
            text_color="#FFFFFF",
            corner_radius=6,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            exit_btns,
            text="تسجيل خروج",
            command=self._logout,
            width=108,
            height=26,
            font=("Arial", 11),
            fg_color="transparent",
            hover_color=COLORS["hover"],
            text_color=COLORS["text2"],
            corner_radius=6,
        ).pack(side="left")

        right_bar = ctk.CTkFrame(top_row, fg_color="transparent")
        right_bar.pack(side="right")

        ctk.CTkLabel(right_bar, text="⚖️  مكتب المحاماة الذكي",
                     font=("Arial", 13, "bold"),
                     text_color=COLORS["gold_light"]).pack(side="right", padx=14)

        ctk.CTkFrame(right_bar, fg_color=COLORS["border"],
                     width=1, height=24).pack(side="right", padx=4, pady=7)

        ctk.CTkLabel(right_bar,
                     text=f"👤 {self.current_user['name']}  ({role_labels.get(role, role)})",
                     font=("Arial", 11, "bold"),
                     text_color=COLORS["gold_light"]).pack(side="right", padx=10)

        ctk.CTkFrame(right_bar, fg_color=COLORS["border"],
                     width=1, height=24).pack(side="right", padx=4, pady=7)

        self.branch_status_lbl = ctk.CTkLabel(
            right_bar,
            text=branch_text,
            font=("Arial", 10, "bold"),
            text_color=COLORS["text2"],
        )
        self.branch_status_lbl.pack(side="right", padx=8)

        ctk.CTkFrame(right_bar, fg_color=COLORS["border"],
                     width=1, height=24).pack(side="right", padx=4, pady=7)

        cur_theme_label = ALL_THEMES.get(CURRENT_THEME, ("🎨",))[0]
        self.theme_btn = ctk.CTkButton(
            right_bar,
            text=f"🎨 {cur_theme_label}",
            width=130, height=26,
            font=("Arial", 10),
            fg_color=COLORS["panel2"],
            hover_color=COLORS["hover"],
            text_color=COLORS["gold_light"],
            corner_radius=6,
            command=self._open_theme_picker
        )
        self.theme_btn.pack(side="right", padx=6, pady=6)

        ctk.CTkFrame(right_bar, fg_color=COLORS["border"],
                     width=1, height=24).pack(side="right", padx=4, pady=7)

        mid_bar = ctk.CTkFrame(top_row, fg_color="transparent")
        mid_bar.pack(side="left", expand=True, fill="both")
        mid_inner = ctk.CTkFrame(mid_bar, fg_color="transparent")
        mid_inner.pack(expand=True)
        try:
            sub_wrap = min(520, max(220, self.winfo_screenwidth() - 240))
        except Exception:
            sub_wrap = 520
        if warn_bar_txt:
            ctk.CTkLabel(
                mid_inner,
                text=warn_bar_txt,
                font=("Arial", 10, "bold"),
                text_color=COLORS["orange"],
                wraplength=sub_wrap,
                justify="center",
            ).pack()
        ctk.CTkLabel(
            mid_inner,
            text=sub_bar_line,
            font=("Arial", 10, "bold"),
            text_color=COLORS["gold_light"],
            wraplength=sub_wrap,
            justify="center",
        ).pack(pady=(2, 0) if warn_bar_txt else (0, 0))

        # ── الصف الثاني: أزرار التنقل (تمرير أفقي على الشاشات الضيقة) ──
        nav_wrap = ctk.CTkFrame(self.toolbar, fg_color=COLORS["panel"], corner_radius=0, height=50)
        nav_wrap.pack(fill="x")
        nav_wrap.pack_propagate(False)
        nav_row = ctk.CTkScrollableFrame(
            nav_wrap,
            orientation="horizontal",
            fg_color=COLORS["panel"],
            corner_radius=0,
            height=46,
            scrollbar_button_color=COLORS["gold_dark"],
            scrollbar_button_hover_color=COLORS["gold"],
        )
        nav_row.pack(fill="both", expand=True, padx=2, pady=2)

        try:
            sw_nav = self.winfo_screenwidth()
            nav_btn_w = 70 if sw_nav < 1024 else (78 if sw_nav < 1280 else 88)
            nav_font = ("Arial", 9, "bold") if sw_nav < 1024 else ("Arial", 10, "bold")
        except Exception:
            nav_btn_w, nav_font = 88, ("Arial", 10, "bold")

        nav_items = [
            ("🏠", "الرئيسية",   "dashboard",  ["dev_master","admin","superfiser","user","trial"]),
            ("👥", "العملاء",    "clients",    ["dev_master","admin","superfiser","user","trial"]),
            ("📁", "القضايا",    "cases",      ["dev_master","admin","superfiser","user","trial"]),
            ("🗓", "الجلسات",    "sessions",   ["dev_master","admin","superfiser","user","trial"]),
            ("💰", "المالية",    "finance",    ["dev_master","admin","superfiser","trial"]),
            ("📜", "العقود",     "contracts",  ["dev_master","admin","superfiser","user","trial"]),
            ("📂", "الوثائق",    "documents",  ["dev_master","admin","superfiser","user","trial"]),
            ("✅", "المهام",     "tasks",      ["dev_master","admin","superfiser","user","trial"]),
            ("📋", "السجلات",    "logs",       ["dev_master","admin","superfiser"]),
            ("🏢", "رقم المكتب", "office_number", ["dev_master","admin","superfiser"]),
            ("👤", "المستخدمون", "users",      ["dev_master","admin","trial"]),
            ("🔑", "السريالات", "serial_licenses", ["dev_master"]),
            ("🟢", "المتصلون",   "online",     ["dev_master","admin","superfiser","user","trial"]),
            ("💾", "النسخ والبيانات", "data_backup", ["dev_master","admin","superfiser"]),
            ("⚙️", "الإعدادات", "settings",   ["dev_master","admin","superfiser","user"]),
            ("ℹ️", "حول",        "about",      ["dev_master","admin","superfiser","user","trial"]),
        ]

        self.nav_buttons = {}
        nav_entries = [(i, l, p, a) for i, l, p, a in nav_items if role in a]
        for icon, label, page_id, allowed_roles in reversed(nav_entries):
            btn = ctk.CTkButton(
                nav_row,
                text=f"{icon} {label}",
                width=nav_btn_w,
                height=36,
                font=nav_font,
                fg_color="transparent",
                hover_color=COLORS["hover"],
                text_color=COLORS["text2"],
                corner_radius=6,
                command=lambda pid=page_id: self._navigate(pid)
            )
            btn.pack(side="left", padx=1, pady=4)
            self.nav_buttons[page_id] = btn

        # ─── منطقة المحتوى: إطار عادي (وليس CTkScrollableFrame) حتى يمتد المحتوى لعرض وارتفاع
        #     النافذة بالكامل؛ الإطار القابل للتمرير داخل كل صفحة يتولى التمرير عند الحاجة.
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg2"], corner_radius=0)
        self.content.pack(fill="both", expand=True)

        # انتقل للصفحة الرئيسية
        self._navigate("dashboard")

    def _navigate(self, page_id: str):
        if page_id != "serial_licenses":
            if not self._require_active_subscription(on_activated=lambda: self._navigate(page_id)):
                return

        # إزالة تمييز الزر السابق
        for pid, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=COLORS["text2"])

        # تمييز الزر الحالي
        if page_id in self.nav_buttons:
            self.nav_buttons[page_id].configure(
                fg_color=COLORS["hover"],
                text_color=COLORS["gold_light"]
            )

        # إخفاء الصفحة السابقة
        if self.active_page and self.active_page in self.pages:
            self.pages[self.active_page].pack_forget()

        # إنشاء الصفحة إذا لم تكن موجودة
        if page_id not in self.pages:
            page_map = {
                "dashboard": DashboardPage,
                "clients":   ClientsPage,
                "cases":     CasesPage,
                "sessions":  SessionsPage,
                "finance":   FinancePage,
                "contracts": ContractsPage,
                "documents": DocumentsPage,
                "tasks":     TasksPage,
                "logs":      LogsPage,
                "office_number": OfficeNumberPage,
                "users":     UsersPage,
                "serial_licenses": SerialLicensesPage,
                "online":    ConnectedUsersPage,
                "data_backup": DataBackupPage,
                "settings":  SettingsPage,
                "about":     AboutPage,
            }
            cls = page_map.get(page_id)
            if cls:
                try:
                    pg = cls(self.content, self.db, self.current_user, self)
                    self.pages[page_id] = pg
                except Exception as e:
                    messagebox.showerror("خطأ", f"تعذر فتح الصفحة:\n{e}", parent=self)
                    return

        # عرض الصفحة (ملء منطقة المحتوى عموديًا وأفقيًا حسب حجم الشاشة/النافذة)
        if page_id in self.pages:
            try:
                self.pages[page_id].pack(fill="both", expand=True)
                self.active_page = page_id
                pg = self.pages[page_id]
                if hasattr(pg, "refresh"):
                    pg.refresh()
                if page_id == "settings":
                    self.after(40, self._apply_startup_window_mode)
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر عرض الصفحة:\n{e}", parent=self)

    def _open_theme_picker(self):
        """نافذة منبثقة لاختيار الثيم"""
        win = ctk.CTkToplevel(self)
        win.title("🎨 اختر ثيم البرنامج")
        win.resizable(False, False)
        win.configure(fg_color=COLORS["bg"])
        win.grab_set()
        center_window(win, 420, 520)

        ctk.CTkLabel(win, text="🎨  اختر ثيم البرنامج",
                     font=("Arial", 16, "bold"),
                     text_color=COLORS["gold_light"]).pack(pady=(20, 4))
        ctk.CTkLabel(win, text="سيتم تطبيق الثيم فوراً",
                     font=("Arial", 11),
                     text_color=COLORS["text3"]).pack(pady=(0, 16))

        sc = ctk.CTkScrollableFrame(win, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=16, pady=4)

        for theme_key, (theme_name, theme_colors) in ALL_THEMES.items():
            is_current = (theme_key == CURRENT_THEME)
            card = ctk.CTkFrame(sc,
                                fg_color=theme_colors["panel"],
                                corner_radius=10,
                                border_width=2,
                                border_color=theme_colors["gold"] if is_current else theme_colors["border"])
            card.pack(fill="x", pady=5)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)

            # معاينة الألوان
            preview = ctk.CTkFrame(inner, fg_color="transparent")
            preview.pack(side="right", padx=8)
            for c_key in ["gold", "accent", "green", "red"]:
                ctk.CTkFrame(preview,
                             fg_color=theme_colors[c_key],
                             width=18, height=18,
                             corner_radius=9).pack(side="right", padx=2)

            # الاسم والوصف
            name_frame = ctk.CTkFrame(inner, fg_color="transparent")
            name_frame.pack(side="right", fill="x", expand=True)

            lbl_text = f"✅  {theme_name}" if is_current else theme_name
            ctk.CTkLabel(name_frame, text=lbl_text,
                         font=("Arial", 13, "bold"),
                         text_color=theme_colors["gold_light"]).pack(anchor="e")
            if is_current:
                ctk.CTkLabel(name_frame, text="الثيم الحالي",
                             font=("Arial", 10),
                             text_color=theme_colors["text3"]).pack(anchor="e")

            def _apply(tk=theme_key, w=win):
                self._set_theme(tk)
                w.destroy()

            card.bind("<Button-1>", lambda e, fn=_apply: fn())
            inner.bind("<Button-1>", lambda e, fn=_apply: fn())
            name_frame.bind("<Button-1>", lambda e, fn=_apply: fn())

            ctk.CTkButton(card, text="تطبيق", command=_apply,
                          width=80, height=28,
                          fg_color=theme_colors["gold_dark"],
                          hover_color=theme_colors["gold"],
                          text_color="#000000" if theme_key == "light" else "#FFFFFF",
                          font=("Arial", 12, "bold"),
                          corner_radius=6).pack(side="left", padx=14, pady=8)

    def _set_theme(self, theme_key: str):
        apply_theme(theme_key)
        self.db.set_setting("theme", theme_key)
        if hasattr(self, 'toolbar'):
            self.toolbar.destroy()
        if hasattr(self, 'content'):
            self.content.destroy()
        self.pages.clear()
        self.active_page = None
        self._build_main_ui()

    def _toggle_theme(self):
        new_theme = "light" if CURRENT_THEME == "dark" else "dark"
        apply_theme(new_theme)
        self.db.set_setting("theme", new_theme)
        # إعادة بناء الواجهة لتطبيق الثيم فوراً
        if hasattr(self, 'toolbar'):
            self.toolbar.destroy()
        if hasattr(self, 'content'):
            self.content.destroy()
        self.pages.clear()
        self.active_page = None
        self._build_main_ui()

    def _quit_application(self) -> None:
        """إغلاق البرنامج بالكامل (ليس تسجيل خروج من الحساب)."""
        if not messagebox.askyesno(
            "إنهاء البرنامج",
            "هل تريد إغلاق البرنامج بالكامل؟",
            parent=self,
        ):
            return
        self.on_closing()

    def _logout(self):
        if messagebox.askyesno(
            "تسجيل خروج",
            "هل تريد تسجيل الخروج من الحساب والعودة لشاشة الدخول؟", parent=self
        ):
            self.db.log(self.current_user["username"], "تسجيل خروج",
                        f"تسجيل خروج: {self.current_user['name']}",
                        self.current_user["username"])
            self._stop_auto_export_scheduler()
            self._stop_online_presence()
            self._stop_db_auto_refresh()
            # مسح الواجهة
            self.toolbar.destroy()
            self.content.destroy()
            self.pages.clear()
            self.current_user = None
            self._exit_fullscreen_safe()
            self.withdraw()
            self.after(200, self._show_login)

    def on_closing(self):
        self._exit_fullscreen_safe()
        self._stop_auto_export_scheduler()
        self._stop_online_presence()
        self._stop_db_auto_refresh()
        self.db.close()
        self.destroy()


# ════════════════════════════════════════════════════════════
#  نقطة الدخول
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
