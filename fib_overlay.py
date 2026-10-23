import sys, os, json, math, random, time, winsound, ctypes, traceback, datetime
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QWidget, QInputDialog, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel, QDialog,
                             QCheckBox, QSpinBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                             QGridLayout, QColorDialog, QScrollArea, QSizePolicy,
                             QKeySequenceEdit, QFrame, QComboBox, QMessageBox,
                             QMenu, QSpacerItem, QFileDialog, QLayout, QSlider, QAbstractSpinBox)
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, QPointF, QSize, QAbstractNativeEventFilter, QTimer
from PyQt5.QtGui import (QPainter, QPen, QColor, QFont, QKeySequence, QIcon, QPixmap,
                         QPainterPath, QTransform, QCursor, QPalette, QPolygonF)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
GWL_EXSTYLE = -20
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW = 0x80000, 0x20, 0x80
WM_HOTKEY, MOD_NOREPEAT = 0x0312, 0x4000
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN = 0x1, 0x2, 0x4, 0x8
SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER = 0x1, 0x2, 0x4
SWP_NOACTIVATE, SWP_FRAMECHANGED = 0x10, 0x20
SW_RESTORE = 9
SRCCOPY = 0x00CC0020
WDA_NONE, WDA_EXCLUDEFROMCAPTURE = 0x0, 0x11

# Handles sind 64 Bit - ohne Typangaben schneidet ctypes sie ab
user32.GetDC.restype = wintypes.HDC; user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
gdi32.CreateCompatibleDC.restype = wintypes.HDC; gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wintypes.HGDIOBJ; gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.BitBlt.argtypes = [wintypes.HDC] + [ctypes.c_int] * 4 + [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]; gdi32.DeleteDC.argtypes = [wintypes.HDC]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                            ctypes.POINTER(BITMAPINFOHEADER), wintypes.UINT]

# ===== DATEIEN =====
# Liegen in %APPDATA%\FibOverlay - so ist egal, von wo aus die EXE gestartet wird
APP_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "FibOverlay")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
PRESET_DIR = os.path.join(APP_DIR, "presets")
CRASH_LOG = os.path.join(APP_DIR, "crash_log.txt")
os.makedirs(PRESET_DIR, exist_ok=True)

# ===== GLOBALE EINSTELLUNGEN =====
USE_GLOBAL_R = True
GLOBAL_TP1_R = 3.0
GLOBAL_TP2_R = 5.0
GLOBAL_TP3_R = 7.0
AUTO_RESIZE_WINDOW = True
SHOW_RULES = False
PRICE_REF = "hl"        # "hl" = Preise bei 0% / 100% abfragen, "entry" = bei Entry 1 / SL 1
PRICE_DECIMALS = 5
MAGNET_ON = True
MAGNET_MODE = "weak"    # "weak" = nur in der Nähe einer Kerze einrasten, "strong" = immer an der Kerze unterm Cursor

MARGIN_TOP = 3
GAP_1 = 3
GAP_2 = 2
MARGIN_BOTTOM = 13

DEFAULTS = None  # Werkseinstellungen, wird in main() gefüllt

def fmt_num(v): return f"{v:g}"

LINE_KEYS = ("e", "sl", "be", "tp1", "tp2", "tp3")

SETUPS = []
for i in range(1, 5):
    SETUPS.append({
        "n": i,
        "entry": 0.500 if i==1 else (0.559 if i==2 else (0.618 if i==3 else 0.677)),
        "sl": 0.559 if i==1 else (0.618 if i==2 else (0.677 if i==3 else 0.736)),
        "r_tp1": 3.0, "r_tp2": 5.0, "r_tp3": 7.0,
        "color_e": QColor(0, 200, 255), "thick_e": 1, "style_e": "Solid",
        "color_sl": QColor(255, 70, 70), "thick_sl": 1, "style_sl": "Solid",
        "color_be": QColor(255, 220, 60), "thick_be": 1, "style_be": "Solid",
        "color_tp1": QColor(70, 220, 110), "thick_tp1": 1, "style_tp1": "Solid",
        "color_tp2": QColor(70, 220, 110), "thick_tp2": 1, "style_tp2": "Solid",
        "color_tp3": QColor(70, 220, 110), "thick_tp3": 1, "style_tp3": "Solid",
        "active": True,
        **{f"show_{k}": True for k in LINE_KEYS},
    })

# ===== ZEICHENWERKZEUGE =====
TOOL_NAMES = {"trend": "Trendlinie", "ray": "Strahl", "hray": "Horizontaler Strahl", "hline": "Horizontale Linie",
              "rect": "Rechteck"}
TOOL_ARTICLES = {"trend": "die Trendlinie", "ray": "den Strahl", "hray": "den horizontalen Strahl",
                 "hline": "die horizontale Linie", "rect": "das Rechteck"}
TOOL_STYLES = {  # Standard für neue Zeichnungen (einzelne lassen sich per Doppelklick / Rechtsklick ändern)
    "trend": {"color": QColor("#ffffff"), "width": 2, "style": "Solid"},
    "ray":   {"color": QColor("#ffffff"), "width": 2, "style": "Solid"},
    "hray":  {"color": QColor("#ffffff"), "width": 2, "style": "Solid"},
    "hline": {"color": QColor("#ffffff"), "width": 2, "style": "Solid"},
    "rect":  {"color": QColor("#ab47bc"), "width": 1, "style": "Solid",
              "fill": True, "fill_color": QColor("#ab47bc"), "fill_opacity": 15, "midline": False},
}
SETTINGS_VERSION = 2  # ab 2: Werkzeuge weiß / Dicke 2 - ältere gespeicherte Werkzeugfarben werden nicht übernommen

# ===== VERLÄNGERUNG EINES LEVELS NACH RECHTS (z. B. 0,5) + ALARM =====
EXT_STYLE = {
    "on": False, "level": 0.5, "candles": 10,           # Länge in Kerzen (Kerzenabstand wird am Bildschirm gemessen)
    "width": 2, "style": "Dash",
    "color_up": QColor("#2ecc71"), "color_down": QColor("#f23645"), "color_neutral": QColor("#ffffff"),
    "live": True,                                        # Farbe nach Kurs: letzte Kerze am Bildschirm erkennen (Test)
    "alarm": False, "pre_alert": 0.0,                    # Ton beim Kreuzen / Vorwarnung ab Abstand (Fib-Einheiten)
}

# ===== MATRIX-REGEN =====
MATRIX_STYLE = {"own_color": False, "color": QColor("#00ff41"), "head": QColor("#ffffff"), "speed": 100, "size": 13}

def style_to_json(st):
    return {k: (v.name(QColor.HexArgb) if isinstance(v, QColor) else v) for k, v in st.items()}

def style_from_json(st, data):
    """Übernimmt gespeicherte Werte in ein Einstellungs-Dict - Typ wie beim Standardwert."""
    for k, v in data.items():
        if k in st: st[k] = QColor(v) if isinstance(st[k], QColor) else type(st[k])(v)

# ===== FIB-DARSTELLUNG (wie das Fib-Retracement bei TradingView) =====
FIB_STYLE = {
    "trend": True, "trend_color": QColor(255, 255, 255, 200), "trend_style": "Dash", "trend_width": 1,  # Diagonale
    "extend": "none",            # "none", "left", "right", "both"
    "background": True, "bg_opacity": 25,
    "reverse": False,            # 0 und 1 tauschen
    "prices": True,              # Preis in Klammern hinter dem Level
    "level_fmt": "value",        # "value" = 0,5 / "percent" = 50%
    "names": True,               # E1, SL1 … hinter dem Level
    "label_h": "center", "label_v": "middle",
    "font_size": 10,
    "label_box": False,          # dunkler Kasten hinter der Beschriftung
    "one_color": False, "one_color_value": QColor("#2962ff"),
    "show_0": True, "color_0": QColor(230, 230, 230),   # Linie bei 0 und 1 (dort sitzen die Ankerpunkte)
    "show_1": True, "color_1": QColor(230, 230, 230),
    "num_fmt": "de",             # "de" = 0,5 (81.751,0) / "en" = 0.5 (81751.0)
}
# zusätzliche Level wie in der Level-Liste bei TradingView (an/aus, Wert, Farbe) - anfangs alle aus
FIB_EXTRA = [{"value": v, "color": QColor(c), "on": False} for v, c in
             ((0.236, "#f23645"), (0.382, "#ff9800"), (0.786, "#00bcd4"), (1.618, "#2962ff"), (2.618, "#f23645"))]
PEN_STYLES = {"Solid": Qt.SolidLine, "Dash": Qt.DashLine, "Dot": Qt.DotLine}

def _de(s): return s.replace(",", "§").replace(".", ",").replace("§", ".")

def fmt_level(f):
    s = f"{f * 100:g}%" if FIB_STYLE["level_fmt"] == "percent" else fmt_num(round(f, 6))
    return _de(s) if FIB_STYLE["num_fmt"] == "de" else s

def fmt_price(v):
    return _de(f"{v:,.{PRICE_DECIMALS}f}") if FIB_STYLE["num_fmt"] == "de" else f"{v:.{PRICE_DECIMALS}f}"

# ===== DESIGNS (Dashboard + Einstellungen) =====
VIO, GOLD = "#84329B", "#d4af37"  # Cooler-Master-Violett und Gold
_grad = lambda top, bottom: f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom})"
_hgrad = lambda left, right: f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {left}, stop:1 {right})"
THEMES = {
    "Klassisch (Blau)": dict(
        bg="#222222", box="#222222", border="#4db8ff", title="#4db8ff", title_bg="#2a2a2a", text="#ffffff", muted="#cccccc",
        btn="#444444", btn_border="#555555", btn_hover="#555555", on="#2b579a", on_border="#4db8ff", on_text="#ffffff",
        table_bg="#2a2a2a", head="#333333", head_text="#ffffff", grid="#555555",
        spawn=("#2e8b57", "#7cffb2", "#ffffff"), draw=("#2b579a", "#7ca4ff", "#ffffff"), clear=("#a12b2b", "#ff7c7c", "#ffffff"),
        icon="#dddddd", highlight="#2b579a", field="#8a8a8a", focus="#4db8ff"),
    "1 · Obsidian Violett": dict(
        bg="#0a0a0d", box="#0a0a0d", border=VIO, title=GOLD, title_bg="#140f19", text="#ececec", muted="#a99fb3",
        btn="#17131c", btn_border="#33283d", btn_hover="#251c2f", on=VIO, on_border="#b05cc8", on_text="#ffffff",
        table_bg="#0f0c13", head="#1b1424", head_text=GOLD, grid="#2c2236",
        spawn=(VIO, "#b05cc8", "#ffffff"), draw=("#17131c", GOLD, GOLD), clear=("#24090f", "#8e2a3a", "#ff9aa8"),
        icon=GOLD, highlight=VIO),
    "2 · Royal Gold": dict(
        bg="#000000", box="#050505", border=GOLD, title=GOLD, title_bg="#0f0c03", text="#f3ead2", muted="#b8ab8a",
        btn="#121110", btn_border="#3b3320", btn_hover="#1f1b12", on=GOLD, on_border="#f0d36b", on_text="#000000",
        table_bg="#080807", head="#17140a", head_text=GOLD, grid="#2c2716",
        spawn=(_grad("#e6c45a", "#a8841f"), "#f0d36b", "#000000"), draw=(VIO, "#b05cc8", "#ffffff"),
        clear=("#170707", "#7a1f1f", "#e57373"), icon=GOLD, highlight=GOLD),
    "3 · Cooler Master": dict(
        bg="#07050a", box="#0d0812", border=VIO, title="#ffffff", title_bg=VIO, text="#f0e9f5", muted="#b39cc4",
        btn=_grad("#2a1735", "#150b1b"), btn_border="#4a2a5a", btn_hover="#3a2049",
        on=_grad("#9b45b5", "#6a2380"), on_border=GOLD, on_text="#ffffff",
        table_bg="#0b0710", head="#2a1236", head_text="#ffffff", grid="#2e1d3a",
        spawn=(_grad("#9b45b5", "#5e1f72"), GOLD, "#ffffff"), draw=("#150b1b", VIO, "#e7d3f0"),
        clear=("#1e080d", "#7d2433", "#ff8fa0"), icon="#e7d3f0", highlight=VIO),
    "4 · Schwarz-Gold Minimal": dict(
        bg="#111111", box="#111111", border="#2e2e2e", title=GOLD, title_bg="#111111", text="#e6e6e6", muted="#9a9a9a",
        btn="#1a1a1a", btn_border="#2e2e2e", btn_hover="#242424", on=VIO, on_border=VIO, on_text="#ffffff",
        table_bg="#141414", head="#1a1a1a", head_text=GOLD, grid="#262626",
        spawn=(VIO, VIO, "#ffffff"), draw=("#1a1a1a", "#3a3a3a", "#e6e6e6"), clear=("#1a1a1a", "#5a1f1f", "#ef7676"),
        icon="#cfcfcf", highlight=VIO),
    "5 · Midnight Neon": dict(
        bg="#000000", box="#000000", border="#a24dc4", title="#ffd166", title_bg="#1a0b22", text="#ffffff", muted="#c9a8d8",
        btn="#0c0610", btn_border="#5c2a70", btn_hover="#1c0d26", on="#a24dc4", on_border="#ffd166", on_text="#ffffff",
        table_bg="#05030a", head="#2a1038", head_text="#ffd166", grid="#3a1a4a",
        spawn=("#ffd166", "#ffe29a", "#000000"), draw=(VIO, "#c27ae0", "#ffffff"), clear=("#000000", "#ff4d6d", "#ff4d6d"),
        icon="#ffd166", highlight="#a24dc4"),
    # --- zweite Runde: weiße Überschriften, Knöpfe Violett/Schwarz/Gold, deutliche Rahmen ---
    "6 · Obsidian Weiß": dict(
        bg="#0a0a0d", box="#0a0a0d", border=VIO, title="#ffffff", title_bg="#0a0a0d", text="#ececec", muted="#a99fb3",
        btn="#17131c", btn_border="#33283d", btn_hover="#251c2f", on=VIO, on_border="#ffffff", on_text="#ffffff",
        table_bg="#0f0c13", head="#1b1424", head_text="#ffffff", grid="#2c2236",
        spawn=(VIO, "#ffffff", "#ffffff"), draw=("#17131c", GOLD, GOLD), clear=("#24090f", "#8e2a3a", "#ff9aa8"),
        icon=GOLD, highlight=VIO, rain=VIO, rain_head="#ffffff"),
    "7 · Obsidian Gold-Rahmen": dict(
        bg="#08070a", box="#08070a", border=VIO, title="#ffffff", title_bg="#140f19", text="#f0f0f0", muted="#a99fb3",
        btn="#141118", btn_border="#3a2d45", btn_hover="#221a2b", on=_grad("#9b45b5", "#6a2380"), on_border=GOLD, on_text="#ffffff",
        table_bg="#0d0b10", head="#1b1424", head_text=GOLD, grid="#2a2133",
        spawn=(_grad("#9b45b5", "#5e1f72"), GOLD, "#ffffff"), draw=("#141118", VIO, "#ffffff"),
        clear=("#1e080d", "#7d2433", "#ff8fa0"), icon="#ffffff", highlight=VIO, rain=VIO, rain_head=GOLD),
    "8 · Violett Glow": dict(
        bg="#050307", box="#0b0610", border="#a34fc0", title="#ffffff", title_bg=_grad("#a34fc0", "#6a2380"),
        text="#ffffff", muted="#c6a9d6", btn="#120a18", btn_border="#4a2a5a", btn_hover="#24122f",
        on=_grad("#b25ad0", "#7a2a94"), on_border="#ffffff", on_text="#ffffff",
        table_bg="#08050c", head="#2a1236", head_text="#ffffff", grid="#341d42",
        spawn=(_grad("#b25ad0", "#6a2380"), "#ffffff", "#ffffff"), draw=("#120a18", GOLD, GOLD),
        clear=("#140509", "#8e2a3a", "#ff8fa0"), icon="#e7c6f5", highlight="#a34fc0", rain="#a34fc0", rain_head="#ffffff"),
    "9 · Schwarz-Weiß-Violett": dict(
        bg="#000000", box="#000000", border="#3a3a3a", title="#ffffff", title_bg="#000000", text="#f2f2f2", muted="#9a9a9a",
        btn="#111111", btn_border="#333333", btn_hover="#1e1e1e", on=VIO, on_border="#ffffff", on_text="#ffffff",
        table_bg="#0a0a0a", head="#151515", head_text="#ffffff", grid="#262626",
        spawn=(VIO, "#ffffff", "#ffffff"), draw=("#000000", "#ffffff", "#ffffff"), clear=("#000000", "#b33a3a", "#ff7a7a"),
        icon="#ffffff", highlight=VIO, rain=VIO, rain_head="#ffffff"),
    "10 · Gold Edition": dict(
        bg="#000000", box="#050505", border=GOLD, title="#ffffff", title_bg="#000000", text="#f3ead2", muted="#b8ab8a",
        btn="#121110", btn_border="#3b3320", btn_hover="#1f1b12", on=_grad("#e6c45a", "#a8841f"), on_border="#ffffff", on_text="#000000",
        table_bg="#080807", head="#17140a", head_text=GOLD, grid="#2c2716",
        spawn=(_grad("#9b45b5", "#5e1f72"), GOLD, "#ffffff"), draw=("#000000", VIO, "#ffffff"),
        clear=("#170707", "#7a1f1f", "#e57373"), icon=GOLD, highlight=GOLD, rain=GOLD, rain_head="#ffffff"),
    "11 · Amethyst": dict(
        bg="#0b0710", box="#110a18", border=VIO, title="#f5e6ff", title_bg="#1d0f26", text="#f1e7f7", muted="#b9a3c9",
        btn="#1d0f26", btn_border="#3d2350", btn_hover="#2a1637", on="#b88ad0", on_border="#ffffff", on_text="#14081c",
        table_bg="#0e0814", head="#241430", head_text="#f5e6ff", grid="#33203f",
        spawn=(VIO, "#ffffff", "#ffffff"), draw=("#1d0f26", "#b88ad0", "#e9d5f5"), clear=("#1a070d", "#86304a", "#ff9db4"),
        icon="#d9b8ee", highlight="#b88ad0", rain="#b88ad0", rain_head="#ffffff"),
    "12 · Matrix Violett": dict(
        bg="#000000", box="#000000", border="#6d2a82", title="#ffffff", title_bg="#000000", text="#f0e6f5", muted="#a58bb3",
        btn="#0b0610", btn_border="#3a1d48", btn_hover="#1a0d22", on=VIO, on_border=GOLD, on_text="#ffffff",
        table_bg="#030205", head="#160a1d", head_text=GOLD, grid="#2a1535",
        spawn=(VIO, GOLD, "#ffffff"), draw=("#0b0610", VIO, "#e6d0f0"), clear=("#000000", "#8e2a3a", "#ff8fa0"),
        icon=GOLD, highlight=VIO, rain=VIO, rain_head=GOLD),
    "13 · Matrix Grün": dict(
        bg="#000000", box="#000000", border="#0f7a2e", title="#00ff41", title_bg="#000000", text="#c8ffd4", muted="#6fbf86",
        btn="#03120a", btn_border="#0f5a25", btn_hover="#062a14", on="#0f7a2e", on_border="#00ff41", on_text="#eafff0",
        table_bg="#010603", head="#03150a", head_text="#00ff41", grid="#0a2e16",
        spawn=("#003b14", "#00ff41", "#00ff41"), draw=("#03120a", "#0f7a2e", "#c8ffd4"), clear=("#120303", "#7a1f1f", "#ff6b6b"),
        icon="#00ff41", highlight="#0f7a2e", rain="#00ff41", rain_head="#eafff0", field="#0f7a2e", focus="#00ff41"),
    # --- dritte Runde ---
    "14 · Onyx Violett": dict(
        bg="#000000", box="#000000", border=VIO, title="#ffffff", title_bg="#000000", text="#f2f2f2", muted="#a99fb3",
        btn="#0e0b12", btn_border="#3a2d45", btn_hover="#1c1524", on=VIO, on_border="#ffffff", on_text="#ffffff",
        table_bg="#060509", head="#120d17", head_text=GOLD, grid="#241c2c",
        spawn=(VIO, "#ffffff", "#ffffff"), draw=("#0e0b12", GOLD, GOLD), clear=("#0e0b12", "#8e2a3a", "#ff9aa8"),
        icon="#ffffff", highlight=VIO, rain=VIO, rain_head=GOLD),
    "15 · Lila Neon": dict(
        bg="#030104", box="#030104", border="#c45cff", title="#ffffff", title_bg="#140619", text="#ffffff", muted="#d3a6ea",
        btn="#0d0412", btn_border="#6a2a86", btn_hover="#1d0a27", on="#c45cff", on_border="#ffffff", on_text="#ffffff",
        table_bg="#050207", head="#25092f", head_text="#ffffff", grid="#3c1650",
        spawn=(_grad("#c45cff", "#7a2aa0"), "#ffffff", "#ffffff"), draw=("#0d0412", "#ffd166", "#ffd166"),
        clear=("#0d0412", "#ff4d6d", "#ff4d6d"), icon="#e9b8ff", highlight="#c45cff", rain="#c45cff", rain_head="#ffffff",
        focus="#ffd166"),
    "16 · Gold-Weiß Premium": dict(
        bg="#000000", box="#000000", border=GOLD, title="#ffffff", title_bg="#000000", text="#ffffff", muted="#c9bb8f",
        btn="#0d0c09", btn_border="#4a3f1c", btn_hover="#1a1710", on="#ffffff", on_border=GOLD, on_text="#000000",
        table_bg="#060605", head="#14120a", head_text=GOLD, grid="#2a2516",
        spawn=(_grad("#e6c45a", "#a8841f"), "#ffffff", "#000000"), draw=("#000000", "#ffffff", "#ffffff"),
        clear=("#000000", "#7a1f1f", "#e57373"), icon=GOLD, highlight=GOLD, rain=GOLD, rain_head="#ffffff", focus="#ffffff"),
    "17 · Violett-Gold Verlauf": dict(
        bg="#060408", box="#0a070d", border=VIO, title="#ffffff", title_bg=_hgrad(VIO, "#9c7c1c"), text="#f5f0f7",
        muted="#b9a3c9", btn="#120d16", btn_border="#3d2a48", btn_hover="#1f1626",
        on=_hgrad(VIO, "#b8901f"), on_border="#ffffff", on_text="#ffffff",
        table_bg="#08060a", head="#1b1222", head_text=GOLD, grid="#2a1f31",
        spawn=(_hgrad(VIO, "#c9a227"), "#ffffff", "#ffffff"), draw=("#120d16", GOLD, GOLD),
        clear=("#120d16", "#8e2a3a", "#ff9aa8"), icon=GOLD, highlight=VIO, rain=VIO, rain_head=GOLD),
    "18 · Stealth": dict(
        bg="#050505", box="#050505", border="#262626", title="#ffffff", title_bg="#050505", text="#e8e8e8", muted="#8c8c8c",
        btn="#0f0f0f", btn_border="#2a2a2a", btn_hover="#1a1a1a", on=VIO, on_border="#ffffff", on_text="#ffffff",
        table_bg="#080808", head="#101010", head_text="#ffffff", grid="#1f1f1f",
        spawn=("#0f0f0f", VIO, GOLD), draw=("#0f0f0f", "#3a3a3a", "#e8e8e8"), clear=("#0f0f0f", "#5a1f1f", "#ef7676"),
        icon="#bdbdbd", highlight=VIO, rain=VIO, rain_head="#ffffff"),
}
THEME = "1 · Obsidian Violett"
MATRIX_ON = False  # animierter Matrix-Regen im Dashboard-Hintergrund

def rgba(color, alpha):
    q = QColor(color)
    return f"rgba({q.red()}, {q.green()}, {q.blue()}, {alpha})"

def panel_css(t):
    """Stylesheet fürs Dashboard aus den Theme-Farben."""
    sp, dr, cl = t["spawn"], t["draw"], t["clear"]
    # beim Matrix-Regen sind Kästen und Tabelle leicht durchsichtig, damit der Regen durchschimmert
    box = rgba(t["box"], 105) if MATRIX_ON else t["box"]
    table_bg = rgba(t["table_bg"], 165) if MATRIX_ON else t["table_bg"]
    return f"""
        QDialog {{ background-color: {t['bg']}; }}
        QLabel {{ color: {t['text']}; }}
        QGroupBox#topBox, QGroupBox#btnBox {{ background-color: {box}; border: 1px solid {t['border']}; border-radius: 5px; }}
        QGroupBox#topBox {{ margin-top: 5px; }}
        QGroupBox#btnBox {{ margin-top: 0px; padding: 0px; }}
        QGroupBox#tableBox {{ background-color: {box}; border: 1px solid {t['border']}; border-radius: 5px;
                              margin-top: 15px; font-weight: bold; color: {t['text']}; }}
        QGroupBox#tableBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 2px 8px;
                                     background-color: {t['bg']}; border: 1px solid {t['border']}; border-radius: 4px; color: {t['title']}; }}
        QFrame#titleBox {{ background-color: {t['title_bg']}; border: 1px solid {t['border']}; border-radius: 4px; }}
        QLabel#title {{ font-weight: bold; font-size: 14px; color: {t['title']}; border: none; background: transparent; }}
        QFrame#line {{ color: {t['border']}; }}
        QLabel#rules {{ color: {t['muted']}; font-size: 11px; border: none; background: transparent; }}
        QPushButton#toggle {{ background-color: {t['btn']}; color: {t['text']}; border: 1px solid {t['btn_border']};
                              border-radius: 4px; padding: 4px 8px; font-size: 11px; min-width: 50px; }}
        QPushButton#toggle:checked {{ background-color: {t['on']}; color: {t['on_text']}; border: 1px solid {t['on_border']}; font-weight: bold; }}
        QPushButton#gear, QPushButton#tool {{ background-color: {t['btn']}; border: 1px solid {t['btn_border']}; border-radius: 4px; padding: 0px; }}
        QPushButton#tool:checked {{ background-color: {t['on']}; border: 1px solid {t['on_border']}; }}
        QPushButton#toggle:hover, QPushButton#gear:hover, QPushButton#tool:hover {{ background-color: {t['btn_hover']}; }}
        QPushButton#spawn, QPushButton#draw, QPushButton#clear {{ padding: 8px; border-radius: 4px; font-size: 12px; }}
        QPushButton#spawn {{ background-color: {sp[0]}; border: 1px solid {sp[1]}; color: {sp[2]}; font-weight: bold; }}
        QPushButton#draw {{ background-color: {dr[0]}; border: 1px solid {dr[1]}; color: {dr[2]}; }}
        QPushButton#clear {{ background-color: {cl[0]}; border: 1px solid {cl[1]}; color: {cl[2]}; }}
        QPushButton#spawn:hover, QPushButton#draw:hover, QPushButton#clear:hover {{ border: 1px solid {t['title']}; }}
        QTableWidget {{ background-color: {table_bg}; gridline-color: {t['grid']}; color: {t['text']}; border: 1px solid {t['border']}; }}
        QHeaderView::section {{ background-color: {t['head']}; color: {t['head_text']}; font-weight: bold; border: 1px solid {t['grid']}; padding: 2px; }}
        QTableWidget::item {{ border-bottom: 1px solid {t['grid']}; border-right: 1px solid {t['grid']}; }}
    """ + indicator_css(t)

def check_image(color):
    """Häkchen als PNG - in Stylesheets kann Qt ein Häkchen nur als Bild anzeigen."""
    path = os.path.join(APP_DIR, f"check_{QColor(color).name()[1:]}.png")
    if not os.path.exists(path):
        pm = QPixmap(13, 13); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(QPointF(3, 6.8), QPointF(5.6, 9.4)); p.drawLine(QPointF(5.6, 9.4), QPointF(10.2, 3.6)); p.end()
        pm.save(path)
    return path.replace("\\", "/")

def indicator_css(t):
    """Kästchen für Häkchen (Tabelle und Einstellungen) - sonst sind leere Kästchen auf Schwarz unsichtbar."""
    check = check_image("#000000" if QColor(t["highlight"]).lightness() > 140 else "#ffffff")
    return f"""
        QCheckBox::indicator, QTableWidget::indicator {{ width: 13px; height: 13px; border: 1px solid {t['border']};
                                                        border-radius: 3px; background-color: {t['table_bg']}; }}
        QCheckBox::indicator:checked, QTableWidget::indicator:checked {{ background-color: {t['highlight']};
                                                                        border: 1px solid {t['highlight']}; image: url({check}); }}
        QCheckBox::indicator:hover, QTableWidget::indicator:hover {{ border: 1px solid {t['title']}; }}
    """

def mix(c1, c2, f):
    a, b = QColor(c1), QColor(c2)
    return QColor(int(a.red() + (b.red() - a.red()) * f), int(a.green() + (b.green() - a.green()) * f),
                  int(a.blue() + (b.blue() - a.blue()) * f)).name()

def arrow_image(color, up):
    """Kleiner Pfeil für Zahlenfelder und Auswahllisten (wie das Häkchen als PNG)."""
    path = os.path.join(APP_DIR, f"arrow_{'up' if up else 'down'}_{QColor(color).name()[1:]}.png")
    if not os.path.exists(path):
        pm = QPixmap(9, 5); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(QColor(color))
        pts = [QPointF(0, 5), QPointF(9, 5), QPointF(4.5, 0)] if up else [QPointF(0, 0), QPointF(9, 0), QPointF(4.5, 5)]
        p.drawPolygon(QPolygonF(pts)); p.end()
        pm.save(path)
    return path.replace("\\", "/")

def field_css(t):
    """Eingabefelder mit sichtbarem Rahmen - das Feld, in dem man gerade tippt, leuchtet in der Akzentfarbe."""
    fb, focus = t.get("field", "#b8b8b8"), t.get("focus", GOLD)
    bg = mix(t["bg"], "#ffffff", 0.07)  # etwas heller als der Hintergrund, damit man das Feld sieht
    up, down = arrow_image(t["text"], True), arrow_image(t["text"], False)
    return f"""
        QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{ background-color: {bg}; color: {t['text']};
            border: 1px solid {fb}; border-radius: 3px; padding: 2px 4px; min-height: 18px; }}
        QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QLineEdit:hover {{ border: 1px solid {focus}; }}
        QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {{ border: 2px solid {focus}; padding: 1px 3px; }}
        QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{ color: {t['muted']}; border: 1px solid {t['grid']}; }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right;
            width: 16px; border-left: 1px solid {fb}; border-bottom: 1px solid {fb}; }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right;
            width: 16px; border-left: 1px solid {fb}; }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover,
        QDoubleSpinBox::down-button:hover {{ background-color: {t['highlight']}; }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({up}); width: 9px; height: 5px; }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({down}); width: 9px; height: 5px; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 18px; border-left: 1px solid {fb}; }}
        QComboBox::down-arrow {{ image: url({down}); width: 9px; height: 5px; }}
        QComboBox QAbstractItemView {{ background-color: {bg}; color: {t['text']}; border: 1px solid {fb};
            selection-background-color: {t['highlight']}; selection-color: #ffffff; }}
        QSlider {{ min-width: 120px; }}
        QSlider::groove:horizontal {{ height: 4px; background: {mix(t['bg'], fb, 0.45)}; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {t['highlight']}; border-radius: 2px; }}
        QSlider::handle:horizontal {{ width: 12px; margin: -5px 0; border-radius: 6px; background: {focus}; border: 1px solid {fb}; }}
    """

def apply_app_palette(t):
    """Fusion-Stil mit den Theme-Farben - damit passen auch Häkchen, Auswahllisten und Dialoge zum Design."""
    app = QApplication.instance()
    app.setStyle("Fusion")
    pal = QPalette()
    for role, key in ((QPalette.Window, "bg"), (QPalette.WindowText, "text"), (QPalette.Base, "table_bg"),
                      (QPalette.AlternateBase, "head"), (QPalette.Text, "text"), (QPalette.Button, "bg"),
                      (QPalette.ButtonText, "text"), (QPalette.ToolTipBase, "bg"), (QPalette.ToolTipText, "text"),
                      (QPalette.Highlight, "highlight"), (QPalette.BrightText, "title")):
        pal.setColor(role, QColor(t[key]))
    pal.setColor(QPalette.HighlightedText, QColor("#000000" if QColor(t["highlight"]).lightness() > 140 else "#ffffff"))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        pal.setColor(QPalette.Disabled, role, QColor(t["muted"]))
    app.setPalette(pal)

# ===== HOTKEYS =====
# ID -> Aktion (die IDs gehen an RegisterHotKey und kommen mit WM_HOTKEY zurück)
HK_ACTIONS = {1: "Bearbeiten", 2: "Zeichnen", 3: "Löschen", 4: "Beenden", 5: "Verstecken"}
HK_DEFAULTS = {1: "F7", 2: "F8", 3: "F9", 4: "F10", 5: "F6"}
HK_MODS = {"Ctrl": MOD_CONTROL, "Alt": MOD_ALT, "Shift": MOD_SHIFT, "Meta": MOD_WIN}

def parse_hotkey(text):
    """'Ctrl+Shift+F9' -> (Modifier, Virtual-Key). None, wenn das kein brauchbarer globaler Hotkey ist."""
    parts = text.split(", ")[0].split("+") if text else []
    if not parts or not parts[-1]: return None
    mods, key = 0, parts[-1]
    for m in parts[:-1]:
        if m not in HK_MODS: return None
        mods |= HK_MODS[m]
    if key[0] == "F" and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        return mods, 0x6F + int(key[1:])
    # Buchstaben/Zahlen nur mit Strg/Alt/Win - sonst wäre die Taste beim Tippen überall weg
    if len(key) == 1 and key.isascii() and key.isalnum() and mods & (MOD_CONTROL | MOD_ALT | MOD_WIN):
        return mods, ord(key.upper())
    return None

def recalc_setup(s):
    s["r"] = s["sl"] - s["entry"]
    s["be"] = s["entry"] - 2.0 * s["r"]
    r1 = GLOBAL_TP1_R if USE_GLOBAL_R else s["r_tp1"]
    r2 = GLOBAL_TP2_R if USE_GLOBAL_R else s["r_tp2"]
    r3 = GLOBAL_TP3_R if USE_GLOBAL_R else s["r_tp3"]
    s["tp1"] = s["entry"] - r1 * s["r"]
    s["tp2"] = s["entry"] - r2 * s["r"]
    s["tp3"] = s["entry"] - r3 * s["r"]

for s in SETUPS: recalc_setup(s)

# ===== SPEICHERN / LADEN =====
SETUP_KEYS = ["entry", "sl", "r_tp1", "r_tp2", "r_tp3", "active"] + \
             [f"{p}_{k}" for k in LINE_KEYS for p in ("color", "thick", "style", "show")]

def settings_to_dict(ov):
    setups = [{k: (s[k].name(QColor.HexArgb) if k.startswith("color_") else s[k]) for k in SETUP_KEYS}
              for s in SETUPS]
    return {
        "use_global_r": USE_GLOBAL_R,
        "global_r": [GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R],
        "auto_resize": AUTO_RESIZE_WINDOW,
        "show_rules": SHOW_RULES,
        "spacing": [MARGIN_TOP, GAP_1, GAP_2, MARGIN_BOTTOM],
        "price_ref": PRICE_REF,
        "price_decimals": PRICE_DECIMALS,
        "magnet_on": MAGNET_ON,
        "magnet_mode": MAGNET_MODE,
        "version": SETTINGS_VERSION,
        "tools": {k: style_to_json(v) for k, v in TOOL_STYLES.items()},
        "fib_style": style_to_json(FIB_STYLE),
        "ext_style": style_to_json(EXT_STYLE),
        "matrix_style": style_to_json(MATRIX_STYLE),
        "theme": THEME,
        "matrix": MATRIX_ON,
        "fib_extra": [{"value": l["value"], "color": l["color"].name(QColor.HexArgb), "on": l["on"]} for l in FIB_EXTRA],
        "line_length": ov.line_length,
        "show_price_input": ov.show_price_input,
        "locked": ov.is_locked,
        "hotkeys": {str(k): v for k, v in ov.hk_map.items()},
        "setups": setups,
    }

def apply_settings(data, ov):
    """Übernimmt gespeicherte Werte. Was in der Datei fehlt, bleibt wie es ist."""
    global USE_GLOBAL_R, GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R, AUTO_RESIZE_WINDOW, SHOW_RULES
    global PRICE_REF, PRICE_DECIMALS, MARGIN_TOP, GAP_1, GAP_2, MARGIN_BOTTOM, MAGNET_ON, MAGNET_MODE, THEME, MATRIX_ON
    USE_GLOBAL_R = bool(data.get("use_global_r", USE_GLOBAL_R))
    if "global_r" in data:
        GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R = (float(v) for v in data["global_r"])
    AUTO_RESIZE_WINDOW = bool(data.get("auto_resize", AUTO_RESIZE_WINDOW))
    SHOW_RULES = bool(data.get("show_rules", SHOW_RULES))
    if "spacing" in data:
        MARGIN_TOP, GAP_1, GAP_2, MARGIN_BOTTOM = (int(v) for v in data["spacing"])
    if data.get("price_ref") in ("hl", "entry"): PRICE_REF = data["price_ref"]
    PRICE_DECIMALS = int(data.get("price_decimals", PRICE_DECIMALS))
    MAGNET_ON = bool(data.get("magnet_on", MAGNET_ON))
    if data.get("magnet_mode") in ("weak", "strong"): MAGNET_MODE = data["magnet_mode"]
    if data.get("theme") in THEMES: THEME = data["theme"]
    MATRIX_ON = bool(data.get("matrix", MATRIX_ON))
    if "fib_extra" in data:
        FIB_EXTRA[:] = [{"value": float(d["value"]), "color": QColor(d["color"]), "on": bool(d["on"])} for d in data["fib_extra"]]
    if data.get("version", 1) >= 2:  # ältere Dateien: neue Werkzeug-Standards (weiß, Dicke 2) behalten
        for k, v in data.get("tools", {}).items():
            if k in TOOL_STYLES: style_from_json(TOOL_STYLES[k], v)
    style_from_json(FIB_STYLE, data.get("fib_style", {}))
    style_from_json(EXT_STYLE, data.get("ext_style", {}))
    style_from_json(MATRIX_STYLE, data.get("matrix_style", {}))
    ov.line_length = int(data.get("line_length", ov.line_length))
    ov.show_price_input = bool(data.get("show_price_input", ov.show_price_input))
    ov.is_locked = bool(data.get("locked", ov.is_locked))
    for k, v in data.get("hotkeys", {}).items():
        if int(k) in HK_ACTIONS: ov.hk_map[int(k)] = str(v)
    for s, d in zip(SETUPS, data.get("setups", [])):
        for k in SETUP_KEYS:
            if k not in d: continue
            if k.startswith("color_"): s[k] = QColor(d[k])
            elif k.startswith("thick_"): s[k] = int(d[k])
            elif k.startswith("style_"): s[k] = str(d[k])
            elif k.startswith("show_") or k == "active": s[k] = bool(d[k])
            else: s[k] = float(d[k])
    for s in SETUPS: recalc_setup(s)

def read_json(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)  # erst komplett schreiben, dann tauschen -> nie eine halbe Datei

# ===== MAGNET =====
def grab_screen(x, y, w, h):
    """Bildschirmausschnitt (globale Pixel) als BGRA-Bytes, Zeile für Zeile von oben."""
    scr = user32.GetDC(None); mem = gdi32.CreateCompatibleDC(scr)
    bmp = gdi32.CreateCompatibleBitmap(scr, w, h); old = gdi32.SelectObject(mem, bmp)
    gdi32.BitBlt(mem, 0, 0, w, h, scr, x, y, SRCCOPY)
    bmi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.SelectObject(mem, old); gdi32.DeleteObject(bmp); gdi32.DeleteDC(mem); user32.ReleaseDC(None, scr)
    return buf.raw

def find_wick(buf, w, h, cx, cy, strong):
    """Sucht im Bildausschnitt die Kerze bei (cx, cy) und gibt Hoch oder Tief (x, y) zurück - sonst None.
    Kerzen erkennt man an kräftiger Farbe (grün/rot), Hintergrund, Gitter und Schrift sind grau."""
    def chroma(x, y):
        i = (y * w + x) * 4
        b, g, r = buf[i], buf[i + 1], buf[i + 2]
        return max(r, g, b) - min(r, g, b)
    # 1) Startpunkt: der farbige Pixel am nächsten zum Cursor
    #    schwach = nur im Umkreis von 20 px, stark = irgendwo in der Spalte unter dem Cursor
    rx, ry = (12, h) if strong else (20, 20)
    seed = best = None
    for y in range(max(0, cy - ry), min(h, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(w, cx + rx + 1)):
            if chroma(x, y) > 60:
                d = abs(x - cx) * 8 + abs(y - cy) if strong else (x - cx) ** 2 + (y - cy) ** 2
                if best is None or d < best: seed, best = (x, y), d
    if seed is None: return None
    # 2) ganze Kerze (Docht + Körper) einsammeln - schwächere Farbe zählt mit, damit die Dochtspitze dazugehört
    seen = bytearray(w * h); seen[seed[1] * w + seed[0]] = 1
    stack = [seed]
    top_y = bot_y = seed[1]; top_x, bot_x = [seed[0]], [seed[0]]
    x0 = x1 = seed[0]; count = 0
    while stack:
        x, y = stack.pop(); count += 1
        if count > 50000: return None  # riesige Fläche (z. B. Flächen-Chart) - keine Kerze
        if y < top_y: top_y, top_x = y, [x]
        elif y == top_y: top_x.append(x)
        if y > bot_y: bot_y, bot_x = y, [x]
        elif y == bot_y: bot_x.append(x)
        x0, x1 = min(x0, x), max(x1, x)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and chroma(nx, ny) > 35:
                seen[ny * w + nx] = 1; stack.append((nx, ny))
    if x1 - x0 > 80 or x0 == 0 or x1 == w - 1: return None  # zu breit / läuft raus (z. B. Preislinie) - keine Kerze
    # 3) Hoch oder Tief - was näher am Cursor liegt. Was am Ausschnittrand abgeschnitten ist, zählt nicht.
    cands = []
    if top_y > 0: cands.append((sorted(top_x)[len(top_x) // 2], top_y))
    if bot_y < h - 1: cands.append((sorted(bot_x)[len(bot_x) // 2], bot_y))
    if not cands: return None
    pt = min(cands, key=lambda c: abs(c[1] - cy))
    if not strong and abs(pt[1] - cy) > 25: return None
    return pt

def analyze_candles(buf, w, h, step=2):
    """Kerzen im Bildausschnitt finden. Gibt (Kerzenabstand in px oder None, x und y vom Schlusskurs der Kerze
    ganz rechts) zurück - sonst None. Jede 2. Zeile reicht und hält die Rechenzeit klein."""
    stride, col_rows = w * 4, [[] for _ in range(w)]
    for y in range(0, h, step):
        row = buf[y * stride:(y + 1) * stride]
        for x, (mx, mn) in enumerate(zip(map(max, row[0::4], row[1::4], row[2::4]),
                                         map(min, row[0::4], row[1::4], row[2::4]))):
            if mx - mn > 60: col_rows[x].append(y)
    # Kerzen = Gruppen nebeneinanderliegender farbiger Spalten (breite Gruppen sind Linien, keine Kerzen)
    runs, x = [], 0
    while x < w:
        if col_rows[x]:
            x0 = x
            while x < w and col_rows[x]: x += 1
            if x - x0 <= 60: runs.append((x0, x - 1))
        x += 1
    if not runs: return None
    centers = [(a + b) / 2 for a, b in runs]
    gaps = sorted(b - a for a, b in zip(centers, centers[1:]) if b - a >= 3)
    spacing = int(round(gaps[len(gaps) // 2])) if len(gaps) >= 2 else None
    a, b = runs[-1]
    ys = sorted(y for c in range(a, b + 1) for y in col_rows[c])
    mid_x, mid_y = (a + b) // 2, ys[len(ys) // 2]
    i = (mid_y * w + mid_x) * 4
    green = buf[i + 1] > buf[i + 2]
    # Körper = Zeilen, in denen die Kerze breiter als der Docht ist; Schluss = oben (grün) bzw. unten (rot)
    counts = {}
    for c in range(a, b + 1):
        for y in col_rows[c]: counts[y] = counts.get(y, 0) + 1
    body = [y for y, n in counts.items() if n >= max(2, (b - a + 1) // 2)] or ys
    return spacing, (a + b) // 2, (min(body) if green else max(body))

def dist_to_segment(p, a, b):
    """Abstand von Punkt p zur Strecke a-b (QPointF)."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    l2 = dx * dx + dy * dy
    t = 0 if l2 == 0 else max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / l2))
    return math.hypot(p.x() - a.x() - t * dx, p.y() - a.y() - t * dy)

# ===== SYMBOLE =====
def gear_icon(color="#dddddd"):
    """Zahnrad selbst gezeichnet - sitzt im Gegensatz zum Emoji exakt mittig im Button."""
    n = 64
    c, r_out, r_in, r_hole = n / 2, n * 0.48, n * 0.34, n * 0.15
    gear = QPainterPath(); gear.addEllipse(QPointF(c, c), r_in, r_in)
    tooth = QPainterPath(); tooth.addRect(QRectF(c - n * 0.085, c - r_out, n * 0.17, r_out - r_in + 2))
    for i in range(8):
        gear = gear.united(QTransform().translate(c, c).rotate(i * 45).translate(-c, -c).map(tooth))
    hole = QPainterPath(); hole.addEllipse(QPointF(c, c), r_hole, r_hole)
    pm = QPixmap(n, n); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.fillPath(gear.subtracted(hole), QColor(color)); p.end()
    return QIcon(pm)

def tool_icon(kind, color="#dddddd"):
    """Symbole für die Zeichenwerkzeuge und den Magnet - wie bei TradingView."""
    n = 64
    pm = QPixmap(n, n); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    c = QColor(color)
    p.setPen(QPen(c, 5, Qt.SolidLine, Qt.RoundCap))
    def dot(x, y):
        p.setBrush(QColor("#222")); p.drawEllipse(QPointF(x, y), 7, 7)
    if kind == "trend":
        p.drawLine(QPointF(12, 52), QPointF(52, 12)); dot(12, 52); dot(52, 12)
    elif kind == "ray":
        p.drawLine(QPointF(12, 52), QPointF(62, 2)); dot(12, 52); dot(34, 30)
    elif kind == "hline":
        p.drawLine(QPointF(2, 32), QPointF(62, 32)); dot(32, 32)
    elif kind == "hray":
        p.drawLine(QPointF(14, 32), QPointF(62, 32)); dot(14, 32)
    elif kind == "rect":
        p.setBrush(QColor(c.red(), c.green(), c.blue(), 70)); p.drawRect(QRectF(8, 16, 48, 32))
    elif kind == "magnet":
        u = QPainterPath(); u.moveTo(18, 8); u.lineTo(18, 32)
        u.arcTo(QRectF(18, 18, 28, 28), 180, 180); u.lineTo(46, 8)
        p.setPen(QPen(c, 10, Qt.SolidLine, Qt.FlatCap)); p.setBrush(Qt.NoBrush); p.drawPath(u)
        p.fillRect(QRectF(13, 4, 10, 9), QColor("#ff5252")); p.fillRect(QRectF(41, 4, 10, 9), QColor("#ff5252"))
    p.end()
    return QIcon(pm)

def color_btn_css(color):
    return f"background-color: {color.name()}; border: 1px solid #777; border-radius: 3px;"

def bring_window_to_front(w):
    """Fenster zeigen und nach vorne holen - auch wenn es in die Taskleiste minimiert war."""
    if w.isMinimized(): w.showNormal()
    else: w.show()
    w.setWindowState((w.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
    hwnd = int(w.winId())
    if user32.IsIconic(hwnd): user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    w.raise_(); w.activateWindow()

# ===== CRASH-LOGGER =====
_crash_shown = False

def log_uncaught_exceptions(ex_cls, ex, tb):
    global _crash_shown
    error_msg = "".join(traceback.format_exception(ex_cls, ex, tb))
    with open(CRASH_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n--- CRASH am {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')} ---\n{error_msg}")
    print(error_msg)
    # Fehler im paintEvent kommen oft mehrfach hintereinander - nur ein Fenster zeigen
    if _crash_shown or not QApplication.instance(): return
    _crash_shown = True
    for w in QApplication.topLevelWidgets():
        if w.isVisible(): w.hide()
    msg = QMessageBox()
    msg.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Das Programm ist abgestürzt!")
    msg.setInformativeText(f"Der Fehler wurde gespeichert in:\n{CRASH_LOG}")
    msg.setDetailedText(error_msg)
    msg.setWindowTitle("Crash")
    msg.exec_()

sys.excepthook = log_uncaught_exceptions
# =========================

class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, ov): super().__init__(); self.ov = ov
    def nativeEventFilter(self, evType, msg):
        if evType in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            try: m = wintypes.MSG.from_address(int(msg))
            except Exception: return False, 0
            if m.message == WM_HOTKEY:
                {1: self.ov._hk_edit, 2: self.ov._hk_draw,
                 3: self.ov._hk_clear, 4: self.ov._hk_quit, 5: self.ov._hk_toggle_hide}.get(m.wParam, lambda: None)()
                return True, 0
        return False, 0

class FibOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        vr = QApplication.primaryScreen().geometry()
        for s in QApplication.screens(): vr = vr.united(s.geometry())
        self.setGeometry(vr)
        self.fibs = []          # mehrere Fibs möglich: {"p1", "p2", "price_ref"} - price_ref = [(fib, preis), (fib, preis)]
        self.placing_fib = None # Fib, die gerade gesetzt wird (nach dem 1. Klick)
        self.hover = None
        self.mode = "idle"
        self.tool = None        # was gerade gesetzt wird: "fib" oder ein Zeichenwerkzeug
        self.drawings = []      # einzelne Zeichnungen: {"type", "p1", "p2", "color", "width", "style", ...}
        self.pending = None     # Zeichnung, die gerade entsteht (nach dem 1. Klick)
        self.dragging = None    # (art, index, teil): art "fib"/"draw", teil "p1"/"p2"/"move"
        self.drag_start = self.drag_orig = None
        self._hwnd = None
        self.main_panel = None  # Referenz auf das Dashboard
        self._dialog = None
        self.candle_px = 12     # gemessener Kerzenabstand in Pixeln (für "Verlängerung um N Kerzen")
        self.alert_text, self.alert_until = None, 0.0

        self.line_length = 800
        self.show_price_input = True
        self.is_locked = False
        self.is_hidden = False

        self.hk_map = dict(HK_DEFAULTS)
        # Kurs-Beobachtung für die Verlängerung (Farbe rot/grün, Alarm) - tut nichts, solange sie aus ist
        self.watch_timer = QTimer(self); self.watch_timer.setInterval(700)
        self.watch_timer.timeout.connect(self._watch_price); self.watch_timer.start()

    def showEvent(self, e):
        super().showEvent(e)
        if self._hwnd is None:
            self._hwnd = int(self.winId())
            self._set_ct(True)
            failed = self.register_hotkeys()
            if failed: QTimer.singleShot(500, lambda: self.warn_hotkeys(failed))

    def register_hotkeys(self):
        """Meldet alle Hotkeys neu an. Gibt die zurück, die Windows abgelehnt hat (z. B. schon von anderem Programm belegt)."""
        if self._hwnd is None: return []
        for i in HK_ACTIONS: user32.UnregisterHotKey(self._hwnd, i)
        failed = []
        for i, key_name in self.hk_map.items():
            hk = parse_hotkey(key_name)
            if hk is None or not user32.RegisterHotKey(self._hwnd, i, hk[0] | MOD_NOREPEAT, hk[1]):
                failed.append(f"{HK_ACTIONS[i]}: {key_name}")
        return failed

    def warn_hotkeys(self, failed, parent=None):
        QMessageBox.warning(parent or self.main_panel, "Hotkeys",
            "Diese Hotkeys konnten nicht belegt werden (wahrscheinlich nutzt ein anderes Programm sie schon):\n\n"
            + "\n".join(failed) + "\n\nIn den Einstellungen kannst du andere Tasten wählen.")

    def _set_ct(self, on):
        if self._hwnd is None: self._hwnd = int(self.winId())
        ex = user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
        ex = (ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW) if on \
             else (ex & ~WS_EX_TRANSPARENT)
        user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, ex)
        user32.SetWindowPos(self._hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)

    def _update_ct(self):
        # Klicks gehen komplett durch, wenn versteckt, fixiert oder nichts zu bearbeiten ist
        if self._hwnd is None: return
        self._set_ct(self.is_hidden or self.is_locked or self.mode == "idle")

    def has_content(self):
        return bool(self.fibs) or bool(self.drawings)

    def settings_changed(self):
        self.update()
        if self.main_panel: self.main_panel.schedule_save()

    def set_hidden(self, on):
        self.is_hidden = on
        self._update_ct()
        if self.main_panel: self.main_panel.sync_buttons()
        self.update()

    def set_locked(self, on):
        self.is_locked = on
        self.dragging = None
        self._update_ct()
        if self.main_panel: self.main_panel.sync_buttons()
        self.settings_changed()

    def _activate(self, mode, cursor):
        self.mode = mode
        self.is_hidden = self.is_locked = False  # wer zeichnet/bearbeitet, will es sehen und anfassen
        if self.main_panel: self.main_panel.sync_buttons()
        self._set_ct(False)
        self.setCursor(cursor)
        user32.SetForegroundWindow(self._hwnd)
        user32.BringWindowToTop(self._hwnd)
        self.raise_(); self.activateWindow(); self.settings_changed()

    def _hk_toggle_hide(self):
        self.set_hidden(not self.is_hidden)

    def _hk_draw(self):
        self.pending = self.placing_fib = self.hover = None
        self.tool = "fib"
        self._activate("placing", Qt.CrossCursor)

    def start_tool(self, kind):
        self.pending = self.placing_fib = None
        self.tool = kind
        self._activate("placing", Qt.CrossCursor)

    def spawn_default_fib(self):
        cx, cy = self.width() // 2, self.height() // 2
        off = 30 * (len(self.fibs) % 5)  # mehrere Sofort-Fibs nicht genau übereinander
        f = {"p1": QPoint(cx + 200 + off, cy - 200 + off),  # 0 oben rechts, 1 unten links - wie bei TradingView
             "p2": QPoint(cx - 200 + off, cy + 200 + off), "price_ref": None}
        self.fibs.append(f)
        self.tool = None
        self._activate("edit", Qt.OpenHandCursor)
        QTimer.singleShot(200, lambda: self._finish_placement(f))

    def _hk_edit(self):
        if self.has_content(): self._activate("edit", Qt.OpenHandCursor)

    def _hk_clear(self):
        self.fibs, self.drawings = [], []
        self.placing_fib = self.hover = self.pending = self.tool = self.dragging = None
        self.mode = "idle"
        self._set_ct(True); self.setCursor(Qt.ArrowCursor); self.update()
        if self.main_panel: self.main_panel.placement_finished()

    def _hk_quit(self):
        for i in HK_ACTIONS: user32.UnregisterHotKey(self._hwnd, i)
        QApplication.quit()

    def _end_placing(self):
        self.tool = self.pending = self.placing_fib = None
        self.mode = "edit" if self.has_content() else "idle"
        self._update_ct()
        self.setCursor(Qt.OpenHandCursor if self.mode == "edit" else Qt.ArrowCursor)
        self.update()
        if self.main_panel: self.main_panel.placement_finished()

    def cancel_placing(self):
        if self.placing_fib is not None:
            self.fibs = [f for f in self.fibs if f is not self.placing_fib]
        self.hover = None
        self._end_placing()

    def delete_item(self, kind, idx):
        if kind == "fib": del self.fibs[idx]
        else: del self.drawings[idx]
        self._end_placing()

    def duplicate(self, kind, idx):
        """Kopie leicht versetzt daneben legen."""
        off = QPoint(30, 30)
        if kind == "fib":
            f = self.fibs[idx]
            self.fibs.append({"p1": f["p1"] + off, "p2": f["p2"] + off, "price_ref": f["price_ref"]})
        else:
            d = dict(self.drawings[idx])
            d["p1"], d["p2"] = d["p1"] + off, d["p2"] + off
            for k in ("color", "fill_color"):
                if k in d: d[k] = QColor(d[k])
            self.drawings.append(d)
        self.update()

    def _obj(self, kind, idx):
        return self.fibs[idx] if kind == "fib" else self.drawings[idx]

    def _new_drawing(self, kind, pt):
        st = TOOL_STYLES[kind]
        d = {"type": kind, "p1": pt, "p2": pt, "color": QColor(st["color"]), "width": st["width"], "style": st["style"]}
        if kind == "rect":
            d.update(fill=st["fill"], fill_color=QColor(st["fill_color"]), fill_opacity=st["fill_opacity"], midline=st["midline"])
        return d

    def _hit(self, pos, pt, r=15):
        return pt is not None and (pos - pt).manhattanLength() <= r

    def _hit_test(self, pos):
        """Was liegt unter der Maus? (art, index, teil) oder None - art "fib"/"draw", teil "p1"/"p2"/"move"."""
        for i in reversed(range(len(self.fibs))):
            f = self.fibs[i]
            if self._hit(pos, f["p1"]): return ("fib", i, "p1")
            if self._hit(pos, f["p2"]): return ("fib", i, "p2")
        for i in reversed(range(len(self.drawings))):
            d = self.drawings[i]
            if d["type"] == "hline": continue
            if self._hit(pos, d["p1"], 10): return ("draw", i, "p1")
            if d["type"] != "hray" and self._hit(pos, d["p2"], 10): return ("draw", i, "p2")
        for i in reversed(range(len(self.drawings))):
            if self._on_drawing(pos, self.drawings[i]): return ("draw", i, "move")
        for i in reversed(range(len(self.fibs))):
            if self._on_fib(pos, self.fibs[i]): return ("fib", i, "move")
        return None

    def _on_fib(self, pos, f):
        if f["p2"] is None: return False
        x0, x1, y_of = self._fib_geom(f["p1"], f["p2"])
        if not (x0 <= pos.x() <= x1): return False
        ys = [y_of(lv["frac"]) for lv in self._fib_levels()]
        if not ys: return False  # alle Level ausgeschaltet
        if FIB_STYLE["background"] and min(ys) <= pos.y() <= max(ys): return True
        return any(abs(pos.y() - y) <= 5 for y in ys)

    def _fib_geom(self, a, b):
        """x-Bereich der Fib (wie TradingView: von Punkt zu Punkt) und eine Funktion Level -> y."""
        x0, x1 = min(a.x(), b.x()), max(a.x(), b.x())
        if x1 - x0 < 30: x1 = x0 + self.line_length  # Punkte genau übereinander -> feste Breite
        ext = FIB_STYLE["extend"]
        if ext != "none":
            scr = QApplication.screenAt(self.mapToGlobal(QPoint((x0 + x1) // 2, a.y()))) or QApplication.primaryScreen()
            g = scr.geometry()
            if ext in ("left", "both"): x0 = self.mapFromGlobal(g.topLeft()).x()
            if ext in ("right", "both"): x1 = self.mapFromGlobal(g.topRight()).x()
        ya, yb = (b.y(), a.y()) if FIB_STYLE["reverse"] else (a.y(), b.y())
        return x0, x1, lambda f: ya + (yb - ya) * f

    def _fib_levels(self):
        """Sichtbare Level, sortiert. Gleiche Werte (z. B. SL1 = E2) werden eine Linie mit beiden Namen."""
        groups = {}
        def add(frac, color, thick, style, name):
            g = groups.setdefault(round(frac, 6), {"frac": frac, "color": color, "thick": thick, "style": style, "names": []})
            if name: g["names"].append(name)
        if FIB_STYLE["show_0"]: add(0.0, FIB_STYLE["color_0"], 1, "Solid", None)
        if FIB_STYLE["show_1"]: add(1.0, FIB_STYLE["color_1"], 1, "Solid", None)
        for s in SETUPS:
            if not s["active"]: continue
            n = s["n"]
            for k, frac, label in (("e", s["entry"], f"E{n}"), ("sl", s["sl"], f"SL{n}"), ("be", s["be"], f"BE{n}"),
                                   ("tp1", s["tp1"], f"TP1_{n}"), ("tp2", s["tp2"], f"TP2_{n}"), ("tp3", s["tp3"], f"TP3_{n}")):
                if s[f"show_{k}"]: add(frac, s[f"color_{k}"], s[f"thick_{k}"], s[f"style_{k}"], label)
        for lv in FIB_EXTRA:
            if lv["on"]: add(lv["value"], lv["color"], 1, "Solid", None)
        return sorted(groups.values(), key=lambda g: g["frac"])

    def _level_text(self, lv, f):
        txt = fmt_level(lv["frac"])
        pr = self.price_at(f, lv["frac"]) if FIB_STYLE["prices"] else None
        if pr is not None: txt += f" ({fmt_price(pr)})"
        if FIB_STYLE["names"] and lv["names"]: txt += " · " + " · ".join(lv["names"])
        return txt

    def _screen_span(self, pt):
        # x-Bereich des Bildschirms, auf dem der Punkt liegt
        scr = QApplication.screenAt(self.mapToGlobal(pt)) or QApplication.primaryScreen()
        g = scr.geometry()
        return self.mapFromGlobal(g.topLeft()).x(), self.mapFromGlobal(g.topRight()).x()

    def _line_ends(self, d):
        """Anfang und Ende der Linie, wie sie gezeichnet wird (Strahlen laufen bis zum Rand)."""
        a, b = QPointF(d["p1"]), QPointF(d["p2"])
        if d["type"] == "hline":
            x0, x1 = self._screen_span(d["p1"]); return QPointF(x0, a.y()), QPointF(x1, a.y())
        if d["type"] == "hray":
            return a, QPointF(self._screen_span(d["p1"])[1], a.y())
        if d["type"] == "ray":
            v = b - a
            length = math.hypot(v.x(), v.y())
            return a, (b if length < 1 else a + v * (20000 / length))  # weit über den Bildschirmrand hinaus
        return a, b

    def _on_drawing(self, pos, d):
        p = QPointF(pos)
        if d["type"] == "rect":
            return QRectF(QPointF(d["p1"]), QPointF(d["p2"])).normalized().adjusted(-6, -6, 6, 6).contains(p)
        a, b = self._line_ends(d)
        return dist_to_segment(p, a, b) <= 6

    def snap(self, pos):
        """Magnet: Punkt an Hoch/Tief der Kerze darunter einrasten lassen (Overlay-Koordinaten rein und raus)."""
        if not MAGNET_ON or self._hwnd is None: return pos
        g = self.mapToGlobal(pos)
        scr = QApplication.screenAt(g)
        if not scr: return pos
        sg = scr.geometry()
        strong = MAGNET_MODE == "strong"
        x0, x1 = max(sg.left(), g.x() - 60), min(sg.right() + 1, g.x() + 61)
        y0, y1 = (sg.top(), sg.bottom() + 1) if strong else (max(sg.top(), g.y() - 150), min(sg.bottom() + 1, g.y() + 151))
        buf = self._grab_without_overlay(x0, y0, x1 - x0, y1 - y0)
        if buf is None: return pos
        hit = find_wick(buf, x1 - x0, y1 - y0, g.x() - x0, g.y() - y0, strong)
        return self.mapFromGlobal(QPoint(hit[0] + x0, hit[1] + y0)) if hit else pos

    def _grab_without_overlay(self, x, y, w, h):
        # eigene Linien aus dem Bildschirmfoto nehmen, sonst sieht der Magnet die Fib statt der Kerze
        if not user32.SetWindowDisplayAffinity(self._hwnd, WDA_EXCLUDEFROMCAPTURE): return None
        try: return grab_screen(x, y, w, h)
        finally: user32.SetWindowDisplayAffinity(self._hwnd, WDA_NONE)

    # ----- Verlängerung + Alarm -----
    def _watch_price(self):
        """Für die Verlängerung: letzte Kerze am Bildschirm suchen -> Kurs über oder unter dem Level? (Test-Funktion)"""
        if not (EXT_STYLE["on"] and (EXT_STYLE["live"] or EXT_STYLE["alarm"] or EXT_STYLE["pre_alert"] > 0)): return
        if self.is_hidden or self._hwnd is None or self.dragging or self.mode == "placing": return
        level, changed = EXT_STYLE["level"], False
        for f in self.fibs:
            if f["p2"] is None: continue
            x0, x1, y_of = self._fib_geom(f["p1"], f["p2"])
            if y_of(1) == y_of(0): continue
            ya, yb = sorted((y_of(0), y_of(1)))
            pad = (yb - ya) * 0.35 + 20  # etwas über/unter die Fib hinaus, aber nicht in Kopfzeile oder Menüs
            end = x1 + (EXT_STYLE["candles"] + 3) * self.candle_px
            scr = QApplication.screenAt(self.mapToGlobal(QPoint(int(x1), int(y_of(level)))))
            if not scr: continue
            sg = scr.geometry()
            g0, g1 = self.mapToGlobal(QPoint(int(x0), int(ya - pad))), self.mapToGlobal(QPoint(int(end), int(yb + pad)))
            gx0, gy0 = max(sg.left(), g0.x()), max(sg.top(), g0.y())
            gx1, gy1 = min(sg.right() + 1, g1.x()), min(sg.bottom() + 1, g1.y())
            if gx1 - gx0 < 10 or gy1 - gy0 < 10: continue
            buf = self._grab_without_overlay(gx0, gy0, gx1 - gx0, gy1 - gy0)
            res = analyze_candles(buf, gx1 - gx0, gy1 - gy0) if buf else None
            if not res: continue
            spacing, _, close_y = res
            if spacing and 3 <= spacing <= 80: self.candle_px = spacing
            oy = self.mapFromGlobal(QPoint(0, close_y + gy0)).y()   # Schlusskurs der letzten Kerze (Overlay-y)
            state = "up" if oy < y_of(level) else "down"            # kleiner y = höherer Kurs
            old = f.get("ext_state")
            if old and state != old and EXT_STYLE["alarm"]:
                self._alarm(f"Level {fmt_level(level)} gekreuzt – Kurs jetzt {'darüber' if state == 'up' else 'darunter'}")
            pre = EXT_STYLE["pre_alert"]
            if pre > 0:
                dist = abs((oy - y_of(0)) / (y_of(1) - y_of(0)) - level)
                if dist <= pre and not f.get("pre_done"):
                    f["pre_done"] = True
                    self._alarm(f"Vorwarnung: Kurs nur noch {fmt_level(round(dist, 3))} vom Level {fmt_level(level)} entfernt")
                elif dist > pre * 2: f["pre_done"] = False
            if state != old: f["ext_state"] = state; changed = True
        if changed: self.update()

    def _alarm(self, text):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        self.alert_text, self.alert_until = text, time.time() + 6
        self.update(); QTimer.singleShot(6100, self.update)

    # ----- Maus und Tastatur -----
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape and self.mode == "placing": self.cancel_placing()
        else: super().keyPressEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            if self.mode == "placing": self.cancel_placing()  # Rechtsklick bricht ab wie Esc
            else: self._context_menu(e.pos(), e.globalPos())
            return

        if e.button() != Qt.LeftButton or self.is_locked: return
        if self.mode == "placing":
            pt = self.snap(e.pos())
            if self.tool == "fib":
                f = self.placing_fib
                if f is None:
                    self.placing_fib = {"p1": pt, "p2": None, "price_ref": None}
                    self.fibs.append(self.placing_fib); self.update()
                else:
                    f["p2"] = pt; self.placing_fib = self.tool = None; self.mode = "edit"
                    self.setCursor(Qt.OpenHandCursor)
                    QTimer.singleShot(100, lambda: self._finish_placement(f))
                    self.update()
            elif self.pending is None:
                self.pending = self._new_drawing(self.tool, pt)
                if self.tool in ("hline", "hray"):
                    self.drawings.append(self.pending); self._end_placing()
                else: self.update()
            else:
                self.pending["p2"] = pt
                self.drawings.append(self.pending); self._end_placing()
        elif self.mode == "edit":
            hit = self._hit_test(e.pos())
            if not hit: return
            self.dragging, self.drag_start = hit, e.pos()
            o = self._obj(hit[0], hit[1])
            self.drag_orig = (QPoint(o["p1"]), QPoint(o["p2"]))
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self.is_locked: return
        if self.mode == "placing":
            if self.placing_fib is not None: self.hover = e.pos(); self.update()
            elif self.pending: self.pending["p2"] = e.pos(); self.update()
        elif self.mode == "edit" and self.dragging:
            kind, idx, part = self.dragging
            o = self._obj(kind, idx)
            if part == "move":
                delta = e.pos() - self.drag_start
                o["p1"], o["p2"] = self.drag_orig[0] + delta, self.drag_orig[1] + delta
            else:
                o[part] = e.pos()
                if o.get("type") in ("hline", "hray"): o["p2"] = o["p1"]
            self.update()

    def mouseReleaseEvent(self, e):
        if not self.dragging: return
        (kind, idx, part), self.dragging = self.dragging, None
        o = self._obj(kind, idx)
        # Magnet erst beim Loslassen - während des Ziehens wäre der Bildschirm-Scan zu langsam
        if part in ("p1", "p2"):
            o[part] = self.snap(o[part])
            if o.get("type") in ("hline", "hray"): o["p2"] = o["p1"]
        elif o.get("type") in ("hline", "hray"):
            y = self.snap(QPoint(e.pos().x(), o["p1"].y())).y()
            o["p1"] = o["p2"] = QPoint(o["p1"].x(), y)
        self.setCursor(Qt.OpenHandCursor)
        self.update()

    def mouseDoubleClickEvent(self, e):
        # Doppelklick: Fib -> Fib-Einstellungen, Zeichnung -> ihre Eigenschaften
        if e.button() != Qt.LeftButton or self.is_locked or self.mode != "edit": return
        hit = self._hit_test(e.pos())
        if not hit: return
        self.dragging = None
        if hit[0] == "fib":
            if self.main_panel: self.main_panel.open_settings(fib=True)
        else: self.open_properties(hit[1], e.globalPos())

    def open_properties(self, idx, gpos):
        if self._dialog: self._dialog.close()
        self._dialog = DrawingDialog(self, self.drawings[idx])
        self._dialog.adjustSize(); self._dialog.move(gpos + QPoint(16, 16)); self._dialog.show()

    def _context_menu(self, pos, gpos):
        hit = self._hit_test(pos)
        if not hit:
            if not self.fibs: return
            hit = ("fib", len(self.fibs) - 1, "move")  # z. B. Rechtsklick auf eine Beschriftung neben der Fib
        kind, idx = hit[0], hit[1]
        d = self.drawings[idx] if kind == "draw" else None
        menu = QMenu(self)
        act_props = act_color = act_prices = act_settings = None
        width_acts = {}
        if d:
            act_props = menu.addAction("Eigenschaften …")
            act_color = menu.addAction("Farbe …")
            width_menu = menu.addMenu("Linienstärke")
            for w in (1, 2, 3, 4):
                a = width_menu.addAction(f"{w} px"); a.setCheckable(True); a.setChecked(d["width"] == w)
                width_acts[a] = w
        else:
            act_prices = menu.addAction("Preise eingeben …")
            act_settings = menu.addAction("Einstellungen …")
        act_dup = menu.addAction("Duplizieren")
        menu.addSeparator()
        act_hide = menu.addAction("Verstecken")
        act_show_dash = menu.addAction("Dashboard anzeigen")
        menu.addSeparator()
        act_del = menu.addAction("Löschen")

        action = menu.exec_(gpos)
        if action is None: return
        if action == act_hide:
            self.set_hidden(True)
        elif action == act_show_dash and self.main_panel:
            self.main_panel.bring_to_front()
        elif action == act_del:
            what = TOOL_ARTICLES[d["type"]] if d else "die Fibonacci"
            if self._confirm(f"Möchtest du {what} wirklich löschen?", gpos): self.delete_item(kind, idx)
        elif action == act_dup:
            self.duplicate(kind, idx)
        elif action == act_prices:
            self._prompt_prices(self.fibs[idx])
        elif action == act_settings and self.main_panel:
            self.main_panel.open_settings(fib=True)
        elif action == act_props:
            self.open_properties(idx, gpos)
        elif action == act_color:
            c = QColorDialog.getColor(d["color"], self, "Farbe wählen")
            if c.isValid(): d["color"] = c; self.update()
        elif action in width_acts:
            d["width"] = width_acts[action]; self.update()

    def _confirm(self, text, gpos):
        msg = QMessageBox(QMessageBox.Question, "Löschen bestätigen", text, QMessageBox.Yes | QMessageBox.No, self)
        msg.setDefaultButton(QMessageBox.No)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.adjustSize()
        msg.move(gpos - QPoint(msg.width() // 2, msg.height() // 2))  # direkt beim Mauszeiger statt in der Bildschirmmitte
        return msg.exec_() == QMessageBox.Yes

    # ----- Preise -----
    def _finish_placement(self, f):
        if self.show_price_input and f in self.fibs: self._prompt_prices(f)
        if self.main_panel: self.main_panel.placement_finished()

    def _prompt_prices(self, f):
        if PRICE_REF == "entry":
            e, sl = SETUPS[0]["entry"], SETUPS[0]["sl"]
            refs = [(e, f"Preis am Entry 1 (Fib {fmt_num(e)}):"), (sl, f"Preis am SL 1 (Fib {fmt_num(sl)}):")]
        else:
            first, second = ("2. Klick", "1. Klick") if FIB_STYLE["reverse"] else ("1. Klick", "2. Klick")
            refs = [(0.0, f"Preis am 0%-Punkt ({first}):"), (1.0, f"Preis am 100%-Punkt ({second}):")]
        prices = []
        for frac, text in refs:
            dlg = QInputDialog(self)
            dlg.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
            dlg.setWindowTitle(f"Preis {len(prices) + 1} von 2")
            dlg.setLabelText(text + ("\n(Abbrechen = ohne Preise)" if not prices else ""))
            dlg.setInputMode(QInputDialog.DoubleInput)  # ohne das zeigt Qt ein Textfeld und liefert immer 0
            dlg.setDoubleRange(-1e12, 1e12); dlg.setDoubleDecimals(PRICE_DECIMALS)
            if prices: dlg.setDoubleValue(prices[0][1])  # zweiter Preis liegt meist nah am ersten
            if not dlg.exec_():
                f["price_ref"] = None; self.update(); return
            prices.append((frac, dlg.doubleValue()))
        # zweimal derselbe Preis (z. B. nur OK gedrückt -> 0 und 0) ergibt keine Preise statt lauter Nullen
        f["price_ref"] = prices if prices[0][1] != prices[1][1] and prices[0][0] != prices[1][0] else None
        self.update()

    def price_at(self, f, frac):
        """Preis an einem Fib-Level - linear aus den zwei eingegebenen Preisen."""
        if not f or not f["price_ref"]: return None
        (fa, pa), (fb, pb) = f["price_ref"]
        return pa + (frac - fa) * (pb - pa) / (fb - fa)

    # ----- Zeichnen -----
    def paintEvent(self, e):
        if self.is_hidden: return
        p = QPainter(self)
        if self.mode == "placing":
            # Fast unsichtbare Fläche (Alpha 1): Ohne sie gehen Klicks auf leere Stellen
            # bei transparenten Fenstern unter Windows einfach zum Chart darunter durch
            p.fillRect(self.rect(), QColor(0, 0, 0, 1))
            if self.tool == "fib": hint = "FIB-Modus: 1. Klick = 0% (High)   2. Klick = 100% (Low)"
            elif self.tool in ("hline", "hray"): hint = f"{TOOL_NAMES[self.tool]}: Klick = Position"
            else: hint = f"{TOOL_NAMES.get(self.tool, '')}: 1. Klick = Start   2. Klick = Ende"
            self._banner(p, hint + "   Esc / Rechtsklick = Abbrechen", QColor(255, 255, 255, 240), None)
        for f in self.fibs:
            # Fib zuerst, Zeichnungen darüber. Beim Setzen gibt es schon eine Vorschau bis zur Maus.
            end = f["p2"] or (self.hover if f is self.placing_fib else None)
            if end: self._levels(p, f, end)
            self._anchor(p, f["p1"])
            if f["p2"]: self._anchor(p, f["p2"])
        self._draw_drawings(p)
        if self.alert_text and time.time() < self.alert_until:
            self._banner(p, "⚠  " + self.alert_text, QColor("#ffffff"), QColor(200, 30, 50, 230))

    def _banner(self, p, text, color, bg):
        # Hinweis oben auf dem Bildschirm, auf dem die Maus gerade ist
        scr = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        g = scr.geometry(); tl = self.mapFromGlobal(g.topLeft())
        f = QFont(); f.setPointSize(15); f.setBold(True); p.setFont(f)
        rect = QRect(tl.x(), tl.y() + 20, g.width(), 40)
        if bg:
            w = p.fontMetrics().horizontalAdvance(text) + 40
            p.fillRect(QRect(rect.center().x() - w // 2, rect.top() - 4, w, rect.height()), bg)
        p.setPen(color)
        p.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, text)

    def _draw_drawings(self, p):
        grab = self.mode == "edit" and not self.is_locked
        p.setRenderHint(QPainter.Antialiasing, True)
        for d in self.drawings + ([self.pending] if self.pending else []):
            a, b = self._line_ends(d)
            rect = QRectF(QPointF(d["p1"]), QPointF(d["p2"])).normalized()
            if grab:
                # unsichtbarer breiter Streifen zum Anfassen - dünne Linien wären sonst kaum zu treffen
                p.setPen(QPen(QColor(0, 0, 0, 1), 12)); p.setBrush(Qt.NoBrush)
                if d["type"] == "rect": p.drawRect(rect)
                else: p.drawLine(a, b)
            c = d["color"]
            p.setPen(QPen(c, d["width"], PEN_STYLES.get(d.get("style", "Solid"), Qt.SolidLine)))
            if d["type"] == "rect":
                fill = QColor(d["fill_color"]); fill.setAlpha(int(d["fill_opacity"] * 2.55))
                p.setBrush(fill if d["fill"] else Qt.NoBrush); p.drawRect(rect)
                if d["midline"]:
                    p.setPen(QPen(c, 1, Qt.DashLine))
                    p.drawLine(QPointF(rect.left(), rect.center().y()), QPointF(rect.right(), rect.center().y()))
            else:
                p.setBrush(Qt.NoBrush); p.drawLine(a, b)
            if d["type"] in ("hline", "hray"): self._hline_label(p, d, b)
            if grab and d is not self.pending:
                for h in ([d["p1"]] if d["type"] in ("hline", "hray") else [d["p1"], d["p2"]]):
                    p.setPen(QPen(c, 2)); p.setBrush(QColor(20, 20, 20, 220)); p.drawEllipse(QPointF(h), 4, 4)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setBrush(Qt.NoBrush)

    def _hline_label(self, p, d, right):
        # Preis der Linie - geht nur, wenn an einer Fib Preise eingegeben wurden
        f = next((f for f in reversed(self.fibs) if f["p2"] is not None and f["price_ref"]), None)
        if not f: return
        _, _, y_of = self._fib_geom(f["p1"], f["p2"])
        if y_of(1) == y_of(0): return
        y = d["p1"].y()
        txt = fmt_price(self.price_at(f, (y - y_of(0)) / (y_of(1) - y_of(0))))
        fnt = QFont(); fnt.setPixelSize(int(FIB_STYLE["font_size"] * 1.25)); p.setFont(fnt)
        fm = p.fontMetrics()
        w, h = fm.horizontalAdvance(txt) + 10, fm.height() + 2
        rect = QRect(int(right.x()) - w - 80, y - h - 1, w, h)
        p.fillRect(rect, QColor(0, 0, 0, 200)); p.setPen(d["color"])
        p.drawText(rect, Qt.AlignCenter, txt)

    def _anchor(self, p, pt):
        # Ankerpunkte wie bei TradingView: kleine blaue Kreise, nur solange man bearbeiten kann
        if self.is_locked or self.mode not in ("edit", "placing"): return
        if self.mode == "edit":
            # unsichtbare Greiffläche, damit man den Punkt leicht trifft
            p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 1)); p.drawEllipse(pt, 15, 15)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QPen(QColor("#2962ff"), 2)); p.setBrush(QColor(19, 23, 34)); p.drawEllipse(QPointF(pt), 5, 5)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setBrush(Qt.NoBrush)

    def _levels(self, p, f, b):
        a = f["p1"]
        x0, x1, y_of = self._fib_geom(a, b)
        levels = self._fib_levels()
        one = FIB_STYLE["one_color_value"] if FIB_STYLE["one_color"] else None
        if FIB_STYLE["background"]:
            # Fläche zwischen zwei Leveln in der Farbe des weiter entfernten Levels (wie TradingView)
            for lo, hi in zip(levels, levels[1:]):
                c = QColor(one or hi["color"]); c.setAlpha(int(FIB_STYLE["bg_opacity"] * 2.55))
                ya, yb = y_of(lo["frac"]), y_of(hi["frac"])
                p.fillRect(QRectF(x0, min(ya, yb), x1 - x0, abs(yb - ya)), c)
        if FIB_STYLE["trend"]:
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setPen(QPen(FIB_STYLE["trend_color"], FIB_STYLE["trend_width"], PEN_STYLES[FIB_STYLE["trend_style"]]))
            p.drawLine(a, b)
            p.setRenderHint(QPainter.Antialiasing, False)
        if EXT_STYLE["on"] and f["p2"] is not None:
            # Verlängerung eines Levels nach rechts: grün = Kurs darüber, rot = darunter, sonst neutral
            ly = int(round(y_of(EXT_STYLE["level"])))
            state = f.get("ext_state")
            c = EXT_STYLE["color_up"] if state == "up" else EXT_STYLE["color_down"] if state == "down" else EXT_STYLE["color_neutral"]
            p.setPen(QPen(c, EXT_STYLE["width"], PEN_STYLES[EXT_STYLE["style"]]))
            p.drawLine(x1, ly, int(x1 + EXT_STYLE["candles"] * self.candle_px), ly)
        fnt = QFont(); fnt.setPixelSize(int(FIB_STYLE["font_size"] * 1.25)); p.setFont(fnt)
        fm = p.fontMetrics()
        grab = self.mode == "edit" and not self.is_locked
        for lv in levels:
            y = int(round(y_of(lv["frac"])))
            if not (0 <= y <= self.height()): continue
            c = QColor(one or lv["color"])
            if grab:
                # unsichtbarer Streifen, damit man die Fib auch ohne Hintergrund anfassen kann
                p.setPen(QPen(QColor(0, 0, 0, 1), 9)); p.drawLine(x0, y, x1, y)
            txt = self._level_text(lv, f)
            w, h = fm.horizontalAdvance(txt) + 8, fm.height()
            lx = {"left": x0 - 4 - w, "center": (x0 + x1 - w) // 2, "right": x1 + 4}[FIB_STYLE["label_h"]]
            ly = {"top": y - h - 1, "middle": y - h // 2, "bottom": y + 2}[FIB_STYLE["label_v"]]
            rect = QRect(lx, ly, w, h)
            p.setPen(QPen(c, lv["thick"], PEN_STYLES.get(lv["style"], Qt.SolidLine)))
            if FIB_STYLE["label_v"] == "middle" and FIB_STYLE["label_h"] == "center" and not FIB_STYLE["label_box"]:
                # Linie für die Beschriftung unterbrechen, wie bei TradingView
                if rect.left() > x0: p.drawLine(x0, y, rect.left(), y)
                if rect.right() < x1: p.drawLine(rect.right(), y, x1, y)
            else: p.drawLine(x0, y, x1, y)
            if FIB_STYLE["label_box"]: p.fillRect(rect, QColor(0, 0, 0, 200))
            p.setPen(c); p.drawText(rect, Qt.AlignCenter, txt)


class DrawingDialog(QDialog):
    """Eigenschaften einer einzelnen Zeichnung (Doppelklick): Farbe, Dicke, Stil - beim Rechteck auch Füllung und Mittellinie."""
    def __init__(self, ov, d):
        super().__init__(ov)
        self.ov, self.d = ov, d
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setWindowTitle(f"{TOOL_NAMES[d['type']]} – Eigenschaften")
        t = THEMES[THEME]
        self.setStyleSheet(f"QWidget {{ background-color: {t['bg']}; color: {t['text']}; }}" + indicator_css(t) + field_css(t))
        g = QGridLayout(self)
        g.addWidget(QLabel("Linie"), 0, 0)
        g.addWidget(self._color_btn("color"), 0, 1)
        sp = QSpinBox(); sp.setRange(1, 6); sp.setValue(d["width"]); sp.setMinimumWidth(64)
        sp.valueChanged.connect(lambda v: self._set("width", v))
        g.addWidget(sp, 0, 2)
        cb = QComboBox()
        for text, val in (("Durchgezogen", "Solid"), ("Gestrichelt", "Dash"), ("Gepunktet", "Dot")): cb.addItem(text, val)
        cb.setCurrentIndex(max(0, cb.findData(d.get("style", "Solid"))))
        cb.currentIndexChanged.connect(lambda i: self._set("style", cb.itemData(i)))
        g.addWidget(cb, 0, 3)
        row = 1
        if d["type"] == "rect":
            chk = QCheckBox("Füllung"); chk.setChecked(d["fill"]); chk.toggled.connect(lambda v: self._set("fill", v))
            g.addWidget(chk, row, 0)
            g.addWidget(self._color_btn("fill_color"), row, 1)
            sl = QSlider(Qt.Horizontal); sl.setRange(0, 100); sl.setValue(d["fill_opacity"])
            lbl = QLabel(f"{d['fill_opacity']} %")
            sl.valueChanged.connect(lambda v: (lbl.setText(f"{v} %"), self._set("fill_opacity", v)))
            g.addWidget(sl, row, 2); g.addWidget(lbl, row, 3)
            mid = QCheckBox("Mittellinie"); mid.setChecked(d["midline"]); mid.toggled.connect(lambda v: self._set("midline", v))
            g.addWidget(mid, row + 1, 0, 1, 2)
            row += 2
        ok = QPushButton("Fertig"); ok.clicked.connect(self.accept)
        g.addWidget(ok, row, 0, 1, 4)

    def _color_btn(self, key):
        b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(self.d[key]))
        b.clicked.connect(lambda checked, k=key, btn=b: self._pick(k, btn))
        return b

    def _set(self, key, val):
        self.d[key] = val
        self.ov.update()

    def _pick(self, key, btn):
        c = QColorDialog.getColor(self.d[key], self, "Farbe wählen")
        if c.isValid():
            self.d[key] = c; btn.setStyleSheet(color_btn_css(c)); self.ov.update()


class SettingsPanel(QDialog):
    def __init__(self, overlay, main_panel):
        super().__init__()
        self.ov = overlay
        self.main_panel = main_panel
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("Einstellungen")
        t = THEMES[THEME]
        self.setStyleSheet(f"QWidget {{ background-color: {t['bg']}; color: {t['text']}; }}" + indicator_css(t) + field_css(t))

        self.setMinimumSize(650, 600)
        self.resize(650, 750)

        main_layout = QVBoxLayout()
        self.scroll = scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)

        box_style = f"""
            QGroupBox {{
                border: 1px solid {t['border']};
                border-radius: 5px;
                margin-top: 15px;
                font-weight: bold;
                color: {t['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 2px 8px;
                background-color: {t['bg']};
                border: 1px solid {t['border']};
                border-radius: 4px;
                color: {t['title']};
            }}
        """
        btn_style = (f"QPushButton {{ background-color: {t['btn']}; color: {t['text']}; border: 1px solid {t['btn_border']}; "
                     f"border-radius: 4px; padding: 5px 10px; }} QPushButton:hover {{ background-color: {t['btn_hover']}; }}")

        grp_presets = QGroupBox("Presets (Set-Dateien)")
        grp_presets.setStyleSheet(box_style)
        pr_layout = QVBoxLayout()
        lbl_presets = QLabel("Alle Einstellungen werden automatisch gespeichert und beim nächsten Start geladen.\n"
                             "Zusätzlich kannst du verschiedene Setups als eigene Datei sichern und laden.")
        lbl_presets.setWordWrap(True)
        lbl_presets.setStyleSheet(f"color: {t['muted']}; font-weight: normal;")
        pr_layout.addWidget(lbl_presets)
        pr_btns = QHBoxLayout()
        for text, slot in (("Speichern unter …", self.save_preset), ("Laden …", self.load_preset),
                           ("Standard wiederherstellen", self.reset_defaults)):
            b = QPushButton(text); b.setStyleSheet(btn_style); b.clicked.connect(slot)
            pr_btns.addWidget(b)
        pr_layout.addLayout(pr_btns)
        grp_presets.setLayout(pr_layout)
        layout.addWidget(grp_presets)

        # ===== FIB-DARSTELLUNG - aufgebaut wie der Fib-Retracement-Dialog bei TradingView =====
        self.grp_fib = grp_fib = QGroupBox("Fib-Darstellung (wie TradingView)")
        grp_fib.setStyleSheet(box_style)
        fg = QGridLayout()
        def fib_check(text, key):
            c = QCheckBox(text); c.setChecked(FIB_STYLE[key])
            c.toggled.connect(lambda v, k=key: self.set_fib(k, v))
            return c
        def fib_combo(key, items):
            cb = QComboBox()
            for text, val in items: cb.addItem(text, val)
            cb.setCurrentIndex(max(0, cb.findData(FIB_STYLE[key])))
            cb.currentIndexChanged.connect(lambda i, k=key, c=cb: self.set_fib(k, c.itemData(i)))
            return cb
        def fib_color(key):
            b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(FIB_STYLE[key]))
            b.clicked.connect(lambda checked, k=key, btn=b: self.pick_fib_color(k, btn))
            return b
        def fib_spin(key, lo, hi):
            sp = QSpinBox(); sp.setRange(lo, hi); sp.setValue(FIB_STYLE[key])
            sp.valueChanged.connect(lambda v, k=key: self.set_fib(k, v))
            return sp
        styles = [("Gestrichelt", "Dash"), ("Durchgezogen", "Solid"), ("Gepunktet", "Dot")]
        rows = [
            (fib_check("Trendlinie (Diagonale)", "trend"), fib_color("trend_color"), fib_combo("trend_style", styles)),
            (QLabel("Trendlinie Dicke"), fib_spin("trend_width", 1, 6)),
            (QLabel("Verlängern"), fib_combo("extend", [("Nicht erweitern", "none"), ("Linien nach links", "left"),
                                                         ("Linien nach rechts", "right"), ("Nach beiden Seiten", "both")])),
            (fib_check("Hintergrund (Flächen)", "background"),),
            (fib_check("Umkehren (0 und 1 tauschen)", "reverse"),),
            (fib_check("Preise", "prices"), fib_check("Namen (E1, SL1 …)", "names")),
            (QLabel("Level"), fib_combo("level_fmt", [("Werte (0,5)", "value"), ("Prozent (50%)", "percent")])),
            (QLabel("Beschriftungen"), fib_combo("label_h", [("Links", "left"), ("Zentriert", "center"), ("Rechts", "right")]),
             fib_combo("label_v", [("Oben", "top"), ("Mitte", "middle"), ("Unten", "bottom")])),
            (QLabel("Schriftgröße"), fib_spin("font_size", 6, 24)),
            (fib_check("Dunkler Kasten hinter der Schrift", "label_box"),),
            (fib_check("Eine Farbe verwenden", "one_color"), fib_color("one_color_value")),
            (QLabel("Zahlenformat"), fib_combo("num_fmt", [("Deutsch: 0,5 (81.751,0)", "de"), ("Englisch: 0.5 (81751.0)", "en")])),
            (fib_check("Linie 0 anzeigen", "show_0"), fib_color("color_0")),
            (fib_check("Linie 1 anzeigen", "show_1"), fib_color("color_1")),
        ]
        for r, widgets in enumerate(rows):
            for c, wdg in enumerate(widgets): fg.addWidget(wdg, r, c)
        # Deckkraft-Regler gehört in die Zeile "Hintergrund"
        bg_row = 3
        self.sl_bg = QSlider(Qt.Horizontal); self.sl_bg.setRange(0, 100); self.sl_bg.setValue(FIB_STYLE["bg_opacity"])
        self.lbl_bg = QLabel(f"{FIB_STYLE['bg_opacity']} %")
        self.sl_bg.valueChanged.connect(lambda v: (self.lbl_bg.setText(f"{v} %"), self.set_fib("bg_opacity", v)))
        fg.addWidget(self.sl_bg, bg_row, 1, 1, 1); fg.addWidget(self.lbl_bg, bg_row, 2)
        fg.setColumnStretch(1, 1)
        r = len(rows)
        fg.addWidget(QLabel("<b>Zusätzliche Fib-Level</b>  (Haken = anzeigen, ✕ = entfernen)"), r, 0, 1, 3)
        self.extra_layout = QVBoxLayout()
        for lv in FIB_EXTRA: self._add_extra_row(lv)
        fg.addLayout(self.extra_layout, r + 1, 0, 1, 3)
        btn_add = QPushButton("+ Level hinzufügen"); btn_add.setStyleSheet(btn_style); btn_add.clicked.connect(self.add_extra_level)
        fg.addWidget(btn_add, r + 2, 0, 1, 3)
        btn_tv = QPushButton("Wie mein TradingView-Fib einstellen (Farben + Linien)")
        btn_tv.setStyleSheet(btn_style); btn_tv.clicked.connect(self.apply_tv_look)
        fg.addWidget(btn_tv, r + 3, 0, 1, 3)
        grp_fib.setLayout(fg)
        layout.addWidget(grp_fib)

        # ===== VERLÄNGERUNG EINES LEVELS + ALARM =====
        grp_ext = QGroupBox("Level-Verlängerung nach rechts + Alarm (Test)")
        grp_ext.setStyleSheet(box_style)
        eg = QGridLayout()
        es = EXT_STYLE
        def ext_check(text, key):
            c = QCheckBox(text); c.setChecked(es[key])
            c.toggled.connect(lambda v, k=key: self.set_ext(k, v))
            return c
        eg.addWidget(ext_check("Verlängerung anzeigen (gestrichelte Linie rechts neben der Fib)", "on"), 0, 0, 1, 4)
        eg.addWidget(QLabel("Level"), 1, 0)
        sp_lv = QDoubleSpinBox(); sp_lv.setRange(-10, 10); sp_lv.setDecimals(3); sp_lv.setSingleStep(0.001); sp_lv.setValue(es["level"])
        sp_lv.valueChanged.connect(lambda v: self.set_ext("level", v))
        eg.addWidget(sp_lv, 1, 1)
        eg.addWidget(QLabel("Länge (Kerzen)"), 1, 2)
        sp_len = QSpinBox(); sp_len.setRange(1, 200); sp_len.setValue(es["candles"])
        sp_len.valueChanged.connect(lambda v: self.set_ext("candles", v))
        eg.addWidget(sp_len, 1, 3)
        eg.addWidget(QLabel("Dicke / Stil"), 2, 0)
        sp_ew = QSpinBox(); sp_ew.setRange(1, 6); sp_ew.setValue(es["width"])
        sp_ew.valueChanged.connect(lambda v: self.set_ext("width", v))
        eg.addWidget(sp_ew, 2, 1)
        cb_es = QComboBox()
        for text, val in (("Gestrichelt", "Dash"), ("Durchgezogen", "Solid"), ("Gepunktet", "Dot")): cb_es.addItem(text, val)
        cb_es.setCurrentIndex(max(0, cb_es.findData(es["style"])))
        cb_es.currentIndexChanged.connect(lambda i: self.set_ext("style", cb_es.itemData(i)))
        eg.addWidget(cb_es, 2, 2, 1, 2)
        eg.addWidget(QLabel("Farbe: Kurs darüber / darunter / unbekannt"), 3, 0, 1, 2)
        ext_colors = QHBoxLayout()
        for key in ("color_up", "color_down", "color_neutral"):
            b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(es[key]))
            b.clicked.connect(lambda checked, k=key, btn=b: self.pick_ext_color(k, btn))
            ext_colors.addWidget(b)
        ext_colors.addStretch()
        eg.addLayout(ext_colors, 3, 2, 1, 2)
        eg.addWidget(ext_check("Farbe automatisch nach Kurs (erkennt die letzte Kerze am Bildschirm)", "live"), 4, 0, 1, 4)
        eg.addWidget(ext_check("Alarm mit Ton, wenn der Kurs das Level kreuzt", "alarm"), 5, 0, 1, 4)
        eg.addWidget(QLabel("Vorwarnung ab Abstand (z. B. 0,059 · 0 = aus)"), 6, 0, 1, 2)
        sp_pre = QDoubleSpinBox(); sp_pre.setRange(0, 1); sp_pre.setDecimals(3); sp_pre.setSingleStep(0.001); sp_pre.setValue(es["pre_alert"])
        sp_pre.valueChanged.connect(lambda v: self.set_ext("pre_alert", v))
        eg.addWidget(sp_pre, 6, 2)
        lbl_ext = QLabel("Test-Funktion: Das Programm schaut alle 0,7 Sekunden auf den Bildschirm und sucht die letzte Kerze. "
                         "Das klappt nur, solange der Chart nicht verschoben oder neu skaliert wird.")
        lbl_ext.setWordWrap(True); lbl_ext.setStyleSheet(f"color: {t['muted']}; font-weight: normal;")
        eg.addWidget(lbl_ext, 7, 0, 1, 4)
        eg.setColumnStretch(4, 1)
        grp_ext.setLayout(eg)
        layout.addWidget(grp_ext)

        grp_rules = QGroupBox("Regeln des SK-Systems")
        grp_rules.setStyleSheet(box_style)
        rl_layout = QVBoxLayout()
        lbl_rules = QLabel(
            "• Entry: Einstieg bei 0.5 (oder tiefer)\n"
            "• SL: Nächstes Fib-Level\n"
            "• BE: Bei 2-fachem Risiko (2R)\n"
            "• TP1-3: Teilschließungen bei X-fachem Risiko"
        )
        lbl_rules.setStyleSheet(f"color: {t['muted']}; font-weight: normal; font-size: 13px;")
        rl_layout.addWidget(lbl_rules)
        grp_rules.setLayout(rl_layout)
        layout.addWidget(grp_rules)

        grp_trade = QGroupBox("Handels-Setups")
        grp_trade.setStyleSheet(box_style)
        trade_layout = QVBoxLayout()
        trade_layout.setSpacing(10)

        grp_global = QGroupBox("Globale R-Werte")
        grp_global.setStyleSheet(box_style)
        g_layout = QVBoxLayout()
        self.cb_global = QCheckBox("Globale R-Werte verwenden (für alle Setups)")
        self.cb_global.setChecked(USE_GLOBAL_R)
        self.cb_global.stateChanged.connect(self.toggle_global_r)
        g_layout.addWidget(self.cb_global)

        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("TP1:"))
        self.cb_gtp1 = QComboBox()
        self.cb_gtp1.setEditable(True)
        r_layout.addWidget(self.cb_gtp1)
        r_layout.addWidget(QLabel("TP2:"))
        self.cb_gtp2 = QComboBox()
        self.cb_gtp2.setEditable(True)
        r_layout.addWidget(self.cb_gtp2)
        r_layout.addWidget(QLabel("TP3:"))
        self.cb_gtp3 = QComboBox()
        self.cb_gtp3.setEditable(True)
        r_layout.addWidget(self.cb_gtp3)

        r_vals = [fmt_num(x) for x in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 10, 15, 20]]
        for cb in (self.cb_gtp1, self.cb_gtp2, self.cb_gtp3):
            cb.addItems(r_vals)

        self.cb_gtp1.setCurrentText(fmt_num(GLOBAL_TP1_R))
        self.cb_gtp2.setCurrentText(fmt_num(GLOBAL_TP2_R))
        self.cb_gtp3.setCurrentText(fmt_num(GLOBAL_TP3_R))

        g_layout.addLayout(r_layout)
        grp_global.setLayout(g_layout)
        trade_layout.addWidget(grp_global)

        self.spin_e = []; self.spin_sl = []; self.spin_be = []
        self.spin_tp1 = []; self.spin_tp2 = []; self.spin_tp3 = []
        self.cb_stp1 = []; self.cb_stp2 = []; self.cb_stp3 = []
        self.color_btns = {"e":[], "sl":[], "be":[], "tp1":[], "tp2":[], "tp3":[]}
        self.thick_spins = {"e":[], "sl":[], "be":[], "tp1":[], "tp2":[], "tp3":[]}
        self.style_cbs = {"e":[], "sl":[], "be":[], "tp1":[], "tp2":[], "tp3":[]}

        for i, s in enumerate(SETUPS):
            grp = QGroupBox(f"Setup {s['n']}")
            grp.setStyleSheet(box_style)
            grid = QGridLayout()

            grid.addWidget(QLabel("<b>Linie</b>"), 0, 0)
            grid.addWidget(QLabel("<b>Wert</b>"), 0, 1)
            grid.addWidget(QLabel("<b>R</b>"), 0, 2)
            grid.addWidget(QLabel("<b>Farbe</b>"), 0, 3)
            grid.addWidget(QLabel("<b>Dicke</b>"), 0, 4)
            grid.addWidget(QLabel("<b>Stil</b>"), 0, 5)

            def add_row(row, label, spin_widget, r_combo, key):
                grid.addWidget(QLabel(label), row, 0)
                grid.addWidget(spin_widget, row, 1)
                if r_combo: grid.addWidget(r_combo, row, 2)
                else: grid.addWidget(QLabel("-"), row, 2)

                btn_col = QPushButton()
                btn_col.setFixedSize(24, 24)
                btn_col.setStyleSheet(color_btn_css(s[f'color_{key}']))
                btn_col.clicked.connect(lambda checked, idx=i, k=key: self.pick_color(idx, k))
                self.color_btns[key].append(btn_col)
                grid.addWidget(btn_col, row, 3)

                sp_thick = QSpinBox(); sp_thick.setRange(1, 10); sp_thick.setValue(s[f'thick_{key}'])
                sp_thick.valueChanged.connect(lambda val, idx=i, k=key: self.update_thick(idx, k, val))
                self.thick_spins[key].append(sp_thick)
                grid.addWidget(sp_thick, row, 4)

                cb_style = QComboBox(); cb_style.addItems(["Solid", "Dash", "Dot"])
                cb_style.setCurrentText(s[f'style_{key}'])
                cb_style.currentTextChanged.connect(lambda val, idx=i, k=key: self.update_style(idx, k, val))
                self.style_cbs[key].append(cb_style)
                grid.addWidget(cb_style, row, 5)

            sp_e = QDoubleSpinBox(); sp_e.setRange(-10000, 10000); sp_e.setDecimals(3); sp_e.setSingleStep(0.001); sp_e.setValue(s["entry"])
            sp_e.valueChanged.connect(lambda v, idx=i: self.update_val(idx, "entry", v))
            self.spin_e.append(sp_e)
            add_row(1, "Entry", sp_e, None, "e")

            sp_sl = QDoubleSpinBox(); sp_sl.setRange(-10000, 10000); sp_sl.setDecimals(3); sp_sl.setSingleStep(0.001); sp_sl.setValue(s["sl"])
            sp_sl.valueChanged.connect(lambda v, idx=i: self.update_val(idx, "sl", v))
            self.spin_sl.append(sp_sl)
            add_row(2, "SL", sp_sl, None, "sl")

            sp_be = QDoubleSpinBox(); sp_be.setRange(-10000, 10000); sp_be.setDecimals(3); sp_be.setValue(s["be"])
            sp_be.setReadOnly(True); sp_be.setButtonSymbols(QDoubleSpinBox.NoButtons); sp_be.setStyleSheet("background-color: #333; color: #aaa;")
            self.spin_be.append(sp_be)
            add_row(3, "BE", sp_be, None, "be")

            sp_tp1 = QDoubleSpinBox(); sp_tp1.setRange(-10000, 10000); sp_tp1.setDecimals(3); sp_tp1.setValue(s["tp1"])
            sp_tp1.setReadOnly(True); sp_tp1.setButtonSymbols(QDoubleSpinBox.NoButtons); sp_tp1.setStyleSheet("background-color: #333; color: #aaa;")
            self.spin_tp1.append(sp_tp1)
            cb_stp1 = QComboBox(); cb_stp1.setEditable(True); cb_stp1.addItems(r_vals); cb_stp1.setCurrentText(fmt_num(s["r_tp1"]))
            cb_stp1.currentTextChanged.connect(lambda v, idx=i: self.update_r_setup(idx, "r_tp1", v))
            self.cb_stp1.append(cb_stp1)
            add_row(4, "TP1", sp_tp1, cb_stp1, "tp1")

            sp_tp2 = QDoubleSpinBox(); sp_tp2.setRange(-10000, 10000); sp_tp2.setDecimals(3); sp_tp2.setValue(s["tp2"])
            sp_tp2.setReadOnly(True); sp_tp2.setButtonSymbols(QDoubleSpinBox.NoButtons); sp_tp2.setStyleSheet("background-color: #333; color: #aaa;")
            self.spin_tp2.append(sp_tp2)
            cb_stp2 = QComboBox(); cb_stp2.setEditable(True); cb_stp2.addItems(r_vals); cb_stp2.setCurrentText(fmt_num(s["r_tp2"]))
            cb_stp2.currentTextChanged.connect(lambda v, idx=i: self.update_r_setup(idx, "r_tp2", v))
            self.cb_stp2.append(cb_stp2)
            add_row(5, "TP2", sp_tp2, cb_stp2, "tp2")

            sp_tp3 = QDoubleSpinBox(); sp_tp3.setRange(-10000, 10000); sp_tp3.setDecimals(3); sp_tp3.setValue(s["tp3"])
            sp_tp3.setReadOnly(True); sp_tp3.setButtonSymbols(QDoubleSpinBox.NoButtons); sp_tp3.setStyleSheet("background-color: #333; color: #aaa;")
            self.spin_tp3.append(sp_tp3)
            cb_stp3 = QComboBox(); cb_stp3.setEditable(True); cb_stp3.addItems(r_vals); cb_stp3.setCurrentText(fmt_num(s["r_tp3"]))
            cb_stp3.currentTextChanged.connect(lambda v, idx=i: self.update_r_setup(idx, "r_tp3", v))
            self.cb_stp3.append(cb_stp3)
            add_row(6, "TP3", sp_tp3, cb_stp3, "tp3")

            grp.setLayout(grid)
            trade_layout.addWidget(grp)

        grp_trade.setLayout(trade_layout)
        layout.addWidget(grp_trade)

        grp_layout = QGroupBox("Darstellung && Verhalten")  # && = ein "&" (einzelnes & wird sonst zu "_")
        grp_layout.setStyleSheet(box_style)
        l_layout = QVBoxLayout()

        design_layout = QHBoxLayout()
        design_layout.addWidget(QLabel("Design:"))
        self.cb_theme = QComboBox(); self.cb_theme.addItems(list(THEMES)); self.cb_theme.setCurrentText(THEME)
        self.cb_theme.currentTextChanged.connect(self.set_theme)
        design_layout.addWidget(self.cb_theme, 1)
        self.cb_matrix = QCheckBox("Matrix-Regen"); self.cb_matrix.setChecked(MATRIX_ON)
        self.cb_matrix.toggled.connect(self.main_panel.set_matrix)
        design_layout.addWidget(self.cb_matrix)
        l_layout.addLayout(design_layout)

        self.cb_rules = QCheckBox("Regeln des SK-Systems im Dashboard anzeigen")
        self.cb_rules.setChecked(SHOW_RULES)
        self.cb_rules.stateChanged.connect(self.toggle_rules)
        l_layout.addWidget(self.cb_rules)

        self.cb_auto_resize = QCheckBox("Fensterhöhe automatisch an Inhalt anpassen")
        self.cb_auto_resize.setChecked(AUTO_RESIZE_WINDOW)
        self.cb_auto_resize.stateChanged.connect(self.toggle_auto_resize)
        l_layout.addWidget(self.cb_auto_resize)

        len_layout = QHBoxLayout()
        len_layout.addWidget(QLabel("Fib-Breite, wenn beide Punkte genau übereinander liegen (px):"))
        self.spin_len = QSpinBox()
        self.spin_len.setRange(100, 3000)
        self.spin_len.setValue(self.ov.line_length)
        self.spin_len.setSingleStep(50)
        self.spin_len.valueChanged.connect(self.update_length)
        len_layout.addWidget(self.spin_len)
        l_layout.addLayout(len_layout)

        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Preise abfragen bei:"))
        self.cb_price_ref = QComboBox()
        self.cb_price_ref.addItem("0% und 100% (High / Low)", "hl")
        self.cb_price_ref.addItem("Entry 1 und SL 1", "entry")
        self.cb_price_ref.setCurrentIndex(self.cb_price_ref.findData(PRICE_REF))
        self.cb_price_ref.currentIndexChanged.connect(self.update_price_ref)
        price_layout.addWidget(self.cb_price_ref)
        price_layout.addWidget(QLabel("Nachkommastellen:"))
        self.spin_dec = QSpinBox(); self.spin_dec.setRange(0, 8); self.spin_dec.setValue(PRICE_DECIMALS)
        self.spin_dec.valueChanged.connect(self.update_decimals)
        price_layout.addWidget(self.spin_dec)
        l_layout.addLayout(price_layout)

        grp_layout.setLayout(l_layout)
        layout.addWidget(grp_layout)

        grp_tools = QGroupBox("Zeichenwerkzeuge && Magnet")
        grp_tools.setStyleSheet(box_style)
        t_layout = QVBoxLayout()
        t_grid = QGridLayout()
        for c, head in enumerate(("Werkzeug", "Farbe", "Dicke", "Stil")): t_grid.addWidget(QLabel(f"<b>{head}</b>"), 0, c)
        self.tool_color_btns = {}
        line_styles = [("Durchgezogen", "Solid"), ("Gestrichelt", "Dash"), ("Gepunktet", "Dot")]
        for row, kind in enumerate(TOOL_NAMES, start=1):
            st = TOOL_STYLES[kind]
            t_grid.addWidget(QLabel(TOOL_NAMES[kind]), row, 0)
            b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(st["color"]))
            b.clicked.connect(lambda checked, k=kind: self.pick_tool_color(k))
            self.tool_color_btns[kind] = b
            t_grid.addWidget(b, row, 1)
            sp = QSpinBox(); sp.setRange(1, 6); sp.setValue(st["width"])
            sp.valueChanged.connect(lambda v, k=kind: self.update_tool_width(k, v))
            t_grid.addWidget(sp, row, 2)
            cb = QComboBox()
            for text, val in line_styles: cb.addItem(text, val)
            cb.setCurrentIndex(max(0, cb.findData(st["style"])))
            cb.currentIndexChanged.connect(lambda i, k=kind, c=cb: self.set_tool(k, "style", c.itemData(i)))
            t_grid.addWidget(cb, row, 3)
        # Rechteck: Füllung (Farbe + Deckkraft) und Mittellinie - wie bei TradingView
        r, rs = len(TOOL_NAMES) + 1, TOOL_STYLES["rect"]
        chk_fill = QCheckBox("Rechteck: Füllung"); chk_fill.setChecked(rs["fill"])
        chk_fill.toggled.connect(lambda v: self.set_tool("rect", "fill", v))
        t_grid.addWidget(chk_fill, r, 0)
        btn_fill = QPushButton(); btn_fill.setFixedSize(24, 24); btn_fill.setStyleSheet(color_btn_css(rs["fill_color"]))
        btn_fill.clicked.connect(lambda checked, btn=btn_fill: self.pick_tool_key("rect", "fill_color", btn))
        t_grid.addWidget(btn_fill, r, 1)
        sl_fill = QSlider(Qt.Horizontal); sl_fill.setRange(0, 100); sl_fill.setValue(rs["fill_opacity"])
        lbl_fill = QLabel(f"Deckkraft {rs['fill_opacity']} %")
        sl_fill.valueChanged.connect(lambda v: (lbl_fill.setText(f"Deckkraft {v} %"), self.set_tool("rect", "fill_opacity", v)))
        t_grid.addWidget(sl_fill, r, 2); t_grid.addWidget(lbl_fill, r, 3)
        chk_mid = QCheckBox("Rechteck: Mittellinie"); chk_mid.setChecked(rs["midline"])
        chk_mid.toggled.connect(lambda v: self.set_tool("rect", "midline", v))
        t_grid.addWidget(chk_mid, r + 1, 0, 1, 2)
        t_grid.setColumnStretch(4, 1)
        t_layout.addLayout(t_grid)
        self.cb_magnet = QCheckBox("Magnet an (Punkte rasten an Hoch / Tief der Kerze ein)")
        self.cb_magnet.setChecked(MAGNET_ON)
        self.cb_magnet.stateChanged.connect(lambda st: self.main_panel.set_magnet(bool(st)))
        t_layout.addWidget(self.cb_magnet)
        mag_layout = QHBoxLayout()
        mag_layout.addWidget(QLabel("Magnet-Stärke:"))
        self.cb_magnet_mode = QComboBox()
        self.cb_magnet_mode.addItem("Schwach – nur wenn du nah an der Kerze klickst", "weak")
        self.cb_magnet_mode.addItem("Stark – immer an der Kerze unter dem Mauszeiger", "strong")
        self.cb_magnet_mode.setCurrentIndex(self.cb_magnet_mode.findData(MAGNET_MODE))
        self.cb_magnet_mode.currentIndexChanged.connect(self.update_magnet_mode)
        mag_layout.addWidget(self.cb_magnet_mode, 1)
        t_layout.addLayout(mag_layout)
        lbl_tools = QLabel("Neue Zeichnungen bekommen diese Werte. Einzelne Zeichnungen änderst du per Doppelklick oder Rechtsklick.")
        lbl_tools.setWordWrap(True)
        lbl_tools.setStyleSheet(f"color: {t['muted']}; font-weight: normal;")
        t_layout.addWidget(lbl_tools)
        grp_tools.setLayout(t_layout)
        layout.addWidget(grp_tools)

        # ===== MATRIX-REGEN =====
        grp_mx = QGroupBox("Matrix-Regen")
        grp_mx.setStyleSheet(box_style)
        mg = QGridLayout()
        ms = MATRIX_STYLE
        chk_own = QCheckBox("Eigene Farben statt der Design-Farben"); chk_own.setChecked(ms["own_color"])
        chk_own.toggled.connect(lambda v: self.set_matrix_style("own_color", v))
        mg.addWidget(chk_own, 0, 0, 1, 3)
        mg.addWidget(QLabel("Farbe Zeichen / vorderstes Zeichen"), 1, 0)
        for c, key in enumerate(("color", "head"), start=1):
            b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(ms[key]))
            b.clicked.connect(lambda checked, k=key, btn=b: self.pick_matrix_color(k, btn))
            mg.addWidget(b, 1, c)
        mg.addWidget(QLabel("Tempo"), 2, 0)
        sl_speed = QSlider(Qt.Horizontal); sl_speed.setRange(20, 300); sl_speed.setValue(ms["speed"])
        lbl_speed = QLabel(f"{ms['speed']} %")
        sl_speed.valueChanged.connect(lambda v: (lbl_speed.setText(f"{v} %"), self.set_matrix_style("speed", v)))
        mg.addWidget(sl_speed, 2, 1, 1, 2); mg.addWidget(lbl_speed, 2, 3)
        mg.addWidget(QLabel("Schriftgröße (px)"), 3, 0)
        sp_size = QSpinBox(); sp_size.setRange(8, 32); sp_size.setValue(ms["size"])
        sp_size.valueChanged.connect(lambda v: self.set_matrix_style("size", v))
        mg.addWidget(sp_size, 3, 1, 1, 2)
        lbl_mx = QLabel("Einschalten oben bei „Design“ → Matrix-Regen.")
        lbl_mx.setStyleSheet(f"color: {t['muted']}; font-weight: normal;")
        mg.addWidget(lbl_mx, 4, 0, 1, 4)
        mg.setColumnStretch(4, 1)
        grp_mx.setLayout(mg)
        layout.addWidget(grp_mx)

        # ===== ABSTÄNDE ANPASSEN =====
        grp_spacing = QGroupBox("Abstände anpassen (Dashboard)")
        grp_spacing.setStyleSheet(box_style)
        sp_layout = QVBoxLayout()

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("1. Abstand Oben (Rand -> Oberer Kasten):"))
        self.sp_top = QSpinBox(); self.sp_top.setRange(0, 50); self.sp_top.setValue(MARGIN_TOP)
        self.sp_top.valueChanged.connect(self.update_spacing)
        h1.addWidget(self.sp_top)
        sp_layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("2. Abstand Oberer Kasten -> Tabelle:"))
        self.sp_gap1 = QSpinBox(); self.sp_gap1.setRange(0, 50); self.sp_gap1.setValue(GAP_1)
        self.sp_gap1.valueChanged.connect(self.update_spacing)
        h2.addWidget(self.sp_gap1)
        sp_layout.addLayout(h2)

        h3 = QHBoxLayout()
        h3.addWidget(QLabel("3. Abstand Tabelle -> Buttons:"))
        self.sp_gap2 = QSpinBox(); self.sp_gap2.setRange(0, 50); self.sp_gap2.setValue(GAP_2)
        self.sp_gap2.valueChanged.connect(self.update_spacing)
        h3.addWidget(self.sp_gap2)
        sp_layout.addLayout(h3)

        h4 = QHBoxLayout()
        h4.addWidget(QLabel("4. Abstand Unten (Kasten -> Rand):"))
        self.sp_bot = QSpinBox(); self.sp_bot.setRange(0, 50); self.sp_bot.setValue(MARGIN_BOTTOM)
        self.sp_bot.valueChanged.connect(self.update_spacing)
        h4.addWidget(self.sp_bot)
        sp_layout.addLayout(h4)

        grp_spacing.setLayout(sp_layout)
        layout.addWidget(grp_spacing)

        grp_hotkeys = QGroupBox("Hotkeys / Tastaturbelegung")
        grp_hotkeys.setStyleSheet(box_style)
        hk_outer = QVBoxLayout()
        hk_layout = QGridLayout()
        self.hk_edits = {}
        for idx, hk_id in enumerate((2, 3, 5, 1, 4)):  # Zeichnen, Löschen, Verstecken, Bearbeiten, Beenden
            row = idx // 3
            col = (idx % 3) * 2
            hk_layout.addWidget(QLabel(HK_ACTIONS[hk_id]), row, col)
            edit = QKeySequenceEdit(QKeySequence(self.ov.hk_map[hk_id]))
            edit.setFixedWidth(110)
            edit.editingFinished.connect(lambda hk_id=hk_id: self.update_hotkey(hk_id))
            self.hk_edits[hk_id] = edit
            hk_layout.addWidget(edit, row, col+1)
        hk_outer.addLayout(hk_layout)
        lbl_hk = QLabel("Ins Feld klicken und die neue Taste drücken, z. B. F8 oder Strg+F9.\n"
                        "Achtung: Diese Tasten werden in allen Programmen abgefangen (auch in MT5 / TradingView).")
        lbl_hk.setWordWrap(True)
        lbl_hk.setStyleSheet(f"color: {t['muted']}; font-weight: normal;")
        hk_outer.addWidget(lbl_hk)
        grp_hotkeys.setLayout(hk_outer)
        layout.addWidget(grp_hotkeys)

        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.cb_gtp1.currentTextChanged.connect(lambda v: self.update_r_global("GLOBAL_TP1_R", v))
        self.cb_gtp2.currentTextChanged.connect(lambda v: self.update_r_global("GLOBAL_TP2_R", v))
        self.cb_gtp3.currentTextChanged.connect(lambda v: self.update_r_global("GLOBAL_TP3_R", v))

        # Zahlenfelder einheitlich breit - nicht winzig (Dicke) und nicht über die ganze Zeile (Abstände)
        for sb in self.findChildren(QAbstractSpinBox):
            sb.setMinimumWidth(max(sb.minimumWidth(), 72)); sb.setMaximumWidth(140)

        self.toggle_global_r(USE_GLOBAL_R)

    def set_tool(self, kind, key, val):
        TOOL_STYLES[kind][key] = val
        self.ov.settings_changed()

    def pick_tool_key(self, kind, key, btn):
        color = QColorDialog.getColor(TOOL_STYLES[kind][key], self, "Farbe wählen")
        if color.isValid():
            TOOL_STYLES[kind][key] = color; btn.setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def set_ext(self, key, val):
        EXT_STYLE[key] = val
        if key == "level":
            for f in self.ov.fibs: f.pop("ext_state", None)  # neues Level -> Farbe neu bestimmen
        self.ov.settings_changed()

    def pick_ext_color(self, key, btn):
        color = QColorDialog.getColor(EXT_STYLE[key], self, "Farbe wählen")
        if color.isValid():
            EXT_STYLE[key] = color; btn.setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def set_matrix_style(self, key, val):
        MATRIX_STYLE[key] = val
        self.main_panel.update()
        self.ov.settings_changed()

    def pick_matrix_color(self, key, btn):
        color = QColorDialog.getColor(MATRIX_STYLE[key], self, "Farbe wählen")
        if color.isValid():
            MATRIX_STYLE[key] = color; btn.setStyleSheet(color_btn_css(color))
            self.main_panel.update(); self.ov.settings_changed()

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Preset speichern", os.path.join(PRESET_DIR, "Mein Setup.set"),
                                              "Fib-Preset (*.set)")
        if not path: return
        if not path.lower().endswith(".set"): path += ".set"
        try: write_json(path, settings_to_dict(self.ov))
        except OSError as ex: QMessageBox.warning(self, "Preset", f"Speichern fehlgeschlagen:\n{ex}")

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Preset laden", PRESET_DIR, "Fib-Preset (*.set);;Alle Dateien (*)")
        if not path: return
        try: self.main_panel.apply_all(read_json(path))
        except Exception as ex: QMessageBox.warning(self, "Preset", f"Die Datei konnte nicht geladen werden:\n{ex}")

    def reset_defaults(self):
        reply = QMessageBox.question(self, "Standard wiederherstellen",
                                     "Alle Einstellungen auf den Auslieferungszustand zurücksetzen?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: self.main_panel.apply_all(DEFAULTS)

    def update_spacing(self):
        global MARGIN_TOP, MARGIN_BOTTOM, GAP_1, GAP_2
        MARGIN_TOP = self.sp_top.value()
        GAP_1 = self.sp_gap1.value()
        GAP_2 = self.sp_gap2.value()
        MARGIN_BOTTOM = self.sp_bot.value()

        self.main_panel.apply_spacing()
        self.ov.settings_changed()

    def toggle_rules(self, state):
        global SHOW_RULES
        SHOW_RULES = bool(state)
        self.main_panel.update_rules_visibility()
        self.ov.settings_changed()

    def toggle_auto_resize(self, state):
        global AUTO_RESIZE_WINDOW
        AUTO_RESIZE_WINDOW = bool(state)
        self.main_panel.fit_to_content()
        self.ov.settings_changed()

    def toggle_global_r(self, state):
        global USE_GLOBAL_R
        USE_GLOBAL_R = bool(state)
        self.cb_gtp1.setEnabled(USE_GLOBAL_R)
        self.cb_gtp2.setEnabled(USE_GLOBAL_R)
        self.cb_gtp3.setEnabled(USE_GLOBAL_R)

        for i in range(len(SETUPS)):
            self.cb_stp1[i].setEnabled(not USE_GLOBAL_R)
            self.cb_stp2[i].setEnabled(not USE_GLOBAL_R)
            self.cb_stp3[i].setEnabled(not USE_GLOBAL_R)
            recalc_setup(SETUPS[i])
            self.update_spinboxes(i)

        self.ov.settings_changed()
        self.main_panel.update_table()

    def update_r_global(self, var_name, val):
        global GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R
        if not val or str(val).strip() == "": return
        try:
            v = float(str(val).replace(",", "."))
        except ValueError:
            return

        if var_name == "GLOBAL_TP1_R": GLOBAL_TP1_R = v
        elif var_name == "GLOBAL_TP2_R": GLOBAL_TP2_R = v
        elif var_name == "GLOBAL_TP3_R": GLOBAL_TP3_R = v

        # Die R-Werte der einzelnen Setups bleiben unangetastet - die gelten wieder,
        # sobald "Globale R-Werte" ausgeschaltet wird
        if USE_GLOBAL_R:
            for i in range(len(SETUPS)):
                recalc_setup(SETUPS[i])
                self.update_spinboxes(i)
            self.main_panel.update_table()
        self.ov.settings_changed()

    def update_r_setup(self, idx, key, val):
        if not val or str(val).strip() == "": return
        try:
            v = float(str(val).replace(",", "."))
        except ValueError:
            return
        SETUPS[idx][key] = v
        if not USE_GLOBAL_R:
            recalc_setup(SETUPS[idx])
            self.update_spinboxes(idx)
            self.main_panel.update_table()
        self.ov.settings_changed()

    def update_spinboxes(self, idx):
        s = SETUPS[idx]
        for sp, val in [(self.spin_be[idx], s["be"]), (self.spin_tp1[idx], s["tp1"]),
                        (self.spin_tp2[idx], s["tp2"]), (self.spin_tp3[idx], s["tp3"])]:
            sp.blockSignals(True); sp.setValue(val); sp.blockSignals(False)

    def mousePressEvent(self, e):
        user32.SetForegroundWindow(int(self.winId()))
        self.raise_(); self.activateWindow()
        super().mousePressEvent(e)

    def update_hotkey(self, hk_id):
        edit = self.hk_edits[hk_id]
        new_key = edit.keySequence().toString().split(", ")[0]
        old_key = self.ov.hk_map[hk_id]
        if new_key == old_key: return
        if parse_hotkey(new_key) is None:
            QMessageBox.warning(self, "Hotkey", f"„{new_key}“ geht nicht als Hotkey.\n\n"
                                "Möglich sind F1–F24 (auch mit Strg/Alt/Umschalt) oder Strg/Alt + Buchstabe/Zahl.")
            edit.setKeySequence(QKeySequence(old_key))
            return
        # Ist die Taste schon für eine andere Aktion vergeben? Dann tauschen die beiden.
        for other_id, key in self.ov.hk_map.items():
            if other_id != hk_id and key == new_key:
                self.ov.hk_map[other_id] = old_key
                self.hk_edits[other_id].setKeySequence(QKeySequence(old_key))
        self.ov.hk_map[hk_id] = new_key
        edit.setKeySequence(QKeySequence(new_key))
        failed = self.ov.register_hotkeys()
        if failed: self.ov.warn_hotkeys(failed, self)
        self.ov.settings_changed()

    def pick_color(self, idx, key):
        color = QColorDialog.getColor(SETUPS[idx][f"color_{key}"], self, "Farbe wählen")
        if color.isValid():
            SETUPS[idx][f"color_{key}"] = color
            self.color_btns[key][idx].setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def pick_tool_color(self, kind):
        color = QColorDialog.getColor(TOOL_STYLES[kind]["color"], self, "Farbe wählen")
        if color.isValid():
            TOOL_STYLES[kind]["color"] = color
            self.tool_color_btns[kind].setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def update_tool_width(self, kind, val):
        TOOL_STYLES[kind]["width"] = val
        self.ov.settings_changed()

    def update_magnet_mode(self, idx):
        global MAGNET_MODE
        MAGNET_MODE = self.cb_magnet_mode.itemData(idx)
        self.ov.settings_changed()

    def update_thick(self, idx, key, val):
        SETUPS[idx][f"thick_{key}"] = val
        self.ov.settings_changed()

    def update_style(self, idx, key, val):
        SETUPS[idx][f"style_{key}"] = val
        self.ov.settings_changed()

    def update_val(self, idx, key, val):
        SETUPS[idx][key] = val
        recalc_setup(SETUPS[idx])
        self.update_spinboxes(idx)
        self.ov.settings_changed()
        self.main_panel.update_table()

    def update_length(self, val):
        self.ov.line_length = val
        self.ov.settings_changed()

    def update_price_ref(self, idx):
        global PRICE_REF
        PRICE_REF = self.cb_price_ref.itemData(idx)
        self.ov.settings_changed()

    def update_decimals(self, val):
        global PRICE_DECIMALS
        PRICE_DECIMALS = val
        self.ov.settings_changed()

    def set_theme(self, name):
        global THEME
        THEME = name
        self.main_panel.apply_theme()
        self.ov.settings_changed()
        QTimer.singleShot(0, self.main_panel.rebuild_settings_panel)  # Einstellungsfenster in den neuen Farben neu aufbauen

    def set_fib(self, key, val):
        FIB_STYLE[key] = val
        self.ov.settings_changed()

    def _add_extra_row(self, lv):
        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0)
        cb = QCheckBox(); cb.setChecked(lv["on"]); cb.toggled.connect(lambda v, lv=lv: self._set_extra(lv, "on", v))
        sp = QDoubleSpinBox(); sp.setRange(-10, 10); sp.setDecimals(3); sp.setSingleStep(0.01); sp.setFixedWidth(90)
        sp.setValue(lv["value"]); sp.valueChanged.connect(lambda v, lv=lv: self._set_extra(lv, "value", v))
        col = QPushButton(); col.setFixedSize(24, 24); col.setStyleSheet(color_btn_css(lv["color"]))
        col.clicked.connect(lambda checked, lv=lv, b=col: self._pick_extra_color(lv, b))
        rm = QPushButton("✕"); rm.setFixedSize(24, 24); rm.setToolTip("Level entfernen")
        rm.clicked.connect(lambda checked, lv=lv, w=row: self._remove_extra(lv, w))
        for wdg in (cb, sp, col, rm): h.addWidget(wdg)
        h.addStretch()
        self.extra_layout.addWidget(row)

    def add_extra_level(self):
        lv = {"value": 0.786, "color": QColor("#00bcd4"), "on": True}
        FIB_EXTRA.append(lv); self._add_extra_row(lv)
        self.ov.settings_changed()

    def _set_extra(self, lv, key, val):
        lv[key] = val
        self.ov.settings_changed()

    def _pick_extra_color(self, lv, btn):
        color = QColorDialog.getColor(lv["color"], self, "Farbe wählen")
        if color.isValid():
            lv["color"] = color; btn.setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def _remove_extra(self, lv, row):
        FIB_EXTRA[:] = [x for x in FIB_EXTRA if x is not lv]
        row.deleteLater()
        self.ov.settings_changed()

    def pick_fib_color(self, key, btn):
        color = QColorDialog.getColor(FIB_STYLE[key], self, "Farbe wählen", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            FIB_STYLE[key] = color
            btn.setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def show_fib_section(self):
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(self.grp_fib.y()))

    def apply_tv_look(self):
        reply = QMessageBox.question(self, "TradingView-Look",
            "Farben und sichtbare Linien wie dein TradingView-Fib einstellen?\n\n"
            "Entry und SL aller Setups an, BE und TP aus.\n"
            "0,5 weiß · 0,559 grün · 0,618 gelb · 0,677 türkis · 0,736 rot.\n\n"
            "Tipp: Deine jetzigen Einstellungen kannst du vorher mit „Speichern unter …“ sichern.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply != QMessageBox.Yes: return
        data = settings_to_dict(self.ov)
        # Entry von Setup n und SL von Setup n-1 liegen auf demselben Level -> gleiche Farbe
        colors = ["#ffffff", "#4caf50", "#ffeb3b", "#00bcd4", "#f23645"]
        for i, s in enumerate(data["setups"]):
            s.update({"active": True, "color_e": colors[i], "color_sl": colors[i + 1], "show_e": True, "show_sl": True,
                      "thick_e": 1, "thick_sl": 1, "style_e": "Solid", "style_sl": "Solid"})
            for k in ("be", "tp1", "tp2", "tp3"): s[f"show_{k}"] = False
        data["fib_style"].update({"trend": True, "trend_color": "#c8ffffff", "trend_style": "Dash", "trend_width": 1,
                                  "extend": "none", "background": True, "bg_opacity": 25, "reverse": False,
                                  "prices": True, "level_fmt": "value", "label_h": "center", "label_v": "middle",
                                  "font_size": 10, "label_box": False, "one_color": False,
                                  "show_0": True, "color_0": "#ffffffff", "show_1": True, "color_1": "#ffffffff"})
        data["fib_extra"] = [dict(d, on=False) for d in data["fib_extra"]]
        self.main_panel.apply_all(data)


class MatrixRain:
    """Matrix-Regen: Zeichen fallen in Spalten herunter. Das Dashboard malt ihn in seinen Hintergrund."""
    CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789Z:.=*+<>"

    @property
    def STEP(self): return MATRIX_STYLE["size"] + 1  # Pixel pro Zeichen, folgt der eingestellten Schriftgröße

    def __init__(self, widget):
        self.w = widget
        self.cols = []
        self.font = QFont("MS Gothic"); self.font.setPixelSize(13)
        self.timer = QTimer(widget); self.timer.setInterval(70)  # ~14 Bilder pro Sekunde reichen
        self.timer.timeout.connect(self._tick)

    def set_running(self, on):
        if on: self.timer.start()
        else: self.timer.stop(); self.cols = []

    def _new_col(self, start):
        return {"y": start, "speed": random.uniform(0.25, 0.9), "len": random.randint(6, 18),
                "chars": [random.choice(self.CHARS) for _ in range(64)]}

    def _tick(self):
        if not self.w.isVisible() or self.w.isMinimized(): return
        rows = self.w.height() // self.STEP + 1
        n = self.w.width() // self.STEP + 1
        while len(self.cols) < n: self.cols.append(self._new_col(random.uniform(-rows, 0)))
        del self.cols[n:]
        for i, c in enumerate(self.cols):
            c["y"] += c["speed"] * MATRIX_STYLE["speed"] / 100
            if c["y"] - c["len"] > rows: self.cols[i] = self._new_col(random.uniform(-8, 0))
            elif random.random() < 0.3: c["chars"][random.randrange(64)] = random.choice(self.CHARS)
        self.w.update()

    def paint(self, p, trail, head):
        if self.font.pixelSize() != MATRIX_STYLE["size"]: self.font.setPixelSize(MATRIX_STYLE["size"])
        p.setFont(self.font)
        rows = self.w.height() // self.STEP + 1
        for i, c in enumerate(self.cols):
            top = int(c["y"])
            for k in range(c["len"]):
                row = top - k
                if row < 0 or row > rows: continue
                col = QColor(head if k == 0 else trail)  # vorderstes Zeichen hell, dahinter verblassend
                if k: col.setAlpha(int(220 * (1 - k / c["len"])))
                p.setPen(col)
                p.drawText(i * self.STEP + 1, (row + 1) * self.STEP - 2, c["chars"][row % 64])


class FibTable(QTableWidget):
    """Tabelle, deren Spalten beim Breiterziehen des Fensters im gleichen Verhältnis mitwachsen."""
    def __init__(self, rows, cols):
        super().__init__(rows, cols)
        self.natural = []

    def update_natural_widths(self):
        # Platzbedarf jeder Spalte messen - das ist gleichzeitig die Mindestbreite
        self.resizeColumnsToContents()
        fm = self.fontMetrics()
        self.natural = []
        for c in range(self.columnCount()):
            texts = [self.item(r, c).text() for r in range(self.rowCount()) if self.item(r, c)]
            need = max((fm.horizontalAdvance(t) for t in texts), default=0) + 13 + 20  # Text + Kästchen + Abstände
            self.natural.append(max(self.columnWidth(c), need))
        frame = 2 * self.frameWidth()
        self.setMinimumWidth(sum(self.natural) + frame)
        rows = self.rowCount() * self.verticalHeader().defaultSectionSize()
        self.setMinimumHeight(self.horizontalHeader().sizeHint().height() + rows + frame)
        self._spread()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._spread()

    def _spread(self):
        total, avail = sum(self.natural), self.width() - 2 * self.frameWidth()
        if total <= 0 or avail <= 0: return
        acc = prev = 0
        for i, w in enumerate(self.natural):
            # Spaltengrenzen kumuliert runden: Rundungsrest verteilt sich, rechts bleibt keine Lücke
            acc += w
            edge = round(acc * avail / total)
            self.setColumnWidth(i, edge - prev); prev = edge


class ControlPanel(QDialog):
    def __init__(self, overlay):
        super().__init__()
        self.ov = overlay
        self.ov.main_panel = self # Referenz für den Rechtsklick
        self.settings_panel = None
        self.loaded = False  # erst nach dem Laden speichern, sonst überschreiben die Standardwerte die Datei
        self._hidden_for_placing = False
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True); self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(self.save_settings)
        self.rain = MatrixRain(self)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle("Fib Overlay Steuerung")
        self.move(20, 20)

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setSizeConstraint(QLayout.SetMinimumSize)  # kleiner als der Inhalt geht nicht, größer schon

        # --- OBERER KASTEN (kompakter) ---
        self.top_group = QGroupBox()
        self.top_group.setObjectName("topBox")
        self.top_layout = QVBoxLayout(self.top_group)
        self.top_layout.setContentsMargins(10, 8, 10, 8)

        title_hlay = QHBoxLayout()
        title_hlay.setContentsMargins(0, 0, 0, 0)
        title_box = QFrame()
        title_box.setObjectName("titleBox")
        t_box_layout = QVBoxLayout(title_box)
        t_box_layout.setContentsMargins(10, 0, 10, 0)
        title_lbl = QLabel("Fib Overlay (SK-System)")
        title_lbl.setObjectName("title")
        title_lbl.setAlignment(Qt.AlignCenter)
        t_box_layout.addWidget(title_lbl)

        line_left = QFrame(); line_left.setFrameShape(QFrame.HLine); line_left.setObjectName("line")
        line_right = QFrame(); line_right.setFrameShape(QFrame.HLine); line_right.setObjectName("line")

        title_hlay.addWidget(line_left, 1)
        title_hlay.addWidget(title_box, 0)
        title_hlay.addWidget(line_right, 1)
        self.top_layout.addLayout(title_hlay)

        self.rules_container = QWidget()
        rules_layout = QVBoxLayout(self.rules_container)
        rules_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_lbl = QLabel(
            "Regeln des SK-Systems:\n"
            "• Entry: Einstieg bei 0.5 (oder tiefer)\n"
            "• SL: Nächstes Fib-Level\n"
            "• BE: Bei 2-fachem Risiko (2R)\n"
            "• TP1-3: Teilschließungen bei X-fachem Risiko"
        )
        self.rules_lbl.setObjectName("rules")
        rules_layout.addWidget(self.rules_lbl)
        self.top_layout.addWidget(self.rules_container)

        btn_layout = QHBoxLayout()

        self.btn_price = QPushButton("Preise")
        self.btn_price.setCheckable(True)
        self.btn_price.setObjectName("toggle")
        self.btn_price.clicked.connect(self.toggle_price_input)
        btn_layout.addWidget(self.btn_price)

        self.btn_lock = QPushButton("Fix")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setObjectName("toggle")
        self.btn_lock.clicked.connect(self.ov.set_locked)
        btn_layout.addWidget(self.btn_lock)

        self.btn_hide = QPushButton("Hide")
        self.btn_hide.setCheckable(True)
        self.btn_hide.setObjectName("toggle")
        self.btn_hide.clicked.connect(self.ov.set_hidden)
        btn_layout.addWidget(self.btn_hide)

        self.btn_settings = btn_settings = QPushButton()
        btn_settings.setObjectName("gear"); btn_settings.setIconSize(QSize(16, 16))
        btn_settings.setToolTip("Einstellungen")
        btn_settings.setFixedSize(24, 24)
        btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(btn_settings, alignment=Qt.AlignRight)

        self.top_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.top_group)

        self.spacer1 = QSpacerItem(0, GAP_1, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.main_layout.addItem(self.spacer1)

        # --- MITTLERER KASTEN (Tabelle) ---
        self.table_group = QGroupBox("Fibonacci-Stufen")
        self.table_group.setObjectName("tableBox")
        table_layout = QVBoxLayout(self.table_group)
        table_layout.setContentsMargins(5, 15, 5, 5)

        self.table = FibTable(4, 7)
        self.table.setHorizontalHeaderLabels(["Setup", "Entry", "SL", "BE", "TP1", "TP2", "TP3"])

        # Spaltenbreiten verteilt FibTable selbst, Zeilen teilen sich die Höhe
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.horizontalHeader().setMinimumSectionSize(20)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self.table_item_changed)
        table_layout.addWidget(self.table)

        self.main_layout.addWidget(self.table_group, 1)
        self.update_table()
        self.update_rules_visibility()

        self.spacer2 = QSpacerItem(0, GAP_2, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.main_layout.addItem(self.spacer2)

        # --- UNTERER KASTEN (Werkzeuge + Buttons) ---
        self.btn_group = QGroupBox()
        self.btn_group.setObjectName("btnBox")
        btn_group_layout = QVBoxLayout(self.btn_group)
        btn_group_layout.setContentsMargins(5, 5, 5, 5)

        # Werkzeugleiste wie bei TradingView: Trendlinie, Strahl, Horizontale, Rechteck + Magnet
        tools_row = QHBoxLayout()
        tools_row.setSpacing(4)
        self.tool_btns = {}  # Symbole bekommen in apply_theme die Farbe des Designs
        for kind in TOOL_NAMES:
            b = QPushButton(); b.setObjectName("tool"); b.setIconSize(QSize(18, 18)); b.setFixedHeight(28)
            b.setToolTip(TOOL_NAMES[kind])
            b.clicked.connect(lambda checked, k=kind: self.start_tool(k))
            tools_row.addWidget(b); self.tool_btns[kind] = b
        self.btn_magnet = QPushButton(); self.btn_magnet.setObjectName("tool"); self.btn_magnet.setIconSize(QSize(18, 18))
        self.btn_magnet.setFixedHeight(28); self.btn_magnet.setCheckable(True)
        self.tool_btns["magnet"] = self.btn_magnet
        self.btn_magnet.setToolTip("Magnet: Punkte rasten an Hoch / Tief der Kerze ein")
        self.btn_magnet.clicked.connect(self.set_magnet)
        tools_row.addWidget(self.btn_magnet)
        btn_group_layout.addLayout(tools_row)

        btn_spawn = QPushButton("Sofort-Fib (Drag && Drop)")  # && = ein "&" (einzelnes & macht Qt zum Tastenkürzel)
        btn_spawn.setObjectName("spawn")
        btn_spawn.clicked.connect(self.spawn_and_hide)
        btn_group_layout.addWidget(btn_spawn)

        btn_draw = QPushButton("Manuell zeichnen")
        btn_draw.setObjectName("draw")
        btn_draw.clicked.connect(self.start_drawing)
        btn_group_layout.addWidget(btn_draw)

        btn_clear = QPushButton("Alles löschen")
        btn_clear.setObjectName("clear")
        btn_clear.clicked.connect(self.confirm_clear)
        btn_group_layout.addWidget(btn_clear)

        self.main_layout.addWidget(self.btn_group)

        self.setLayout(self.main_layout)
        self.apply_theme()
        self.sync_buttons()

        self.apply_spacing()
        self.resize(self.minimumSizeHint())

    def apply_spacing(self):
        self.main_layout.setContentsMargins(10, MARGIN_TOP, 10, MARGIN_BOTTOM)
        self.spacer1.changeSize(0, GAP_1, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.spacer2.changeSize(0, GAP_2, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.main_layout.invalidate()
        QTimer.singleShot(0, self.fit_to_content)

    def paintEvent(self, e):
        super().paintEvent(e)
        if MATRIX_ON:
            t, ms = THEMES[THEME], MATRIX_STYLE
            trail, head = (ms["color"], ms["head"]) if ms["own_color"] else (t.get("rain", t["border"]), t.get("rain_head", "#ffffff"))
            self.rain.paint(QPainter(self), trail, head)

    def set_matrix(self, on):
        global MATRIX_ON
        MATRIX_ON = on
        self.apply_theme()  # Kästen durchsichtig bzw. wieder deckend
        self.update()
        self.ov.settings_changed()

    def apply_theme(self):
        t = THEMES[THEME]
        apply_app_palette(t)
        self.setStyleSheet(panel_css(t))
        self.rain.set_running(MATRIX_ON)
        self.btn_settings.setIcon(gear_icon(t["icon"]))
        for kind, b in self.tool_btns.items():
            icon = tool_icon(kind, t["icon"])
            # eingeschaltet (z. B. Magnet an): Symbol in der Schriftfarbe des aktiven Knopfs, sonst Gold auf Gold
            icon.addPixmap(tool_icon(kind, t["on_text"]).pixmap(64), QIcon.Normal, QIcon.On)
            b.setIcon(icon)
        # neu messen, sobald das Design angewendet ist (Schrift und Kästchen können sich ändern)
        QTimer.singleShot(0, lambda: (self.table.update_natural_widths(), self.fit_to_content()))

    def fit_to_content(self):
        """Höhe an den Inhalt anpassen. Die Breite bleibt, wie du sie gezogen hast."""
        if not AUTO_RESIZE_WINDOW: return
        self.main_layout.activate()
        hint = self.minimumSizeHint()
        self.resize(max(self.width(), hint.width()), hint.height())

    def confirm_clear(self):
        reply = QMessageBox.question(self, 'Löschen bestätigen',
                                     'Möchtest du wirklich die Fib und alle Zeichnungen löschen?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ov._hk_clear()

    def update_rules_visibility(self):
        self.rules_container.setVisible(SHOW_RULES)
        QTimer.singleShot(0, self.fit_to_content)

    def sync_buttons(self):
        for btn, on in ((self.btn_price, self.ov.show_price_input), (self.btn_lock, self.ov.is_locked),
                        (self.btn_hide, self.ov.is_hidden), (self.btn_magnet, MAGNET_ON)):
            btn.setChecked(on)

    def toggle_price_input(self, on):
        self.ov.show_price_input = on
        self.ov.settings_changed()

    def set_magnet(self, on):
        global MAGNET_ON
        MAGNET_ON = on
        self.sync_buttons()
        if self.settings_panel:
            cb = self.settings_panel.cb_magnet
            cb.blockSignals(True); cb.setChecked(on); cb.blockSignals(False)
        self.ov.settings_changed()

    def update_table(self):
        self.table.blockSignals(True)
        for i, s in enumerate(SETUPS):
            def make_item(text, key):
                item = QTableWidgetItem(text)
                item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable)
                item.setCheckState(Qt.Checked if s[key] else Qt.Unchecked)
                item.setData(Qt.UserRole, key)
                return item

            self.table.setItem(i, 0, make_item(str(s['n']), "active"))
            for col, k in enumerate(LINE_KEYS, start=1):
                val = s["entry" if k == "e" else k]
                self.table.setItem(i, col, make_item(f"{val:.3f}", f"show_{k}"))
        self.table.blockSignals(False)
        self.table.update_natural_widths()
        QTimer.singleShot(0, self.fit_to_content)

    def table_item_changed(self, item):
        row = item.row()
        key = item.data(Qt.UserRole)
        if not key or row >= len(SETUPS): return
        s = SETUPS[row]
        checked = (item.checkState() == Qt.Checked)
        if s[key] == checked: return
        s[key] = checked

        self.table.blockSignals(True)
        if key == "active":
            # ganze Zeile an/aus
            for col, k in enumerate(LINE_KEYS, start=1):
                s[f"show_{k}"] = checked
                self.table.item(row, col).setCheckState(item.checkState())
        elif checked and not s["active"]:
            # eine Linie einschalten, obwohl das Setup aus ist -> Setup wieder an
            s["active"] = True
            self.table.item(row, 0).setCheckState(Qt.Checked)
        self.table.blockSignals(False)
        self.ov.settings_changed()

    def open_settings(self, fib=False):
        if not self.settings_panel:
            self.settings_panel = SettingsPanel(self.ov, self)
        bring_window_to_front(self.settings_panel)
        if fib: self.settings_panel.show_fib_section()

    def rebuild_settings_panel(self):
        # nach dem Laden eines Presets: Einstellungsfenster mit den neuen Werten neu aufbauen
        old = self.settings_panel
        if not old: return
        visible, geo = old.isVisible(), old.geometry()
        old.hide(); old.deleteLater()
        self.settings_panel = SettingsPanel(self.ov, self)
        self.settings_panel.setGeometry(geo)
        if visible: self.settings_panel.show()

    def apply_all(self, data, restore_window=False):
        backup = settings_to_dict(self.ov)
        try:
            apply_settings(data, self.ov)
        except Exception:
            apply_settings(backup, self.ov)  # kaputte Datei -> alles wie vorher
            raise
        self.ov.set_locked(self.ov.is_locked)
        failed = self.ov.register_hotkeys()
        self.apply_theme()
        self.sync_buttons()
        self.update_table()
        self.apply_spacing()
        self.update_rules_visibility()
        if restore_window and "window" in data:
            x, y, w, h = (int(v) for v in data["window"])
            if QApplication.screenAt(QPoint(x + 30, y + 10)):  # nur, wenn der Platz noch auf einem Bildschirm liegt
                self.setGeometry(x, y, w, h)
        self.rebuild_settings_panel()
        self.ov.settings_changed()
        if failed: QTimer.singleShot(300, lambda: self.ov.warn_hotkeys(failed))

    def schedule_save(self):
        if self.loaded: self.save_timer.start()

    def save_settings(self):
        if not self.loaded: return
        data = settings_to_dict(self.ov)
        g = self.geometry()
        data["window"] = [g.x(), g.y(), g.width(), g.height()]
        try: write_json(SETTINGS_FILE, data)
        except OSError as ex: print("Einstellungen konnten nicht gespeichert werden:", ex)

    def moveEvent(self, e):
        super().moveEvent(e); self.schedule_save()

    def resizeEvent(self, e):
        super().resizeEvent(e); self.schedule_save()

    def bring_to_front(self):
        self._hidden_for_placing = False
        bring_window_to_front(self)

    def placement_finished(self):
        # Dashboard kommt zurück, sobald die Zeichnung steht (oder abgebrochen wurde)
        if self._hidden_for_placing:
            self._hidden_for_placing = False
            if self.isMinimized(): self.showNormal()
            else: self.show()

    def _hide_for_placing(self):
        self._hidden_for_placing = True
        self.hide()

    def spawn_and_hide(self):
        self._hide_for_placing()
        QTimer.singleShot(100, self.ov.spawn_default_fib)

    def start_drawing(self):
        self._hide_for_placing()
        QTimer.singleShot(100, self.ov._hk_draw)

    def start_tool(self, kind):
        self._hide_for_placing()
        QTimer.singleShot(100, lambda: self.ov.start_tool(kind))

def main():
    global DEFAULTS
    app = QApplication(sys.argv)
    ov = FibOverlay()
    panel = ControlPanel(ov)
    DEFAULTS = settings_to_dict(ov)
    if os.path.exists(SETTINGS_FILE):
        try: panel.apply_all(read_json(SETTINGS_FILE), restore_window=True)
        except Exception as ex:
            print("Einstellungen konnten nicht geladen werden:", ex)
            os.replace(SETTINGS_FILE, SETTINGS_FILE + ".defekt")  # aufheben statt überschreiben
    panel.loaded = True
    app.aboutToQuit.connect(panel.save_settings)
    hotkey_filter = HotkeyFilter(ov)  # Referenz behalten, sonst räumt Python den Filter weg
    app.installNativeEventFilter(hotkey_filter)
    ov.show()
    panel.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
