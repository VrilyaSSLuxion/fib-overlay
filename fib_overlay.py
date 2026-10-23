import sys, os, json, math, random, time, winsound, ctypes, traceback, datetime
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QWidget, QInputDialog, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel, QDialog,
                             QCheckBox, QSpinBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                             QGridLayout, QColorDialog, QScrollArea, QSizePolicy,
                             QKeySequenceEdit, QFrame, QComboBox, QMessageBox,
                             QMenu, QSpacerItem, QFileDialog, QLayout, QSlider, QAbstractSpinBox,
                             QLineEdit, QToolTip, QWidgetAction, QTabWidget, QPlainTextEdit)
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
GAP_1 = 8
GAP_2 = 13
MARGIN_BOTTOM = 18

MAGNET_DRAWINGS = True  # Magnet auch für Linien und Rechtecke, nicht nur für die Fib
NUM_KEEP = True         # Objekt-Nummern behalten (Rechteck 3 bleibt Rechteck 3)
AUTO_MODE = False       # Automatik (Test): Setups weiterschalten, wenn der Kurs durch den SL läuft
APP_VERSION = "6"

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
        **{f"fill_{k}": k == "sl" for k in LINE_KEYS},  # Fläche zum nächsten Level darüber - Standard nur SL (Entry -> SL)
    })

# ===== ZEICHENWERKZEUGE =====
TOOL_NAMES = {"trend": "Trendlinie", "ray": "Strahl", "hray": "Horizontaler Strahl", "hline": "Horizontale Linie",
              "rect": "Rechteck"}
TOOL_ARTICLES = {"trend": "die Trendlinie", "ray": "den Strahl", "hray": "den horizontalen Strahl",
                 "hline": "die horizontale Linie", "rect": "das Rechteck"}
def _txt(v, h):
    # Text an der Zeichnung wie bei TradingView: Farbe, Größe, fett/kursiv, Ausrichtung
    return {"text": "", "text_color": QColor("#ffffff"), "text_size": 12, "text_bold": True, "text_italic": False,
            "text_v": v, "text_h": h}

TOOL_STYLES = {  # Standard für neue Zeichnungen (einzelne lassen sich per Doppelklick / Rechtsklick ändern)
    "trend": {"color": QColor("#ffffff"), "width": 2, "style": "Solid", **_txt("top", "center")},
    "ray":   {"color": QColor("#ffffff"), "width": 2, "style": "Solid", **_txt("top", "center")},
    "hray":  {"color": QColor("#ffffff"), "width": 2, "style": "Solid",
              "len_mode": "endless", "len_px": 300, "len_candles": 20,  # Länge: endlos / Pixel / Kerzen
              **_txt("middle", "right")},
    "hline": {"color": QColor("#ffffff"), "width": 2, "style": "Solid", **_txt("middle", "right")},
    "rect":  {"color": QColor("#ffeb3b"), "width": 1, "style": "Solid", "extend": "none",
              "fill": True, "fill_color": QColor("#ab47bc"), "fill_opacity": 25,
              "midline": True, "mid_color": QColor("#ffffff"), "mid_width": 1, "mid_style": "Dash",
              **_txt("middle", "center")},
}
SETTINGS_VERSION = 4  # ab 4: Rechteck violett gefüllt, Linie 0 gelb / 1 rot - ältere gespeicherte Werte werden nicht übernommen

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
    "level_width": 1, "level_style": "Solid",            # "Levels-Linie" wie bei TradingView: gilt für die Level-Liste
    "num_fmt": "de",             # "de" = 0,5 (81.751,0) / "en" = 0.5 (81751.0)
    # Was die Fib zeigt - entweder oder, damit nichts doppelt auf einer Linie steht:
    # "setups" = Linien der Setups 1-4 (einzeln an/aus) / "levels" = Level-Liste wie bei TradingView
    "source": "setups",
    "frame_01": True,            # bei "setups": 0 und 1 als Rahmen dazu
}
# Level-Liste 1:1 wie bei TradingView: 24 Plätze (Haken, Wert, Farbe), Reihenfolge = 2 Spalten zeilenweise
_TV_LEVELS = [(-0.382, "#a19c3a", 0), (-0.272, "#3d7a42", 0), (0.0, "#ffeb3b", 1), (0.028, "#8b2e3a", 0),
              (0.087, "#9e9e9e", 0), (0.146, "#9e9e9e", 0), (0.205, "#9e9e9e", 0), (0.264, "#9e9e9e", 0),
              (0.323, "#9e9e9e", 0), (0.886, "#1e7f86", 0), (0.441, "#a19c3a", 0), (0.5, "#ffffff", 1),
              (0.559, "#4caf50", 1), (0.618, "#ffeb3b", 1), (0.677, "#00bcd4", 1), (0.736, "#f23645", 1),
              (0.795, "#1e7f86", 0), (0.854, "#6a2a86", 0), (0.913, "#8b2e3a", 0), (0.972, "#9e9e9e", 0),
              (1.0, "#f23645", 1), (1.031, "#9e9e9e", 0), (1.09, "#8b2e3a", 0), (1.149, "#8b2e3a", 0)]
_NO_FILL = (0.5, 1.0)  # Standard: keine Fläche zwischen 0 und 0,5 sowie zwischen 0,736 und 1
def default_fib_levels_json():
    return [{"value": v, "color": QColor(c).name(QColor.HexArgb), "on": bool(on), "fill": v not in _NO_FILL,
             "fill_color": QColor(c).name(QColor.HexArgb)} for v, c, on in _TV_LEVELS]
FIB_LEVELS = [{"value": v, "color": QColor(c), "on": bool(on), "fill": v not in _NO_FILL, "fill_color": QColor(c)}
              for v, c, on in _TV_LEVELS]
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

def _vt(**kw):
    """Grundlage für die Schwarz-Violett-Gold-Designs - es werden nur die Abweichungen angegeben."""
    t = dict(bg="#000000", box="#000000", border=VIO, title="#ffffff", title_bg="#000000", title_border=GOLD,
             text="#f0f0f0", muted="#a99fb3", btn="#0e0b12", btn_border="#3a2d45", btn_hover="#1c1524",
             on=VIO, on_border=GOLD, on_text="#ffffff", table_bg="#060509", head="#120d17", head_text=GOLD,
             grid="#241c2c", spawn=(VIO, GOLD, "#ffffff"), draw=("#0e0b12", "#ffffff", "#ffffff"),
             clear=("#0e0b12", "#8e2a3a", "#ff9aa8"), icon=GOLD, highlight=VIO, rain=VIO, rain_head=GOLD)
    t.update(kw)
    return t

THEMES.update({
    "19 · Schwarz-Violett Classic": _vt(),
    "20 · Goldrand": _vt(bg="#050505", box="#050505", border=GOLD, title_border=VIO, on=_grad("#e6c45a", "#a8841f"),
                         on_border="#ffffff", on_text="#000000", spawn=(_grad("#9b45b5", "#5e1f72"), "#ffffff", "#ffffff"),
                         draw=("#050505", GOLD, GOLD), head_text="#ffffff", highlight=GOLD, rain=GOLD, rain_head="#ffffff"),
    "21 · Violett Samt": _vt(bg="#0c0612", box="#120a1a", border="#9b45b5", title=GOLD, title_border="#ffffff", title_bg="#1a0f24",
                             btn="#1a0f24", btn_border="#4a2a5a", btn_hover="#2a1637", on=_grad("#9b45b5", "#5e1f72"),
                             spawn=(_grad("#9b45b5", "#5e1f72"), GOLD, "#ffffff"), draw=("#1a0f24", GOLD, GOLD),
                             table_bg="#0e0815", head="#22122e", grid="#33203f", highlight="#9b45b5"),
    "22 · Gold Minimal": _vt(border="#3a3320", title=GOLD, btn="#0d0c09", btn_border="#3a3320", btn_hover="#1a1710",
                             spawn=("#000000", GOLD, GOLD), draw=("#000000", VIO, "#ffffff"), table_bg="#050504",
                             head="#100e08", grid="#221e12"),
    "23 · Royal Violett": _vt(bg="#05030a", box="#05030a", border="#6d2a82", title_border="#c9a227", on_border="#ffffff",
                              spawn=(_grad(VIO, "#3d1648"), "#c9a227", "#ffffff"), draw=("#0b0610", VIO, "#e6d0f0"),
                              head="#1d0e26", head_text="#c9a227", grid="#2a1535"),
    "24 · Neon Gold": _vt(border="#ffd166", title_border="#a24dc4", on="#ffd166", on_border="#ffffff", on_text="#000000",
                          spawn=(_grad("#a24dc4", "#5e1f72"), "#ffd166", "#ffffff"), draw=("#000000", "#ffd166", "#ffd166"),
                          head_text="#ffd166", highlight="#a24dc4", icon="#ffd166", rain="#ffd166", focus="#ffffff"),
    "25 · Dunkelviolett Glas": _vt(bg="#0a0610", box="#0f0916", border="#5a2470", title="#f2e6ff", btn="#1a1022",
                                   btn_border="#3d2350", btn_hover="#2a1637", on_border="#f2e6ff",
                                   spawn=(VIO, "#f2e6ff", "#ffffff"), draw=("#1a1022", GOLD, GOLD),
                                   table_bg="#0c0712", head="#1a1022", grid="#2e1c3a"),
    "26 · Gold-Violett Duo": _vt(title=GOLD, title_border="#ffffff", spawn=(_grad("#e6c45a", "#a8841f"), VIO, "#000000"),
                                 draw=(VIO, VIO, "#ffffff")),
    "27 · Mitternacht": _vt(bg="#04040a", box="#04040a", border="#3b2a6b", on_border="#ffffff", spawn=(VIO, "#ffffff", "#ffffff"),
                            draw=("#04040a", GOLD, GOLD), table_bg="#06060e", head="#0d0b1d", head_text="#ffffff",
                            grid="#1c1838", icon="#d9c27a", highlight="#5b3fa0"),
    "28 · Amethyst Gold": _vt(bg="#08050b", box="#08050b", border="#b88ad0", title=GOLD, title_border="#ffffff", on="#b88ad0",
                              on_border="#ffffff", on_text="#14081c", spawn=(_grad("#e6c45a", "#a8841f"), "#ffffff", "#000000"),
                              draw=("#120b18", "#b88ad0", "#e9d5f5"), head="#1d1226", grid="#33203f", highlight="#b88ad0",
                              rain="#b88ad0"),
})
THEMES.update({
    "29 · Schwarz-Gold Linie": _vt(border="#b8901f", title=GOLD, title_border="#ffffff", spawn=(VIO, "#b8901f", "#ffffff"),
                                   draw=("#000000", "#b8901f", GOLD)),
    "30 · Violett Kante": _vt(border="#a855c7", on="#a855c7", highlight="#a855c7", rain="#a855c7"),
    "31 · Nachtgold": _vt(bg="#07060a", box="#07060a", border="#4a3a1a", title=GOLD,
                          spawn=(_grad("#e6c45a", "#8c6d12"), "#ffffff", "#000000")),
    "32 · Lila Rahmen Weiß": _vt(border="#c45cff", title_border="#ffffff", on="#c45cff", on_border="#ffffff",
                                 spawn=("#000000", "#c45cff", "#ffffff"), highlight="#c45cff", rain="#c45cff"),
    "33 · Gold Glow": _vt(border=GOLD, title_border="#ffffff", on=_grad("#f0d36b", "#b8901f"), on_text="#000000", on_border="#ffffff",
                          spawn=(_grad("#f0d36b", "#b8901f"), "#ffffff", "#000000"), draw=("#000000", VIO, "#ffffff"),
                          highlight=GOLD, rain=GOLD, rain_head="#ffffff"),
    "34 · Violett Tiefe": _vt(bg="#09040d", box="#0e0614", border="#5e1f72", title="#f0d9ff", btn="#16091e",
                              on=_grad(VIO, "#3d1648"), spawn=(_grad(VIO, "#3d1648"), GOLD, "#ffffff"), table_bg="#0b0510", head="#1a0b22"),
    "35 · Kontrast Pur": _vt(border="#ffffff", title_border=VIO, on_border="#ffffff", spawn=(VIO, "#ffffff", "#ffffff"),
                             draw=("#000000", GOLD, GOLD), head_text="#ffffff", grid="#333333"),
    "36 · Goldene Tabelle": _vt(head="#1a1508", grid="#3a3018", table_bg="#080704"),
    "37 · Amethyst Nacht": _vt(bg="#060309", box="#060309", border="#9b45b5", title_border="#e6c45a", on="#9b45b5",
                               spawn=("#9b45b5", "#e6c45a", "#ffffff"), highlight="#9b45b5", rain="#9b45b5"),
    "38 · Schwarz Samt Gold": _vt(bg="#0a0a0a", box="#0f0f0f", border="#2e2a20", title=GOLD, btn="#161616", btn_border="#2e2a20",
                                  on=GOLD, on_text="#000000", on_border="#ffffff", spawn=("#161616", GOLD, GOLD),
                                  draw=("#161616", VIO, "#ffffff"), highlight=GOLD, table_bg="#0c0c0c", head="#161410"),
    "39 · Violett-Weiß Duo": _vt(title_border="#ffffff", spawn=("#ffffff", VIO, "#000000"), draw=(VIO, "#ffffff", "#ffffff")),
    "40 · Royal Schwarz": _vt(border="#3d1648", title=GOLD, title_border=VIO, btn="#0b0610", spawn=(_grad(VIO, "#3d1648"), GOLD, GOLD)),
    "41 · Neon Violett": _vt(border="#d36bff", title_border="#ffd166", on="#d36bff", on_text="#000000", on_border="#ffffff",
                             spawn=(_grad("#d36bff", VIO), "#ffd166", "#ffffff"), highlight="#d36bff", rain="#d36bff",
                             icon="#ffd166", focus="#ffd166"),
    "42 · Gold Rahmen Violett Knopf": _vt(border=GOLD, title_border=VIO, spawn=(VIO, GOLD, "#ffffff"), draw=(VIO, GOLD, "#ffffff")),
    "43 · Mondlicht": _vt(bg="#05050a", box="#05050a", border="#5b4b8a", title="#e8e8ff", on="#5b4b8a",
                          spawn=("#5b4b8a", "#e8e8ff", "#ffffff"), highlight="#5b4b8a", icon="#e8e8ff", rain="#5b4b8a"),
    "44 · Bernstein": _vt(border="#c98a1a", title="#ffcc66", title_border=VIO, on=_grad("#e0a030", "#a06010"), on_text="#000000",
                          spawn=(_grad("#e0a030", "#a06010"), "#ffffff", "#000000"), highlight="#c98a1a", rain="#c98a1a",
                          icon="#ffcc66"),
    "45 · Violett Minimal": _vt(border="#2a2230", title_border=VIO, btn="#0d0b10", btn_border="#2a2230",
                                spawn=("#0d0b10", VIO, "#ffffff"), draw=("#0d0b10", "#2a2230", "#d8d8d8")),
    "46 · Gold Minimal Weiß": _vt(border="#2a2a2a", btn="#0d0d0d", btn_border="#2a2a2a", on=GOLD, on_text="#000000",
                                  spawn=("#0d0d0d", GOLD, GOLD), draw=("#0d0d0d", "#2a2a2a", "#d8d8d8"), highlight=GOLD),
    "47 · Cyber Violett": _vt(bg="#020104", box="#020104", border="#8a2be2", title_border="#ffd166", on="#8a2be2",
                              spawn=(_grad("#8a2be2", "#4b0082"), "#ffd166", "#ffffff"), highlight="#8a2be2", rain="#8a2be2"),
    "48 · Gold-Violett Verlauf": _vt(border=GOLD, title_border="#ffffff", on=_hgrad(VIO, GOLD), spawn=(_hgrad(GOLD, VIO), "#ffffff", "#ffffff"),
                                     draw=("#000000", GOLD, GOLD)),
    "49 · Finale Edition": _vt(bg="#030205", box="#06040a", title=GOLD, title_border="#ffffff", on=_grad("#9b45b5", "#5e1f72"),
                               spawn=(_grad("#9b45b5", "#5e1f72"), GOLD, "#ffffff"), draw=("#06040a", GOLD, GOLD), head="#140a1c"),
})
# Überschrift-Rahmen ("Fib Overlay", "Fibonacci-Stufen") in anderer Farbe als der Kasten drumherum
for _name, _tb in (("Klassisch (Blau)", "#ffffff"), ("13 · Matrix Grün", "#00ff41"), ("2 · Royal Gold", VIO),
                   ("10 · Gold Edition", VIO), ("16 · Gold-Weiß Premium", VIO)):
    THEMES[_name].setdefault("title_border", _tb)
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
    tb, focus = t.get("title_border", GOLD), t.get("focus", GOLD)
    hover = mix(t["bg"], t["highlight"], 0.5)  # deutlich sichtbar, wenn die Maus über einem Knopf ist
    return f"""
        QDialog {{ background-color: {t['bg']}; }}
        QLabel {{ color: {t['text']}; }}
        QGroupBox#topBox, QGroupBox#btnBox {{ background-color: {box}; border: 1px solid {t['border']}; border-radius: 5px; }}
        QGroupBox#topBox {{ margin-top: 5px; }}
        QGroupBox#btnBox {{ margin-top: 0px; padding: 0px; }}
        QGroupBox#tableBox {{ background-color: {box}; border: 1px solid {t['border']}; border-radius: 5px;
                              margin-top: 15px; font-weight: bold; color: {t['text']}; }}
        QGroupBox#tableBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 2px 8px;
                                     background-color: {t['bg']}; border: 1px solid {tb}; border-radius: 4px; color: {t['title']}; }}
        QFrame#titleBox {{ background-color: {t['title_bg']}; border: 1px solid {tb}; border-radius: 4px; }}
        QLabel#title {{ font-weight: bold; font-size: 14px; color: {t['title']}; border: none; background: transparent; }}
        QFrame#line {{ color: {t['border']}; }}
        QLabel#rules {{ color: {t['muted']}; font-size: 11px; border: none; background: transparent; }}
        QPushButton#toggle {{ background-color: {t['btn']}; color: {t['text']}; border: 1px solid {t['btn_border']};
                              border-radius: 4px; padding: 4px 8px; font-size: 11px; min-width: 50px; }}
        QPushButton#toggle:hover {{ background-color: {hover}; border: 1px solid {focus}; }}
        QPushButton#toggle:checked {{ background-color: {t['on']}; color: {t['on_text']}; border: 1px solid {t['on_border']}; font-weight: bold; }}
        QPushButton#toggle:checked:hover {{ border: 1px solid {focus}; }}
        QPushButton#gear {{ background-color: {t['btn']}; border: 2px solid {focus}; border-radius: 5px; padding: 0px; }}
        QPushButton#gear:hover {{ background-color: {hover}; border: 2px solid #ffffff; }}
        QPushButton#tool {{ background-color: {t['btn']}; border: 1px solid {t['btn_border']}; border-radius: 4px; padding: 0px; }}
        QPushButton#tool:hover {{ background-color: {hover}; border: 1px solid {focus}; }}
        QPushButton#tool:checked {{ background-color: {t['on']}; border: 1px solid {t['on_border']}; }}
        QPushButton#tool:checked:hover {{ border: 2px solid {focus}; }}
        QPushButton#spawn, QPushButton#draw, QPushButton#clear {{ padding: 8px; border-radius: 4px; font-size: 12px; }}
        QPushButton#spawn {{ background-color: {sp[0]}; border: 1px solid {sp[1]}; color: {sp[2]}; font-weight: bold; }}
        QPushButton#draw {{ background-color: {dr[0]}; border: 1px solid {dr[1]}; color: {dr[2]}; }}
        QPushButton#clear {{ background-color: {cl[0]}; border: 1px solid {cl[1]}; color: {cl[2]}; }}
        QPushButton#spawn:hover, QPushButton#draw:hover, QPushButton#clear:hover {{ border: 1px solid {focus}; }}
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
        QTableWidget::indicator:checked:disabled {{ background-color: {t['grid']}; border: 1px solid {t['grid']}; }}
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

def settings_css(t):
    """Stylesheet fürs Einstellungsfenster - als Ganzes, damit ein Design-Wechsel nur die Farben tauscht."""
    tb, focus = t.get("title_border", GOLD), t.get("focus", GOLD)
    return (f"QWidget {{ background-color: {t['bg']}; color: {t['text']}; }}"
            f"QGroupBox {{ border: 1px solid {t['border']}; border-radius: 5px; margin-top: 15px; font-weight: bold; color: {t['text']}; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 2px 8px;"
            f" background-color: {t['bg']}; border: 1px solid {tb}; border-radius: 4px; color: {t['title']}; }}"
            f"QPushButton {{ background-color: {t['btn']}; color: {t['text']}; border: 1px solid {t['btn_border']};"
            f" border-radius: 4px; padding: 5px 10px; }}"
            f"QPushButton:hover {{ background-color: {t['btn_hover']}; border: 1px solid {focus}; }}"
            f"QPushButton:checked {{ background-color: {t['on']}; color: {t['on_text']}; border: 1px solid {t['on_border']};"
            f" font-weight: bold; }}"
            f"QCheckBox[dim=\"true\"] {{ color: {t['muted']}; }}"
            f"QLabel#muted {{ color: {t['muted']}; font-weight: normal; }}"
            f"QLabel#hint {{ color: {focus}; font-weight: normal; }}"
            f"QLabel#verHead {{ color: {t['title']}; font-weight: bold; font-size: 14px; border: 1px solid {tb};"
            f" border-radius: 4px; padding: 4px 10px; }}"
            f"QDoubleSpinBox#readonly {{ background-color: {mix(t['bg'], '#ffffff', 0.12)}; color: {t['muted']}; }}"
            + indicator_css(t) + field_css(t))

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

def set_setup_flag(s, key, on):
    """Häkchen eines Setups setzen. "active" ist der Hauptschalter: Die Linien-Häkchen bleiben, wie du sie gesetzt hast,
    und lassen sich auch bei ausgeschaltetem Setup vorbereiten. Ist beim Einschalten keine Linie an, kommen alle."""
    if key == "active":
        s["active"] = on
        if on and not any(s[f"show_{k}"] for k in LINE_KEYS):
            for k in LINE_KEYS: s[f"show_{k}"] = True
    else:
        s[f"show_{key}"] = on

for s in SETUPS: recalc_setup(s)

# ===== SPEICHERN / LADEN =====
SETUP_KEYS = ["entry", "sl", "r_tp1", "r_tp2", "r_tp3", "active"] + \
             [f"{p}_{k}" for k in LINE_KEYS for p in ("color", "thick", "style", "show", "fill")]

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
        "fib_levels": [{"value": l["value"], "color": l["color"].name(QColor.HexArgb), "on": l["on"], "fill": l["fill"],
                        "fill_color": l["fill_color"].name(QColor.HexArgb)} for l in FIB_LEVELS],
        "auto_setup": AUTO_MODE,
        "magnet_drawings": MAGNET_DRAWINGS,
        "num_keep": NUM_KEEP,
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
    global MAGNET_DRAWINGS, NUM_KEEP, AUTO_MODE
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
    MAGNET_DRAWINGS = bool(data.get("magnet_drawings", MAGNET_DRAWINGS))
    NUM_KEEP = bool(data.get("num_keep", NUM_KEEP))
    AUTO_MODE = bool(data.get("auto_setup", AUTO_MODE))
    if isinstance(data.get("fib_levels"), list) and data["fib_levels"] and data.get("version", 1) >= 4:
        FIB_LEVELS[:] = [{"value": float(d["value"]), "color": QColor(d["color"]), "on": bool(d["on"]),
                          "fill": bool(d.get("fill", float(d["value"]) not in _NO_FILL)),
                          "fill_color": QColor(d.get("fill_color", d["color"]))} for d in data["fib_levels"]]
    if data.get("version", 1) >= SETTINGS_VERSION:  # ältere Dateien: neue Werkzeug-Standards behalten
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
            elif k.startswith(("show_", "fill_")) or k == "active": s[k] = bool(d[k])
            else: s[k] = float(d[k])
    for s in SETUPS: recalc_setup(s)

def read_json(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)  # erst komplett schreiben, dann tauschen -> nie eine halbe Datei

# ===== VORLAGEN (je Werkzeug) UND SPEICHERPLÄTZE - eigene Dateien, bleiben beim Zurücksetzen erhalten =====
TEMPLATES_FILE = os.path.join(APP_DIR, "vorlagen.json")
SLOTS_FILE = os.path.join(APP_DIR, "speicherplaetze.json")

def _load_or(path, default):
    try: return read_json(path)
    except Exception: return default

TEMPLATES = _load_or(TEMPLATES_FILE, {})  # {werkzeug: {name: stil}}

def save_templates():
    try: write_json(TEMPLATES_FILE, TEMPLATES)
    except OSError as ex: print("Vorlagen konnten nicht gespeichert werden:", ex)

def load_slots():
    slots = _load_or(SLOTS_FILE, [])
    if not isinstance(slots, list): slots = []
    return (slots + [{"name": "", "saved": "", "data": None} for _ in range(5)])[:5]

def save_slots(slots):
    try: write_json(SLOTS_FILE, slots)
    except OSError as ex: print("Speicherplätze konnten nicht gespeichert werden:", ex)

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
    rx, ry = (12, 200) if strong else (20, 20)
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
    elif kind == "palette":
        p.setPen(QPen(c, 4)); p.setBrush(Qt.NoBrush); p.drawEllipse(QRectF(8, 10, 48, 44))
        p.setPen(Qt.NoPen)
        for x, y, col in ((22, 24, "#ff5252"), (36, 19, "#ffd54f"), (47, 31, "#69f0ae"), (22, 40, "#b388ff")):
            p.setBrush(QColor(col)); p.drawEllipse(QPointF(x, y), 5, 5)
    elif kind == "list":
        for y in (16, 32, 48):
            p.setPen(Qt.NoPen); p.setBrush(c); p.drawEllipse(QPointF(12, y), 4, 4)
            p.setPen(QPen(c, 5, Qt.SolidLine, Qt.RoundCap)); p.drawLine(QPointF(24, y), QPointF(56, y))
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

RECT_PARTS = ("tl", "tr", "bl", "br", "t", "b", "l", "r")  # Griffpunkte am Rechteck: Ecken + Seitenmitten
STYLE_SKIP = ("type", "p1", "p2", "num", "hidden", "locked", "price_ref", "ext_state", "pre_done",
              "alarm", "alarm_state", "deepest", "auto_idx")  # keine Stil-Werte (gehören nicht in Vorlagen)
PART_CURSORS = {"tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor, "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
                "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor, "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
                "p1": Qt.SizeAllCursor, "p2": Qt.SizeAllCursor, "move": Qt.SizeAllCursor}  # Mauszeiger wie bei TradingView


def copy_obj(o):
    """Tiefe Kopie eines Objekts (Farben/Punkte werden mitkopiert, nicht nur verlinkt)."""
    return {k: (QColor(v) if isinstance(v, QColor) else QPoint(v) if isinstance(v, QPoint)
                else list(v) if isinstance(v, list) else v) for k, v in o.items()}


def template_style(d):
    return {k: (v.name(QColor.HexArgb) if isinstance(v, QColor) else v) for k, v in d.items() if k not in STYLE_SKIP}


def fill_template_menu(menu, ov, d, parent, after_apply=None):
    """Vorlagen-Menü wie bei TradingView: speichern als, voreingestellte anwenden, eigene Vorlagen (mit Papierkorb)."""
    kind = d["type"]
    a_save = menu.addAction("Zeichenvorlage speichern als …")
    a_default = menu.addAction("Voreingestellte Vorlage anwenden")
    a_make_default = menu.addAction(f"Als Standard für neue: {TOOL_NAMES[kind]}")
    names = sorted(TEMPLATES.get(kind, {}), key=str.lower)
    if names: menu.addSeparator()
    t = THEMES[THEME]
    for name in names:
        # eine Zeile je Vorlage: Name anklicken = anwenden, 🗑 = löschen
        row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(8, 1, 6, 1)
        b = QPushButton(name); b.setFlat(True); b.setStyleSheet(f"text-align: left; color: {t['text']}; padding: 3px 6px;")
        rm = QPushButton("🗑"); rm.setFlat(True); rm.setFixedWidth(26); rm.setToolTip("Vorlage löschen")
        h.addWidget(b, 1); h.addWidget(rm)
        wa = QWidgetAction(menu); wa.setDefaultWidget(row); menu.addAction(wa)
        def apply(checked=False, n=name):
            style_from_json(d, TEMPLATES[kind][n]); ov.update(); menu.close()
            if after_apply: after_apply()
        def remove(checked=False, n=name):
            TEMPLATES[kind].pop(n, None); save_templates(); menu.close()
        b.clicked.connect(apply); rm.clicked.connect(remove)
    def on_action(act):
        if act == a_save:
            name, ok = QInputDialog.getText(parent, "Zeichenvorlage speichern", f"Name der Vorlage für {TOOL_NAMES[kind]}:")
            if ok and name.strip():
                TEMPLATES.setdefault(kind, {})[name.strip()] = template_style(d); save_templates()
        elif act == a_default:
            style_from_json(d, style_to_json(TOOL_STYLES[kind])); ov.update()
            if after_apply: after_apply()
        elif act == a_make_default:
            for k, v in template_style(d).items():
                if k in TOOL_STYLES[kind]:
                    TOOL_STYLES[kind][k] = QColor(v) if isinstance(TOOL_STYLES[kind][k], QColor) else v
            ov.settings_changed()
    menu.triggered.connect(on_action)


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
        self.fibs = []          # mehrere Fibs möglich: {"type": "fib", "p1", "p2", "price_ref", "num", ...}
        self.placing_fib = None # Fib, die gerade gesetzt wird (nach dem 1. Klick)
        self.hover = None
        self.mode = "idle"
        self.tool = None        # was gerade gesetzt wird: "fib" oder ein Zeichenwerkzeug
        self.drawings = []      # einzelne Zeichnungen: {"type", "p1", "p2", "color", "width", "style", "text", ...}
        self.pending = None     # Zeichnung, die gerade entsteht (nach dem 1. Klick)
        self.dragging = None    # (art, index, teil): art "fib"/"draw", teil "p1"/"p2"/"move" oder Rechteck-Griff
        self.drag_start = self.drag_orig = None
        self._moved = False
        self.selected = None    # zuletzt angeklicktes Objekt - für Entf, Strg+C und "+ Text hinzufügen"
        self.clipboard = None   # kopiertes Objekt (Strg+C) zum Einfügen (Strg+V)
        self._placeholder = None
        self._hwnd = None
        self.main_panel = None  # Referenz auf das Dashboard
        self._dialog = self.list_dialog = None
        self.counters = {}      # laufende Nummer je Objektart (Rechteck 1, Rechteck 2 …)
        self.candle_px = 12     # gemessener Kerzenabstand in Pixeln (für Längen "in Kerzen")
        self.alert_text, self.alert_until = None, 0.0
        self.snap_pt = None     # Magnet-Vorschau: hier würde der Punkt einrasten
        self._last_mouse = None

        self.line_length = 800
        self.show_price_input = True
        self.is_locked = False
        self.is_hidden = False

        self.hk_map = dict(HK_DEFAULTS)
        # Kurs-Beobachtung (Verlängerung rot/grün, Alarme, Automatik) - tut nichts, solange nichts davon an ist
        self.watch_timer = QTimer(self); self.watch_timer.setInterval(700)
        self.watch_timer.timeout.connect(self._watch_price); self.watch_timer.start()
        # Magnet-Vorschau: kurz nach der letzten Mausbewegung einmal den Bildschirm prüfen
        self.preview_timer = QTimer(self); self.preview_timer.setSingleShot(True); self.preview_timer.setInterval(45)
        self.preview_timer.timeout.connect(self._preview_snap)

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

    def objects_changed(self):
        # Objektliste aktuell halten (neue, gelöschte, umbenannte Objekte)
        self.update()
        if self.list_dialog and self.list_dialog.isVisible(): self.list_dialog.refresh()

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

    # ----- Objekte: Nummern, Namen -----
    def _assign_num(self, o):
        kind = o.get("type", "fib")
        self.counters[kind] = self.counters.get(kind, 0) + 1
        o["num"] = self.counters[kind]

    def name_of(self, o):
        """Anzeigename wie "Rechteck 2" - Nummer bleibt fest oder wird neu durchgezählt (Einstellung)."""
        kind = o.get("type", "fib")
        label = "Fib" if kind == "fib" else TOOL_NAMES[kind]
        if NUM_KEEP: n = o.get("num", 1)
        else:
            same = self.fibs if kind == "fib" else [d for d in self.drawings if d["type"] == kind]
            n = next((i + 1 for i, x in enumerate(same) if x is o), 1)
        return f"{label} {n}"

    def _new_fib(self, p1, p2):
        f = {"type": "fib", "p1": p1, "p2": p2, "price_ref": None}
        self._assign_num(f)
        return f

    def _new_drawing(self, kind, pt):
        d = {"type": kind, "p1": pt, "p2": pt}
        for k, v in TOOL_STYLES[kind].items(): d[k] = QColor(v) if isinstance(v, QColor) else v
        return d

    def _add_drawing(self, d):
        self._assign_num(d)
        self.drawings.append(d)
        if d["type"] == "hray" and d.get("len_mode") == "candles": self._estimate_candle_px(d["p1"])
        self.objects_changed()

    def _list_of(self, kind):
        return self.fibs if kind == "fib" else self.drawings

    def _index_of(self, kind, o):
        return next((i for i, x in enumerate(self._list_of(kind)) if x is o), None)

    # ----- Zeichnen starten / beenden -----
    def _hk_draw(self):
        self.pending = self.placing_fib = self.hover = None
        self.tool = "fib"
        self._activate("placing", Qt.CrossCursor)

    def start_tool(self, kind):
        self.pending = self.placing_fib = None
        self.tool = kind
        self._activate("placing", Qt.CrossCursor)

    def _fib_added(self, f):
        # neue Fib: Automatik fängt wieder bei Setup 1 an
        self.fibs.append(f)
        if AUTO_MODE: self._auto_set(f, 0, announce=False)
        self.objects_changed()

    def spawn_default_fib(self):
        cx, cy = self.width() // 2, self.height() // 2
        off = 30 * (len(self.fibs) % 5)  # mehrere Sofort-Fibs nicht genau übereinander
        f = self._new_fib(QPoint(cx + 200 + off, cy - 200 + off),  # 0 oben rechts, 1 unten links - wie bei TradingView
                          QPoint(cx - 200 + off, cy + 200 + off))
        self.tool = None
        self._activate("edit", Qt.OpenHandCursor)
        self._fib_added(f)
        QTimer.singleShot(200, lambda: self._finish_placement(f))

    def _hk_edit(self):
        if self.has_content(): self._activate("edit", Qt.OpenHandCursor)

    def _hk_clear(self):
        self.fibs, self.drawings, self.counters = [], [], {}
        self.placing_fib = self.hover = self.pending = self.tool = self.dragging = self.snap_pt = self.selected = None
        self.mode = "idle"
        self._set_ct(True); self.setCursor(Qt.ArrowCursor)
        self.objects_changed()
        if self.main_panel: self.main_panel.placement_finished()

    def _hk_quit(self):
        for i in HK_ACTIONS: user32.UnregisterHotKey(self._hwnd, i)
        QApplication.quit()

    def _end_placing(self):
        self.tool = self.pending = self.placing_fib = self.snap_pt = None
        self.mode = "edit" if self.has_content() else "idle"
        self._update_ct()
        self.setCursor(Qt.ArrowCursor)
        self.update()
        if self.main_panel: self.main_panel.placement_finished()

    def cancel_placing(self):
        if self.placing_fib is not None:
            self.fibs = [f for f in self.fibs if f is not self.placing_fib]
        self.hover = None
        self._end_placing()
        self.objects_changed()

    def delete_item(self, kind, idx):
        o = self._list_of(kind)[idx]
        if self.selected and self.selected[1] is o: self.selected = None
        del self._list_of(kind)[idx]
        self._end_placing()
        self.objects_changed()

    def duplicate(self, kind, idx, offset=QPoint(30, 30)):
        """Kopie (leicht versetzt) daneben legen - bekommt eine eigene Nummer. Gibt den neuen Index zurück."""
        o = copy_obj(self._list_of(kind)[idx])
        for k in ("hidden", "locked", "alarm", "alarm_state"): o.pop(k, None)
        o["p1"], o["p2"] = o["p1"] + offset, o["p2"] + offset
        if kind == "fib":
            self._assign_num(o); self.fibs.append(o); self.objects_changed()
        else: self._add_drawing(o)
        return len(self._list_of(kind)) - 1

    def copy_selected(self):
        if self.selected: self.clipboard = (self.selected[0], copy_obj(self.selected[1]))

    def paste(self, pos=None):
        """Kopiertes Objekt einfügen - an der Mausposition (wie Strg+V bei TradingView)."""
        if not self.clipboard: return
        kind, src = self.clipboard
        o = copy_obj(src)
        for k in ("hidden", "locked", "alarm", "alarm_state"): o.pop(k, None)
        pos = pos or self.mapFromGlobal(QCursor.pos())
        delta = pos - o["p1"]
        o["p1"], o["p2"] = o["p1"] + delta, o["p2"] + delta
        if kind == "fib":
            self._assign_num(o); self.fibs.append(o); self.objects_changed()
        else: self._add_drawing(o)
        self.selected = (kind, o)
        if self.mode == "idle": self._activate("edit", Qt.ArrowCursor)

    def reorder(self, kind, idx, to_front):
        # visuelle Reihenfolge: nach vorne = wird zuletzt gezeichnet
        lst = self._list_of(kind)
        o = lst.pop(idx)
        if to_front: lst.append(o)
        else: lst.insert(0, o)
        self.objects_changed()

    def _obj(self, kind, idx):
        return self._list_of(kind)[idx]

    def all_objects(self):
        """Alle fertigen Objekte als (art, index, objekt) - für Objektliste und Menüs."""
        return ([("fib", i, f) for i, f in enumerate(self.fibs) if f["p2"] is not None]
                + [("draw", i, d) for i, d in enumerate(self.drawings)])

    # ----- Treffer-Tests -----
    def _hit(self, pos, pt, r=15):
        return pt is not None and (pos - pt).manhattanLength() <= r

    def _handles(self, d):
        """Griffpunkte einer Zeichnung {name: punkt}. Rechteck wie bei TradingView: Ecken + Seitenmitten."""
        if d["type"] in ("hline", "hray"): return {"p1": d["p1"]}
        if d["type"] != "rect": return {"p1": d["p1"], "p2": d["p2"]}
        x0, x1 = sorted((d["p1"].x(), d["p2"].x())); y0, y1 = sorted((d["p1"].y(), d["p2"].y()))
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        return {"tl": QPoint(x0, y0), "tr": QPoint(x1, y0), "bl": QPoint(x0, y1), "br": QPoint(x1, y1),
                "t": QPoint(cx, y0), "b": QPoint(cx, y1), "l": QPoint(x0, cy), "r": QPoint(x1, cy)}

    def _hit_test(self, pos):
        """Was liegt unter der Maus? (art, index, teil) oder None. Verborgene Objekte zählen nicht."""
        for i in reversed(range(len(self.fibs))):
            f = self.fibs[i]
            if f.get("hidden"): continue
            if self._hit(pos, f["p1"]): return ("fib", i, "p1")
            if self._hit(pos, f["p2"]): return ("fib", i, "p2")
        for i in reversed(range(len(self.drawings))):
            d = self.drawings[i]
            if d.get("hidden") or d["type"] == "hline": continue
            for part, pt in self._handles(d).items():
                if self._hit(pos, pt, 9): return ("draw", i, part)
        for i in reversed(range(len(self.drawings))):
            d = self.drawings[i]
            if not d.get("hidden") and self._on_drawing(pos, d): return ("draw", i, "move")
        for i in reversed(range(len(self.fibs))):
            f = self.fibs[i]
            if not f.get("hidden") and self._on_fib(pos, f): return ("fib", i, "move")
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
        """Sichtbare Level, sortiert - entweder die Level-Liste (wie TradingView) oder die Linien der Setups.
        Bei den Setups werden gleiche Werte eine Linie mit allen Namen, z. B. 0,559 · SL1 · E2."""
        groups = {}
        def add(frac, color, thick, style, name, fill=True, fill_color=None, edge=False):
            g = groups.setdefault(round(frac, 6), {"frac": frac, "color": color, "thick": thick, "style": style, "names": [],
                                                   "fill": fill, "fill_color": fill_color or color, "edge": edge})
            if name: g["names"].append(name)
        if FIB_STYLE["source"] == "levels":
            for lv in FIB_LEVELS:
                if lv["on"]: add(lv["value"], lv["color"], FIB_STYLE["level_width"], FIB_STYLE["level_style"], None,
                                 lv.get("fill", True), lv.get("fill_color"))
            return sorted(groups.values(), key=lambda g: g["frac"])
        if FIB_STYLE["frame_01"]:
            # 0 und 1 als Rahmen (Farbe aus der Level-Liste) - ohne Fläche bis zur ersten bzw. nach der letzten Setup-Linie
            for v, fallback in ((0.0, "#ffeb3b"), (1.0, "#f23645")):
                lv = next((l for l in FIB_LEVELS if abs(l["value"] - v) < 1e-9), None)
                add(v, QColor(lv["color"] if lv else fallback), FIB_STYLE["level_width"], FIB_STYLE["level_style"], None,
                    False, edge=True)
        for s in SETUPS:
            if not s["active"]: continue
            n = s["n"]
            for k, frac, label in (("e", s["entry"], f"E{n}"), ("sl", s["sl"], f"SL{n}"), ("be", s["be"], f"BE{n}"),
                                   ("tp1", s["tp1"], f"TP1_{n}"), ("tp2", s["tp2"], f"TP2_{n}"), ("tp3", s["tp3"], f"TP3_{n}")):
                # Fläche je Linie an/aus (Einstellungen, Spalte "Fläche") - z. B. SL: rot zwischen Entry und SL
                if s[f"show_{k}"]: add(frac, s[f"color_{k}"], s[f"thick_{k}"], s[f"style_{k}"], label, s[f"fill_{k}"])
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
            mode = d.get("len_mode", "endless")
            if mode == "px": end = a.x() + d.get("len_px", 300)
            elif mode == "candles": end = a.x() + d.get("len_candles", 20) * self.candle_px
            else: end = self._screen_span(d["p1"])[1]
            return a, QPointF(end, a.y())
        if d["type"] == "ray":
            v = b - a
            length = math.hypot(v.x(), v.y())
            return a, (b if length < 1 else a + v * (20000 / length))  # weit über den Bildschirmrand hinaus
        return a, b

    def _rect_area(self, d):
        """Gezeichnete Fläche des Rechtecks - mit "Verlängern" bis zum Bildschirmrand."""
        r = QRectF(QPointF(d["p1"]), QPointF(d["p2"])).normalized()
        ext = d.get("extend", "none")
        if ext != "none":
            x0, x1 = self._screen_span(d["p1"])
            if ext in ("left", "both"): r.setLeft(x0)
            if ext in ("right", "both"): r.setRight(x1)
        return r

    def _on_drawing(self, pos, d):
        p = QPointF(pos)
        if d["type"] == "rect": return self._rect_area(d).adjusted(-6, -6, 6, 6).contains(p)
        a, b = self._line_ends(d)
        return dist_to_segment(p, a, b) <= 6

    # ----- Magnet -----
    def snap(self, pos, drawing=False):
        """Magnet: Punkt an Hoch/Tief der Kerze darunter einrasten lassen (Overlay-Koordinaten rein und raus)."""
        if not MAGNET_ON or self._hwnd is None or (drawing and not MAGNET_DRAWINGS): return pos
        g = self.mapToGlobal(pos)
        scr = QApplication.screenAt(g)
        if not scr: return pos
        sg = scr.geometry()
        strong = MAGNET_MODE == "strong"
        # auch "stark" sucht nur in der Nähe - sonst springt der Punkt z. B. in die Kopfzeile der Webseite
        reach = 250 if strong else 150
        x0, x1 = max(sg.left(), g.x() - 60), min(sg.right() + 1, g.x() + 61)
        y0, y1 = max(sg.top(), g.y() - reach), min(sg.bottom() + 1, g.y() + reach + 1)
        buf = self._grab_without_overlay(x0, y0, x1 - x0, y1 - y0)
        if buf is None: return pos
        hit = find_wick(buf, x1 - x0, y1 - y0, g.x() - x0, g.y() - y0, strong)
        return self.mapFromGlobal(QPoint(hit[0] + x0, hit[1] + y0)) if hit else pos

    def _grab_without_overlay(self, x, y, w, h):
        # eigene Linien aus dem Bildschirmfoto nehmen, sonst sieht der Magnet die Fib statt der Kerze
        if not user32.SetWindowDisplayAffinity(self._hwnd, WDA_EXCLUDEFROMCAPTURE): return None
        try: return grab_screen(x, y, w, h)
        finally: user32.SetWindowDisplayAffinity(self._hwnd, WDA_NONE)

    def _estimate_candle_px(self, pt):
        # Kerzenabstand rund um den Punkt messen (für Längen "in Kerzen")
        if self._hwnd is None: return
        g = self.mapToGlobal(pt); scr = QApplication.screenAt(g)
        if not scr: return
        sg = scr.geometry()
        x0, x1 = max(sg.left(), g.x() - 300), min(sg.right() + 1, g.x() + 300)
        y0, y1 = max(sg.top(), g.y() - 200), min(sg.bottom() + 1, g.y() + 200)
        buf = self._grab_without_overlay(x0, y0, x1 - x0, y1 - y0)
        res = analyze_candles(buf, x1 - x0, y1 - y0) if buf else None
        if res and res[0] and 3 <= res[0] <= 80: self.candle_px = res[0]; self.update()

    def _magnet_target(self, pos, part, drawing):
        # wohin der Magnet einen gezogenen Griff setzt: Seiten oben/unten nur in der Höhe, links/rechts gar nicht
        if part in ("l", "r", "move"): return pos
        sp = self.snap(pos, drawing)
        return QPoint(pos.x(), sp.y()) if part in ("t", "b") else sp

    def _preview_snap(self):
        """Magnet-Vorschau wie bei TradingView: schon vor dem Klick bzw. beim Ziehen zeigen, wo es einrastet."""
        pos = self._last_mouse
        if pos is None or not MAGNET_ON: return
        if self.mode == "placing":
            sp = self.snap(pos, drawing=self.tool != "fib")
            self.snap_pt = sp if sp != pos else None
            if self.pending: self.pending["p2"] = sp
            elif self.placing_fib is not None: self.hover = sp
            self.update()
        elif self.mode == "edit" and self.dragging and self.dragging[2] != "move":
            self._apply_drag(self._magnet_target(pos, self.dragging[2], self.dragging[0] == "draw"))
            self.update()

    # ----- Preis aus der Bildschirmhöhe (über eine Fib mit eingegebenen Preisen) -----
    def price_map(self):
        """(y -> Preis, Preis -> y) aus der neuesten Fib mit Preisen - oder None."""
        f = next((f for f in reversed(self.fibs) if f["p2"] is not None and f.get("price_ref")), None)
        if not f: return None
        _, _, y_of = self._fib_geom(f["p1"], f["p2"])
        y0, y1 = y_of(0), y_of(1)
        if y1 == y0: return None
        to_price = lambda y: self.price_at(f, (y - y0) / (y1 - y0))
        p0, p1 = to_price(y0), to_price(y1)
        if p1 == p0: return None
        return to_price, (lambda pr: y0 + (pr - p0) / (p1 - p0) * (y1 - y0))

    # ----- Kurs beobachten: Verlängerung, Alarme, Automatik -----
    def _last_candle(self, x0, x1, y0, y1):
        """Schlusskurs der letzten Kerze im Bereich (Overlay-Koordinaten) -> (x, y) oder None. Misst nebenbei den Kerzenabstand."""
        scr = QApplication.screenAt(self.mapToGlobal(QPoint(int((x0 + x1) / 2), int((y0 + y1) / 2))))
        if not scr: return None
        sg = scr.geometry()
        g0, g1 = self.mapToGlobal(QPoint(int(x0), int(y0))), self.mapToGlobal(QPoint(int(x1), int(y1)))
        gx0, gy0 = max(sg.left(), g0.x()), max(sg.top(), g0.y())
        gx1, gy1 = min(sg.right() + 1, g1.x()), min(sg.bottom() + 1, g1.y())
        if gx1 - gx0 < 10 or gy1 - gy0 < 10: return None
        buf = self._grab_without_overlay(gx0, gy0, gx1 - gx0, gy1 - gy0)
        res = analyze_candles(buf, gx1 - gx0, gy1 - gy0) if buf else None
        if not res: return None
        spacing, cx, cy = res
        if spacing and 3 <= spacing <= 80: self.candle_px = spacing
        p = self.mapFromGlobal(QPoint(cx + gx0, cy + gy0))
        return p.x(), p.y()

    def _watch_price(self):
        """Alle 0,7 s: letzte Kerze am Bildschirm suchen (Test-Funktion) - für Verlängerung, Alarme und Automatik."""
        need_fib = EXT_STYLE["on"] and (EXT_STYLE["live"] or EXT_STYLE["alarm"] or EXT_STYLE["pre_alert"] > 0)
        alarm_draw = [d for d in self.drawings if d.get("alarm") and not d.get("hidden")]
        if not (need_fib or AUTO_MODE or alarm_draw): return
        if self.is_hidden or self._hwnd is None or self.dragging or self.mode == "placing": return
        changed = False
        for f in self.fibs:
            if f["p2"] is None or f.get("hidden"): continue
            x0, x1, y_of = self._fib_geom(f["p1"], f["p2"])
            if y_of(1) == y_of(0): continue
            ya, yb = sorted((y_of(0), y_of(1)))
            pad = (yb - ya) * 0.35 + 20  # etwas über/unter die Fib hinaus, aber nicht in Kopfzeile oder Menüs
            hit = self._last_candle(x0, x1 + (EXT_STYLE["candles"] + 3) * self.candle_px, ya - pad, yb + pad)
            if not hit: continue
            oy = hit[1]
            frac = (oy - y_of(0)) / (y_of(1) - y_of(0))   # wo der Kurs gerade in der Fib steht
            if AUTO_MODE and f is self._auto_fib(): changed |= self._auto_step(f, frac)
            if not need_fib: continue
            level = EXT_STYLE["level"]
            state = "up" if oy < y_of(level) else "down"   # kleiner y = höherer Kurs
            old = f.get("ext_state")
            if old and state != old and EXT_STYLE["alarm"]:
                self._alarm(f"{self.name_of(f)}: Level {fmt_level(level)} gekreuzt – Kurs jetzt {'darüber' if state == 'up' else 'darunter'}")
            pre = EXT_STYLE["pre_alert"]
            if pre > 0:
                dist = abs(frac - level)
                if dist <= pre and not f.get("pre_done"):
                    f["pre_done"] = True
                    self._alarm(f"Vorwarnung: Kurs nur noch {fmt_level(round(dist, 3))} vom Level {fmt_level(level)} entfernt")
                elif dist > pre * 2: f["pre_done"] = False
            if state != old: f["ext_state"] = state; changed = True
        for d in alarm_draw: self._watch_drawing(d)
        if changed: self.update()

    def _watch_drawing(self, d):
        """Alarm für Rechteck/Linie: Kurs erreicht das Rechteck bzw. kreuzt die Linie."""
        sx0, sx1 = self._screen_span(d["p1"])
        if d["type"] == "rect":
            r = self._rect_area(d)
            x0, x1, y0, y1 = r.left(), r.right() + 10 * self.candle_px, r.top() - 60, r.bottom() + 60
        else:
            a, b = self._line_ends(d)
            x0 = sx0 if d["type"] == "hline" else min(a.x(), b.x())
            x1 = sx1 - (sx1 - sx0) * 0.22 if d["type"] in ("hline", "ray") else max(a.x(), b.x())  # rechts Platz für Menüs der Webseite
            y0, y1 = min(a.y(), b.y()) - 120, max(a.y(), b.y()) + 120
        hit = self._last_candle(max(x0, sx0), min(x1, sx1), y0, y1)
        if not hit: return
        cx, cy = hit
        if d["type"] == "rect":
            r = self._rect_area(d)
            state = "in" if r.top() <= cy <= r.bottom() else ("above" if cy < r.top() else "below")
            if d.get("alarm_state") not in (None, "in") and state == "in":
                self._alarm(f"{self.name_of(d)}: Kurs hat das Rechteck erreicht")
        else:
            a, b = self._line_ends(d)
            if b.x() == a.x(): return
            line_y = a.y() + (b.y() - a.y()) * (cx - a.x()) / (b.x() - a.x())
            state = "up" if cy < line_y else "down"
            if d.get("alarm_state") and state != d["alarm_state"]:
                self._alarm(f"{self.name_of(d)}: Kurs hat die Linie gekreuzt – jetzt {'darüber' if state == 'up' else 'darunter'}")
        d["alarm_state"] = state

    def _auto_fib(self):
        # Automatik arbeitet mit der neuesten sichtbaren Fib
        return next((f for f in reversed(self.fibs) if f["p2"] is not None and not f.get("hidden")), None)

    def _auto_set(self, f, idx, announce=True):
        f["auto_idx"] = idx
        for i, s in enumerate(SETUPS): set_setup_flag(s, "active", i == idx)  # Linien-Häkchen bleiben, wie du sie gesetzt hast
        if self.main_panel: self.main_panel.update_table()
        if announce:
            s = SETUPS[idx]
            self._alarm(f"Automatik: Setup {s['n']} aktiv (Entry {fmt_level(s['entry'])} · SL {fmt_level(s['sl'])})", beep=False)

    def _auto_step(self, f, frac):
        """Automatik (Test): läuft der Kurs durch den SL des aktiven Setups, kommt das nächste Setup - nur vorwärts."""
        f["deepest"] = max(f.get("deepest", -1e9), frac)
        idx = f.get("auto_idx", 0)
        new = idx
        while new < len(SETUPS) - 1 and f["deepest"] >= SETUPS[new]["sl"]: new += 1
        if new != idx:
            self._auto_set(f, new); return True
        return False

    def _alarm(self, text, beep=True):
        if beep: winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        self.alert_text, self.alert_until = text, time.time() + 6
        self.update(); QTimer.singleShot(6100, self.update)

    # ----- Maus und Tastatur -----
    def keyPressEvent(self, e):
        ctrl = bool(e.modifiers() & Qt.ControlModifier)
        if e.key() == Qt.Key_Escape and self.mode == "placing": self.cancel_placing()
        elif e.key() == Qt.Key_Delete and self.selected and self.mode == "edit":
            kind, o = self.selected; idx = self._index_of(kind, o)
            if idx is not None and self._confirm(f"Möchtest du „{self.name_of(o)}“ wirklich entfernen?", QCursor.pos()):
                self.delete_item(kind, idx)
        elif ctrl and e.key() == Qt.Key_C: self.copy_selected()
        elif ctrl and e.key() == Qt.Key_V: self.paste()
        else: super().keyPressEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            if self.mode == "placing": self.cancel_placing()  # Rechtsklick bricht ab wie Esc
            else: self._context_menu(e.pos(), e.globalPos())
            return

        if e.button() != Qt.LeftButton or self.is_locked: return
        if self.mode == "placing":
            self.preview_timer.stop()
            pt = self.snap(e.pos(), drawing=self.tool != "fib")
            if self.tool == "fib":
                f = self.placing_fib
                if f is None:
                    self.placing_fib = self._new_fib(pt, None)
                    self._fib_added(self.placing_fib); self.update()
                else:
                    f["p2"] = pt; self.placing_fib = self.tool = self.snap_pt = None; self.mode = "edit"
                    self.setCursor(Qt.ArrowCursor)
                    self.objects_changed()
                    QTimer.singleShot(100, lambda: self._finish_placement(f))
            elif self.pending is None:
                self.pending = self._new_drawing(self.tool, pt)
                if self.tool in ("hline", "hray"):
                    d = self.pending; self.pending = None
                    self._add_drawing(d); self.selected = ("draw", d); self._end_placing()
                else: self.update()
            else:
                d = self.pending; d["p2"] = pt; self.pending = None
                self._add_drawing(d); self.selected = ("draw", d); self._end_placing()
        elif self.mode == "edit":
            hit = self._hit_test(e.pos())
            if not hit: return
            kind, idx, part = hit
            if part == "move" and e.modifiers() & Qt.ControlModifier and not self._obj(kind, idx).get("locked"):
                idx = self.duplicate(kind, idx, QPoint(0, 0))  # Klonen wie bei TradingView: Strg + Ziehen
                hit = (kind, idx, part)
            o = self._obj(kind, idx)
            self.selected = (kind, o)
            self.update()
            if o.get("locked"): return  # fixiertes Objekt bleibt, wo es ist
            if o.get("type") == "rect":
                # Ecken ordnen (p1 = oben links, p2 = unten rechts), damit jeder Griff weiß, welche Seite er bewegt
                x0, x1 = sorted((o["p1"].x(), o["p2"].x())); y0, y1 = sorted((o["p1"].y(), o["p2"].y()))
                o["p1"], o["p2"] = QPoint(x0, y0), QPoint(x1, y1)
            self.dragging, self.drag_start, self._moved = hit, e.pos(), False
            self.drag_orig = (QPoint(o["p1"]), QPoint(o["p2"]))
            self.setCursor(PART_CURSORS.get(part, Qt.SizeAllCursor))

    def _apply_drag(self, pos):
        kind, idx, part = self.dragging
        o = self._obj(kind, idx)
        if part == "move":
            delta = pos - self.drag_start
            o["p1"], o["p2"] = self.drag_orig[0] + delta, self.drag_orig[1] + delta
        elif part in RECT_PARTS:
            p1, p2 = QPoint(o["p1"]), QPoint(o["p2"])
            if part in ("tl", "l", "bl"): p1.setX(pos.x())
            if part in ("tr", "r", "br"): p2.setX(pos.x())
            if part in ("tl", "t", "tr"): p1.setY(pos.y())
            if part in ("bl", "b", "br"): p2.setY(pos.y())
            o["p1"], o["p2"] = p1, p2
        else:
            o[part] = pos
            if o.get("type") in ("hline", "hray"): o["p2"] = o["p1"]

    def mouseMoveEvent(self, e):
        self._last_mouse = e.pos()
        if self.is_locked: return
        if self.mode == "placing":
            if self.placing_fib is not None: self.hover = e.pos(); self.update()
            elif self.pending: self.pending["p2"] = e.pos(); self.update()
            if MAGNET_ON: self.preview_timer.start()
        elif self.mode == "edit" and self.dragging:
            if (e.pos() - self.drag_start).manhattanLength() > 2: self._moved = True
            self._apply_drag(e.pos())
            if MAGNET_ON and self.dragging[2] != "move": self.preview_timer.start()
            self.update()
        elif self.mode == "edit":
            # Mauszeiger je nach Griff - wie bei TradingView (↔ ↕ ⤡ ✥)
            hit = self._hit_test(e.pos())
            locked = hit and self._obj(hit[0], hit[1]).get("locked")
            self.setCursor(Qt.ArrowCursor if not hit or locked else PART_CURSORS.get(hit[2], Qt.SizeAllCursor))

    def mouseReleaseEvent(self, e):
        if not self.dragging: return
        self.preview_timer.stop()
        kind, idx, part = self.dragging
        o = self._obj(kind, idx)
        if not self._moved:
            # nur geklickt, nicht gezogen: Klick auf "+ Text hinzufügen" öffnet den Text-Reiter
            self.dragging = None
            if self._placeholder and kind == "draw" and self._placeholder.contains(QPointF(e.pos())):
                self.open_properties(idx, e.globalPos(), tab="text")
            return
        # Magnet beim Loslassen: Endpunkt/Ecke einrasten, verschobene horizontale Linien in der Höhe
        if part != "move": self._apply_drag(self._magnet_target(e.pos(), part, kind == "draw"))
        elif o.get("type") in ("hline", "hray"):
            y = self.snap(QPoint(e.pos().x(), o["p1"].y()), drawing=True).y()
            o["p1"] = o["p2"] = QPoint(o["p1"].x(), y)
        if o.get("type") == "rect":
            x0, x1 = sorted((o["p1"].x(), o["p2"].x())); y0, y1 = sorted((o["p1"].y(), o["p2"].y()))
            o["p1"], o["p2"] = QPoint(x0, y0), QPoint(x1, y1)
        self.dragging = None
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

    def open_properties(self, idx, gpos, tab="style"):
        if self._dialog: self._dialog.close()
        self._dialog = DrawingDialog(self, self.drawings[idx], tab)
        self._dialog.adjustSize(); self._dialog.move(gpos + QPoint(16, 16)); self._dialog.show()

    def open_object_list(self, gpos=None):
        if not self.list_dialog: self.list_dialog = ObjectListDialog(self)
        self.list_dialog.refresh()
        if gpos is not None: self.list_dialog.move(gpos + QPoint(16, 16))
        bring_window_to_front(self.list_dialog)

    def _context_menu(self, pos, gpos):
        """Rechtsklick-Menü aufgebaut wie bei TradingView."""
        hit = self._hit_test(pos)
        if not hit:
            visible = [i for i, f in enumerate(self.fibs) if not f.get("hidden") and f["p2"] is not None]
            if not visible: return
            hit = ("fib", visible[-1], "move")  # z. B. Rechtsklick auf eine Beschriftung neben der Fib
        kind, idx = hit[0], hit[1]
        o = self._obj(kind, idx)
        self.selected = (kind, o)
        d = o if kind == "draw" else None
        name = self.name_of(o)
        menu = QMenu(self)
        menu.addSection(name)
        act_alarm = menu.addAction(("Alarm entfernen" if o.get("alarm") else f"Alarm für {name} hinzufügen …") if d
                                   else f"Alarm für {name} hinzufügen …")
        tpl_menu = menu.addMenu("Vorlage")
        slot_acts = {}
        if d: fill_template_menu(tpl_menu, self, d, self)
        else:
            # bei der Fib sind die Vorlagen die Speicherplätze aus den Einstellungen
            for i, slot in enumerate(load_slots()):
                a = tpl_menu.addAction(slot["name"] or f"Speicherplatz {i + 1}"); a.setEnabled(bool(slot.get("data")))
                slot_acts[a] = slot
        order = menu.addMenu("Visuelle Reihenfolge")
        act_front = order.addAction("Nach vorne bringen"); act_back = order.addAction("Nach hinten schicken")
        act_tree = menu.addAction("Objektbaum")
        menu.addSeparator()
        act_clone = menu.addAction("Klonen\tStrg+Ziehen")
        act_copy = menu.addAction("Kopieren\tStrg+C")
        act_paste = menu.addAction("Einfügen\tStrg+V") if self.clipboard else None
        menu.addSeparator()
        act_lock = menu.addAction("Lösen" if o.get("locked") else "Fixieren")
        act_hide_obj = menu.addAction("Verbergen")
        act_del = menu.addAction("Entfernen\tEntf")
        menu.addSeparator()
        act_prices = None if d else menu.addAction("Preise eingeben …")
        act_settings = menu.addAction("Einstellungen …")
        menu.addSeparator()
        act_hide = menu.addAction("Alles verstecken")
        act_show_dash = menu.addAction("Dashboard anzeigen")

        action = menu.exec_(gpos)
        if action is None: return
        if action == act_hide: self.set_hidden(True)
        elif action == act_show_dash and self.main_panel: self.main_panel.bring_to_front()
        elif action == act_del:
            if self._confirm(f"Möchtest du „{name}“ wirklich entfernen?", gpos): self.delete_item(kind, idx)
        elif action == act_clone: self.duplicate(kind, idx)
        elif action == act_copy: self.copy_selected()
        elif action == act_paste: self.paste(pos)
        elif action == act_front: self.reorder(kind, idx, True)
        elif action == act_back: self.reorder(kind, idx, False)
        elif action == act_tree: self.open_object_list(gpos)
        elif action == act_lock: o["locked"] = not o.get("locked"); self.objects_changed()
        elif action == act_hide_obj: o["hidden"] = True; self.objects_changed()
        elif action == act_alarm:
            if d:
                d["alarm"] = not d.get("alarm"); d.pop("alarm_state", None); self.update()
                if d["alarm"]: self._alarm(f"Alarm für {name} ist an (Test-Funktion: erkennt die letzte Kerze am Bildschirm)", beep=False)
            elif self.main_panel: self.main_panel.open_settings(section="alarm")
        elif action in slot_acts and self.main_panel: self.main_panel.apply_all(slot_acts[action]["data"])
        elif action == act_prices: self._prompt_prices(o)
        elif action == act_settings:
            if d: self.open_properties(idx, gpos)
            elif self.main_panel: self.main_panel.open_settings(fib=True)

    def _confirm(self, text, gpos):
        msg = QMessageBox(QMessageBox.Question, "Entfernen bestätigen", text, QMessageBox.Yes | QMessageBox.No, self)
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
            dlg.setWindowTitle(f"{self.name_of(f)} – Preis {len(prices) + 1} von 2")
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
        if not f or not f.get("price_ref"): return None
        (fa, pa), (fb, pb) = f["price_ref"]
        return pa + (frac - fa) * (pb - pa) / (fb - fa)

    # ----- Zeichnen -----
    def paintEvent(self, e):
        if self.is_hidden: return
        p = QPainter(self)
        self._placeholder = None
        if self.mode == "placing":
            # Fast unsichtbare Fläche (Alpha 1): Ohne sie gehen Klicks auf leere Stellen
            # bei transparenten Fenstern unter Windows einfach zum Chart darunter durch
            p.fillRect(self.rect(), QColor(0, 0, 0, 1))
            if self.tool == "fib": hint = "FIB-Modus: 1. Klick = 0% (High)   2. Klick = 100% (Low)"
            elif self.tool in ("hline", "hray"): hint = f"{TOOL_NAMES[self.tool]}: Klick = Position"
            else: hint = f"{TOOL_NAMES.get(self.tool, '')}: 1. Klick = Start   2. Klick = Ende"
            self._banner(p, hint + "   Esc / Rechtsklick = Abbrechen", QColor(255, 255, 255, 240), None)
        for f in self.fibs:
            if f.get("hidden"): continue
            # Fib zuerst, Zeichnungen darüber. Beim Setzen gibt es schon eine Vorschau bis zur Maus.
            end = f["p2"] or (self.hover if f is self.placing_fib else None)
            if end: self._levels(p, f, end)
            self._anchor(p, f["p1"], f)
            if f["p2"]: self._anchor(p, f["p2"], f)
        self._draw_drawings(p)
        if self.mode == "placing" and self.snap_pt is not None:
            # Magnet-Vorschau: kleiner Ring mit Kreuz, wo der Klick einrasten würde
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setPen(QPen(QColor("#2962ff"), 2)); p.setBrush(QColor(41, 98, 255, 60))
            p.drawEllipse(QPointF(self.snap_pt), 7, 7)
            p.drawLine(self.snap_pt + QPoint(-11, 0), self.snap_pt + QPoint(11, 0))
            p.drawLine(self.snap_pt + QPoint(0, -11), self.snap_pt + QPoint(0, 11))
            p.setRenderHint(QPainter.Antialiasing, False); p.setBrush(Qt.NoBrush)
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

    def _text_font(self, d):
        f = QFont(); f.setPixelSize(int(d.get("text_size", 12) * 1.25))
        f.setBold(d.get("text_bold", False)); f.setItalic(d.get("text_italic", False))
        return f

    def _draw_line_with_text(self, p, d, a, b, reserve=0):
        """Linie zeichnen, Text wie bei TradingView: Oben/Mitte/Unten und Links/Zentrieren/Rechts. Bei "Mitte"
        wird die Linie für den Text unterbrochen; schräge Linien bekommen den Text schräg mitgedreht."""
        txt = " ".join(d.get("text", "").split())
        length = math.hypot(b.x() - a.x(), b.y() - a.y())
        if not txt or length < 1:
            p.drawLine(a, b); return
        p.setFont(self._text_font(d)); fm = p.fontMetrics()
        w, h = fm.horizontalAdvance(txt) + 8, fm.height()
        ux, uy = (b.x() - a.x()) / length, (b.y() - a.y()) / length
        # reserve = Platz für das Preisschild am rechten Ende, damit rechts ausgerichteter Text nicht darunter liegt
        s = {"left": 8 + w / 2, "center": length / 2, "right": length - 8 - reserve - w / 2}[d.get("text_h", "right")]
        s = max(w / 2, min(length - w / 2, s))
        v = d.get("text_v", "middle")
        if v == "middle":
            gap0, gap1 = s - w / 2 - 2, s + w / 2 + 2
            if gap0 > 0: p.drawLine(a, QPointF(a.x() + ux * gap0, a.y() + uy * gap0))
            if gap1 < length: p.drawLine(QPointF(a.x() + ux * gap1, a.y() + uy * gap1), b)
        else: p.drawLine(a, b)
        off = {"top": -(h / 2 + 3), "middle": 0, "bottom": h / 2 + 3}[v]
        cx, cy = a.x() + ux * s - uy * off, a.y() + uy * s + ux * off
        angle = math.degrees(math.atan2(uy, ux))
        if angle > 90 or angle < -90: angle += 180  # Text nie auf dem Kopf
        p.save()
        p.translate(cx, cy); p.rotate(angle)
        col = d.get("text_color", QColor("#ffffff"))
        if abs(angle) < 0.5:
            p.setPen(col); p.drawText(QRectF(-w / 2, -h / 2, w, h), Qt.AlignCenter, txt)
        else:
            # schräger Text als Pfad - sonst stehen die Buchstaben gedreht unsauber und ungleichmäßig
            path = QPainterPath(); path.addText(-fm.horizontalAdvance(txt) / 2, fm.ascent() - h / 2, p.font(), txt)
            p.setPen(Qt.NoPen); p.fillPath(path, col)
        p.restore()

    def _rect_text_box(self, p, d, r):
        # Textbereich im Rechteck nach Ausrichtung (oder None, wenn kein Text)
        txt = d.get("text", "")
        if not txt: return None
        p.setFont(self._text_font(d)); fm = p.fontMetrics()
        lines = txt.split("\n")
        w, h = max(fm.horizontalAdvance(l) for l in lines) + 10, fm.height() * len(lines)
        x = {"left": r.left() + 6, "center": r.center().x() - w / 2, "right": r.right() - 6 - w}[d.get("text_h", "center")]
        y = {"top": r.top() + 4, "middle": r.center().y() - h / 2, "bottom": r.bottom() - 4 - h}[d.get("text_v", "middle")]
        return QRectF(x, y, w, h)

    def _draw_drawings(self, p):
        editing = self.mode == "edit" and not self.is_locked
        sel = self.selected[1] if self.selected else None
        p.setRenderHint(QPainter.Antialiasing, True)
        for d in self.drawings + ([self.pending] if self.pending else []):
            if d.get("hidden"): continue
            grab = editing and not d.get("locked")
            a, b = self._line_ends(d)
            rect = self._rect_area(d) if d["type"] == "rect" else None
            if grab:
                # unsichtbarer breiter Streifen zum Anfassen - dünne Linien wären sonst kaum zu treffen
                p.setPen(QPen(QColor(0, 0, 0, 1), 12)); p.setBrush(Qt.NoBrush)
                if rect is not None: p.drawRect(rect)
                else: p.drawLine(a, b)
            c = d["color"]
            p.setPen(QPen(c, d["width"], PEN_STYLES.get(d.get("style", "Solid"), Qt.SolidLine)))
            if rect is not None:
                fill = QColor(d["fill_color"]); fill.setAlpha(int(d["fill_opacity"] * 2.55))
                p.setBrush(fill if d["fill"] else Qt.NoBrush); p.drawRect(rect)
                p.setBrush(Qt.NoBrush)
                tbox = self._rect_text_box(p, d, rect)
                if d["midline"]:
                    p.setPen(QPen(d["mid_color"], d["mid_width"], PEN_STYLES.get(d["mid_style"], Qt.DashLine)))
                    my = rect.center().y()
                    if tbox is not None and tbox.top() <= my <= tbox.bottom():
                        # Mittellinie für den Text unterbrechen (wie "ORDERBLOCK" bei TradingView)
                        if tbox.left() - 4 > rect.left(): p.drawLine(QPointF(rect.left(), my), QPointF(tbox.left() - 4, my))
                        if tbox.right() + 4 < rect.right(): p.drawLine(QPointF(tbox.right() + 4, my), QPointF(rect.right(), my))
                    else: p.drawLine(QPointF(rect.left(), my), QPointF(rect.right(), my))
                if tbox is not None:
                    p.setFont(self._text_font(d)); p.setPen(d.get("text_color", QColor("#ffffff")))
                    align = {"left": Qt.AlignLeft, "center": Qt.AlignHCenter, "right": Qt.AlignRight}[d.get("text_h", "center")]
                    p.drawText(tbox, align | Qt.AlignVCenter, d["text"])
                elif grab and d is sel:
                    # wie bei TradingView: leeres, ausgewähltes Rechteck zeigt "+ Text hinzufügen"
                    f = QFont(); f.setPixelSize(13); p.setFont(f)
                    txt = "+ Text hinzufügen"; w = p.fontMetrics().horizontalAdvance(txt) + 12
                    self._placeholder = QRectF(rect.center().x() - w / 2, rect.center().y() - 10, w, 20)
                    p.setPen(QColor(255, 255, 255, 150)); p.drawText(self._placeholder, Qt.AlignCenter, txt)
            else:
                self._draw_line_with_text(p, d, a, b, self._price_tag_w(p, d))
            if d["type"] in ("hline", "hray"): self._hline_label(p, d, b)
            if d.get("alarm"):
                p.setFont(QFont()); p.setPen(QColor("#ffd166"))
                at = (rect.topRight() + QPointF(-46, 14)) if rect is not None else (b + QPointF(-60, -6))
                p.drawText(at, "⏰ Alarm")
            if grab and d is not self.pending:
                for h in self._handles(d).values():
                    p.setPen(QPen(QColor("#2962ff"), 2)); p.setBrush(QColor(19, 23, 34)); p.drawEllipse(QPointF(h), 4.5, 4.5)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setBrush(Qt.NoBrush)

    def _price_tag_w(self, p, d):
        # Breite des Preisschilds am rechten Ende (0 = keins)
        pm = self.price_map()
        if not pm or d["type"] not in ("hline", "hray"): return 0
        fnt = QFont(); fnt.setPixelSize(int(FIB_STYLE["font_size"] * 1.25)); fnt.setBold(True); p.setFont(fnt)
        return p.fontMetrics().horizontalAdvance(fmt_price(pm[0](d["p1"].y()))) + 10

    def _hline_label(self, p, d, right):
        # Preisschild am rechten Ende - wie bei TradingView in der Linienfarbe (nur wenn an einer Fib Preise eingegeben sind)
        pm = self.price_map()
        if not pm: return
        y = d["p1"].y()
        txt = fmt_price(pm[0](y))
        fnt = QFont(); fnt.setPixelSize(int(FIB_STYLE["font_size"] * 1.25)); fnt.setBold(True); p.setFont(fnt)
        fm = p.fontMetrics()
        w, h = fm.horizontalAdvance(txt) + 10, fm.height() + 2
        rect = QRectF(right.x() - w, y - h / 2, w, h)
        c = QColor(d["color"]); p.setPen(Qt.NoPen); p.setBrush(c); p.drawRoundedRect(rect, 2, 2)
        p.setBrush(Qt.NoBrush)
        p.setPen(QColor("#000000") if c.lightness() > 140 else QColor("#ffffff"))
        p.drawText(rect, Qt.AlignCenter, txt)

    def _anchor(self, p, pt, f):
        # Ankerpunkte wie bei TradingView: kleine blaue Kreise, nur solange man bearbeiten kann
        if self.is_locked or f.get("locked") or self.mode not in ("edit", "placing"): return
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
            # Fläche zwischen zwei Leveln gehört zum weiter entfernten Level (wie TradingView) -
            # dort ist sie einzeln ein-/ausschaltbar und hat eine eigene Flächenfarbe
            for lo, hi in zip(levels, levels[1:]):
                if not hi.get("fill", True) or lo.get("edge"): continue
                c = QColor(one or hi.get("fill_color") or hi["color"]); c.setAlpha(int(FIB_STYLE["bg_opacity"] * 2.55))
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
        grab = self.mode == "edit" and not self.is_locked and not f.get("locked")
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


def themed_dialog_css():
    t = THEMES[THEME]
    return (f"QWidget {{ background-color: {t['bg']}; color: {t['text']}; }}" + indicator_css(t) + field_css(t)
            + f"QPushButton {{ background-color: {t['btn']}; color: {t['text']}; border: 1px solid {t['btn_border']};"
              f" border-radius: 4px; padding: 4px 10px; }} QPushButton:hover {{ border: 1px solid {t.get('focus', GOLD)}; }}"
              f" QPushButton:checked {{ background-color: {t['highlight']}; border: 1px solid {t.get('focus', GOLD)}; }}"
              f" QTabWidget::pane {{ border: 1px solid {t['border']}; border-radius: 4px; top: -1px; }}"
              f" QTabBar::tab {{ background: {t['bg']}; color: {t['muted']}; padding: 6px 12px; border: none; }}"
              f" QTabBar::tab:selected {{ color: {t['text']}; border-bottom: 2px solid {t.get('focus', GOLD)}; }}"
              f" QPlainTextEdit {{ background-color: {mix(t['bg'], '#ffffff', 0.07)}; border: 1px solid {t.get('field', '#b8b8b8')};"
              f" border-radius: 3px; }} QPlainTextEdit:focus {{ border: 2px solid {t.get('focus', GOLD)}; }}")


class DrawingDialog(QDialog):
    """Eigenschaften einer Zeichnung (Doppelklick) - wie bei TradingView: Reiter Stil / Text / Koordinaten,
    unten Vorlage / Abbrechen / Ok. Abbrechen macht alle Änderungen rückgängig."""
    LINE_STYLES = (("Durchgezogen", "Solid"), ("Gestrichelt", "Dash"), ("Gepunktet", "Dot"))

    def __init__(self, ov, d, tab="style"):
        super().__init__(ov)
        self.ov, self.d = ov, d
        self._orig = copy_obj(d)  # für "Abbrechen"
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setWindowTitle(ov.name_of(d))
        self.setStyleSheet(themed_dialog_css())
        box = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._style_tab(), "Stil")
        self.tabs.addTab(self._text_tab(), "Text")
        self.tabs.addTab(self._coord_tab(), "Koordinaten")
        if tab == "text": self.tabs.setCurrentIndex(1)
        box.addWidget(self.tabs)
        row = QHBoxLayout()
        self.btn_tpl = QPushButton("Vorlage ▾"); self.btn_tpl.clicked.connect(self._template_menu)
        cancel = QPushButton("Abbrechen"); cancel.clicked.connect(self.reject)
        ok = QPushButton("Ok"); ok.clicked.connect(self.accept)
        row.addWidget(self.btn_tpl); row.addStretch(); row.addWidget(cancel); row.addWidget(ok)
        box.addLayout(row)

    # --- Reiter ---
    def _style_tab(self):
        w = QWidget(); g = QGridLayout(w)
        d, row = self.d, 0
        rect = d["type"] == "rect"
        if rect:
            g.addWidget(QLabel("Verlängern"), row, 0)
            g.addWidget(self._combo("extend", (("Nicht erweitern", "none"), ("Nach links", "left"), ("Nach rechts", "right"),
                                               ("Nach beiden Seiten", "both"))), row, 1, 1, 3)
            row += 1
        g.addWidget(QLabel("Rahmen" if rect else "Linie"), row, 0)
        g.addWidget(self._color_btn("color"), row, 1); g.addWidget(self._spin("width", 1, 6), row, 2)
        g.addWidget(self._combo("style", self.LINE_STYLES), row, 3)
        row += 1
        if rect:
            g.addWidget(self._check("midline", "Mittellinie"), row, 0)
            g.addWidget(self._color_btn("mid_color"), row, 1); g.addWidget(self._spin("mid_width", 1, 6), row, 2)
            g.addWidget(self._combo("mid_style", self.LINE_STYLES), row, 3)
            row += 1
            g.addWidget(self._check("fill", "Hintergrund"), row, 0)
            g.addWidget(self._color_btn("fill_color"), row, 1)
            sl = QSlider(Qt.Horizontal); sl.setRange(0, 100); sl.setValue(d["fill_opacity"])
            lbl = QLabel(f"{d['fill_opacity']} %")
            sl.valueChanged.connect(lambda v: (lbl.setText(f"{v} %"), self._set("fill_opacity", v)))
            g.addWidget(sl, row, 2); g.addWidget(lbl, row, 3)
            row += 1
        if d["type"] == "hray":
            g.addWidget(QLabel("Länge"), row, 0)
            cb = QComboBox()
            for text, val in (("Endlos bis zum Rand", "endless"), ("Pixel", "px"), ("Kerzen (am Bildschirm gemessen)", "candles")):
                cb.addItem(text, val)
            cb.setCurrentIndex(max(0, cb.findData(d["len_mode"])))
            self.sp_px, self.sp_candles = self._spin("len_px", 10, 4000), self._spin("len_candles", 1, 500)
            cb.currentIndexChanged.connect(lambda i: self._set_len_mode(cb.itemData(i)))
            g.addWidget(cb, row, 1, 1, 3)
            row += 1
            g.addWidget(QLabel("Pixel / Kerzen"), row, 0); g.addWidget(self.sp_px, row, 2); g.addWidget(self.sp_candles, row, 3)
            self._set_len_mode(d["len_mode"])
            row += 1
        g.setRowStretch(row, 1)
        return w

    def _text_tab(self):
        w = QWidget(); v = QVBoxLayout(w)
        top = QHBoxLayout()
        top.addWidget(self._color_btn("text_color"))
        top.addWidget(self._spin("text_size", 6, 48))
        for key, label in (("text_bold", "B"), ("text_italic", "I")):
            b = QPushButton(label); b.setCheckable(True); b.setChecked(self.d.get(key, False)); b.setFixedWidth(34)
            f = b.font(); f.setBold(key == "text_bold"); f.setItalic(key == "text_italic"); b.setFont(f)
            b.toggled.connect(lambda on, k=key: self._set(k, on))
            top.addWidget(b)
        top.addStretch()
        v.addLayout(top)
        self.ed_text = QPlainTextEdit(self.d.get("text", "")); self.ed_text.setPlaceholderText("Text hinzufügen")
        self.ed_text.setMinimumHeight(70)
        self.ed_text.textChanged.connect(lambda: self._set("text", self.ed_text.toPlainText()))
        v.addWidget(self.ed_text)
        al = QHBoxLayout(); al.addWidget(QLabel("Textausrichtung"))
        al.addWidget(self._combo("text_v", (("Oben", "top"), ("Mitte", "middle"), ("Unten", "bottom"))))
        al.addWidget(self._combo("text_h", (("Links", "left"), ("Zentrieren", "center"), ("Rechts", "right"))))
        v.addLayout(al)
        return w

    def _coord_tab(self):
        """Koordinaten als Preise - geht, sobald an einer Fib zwei Preise eingegeben sind (Bars kennt das Overlay nicht)."""
        w = QWidget(); g = QGridLayout(w)
        pm = self.ov.price_map()
        points = ["p1"] if self.d["type"] in ("hline", "hray") else ["p1", "p2"]
        if not pm:
            lbl = QLabel("Preise kennt das Overlay erst, wenn du an einer Fib zwei Preise eingegeben hast\n"
                         "(Rechtsklick auf die Fib → Preise eingeben …).")
            lbl.setObjectName("muted"); lbl.setWordWrap(True)
            g.addWidget(lbl, 0, 0, 1, 2)
            return w
        to_price, to_y = pm
        for r, key in enumerate(points):
            g.addWidget(QLabel(f"#{r + 1} (Preis)"), r, 0)
            sp = QDoubleSpinBox(); sp.setRange(-1e12, 1e12); sp.setDecimals(PRICE_DECIMALS); sp.setMinimumWidth(130)
            sp.setValue(to_price(self.d[key].y()))
            def changed(val, k=key):
                y = int(round(to_y(val)))
                self.d[k] = QPoint(self.d[k].x(), y)
                if self.d["type"] in ("hline", "hray"): self.d["p2"] = QPoint(self.d["p1"])
                self.ov.update()
            sp.valueChanged.connect(changed)
            g.addWidget(sp, r, 1)
        g.setRowStretch(len(points), 1)
        return w

    # --- Bausteine ---
    def _color_btn(self, key):
        b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(self.d[key]))
        b.clicked.connect(lambda checked, k=key, btn=b: self._pick(k, btn))
        return b

    def _spin(self, key, lo, hi):
        sp = QSpinBox(); sp.setRange(lo, hi); sp.setValue(self.d[key]); sp.setMinimumWidth(72)
        sp.valueChanged.connect(lambda v, k=key: self._set(k, v))
        return sp

    def _combo(self, key, items):
        cb = QComboBox()
        for text, val in items: cb.addItem(text, val)
        cb.setCurrentIndex(max(0, cb.findData(self.d.get(key))))
        cb.currentIndexChanged.connect(lambda i, k=key, c=cb: self._set(k, c.itemData(i)))
        return cb

    def _check(self, key, text):
        c = QCheckBox(text); c.setChecked(self.d[key]); c.toggled.connect(lambda v, k=key: self._set(k, v))
        return c

    def _set_len_mode(self, mode):
        self.d["len_mode"] = mode
        self.sp_px.setEnabled(mode == "px"); self.sp_candles.setEnabled(mode == "candles")
        if mode == "candles": self.ov._estimate_candle_px(self.d["p1"])
        self.ov.update()

    def _set(self, key, val):
        self.d[key] = val
        self.ov.update()

    def _pick(self, key, btn):
        c = QColorDialog.getColor(self.d[key], self, "Farbe wählen")
        if c.isValid():
            self.d[key] = c; btn.setStyleSheet(color_btn_css(c)); self.ov.update()

    def _template_menu(self):
        m = QMenu(self)
        fill_template_menu(m, self.ov, self.d, self, after_apply=self._reopen)
        m.exec_(self.btn_tpl.mapToGlobal(QPoint(0, self.btn_tpl.height())))

    def _reopen(self):
        # nach "Vorlage anwenden": Fenster mit den neuen Werten neu öffnen (die Änderung bleibt, auch bei Abbrechen danach)
        idx = self.ov._index_of("draw", self.d)
        if idx is None: return
        pos, tab = self.pos(), self.tabs.currentIndex()
        self.accept()
        self.ov.open_properties(idx, pos - QPoint(16, 16), tab="text" if tab == 1 else "style")

    def reject(self):
        # Abbrechen / X: alles wie vorher
        self.d.clear(); self.d.update(copy_obj(self._orig))
        self.ov.update()
        super().reject()


class ObjectListDialog(QDialog):
    """Objektbaum wie bei TradingView: alle Fibs und Zeichnungen - zeigen, fixieren, bearbeiten, entfernen."""
    def __init__(self, ov):
        super().__init__(ov)
        self.ov = ov
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setWindowTitle("Objektbaum")
        self.setStyleSheet(themed_dialog_css())
        box = QVBoxLayout(self)
        host = QWidget(); self.grid = QGridLayout(host); self.grid.setContentsMargins(0, 0, 0, 0)
        box.addWidget(host)
        row = QHBoxLayout()
        for text, key, val in (("Alle zeigen", "hidden", False), ("Alle lösen", "locked", False)):
            b = QPushButton(text); b.clicked.connect(lambda checked, k=key, v=val: self._all(k, v)); row.addWidget(b)
        box.addLayout(row)

    def refresh(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        objs = self.ov.all_objects()
        if not objs: self.grid.addWidget(QLabel("Noch keine Objekte gezeichnet."), 0, 0)
        for r, (kind, idx, o) in enumerate(objs):
            label = self.ov.name_of(o) + (f" – „{o['text'][:18]}“" if o.get("text") else "")
            self.grid.addWidget(QLabel(label), r, 0)
            vis = QCheckBox("sichtbar"); vis.setChecked(not o.get("hidden"))
            vis.toggled.connect(lambda v, o=o: self._set(o, "hidden", not v))
            lock = QCheckBox("fixiert"); lock.setChecked(bool(o.get("locked")))
            lock.toggled.connect(lambda v, o=o: self._set(o, "locked", v))
            props = QPushButton("Einstellungen"); props.clicked.connect(lambda checked, k=kind, o=o: self._props(k, o))
            rm = QPushButton("Entfernen"); rm.clicked.connect(lambda checked, k=kind, o=o: self._delete(k, o))
            for c, w in enumerate((vis, lock, props, rm), start=1): self.grid.addWidget(w, r, c)
        self.adjustSize()

    def _set(self, o, key, val):
        o[key] = val
        self.ov.update()

    def _all(self, key, val):
        for _, _, o in self.ov.all_objects(): o[key] = val
        self.ov.update(); self.refresh()

    def _props(self, kind, o):
        if kind == "fib":
            if self.ov.main_panel: self.ov.main_panel.open_settings(fib=True)
        else:
            idx = self.ov._index_of(kind, o)
            if idx is not None: self.ov.open_properties(idx, QCursor.pos())

    def _delete(self, kind, o):
        idx = self.ov._index_of(kind, o)
        if idx is None: return
        if QMessageBox.question(self, "Entfernen bestätigen", f"Möchtest du „{self.ov.name_of(o)}“ wirklich entfernen?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.ov.delete_item(kind, idx)


class SettingsPanel(QDialog):
    LINE_STYLES = [("Durchgezogen", "Solid"), ("Gestrichelt", "Dash"), ("Gepunktet", "Dot")]

    def __init__(self, overlay, main_panel):
        super().__init__()
        self.ov = overlay
        self.main_panel = main_panel
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowTitle(f"Einstellungen – Version {APP_VERSION}")
        self.t = t = THEMES[THEME]
        self.restyle()

        self.setMinimumSize(700, 600)
        self.resize(700, 800)

        main_layout = QVBoxLayout()
        self.scroll = scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)


        # ===== PRESETS + SPEICHERPLÄTZE =====
        grp_presets = QGroupBox("Presets && Speicherplätze")
        pr_layout = QVBoxLayout()
        lbl_presets = QLabel("Alle Einstellungen werden automatisch gespeichert und beim nächsten Start geladen. "
                             "Zusätzlich hast du 5 Speicherplätze mit eigenem Namen und kannst Set-Dateien sichern.")
        lbl_presets.setWordWrap(True); lbl_presets.setObjectName("muted")
        pr_layout.addWidget(lbl_presets)
        slots_grid = QGridLayout()
        self.slots = load_slots()
        self.slot_names, self.slot_info = [], []
        for i, slot in enumerate(self.slots):
            ed = QLineEdit(slot["name"]); ed.setPlaceholderText(f"Speicherplatz {i + 1}")
            ed.editingFinished.connect(lambda i=i, ed=ed: self._rename_slot(i, ed.text()))
            b_save = QPushButton("Speichern")
            b_save.clicked.connect(lambda checked, i=i: self._save_slot(i))
            b_load = QPushButton("Laden")
            b_load.clicked.connect(lambda checked, i=i: self._load_slot(i))
            info = QLabel(slot.get("saved") or "leer"); info.setObjectName("muted")
            slots_grid.addWidget(QLabel(f"{i + 1}."), i, 0); slots_grid.addWidget(ed, i, 1)
            slots_grid.addWidget(b_save, i, 2); slots_grid.addWidget(b_load, i, 3); slots_grid.addWidget(info, i, 4)
            self.slot_names.append(ed); self.slot_info.append(info)
        slots_grid.setColumnStretch(1, 1)
        pr_layout.addLayout(slots_grid)
        pr_btns = QHBoxLayout()
        for text, slot in (("Set-Datei speichern …", self.save_preset), ("Set-Datei laden …", self.load_preset)):
            b = QPushButton(text); b.clicked.connect(slot)
            pr_btns.addWidget(b)
        b_reset = QPushButton("Auf Standardwerte zurücksetzen")
        b_reset.setStyleSheet("QPushButton { background-color: #7a1f2b; color: #ffffff; border: 1px solid #ff7c8a; border-radius: 4px; "
                              "padding: 5px 10px; font-weight: bold; } QPushButton:hover { background-color: #9a2836; }")
        b_reset.clicked.connect(self.reset_defaults)
        pr_btns.addWidget(b_reset)
        pr_layout.addLayout(pr_btns)
        grp_presets.setLayout(pr_layout)
        layout.addWidget(grp_presets)

        # ===== FIB-DARSTELLUNG - 1:1 wie der Fib-Retracement-Dialog bei TradingView =====
        self.grp_fib = grp_fib = QGroupBox("Fib-Darstellung (wie TradingView)")
        fg = QGridLayout()
        r = 0
        # entweder Setups oder Level-Liste - beides zusammen stünde doppelt auf einer Linie (z. B. 0,5 · E1)
        fg.addWidget(QLabel("<b>Die Fib zeigt</b>"), r, 0)
        src_row = QHBoxLayout()
        self.src_btns = {}
        for key, text in (("setups", "Setups 1–4"), ("levels", "TradingView-Liste")):
            b = QPushButton(text); b.setCheckable(True); b.setMinimumWidth(160)
            b.clicked.connect(lambda checked, k=key: self.main_panel.set_fib_source(k))
            src_row.addWidget(b); self.src_btns[key] = b
        fg.addLayout(src_row, r, 1, 1, 3)
        r += 1
        self.lbl_src_fib = QLabel(); self.lbl_src_fib.setWordWrap(True); self.lbl_src_fib.setObjectName("hint")
        fg.addWidget(self.lbl_src_fib, r, 0, 1, 4)
        r += 1
        self.cb_frame01 = self._fib_check("0 und 1 als Rahmen dazu (nur bei Setups)", "frame_01")
        fg.addWidget(self.cb_frame01, r, 0, 1, 4)
        r += 1
        fg.addWidget(self._fib_check("Trendlinie (Diagonale)", "trend"), r, 0)
        fg.addWidget(self._fib_color("trend_color"), r, 1); fg.addWidget(self._fib_spin("trend_width", 1, 6), r, 2)
        fg.addWidget(self._fib_combo("trend_style", self.LINE_STYLES), r, 3)
        r += 1
        fg.addWidget(QLabel("Levels-Linie"), r, 0)
        fg.addWidget(self._fib_spin("level_width", 1, 6), r, 2); fg.addWidget(self._fib_combo("level_style", self.LINE_STYLES), r, 3)
        r += 1
        fg.addWidget(QLabel("Verlängern"), r, 0)
        fg.addWidget(self._fib_combo("extend", [("Nicht erweitern", "none"), ("Linien nach links", "left"),
                                                ("Linien nach rechts", "right"), ("Nach beiden Seiten", "both")]), r, 1, 1, 3)
        r += 1
        # Level-Liste: 24 Plätze in 2 Spalten - je Haken, Wert, Farbe
        # Level-Liste: 24 Plätze in 2 Spalten - je Haken, Wert, Linienfarbe und eigene Fläche (an/aus + Farbe)
        lv_grid = QGridLayout(); lv_grid.setHorizontalSpacing(6)
        for half in (0, 1):
            for c, head in enumerate(("", "Wert", "Linie", "Fläche", "")):
                if head:
                    lb = QLabel(head); lb.setObjectName("muted"); lv_grid.addWidget(lb, 0, half * 6 + c)
        for i, lv in enumerate(FIB_LEVELS):
            row, col = i // 2 + 1, (i % 2) * 6
            cb = QCheckBox(); cb.setChecked(lv["on"]); cb.toggled.connect(lambda v, lv=lv: self._set_level(lv, "on", v))
            sp = QDoubleSpinBox(); sp.setRange(-10, 10); sp.setDecimals(3); sp.setSingleStep(0.001); sp.setValue(lv["value"])
            sp.valueChanged.connect(lambda v, lv=lv: self._set_level(lv, "value", v))
            b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(lv["color"]))
            b.clicked.connect(lambda checked, lv=lv, btn=b: self._pick_level_color(lv, btn, "color"))
            fc = QCheckBox(); fc.setChecked(lv["fill"]); fc.setToolTip("Fläche zum nächsten Level darüber füllen")
            fc.toggled.connect(lambda v, lv=lv: self._set_level(lv, "fill", v))
            fb = QPushButton(); fb.setFixedSize(24, 24); fb.setStyleSheet(color_btn_css(lv["fill_color"])); fb.setToolTip("Flächenfarbe")
            fb.clicked.connect(lambda checked, lv=lv, btn=fb: self._pick_level_color(lv, btn, "fill_color"))
            for c, w in enumerate((cb, sp, b, fc, fb)): lv_grid.addWidget(w, row, col + c)
        lv_grid.setColumnMinimumWidth(5, 18)
        fg.addLayout(lv_grid, r, 0, 1, 4)
        r += 1
        fg.addWidget(self._fib_check("Eine Farbe verwenden", "one_color"), r, 0); fg.addWidget(self._fib_color("one_color_value"), r, 1)
        r += 1
        fg.addWidget(self._fib_check("Hintergrund", "background"), r, 0)
        self.sl_bg = QSlider(Qt.Horizontal); self.sl_bg.setRange(0, 100); self.sl_bg.setValue(FIB_STYLE["bg_opacity"])
        self.lbl_bg = QLabel(f"{FIB_STYLE['bg_opacity']} %")
        self.sl_bg.valueChanged.connect(lambda v: (self.lbl_bg.setText(f"{v} %"), self.set_fib("bg_opacity", v)))
        fg.addWidget(self.sl_bg, r, 1, 1, 2); fg.addWidget(self.lbl_bg, r, 3)
        r += 1
        fg.addWidget(self._fib_check("Umkehren", "reverse"), r, 0)
        r += 1
        fg.addWidget(self._fib_check("Preise", "prices"), r, 0); fg.addWidget(self._fib_check("Namen (E1, SL1 …)", "names"), r, 1, 1, 3)
        r += 1
        fg.addWidget(QLabel("Level"), r, 0)
        fg.addWidget(self._fib_combo("level_fmt", [("Werte", "value"), ("Prozent", "percent")]), r, 1, 1, 2)
        r += 1
        fg.addWidget(QLabel("Beschriftungen"), r, 0)
        fg.addWidget(self._fib_combo("label_h", [("Links", "left"), ("Zentriert", "center"), ("Rechts", "right")]), r, 1, 1, 2)
        fg.addWidget(self._fib_combo("label_v", [("Oben", "top"), ("Mitte", "middle"), ("Unten", "bottom")]), r, 3)
        r += 1
        fg.addWidget(QLabel("Schriftgröße"), r, 0); fg.addWidget(self._fib_spin("font_size", 6, 24), r, 1)
        r += 1
        fg.addWidget(self._fib_check("Dunkler Kasten hinter der Schrift", "label_box"), r, 0, 1, 2)
        r += 1
        fg.addWidget(QLabel("Zahlenformat"), r, 0)
        fg.addWidget(self._fib_combo("num_fmt", [("Deutsch: 0,5 (81.751,0)", "de"), ("Englisch: 0.5 (81751.0)", "en")]), r, 1, 1, 3)
        r += 1
        btn_tv = QPushButton("Wie mein TradingView-Fib einstellen (Farben + Linien)")
        btn_tv.clicked.connect(self.apply_tv_look)
        fg.addWidget(btn_tv, r, 0, 1, 4)
        fg.setColumnStretch(4, 1)
        grp_fib.setLayout(fg)
        layout.addWidget(grp_fib)

        # ===== VERLÄNGERUNG EINES LEVELS + ALARM =====
        self.grp_ext = grp_ext = QGroupBox("Level-Verlängerung nach rechts + Alarm (Test)")
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
        lbl_ext.setWordWrap(True); lbl_ext.setObjectName("muted")
        eg.addWidget(lbl_ext, 7, 0, 1, 4)
        cb_auto = QCheckBox("Automatik-Modus (Test): Setups automatisch weiterschalten"); cb_auto.setChecked(AUTO_MODE)
        cb_auto.toggled.connect(self.set_auto)
        eg.addWidget(cb_auto, 8, 0, 1, 4)
        lbl_auto = QLabel("Läuft der Kurs durch den SL des aktiven Setups, wird das nächste Setup gezeigt (1 → 2 → 3 → 4, nur vorwärts). "
                          "Eine neue Fib fängt wieder bei Setup 1 an. Nutzt dieselbe Kerzen-Erkennung wie der Alarm. "
                          "Zu sehen ist das nur, wenn die Fib die Setups zeigt.")
        lbl_auto.setWordWrap(True); lbl_auto.setObjectName("muted")
        eg.addWidget(lbl_auto, 9, 0, 1, 4)
        eg.setColumnStretch(4, 1)
        grp_ext.setLayout(eg)
        layout.addWidget(grp_ext)

        grp_rules = QGroupBox("Regeln des SK-Systems")
        rl_layout = QVBoxLayout()
        lbl_rules = QLabel(
            "• Entry: Einstieg bei 0.5 (oder tiefer)\n"
            "• SL: Nächstes Fib-Level\n"
            "• BE: Bei 2-fachem Risiko (2R)\n"
            "• TP1-3: Teilschließungen bei X-fachem Risiko"
        )
        lbl_rules.setObjectName("muted")
        rl_layout.addWidget(lbl_rules)
        grp_rules.setLayout(rl_layout)
        layout.addWidget(grp_rules)

        # ===== HANDELS-SETUPS =====
        grp_trade = QGroupBox("Handels-Setups")
        trade_layout = QVBoxLayout()
        trade_layout.setSpacing(10)

        # Hinweis, solange die Fib die Level-Liste zeigt - dann wirken die Setup-Häkchen nicht
        self.src_setups_box = QWidget()
        sb_lay = QHBoxLayout(self.src_setups_box); sb_lay.setContentsMargins(0, 0, 0, 0)
        lbl_src = QLabel("⚠ Die Fib zeigt gerade die Level-Liste wie TradingView – die Setups werden nicht gezeichnet. "
                         "Deine Häkchen hier kannst du trotzdem schon setzen.")
        lbl_src.setWordWrap(True); lbl_src.setObjectName("hint")
        btn_src = QPushButton("Auf Setups umschalten"); btn_src.clicked.connect(lambda: self.main_panel.set_fib_source("setups"))
        sb_lay.addWidget(lbl_src, 1); sb_lay.addWidget(btn_src)
        trade_layout.addWidget(self.src_setups_box)

        grp_global = QGroupBox("Globale R-Werte")
        g_layout = QVBoxLayout()
        self.cb_global = QCheckBox("Globale R-Werte verwenden (für alle Setups)")
        self.cb_global.setChecked(USE_GLOBAL_R)
        self.cb_global.stateChanged.connect(self.toggle_global_r)
        g_layout.addWidget(self.cb_global)
        r_layout = QHBoxLayout()
        r_vals = [fmt_num(x) for x in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 10, 15, 20]]
        self.cb_gtp = []
        for n, val in ((1, GLOBAL_TP1_R), (2, GLOBAL_TP2_R), (3, GLOBAL_TP3_R)):
            r_layout.addWidget(QLabel(f"TP{n}:"))
            cb = QComboBox(); cb.setEditable(True); cb.addItems(r_vals); cb.setCurrentText(fmt_num(val))
            r_layout.addWidget(cb); self.cb_gtp.append(cb)
        g_layout.addLayout(r_layout)
        self.lbl_global_hint = QLabel("⚠ Globale R-Werte sind aktiv – sie gelten für alle Setups. Die R-Spalte unten zeigt sie "
                                      "ausgegraut an. Die eigenen R-Werte der Setups gelten erst wieder, wenn du „Global“ ausschaltest.")
        self.lbl_global_hint.setWordWrap(True)
        self.lbl_global_hint.setObjectName("hint")
        g_layout.addWidget(self.lbl_global_hint)
        grp_global.setLayout(g_layout)
        trade_layout.addWidget(grp_global)

        self.spin_e = []; self.spin_sl = []; self.spin_be = []
        self.spin_tp1 = []; self.spin_tp2 = []; self.spin_tp3 = []
        self.cb_stp = [[], [], []]  # R-Auswahl TP1/TP2/TP3 je Setup
        self.color_btns = {"e":[], "sl":[], "be":[], "tp1":[], "tp2":[], "tp3":[]}
        # Häkchen wie im Dashboard: ganzes Setup und einzelne Linien an/aus
        self.cb_active = []; self.cb_line = {k: [] for k in LINE_KEYS}

        for i, s in enumerate(SETUPS):
            grp = QGroupBox(f"Setup {s['n']}")
            grid = QGridLayout()
            cb_on = QCheckBox(f"Setup {s['n']} anzeigen  (Hauptschalter – die Linien-Häkchen darunter bleiben, wie du sie setzt)")
            cb_on.setChecked(s["active"])
            cb_on.toggled.connect(lambda on, idx=i: self.set_setup_show(idx, "active", on))
            self.cb_active.append(cb_on)
            grid.addWidget(cb_on, 0, 0, 1, 6)
            for c, head in enumerate(("Linie", "Wert", "R", "Farbe", "Dicke", "Stil", "Fläche")): grid.addWidget(QLabel(f"<b>{head}</b>"), 1, c)

            def add_row(row, label, spin_widget, r_combo, key):
                row += 1  # Zeile 0 = Setup an/aus, Zeile 1 = Überschriften
                cb_ln = QCheckBox(label); cb_ln.setChecked(s[f"show_{key}"])
                cb_ln.setToolTip(f"Linie {label} anzeigen")
                cb_ln.toggled.connect(lambda on, idx=i, k=key: self.set_setup_show(idx, k, on))
                self.cb_line[key].append(cb_ln)
                grid.addWidget(cb_ln, row, 0)
                grid.addWidget(spin_widget, row, 1)
                grid.addWidget(r_combo if r_combo else QLabel("-"), row, 2)
                btn_col = QPushButton(); btn_col.setFixedSize(24, 24)
                btn_col.setStyleSheet(color_btn_css(s[f'color_{key}']))
                btn_col.clicked.connect(lambda checked, idx=i, k=key: self.pick_color(idx, k))
                self.color_btns[key].append(btn_col)
                grid.addWidget(btn_col, row, 3)
                sp_thick = QSpinBox(); sp_thick.setRange(1, 10); sp_thick.setValue(s[f'thick_{key}'])
                sp_thick.valueChanged.connect(lambda val, idx=i, k=key: self.update_thick(idx, k, val))
                grid.addWidget(sp_thick, row, 4)
                cb_style = QComboBox()
                for text, val in self.LINE_STYLES: cb_style.addItem(text, val)
                cb_style.setCurrentIndex(max(0, cb_style.findData(s[f'style_{key}'])))
                cb_style.currentIndexChanged.connect(lambda ix, idx=i, k=key, c=cb_style: self.update_style(idx, k, c.itemData(ix)))
                grid.addWidget(cb_style, row, 5)
                cb_fill = QCheckBox(); cb_fill.setChecked(s[f"fill_{key}"])
                cb_fill.setToolTip(f"Fläche zum nächsten Level darüber füllen (in der Farbe von {label})")
                cb_fill.toggled.connect(lambda on, idx=i, k=key: self.set_setup_fill(idx, k, on))
                grid.addWidget(cb_fill, row, 6, Qt.AlignCenter)

            def value_spin(val, editable, key=None):
                sp = QDoubleSpinBox(); sp.setRange(-10000, 10000); sp.setDecimals(3); sp.setSingleStep(0.001); sp.setValue(val)
                if editable: sp.valueChanged.connect(lambda v, idx=i, k=key: self.update_val(idx, k, v))
                else:
                    sp.setReadOnly(True); sp.setButtonSymbols(QDoubleSpinBox.NoButtons)
                    sp.setObjectName("readonly")
                return sp

            sp_e = value_spin(s["entry"], True, "entry"); self.spin_e.append(sp_e); add_row(1, "Entry", sp_e, None, "e")
            sp_sl = value_spin(s["sl"], True, "sl"); self.spin_sl.append(sp_sl); add_row(2, "SL", sp_sl, None, "sl")
            sp_be = value_spin(s["be"], False); self.spin_be.append(sp_be); add_row(3, "BE", sp_be, None, "be")
            for n, (lst, key) in enumerate(((self.spin_tp1, "tp1"), (self.spin_tp2, "tp2"), (self.spin_tp3, "tp3"))):
                sp = value_spin(s[key], False); lst.append(sp)
                cb = QComboBox(); cb.setEditable(True); cb.addItems(r_vals); cb.setCurrentText(fmt_num(s[f"r_{key}"]))
                cb.currentTextChanged.connect(lambda v, idx=i, k=f"r_{key}": self.update_r_setup(idx, k, v))
                self.cb_stp[n].append(cb)
                add_row(4 + n, key.upper(), sp, cb, key)
            grp.setLayout(grid)
            trade_layout.addWidget(grp)

        grp_trade.setLayout(trade_layout)
        layout.addWidget(grp_trade)

        # ===== DARSTELLUNG & VERHALTEN =====
        grp_layout = QGroupBox("Darstellung && Verhalten")  # && = ein "&" (einzelnes & wird sonst zu "_")
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
        cb_num = QCheckBox("Objekt-Nummern behalten (Rechteck 3 bleibt Rechteck 3, auch wenn ein anderes gelöscht wird)")
        cb_num.setChecked(NUM_KEEP); cb_num.toggled.connect(self.set_num_keep)
        l_layout.addWidget(cb_num)
        len_layout = QHBoxLayout()
        len_layout.addWidget(QLabel("Fib-Breite, wenn beide Punkte genau übereinander liegen (px):"))
        self.spin_len = QSpinBox(); self.spin_len.setRange(100, 3000); self.spin_len.setValue(self.ov.line_length)
        self.spin_len.setSingleStep(50); self.spin_len.valueChanged.connect(self.update_length)
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

        # ===== ZEICHENWERKZEUGE - gleiche Reihenfolge wie im Dashboard, je Werkzeug ein Block =====
        grp_tools = QGroupBox("Zeichenwerkzeuge && Magnet")
        t_layout = QVBoxLayout()
        for kind in TOOL_NAMES:
            sub = QGroupBox(TOOL_NAMES[kind])
            sg = QGridLayout()
            sg.addWidget(QLabel("Rahmen" if kind == "rect" else "Linie"), 0, 0)
            sg.addWidget(self._tool_color(kind, "color"), 0, 1); sg.addWidget(self._tool_spin(kind, "width", 1, 6), 0, 2)
            sg.addWidget(self._tool_combo(kind, "style", self.LINE_STYLES), 0, 3)
            if kind == "hray":
                sg.addWidget(QLabel("Länge"), 1, 0)
                sg.addWidget(self._tool_combo(kind, "len_mode", [("Endlos bis zum Rand", "endless"), ("Pixel", "px"),
                                                                 ("Kerzen (am Bildschirm gemessen)", "candles")]), 1, 1, 1, 3)
                sg.addWidget(QLabel("Pixel / Kerzen"), 2, 0)
                sg.addWidget(self._tool_spin(kind, "len_px", 10, 4000), 2, 2); sg.addWidget(self._tool_spin(kind, "len_candles", 1, 500), 2, 3)
            if kind == "rect":
                sg.addWidget(self._tool_check(kind, "fill", "Füllung"), 1, 0); sg.addWidget(self._tool_color(kind, "fill_color"), 1, 1)
                sl_fill = QSlider(Qt.Horizontal); sl_fill.setRange(0, 100); sl_fill.setValue(TOOL_STYLES["rect"]["fill_opacity"])
                lbl_fill = QLabel(f"{TOOL_STYLES['rect']['fill_opacity']} %")
                sl_fill.valueChanged.connect(lambda v, lbl=lbl_fill: (lbl.setText(f"{v} %"), self.set_tool("rect", "fill_opacity", v)))
                sg.addWidget(sl_fill, 1, 2); sg.addWidget(lbl_fill, 1, 3)
                sg.addWidget(self._tool_check(kind, "midline", "Mittellinie"), 2, 0); sg.addWidget(self._tool_color(kind, "mid_color"), 2, 1)
                sg.addWidget(self._tool_spin(kind, "mid_width", 1, 6), 2, 2); sg.addWidget(self._tool_combo(kind, "mid_style", self.LINE_STYLES), 2, 3)
            if kind == "rect":
                sg.addWidget(QLabel("Verlängern"), 3, 0)
                sg.addWidget(self._tool_combo(kind, "extend", [("Nicht erweitern", "none"), ("Nach links", "left"),
                                                               ("Nach rechts", "right"), ("Nach beiden Seiten", "both")]), 3, 1, 1, 3)
            trow = {"rect": 4, "hray": 3}.get(kind, 1)
            sg.addWidget(QLabel("Text"), trow, 0)
            tl = QHBoxLayout()
            tl.addWidget(self._tool_color(kind, "text_color")); tl.addWidget(self._tool_spin(kind, "text_size", 6, 48))
            tl.addWidget(self._tool_check(kind, "text_bold", "Fett")); tl.addWidget(self._tool_check(kind, "text_italic", "Kursiv"))
            tl.addWidget(self._tool_combo(kind, "text_v", [("Oben", "top"), ("Mitte", "middle"), ("Unten", "bottom")]))
            tl.addWidget(self._tool_combo(kind, "text_h", [("Links", "left"), ("Zentrieren", "center"), ("Rechts", "right")]))
            tl.addStretch()
            sg.addLayout(tl, trow, 1, 1, 4)
            sg.setColumnStretch(4, 1)
            sub.setLayout(sg)
            t_layout.addWidget(sub)
        sub_mag = QGroupBox("Magnet")
        mgl = QVBoxLayout()
        self.cb_magnet = QCheckBox("Magnet an (Punkte rasten an Hoch / Tief der Kerze ein)")
        self.cb_magnet.setChecked(MAGNET_ON)
        self.cb_magnet.stateChanged.connect(lambda st: self.main_panel.set_magnet(bool(st)))
        mgl.addWidget(self.cb_magnet)
        cb_mag_draw = QCheckBox("Magnet auch für Zeichnungen (Linien, Rechtecke)"); cb_mag_draw.setChecked(MAGNET_DRAWINGS)
        cb_mag_draw.toggled.connect(self.set_magnet_drawings)
        mgl.addWidget(cb_mag_draw)
        mag_layout = QHBoxLayout()
        mag_layout.addWidget(QLabel("Magnet-Stärke:"))
        self.cb_magnet_mode = QComboBox()
        self.cb_magnet_mode.addItem("Schwach – nur wenn du nah an der Kerze klickst", "weak")
        self.cb_magnet_mode.addItem("Stark – an der Kerze unter dem Mauszeiger (in der Nähe)", "strong")
        self.cb_magnet_mode.setCurrentIndex(self.cb_magnet_mode.findData(MAGNET_MODE))
        self.cb_magnet_mode.currentIndexChanged.connect(self.update_magnet_mode)
        mag_layout.addWidget(self.cb_magnet_mode, 1)
        mgl.addLayout(mag_layout)
        sub_mag.setLayout(mgl)
        t_layout.addWidget(sub_mag)
        lbl_tools = QLabel("Neue Zeichnungen bekommen diese Werte. Einzelne Zeichnungen änderst du per Doppelklick oder Rechtsklick – "
                           "dort kannst du auch eigene Vorlagen speichern.")
        lbl_tools.setWordWrap(True); lbl_tools.setObjectName("muted")
        t_layout.addWidget(lbl_tools)
        grp_tools.setLayout(t_layout)
        layout.addWidget(grp_tools)

        # ===== MATRIX-REGEN =====
        grp_mx = QGroupBox("Matrix-Regen")
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
        lbl_mx.setObjectName("muted")
        mg.addWidget(lbl_mx, 4, 0, 1, 4)
        mg.setColumnStretch(4, 1)
        grp_mx.setLayout(mg)
        layout.addWidget(grp_mx)

        # ===== ABSTÄNDE ANPASSEN =====
        grp_spacing = QGroupBox("Abstände anpassen (Dashboard)")
        sp_layout = QVBoxLayout()
        self.sp_top, self.sp_gap1, self.sp_gap2, self.sp_bot = (QSpinBox() for _ in range(4))
        for text, sp, val in (("1. Abstand Oben (Rand -> Oberer Kasten):", self.sp_top, MARGIN_TOP),
                              ("2. Abstand Oberer Kasten -> Tabelle:", self.sp_gap1, GAP_1),
                              ("3. Abstand Tabelle -> Buttons:", self.sp_gap2, GAP_2),
                              ("4. Abstand Unten (Kasten -> Rand):", self.sp_bot, MARGIN_BOTTOM)):
            h = QHBoxLayout(); h.addWidget(QLabel(text))
            sp.setRange(0, 50); sp.setValue(val); sp.valueChanged.connect(self.update_spacing)
            h.addWidget(sp); sp_layout.addLayout(h)
        grp_spacing.setLayout(sp_layout)
        layout.addWidget(grp_spacing)

        grp_hotkeys = QGroupBox("Hotkeys / Tastaturbelegung")
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
        lbl_hk.setWordWrap(True); lbl_hk.setObjectName("muted")
        hk_outer.addWidget(lbl_hk)
        grp_hotkeys.setLayout(hk_outer)
        layout.addWidget(grp_hotkeys)

        layout.addStretch()
        scroll.setWidget(scroll_content)
        # Version immer sichtbar oben im Fenster
        lbl_ver = QLabel(f"Fib Overlay (SK-System)  ·  Version {APP_VERSION}"); lbl_ver.setObjectName("verHead")
        lbl_ver.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_ver)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        for n, cb in enumerate(self.cb_gtp, start=1):
            cb.currentTextChanged.connect(lambda v, n=n: self.update_r_global(n, v))

        # Zahlenfelder einheitlich breit - nicht winzig (Dicke) und nicht über die ganze Zeile (Abstände)
        for sb in self.findChildren(QAbstractSpinBox):
            sb.setMinimumWidth(max(sb.minimumWidth(), 72)); sb.setMaximumWidth(140)

        self.toggle_global_r(USE_GLOBAL_R)
        self.sync_setup_checks()
        self.sync_source()

    # ----- kleine Bausteine -----
    def _fib_check(self, text, key):
        c = QCheckBox(text); c.setChecked(FIB_STYLE[key])
        c.toggled.connect(lambda v, k=key: self.set_fib(k, v))
        return c

    def _fib_combo(self, key, items):
        cb = QComboBox()
        for text, val in items: cb.addItem(text, val)
        cb.setCurrentIndex(max(0, cb.findData(FIB_STYLE[key])))
        cb.currentIndexChanged.connect(lambda i, k=key, c=cb: self.set_fib(k, c.itemData(i)))
        return cb

    def _fib_color(self, key):
        b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(FIB_STYLE[key]))
        b.clicked.connect(lambda checked, k=key, btn=b: self.pick_fib_color(k, btn))
        return b

    def _fib_spin(self, key, lo, hi):
        sp = QSpinBox(); sp.setRange(lo, hi); sp.setValue(FIB_STYLE[key])
        sp.valueChanged.connect(lambda v, k=key: self.set_fib(k, v))
        return sp

    def _tool_color(self, kind, key):
        b = QPushButton(); b.setFixedSize(24, 24); b.setStyleSheet(color_btn_css(TOOL_STYLES[kind][key]))
        b.clicked.connect(lambda checked, k=kind, kk=key, btn=b: self.pick_tool_key(k, kk, btn))
        return b

    def _tool_spin(self, kind, key, lo, hi):
        sp = QSpinBox(); sp.setRange(lo, hi); sp.setValue(TOOL_STYLES[kind][key])
        sp.valueChanged.connect(lambda v, k=kind, kk=key: self.set_tool(k, kk, v))
        return sp

    def _tool_combo(self, kind, key, items):
        cb = QComboBox()
        for text, val in items: cb.addItem(text, val)
        cb.setCurrentIndex(max(0, cb.findData(TOOL_STYLES[kind][key])))
        cb.currentIndexChanged.connect(lambda i, k=kind, kk=key, c=cb: self.set_tool(k, kk, c.itemData(i)))
        return cb

    def _tool_check(self, kind, key, text):
        c = QCheckBox(text); c.setChecked(TOOL_STYLES[kind][key])
        c.toggled.connect(lambda v, k=kind, kk=key: self.set_tool(k, kk, v))
        return c

    # ----- Speicherplätze / Presets -----
    def _rename_slot(self, i, name):
        self.slots[i]["name"] = name.strip()
        save_slots(self.slots)

    def _save_slot(self, i):
        name = self.slot_names[i].text().strip() or f"Speicherplatz {i + 1}"
        if self.slots[i].get("data") and QMessageBox.question(
                self, "Speicherplatz", f"„{name}“ mit den aktuellen Einstellungen überschreiben?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) != QMessageBox.Yes: return
        self.slots[i] = {"name": name, "saved": datetime.datetime.now().strftime("%d.%m. %H:%M"), "data": settings_to_dict(self.ov)}
        self.slot_names[i].setText(name); self.slot_info[i].setText(self.slots[i]["saved"])
        save_slots(self.slots)

    def _load_slot(self, i):
        data = self.slots[i].get("data")
        if not data:
            QMessageBox.information(self, "Speicherplatz", "Dieser Speicherplatz ist noch leer."); return
        self.main_panel.apply_all(data)

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Set-Datei speichern", os.path.join(PRESET_DIR, "Mein Setup.set"),
                                              "Fib-Preset (*.set)")
        if not path: return
        if not path.lower().endswith(".set"): path += ".set"
        try: write_json(path, settings_to_dict(self.ov))
        except OSError as ex: QMessageBox.warning(self, "Preset", f"Speichern fehlgeschlagen:\n{ex}")

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Set-Datei laden", PRESET_DIR, "Fib-Preset (*.set);;Alle Dateien (*)")
        if not path: return
        try: self.main_panel.apply_all(read_json(path))
        except Exception as ex: QMessageBox.warning(self, "Preset", f"Die Datei konnte nicht geladen werden:\n{ex}")

    def reset_defaults(self):
        reply = QMessageBox.question(self, "Standardwerte",
                                     "Alle Einstellungen auf die Standardwerte zurücksetzen?\n\n"
                                     "Deine Speicherplätze, Set-Dateien und Vorlagen bleiben erhalten.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: self.main_panel.apply_all(DEFAULTS)

    # ----- Einstellungen übernehmen -----
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

    def set_num_keep(self, on):
        global NUM_KEEP
        NUM_KEEP = on
        self.ov.objects_changed(); self.ov.settings_changed()

    def set_magnet_drawings(self, on):
        global MAGNET_DRAWINGS
        MAGNET_DRAWINGS = on
        self.ov.settings_changed()

    def update_spacing(self):
        global MARGIN_TOP, MARGIN_BOTTOM, GAP_1, GAP_2
        MARGIN_TOP, GAP_1, GAP_2, MARGIN_BOTTOM = (sp.value() for sp in (self.sp_top, self.sp_gap1, self.sp_gap2, self.sp_bot))
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

    def _show_r_values(self):
        # bei globalen R-Werten zeigt die (ausgegraute) R-Spalte die globalen Werte, sonst die eigenen des Setups
        glob = (GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R)
        for n in range(3):
            for i, cb in enumerate(self.cb_stp[n]):
                cb.blockSignals(True)
                cb.setCurrentText(fmt_num(glob[n] if USE_GLOBAL_R else SETUPS[i][f"r_tp{n + 1}"]))
                cb.setEnabled(not USE_GLOBAL_R)
                cb.blockSignals(False)
        self.lbl_global_hint.setVisible(USE_GLOBAL_R)

    def toggle_global_r(self, state):
        global USE_GLOBAL_R
        USE_GLOBAL_R = bool(state)
        for cb in self.cb_gtp: cb.setEnabled(USE_GLOBAL_R)
        for i in range(len(SETUPS)):
            recalc_setup(SETUPS[i])
            self.update_spinboxes(i)
        self._show_r_values()
        self.ov.settings_changed()
        self.main_panel.update_table()

    def update_r_global(self, n, val):
        global GLOBAL_TP1_R, GLOBAL_TP2_R, GLOBAL_TP3_R
        try: v = float(str(val).replace(",", "."))
        except ValueError: return
        if n == 1: GLOBAL_TP1_R = v
        elif n == 2: GLOBAL_TP2_R = v
        else: GLOBAL_TP3_R = v
        # Die eigenen R-Werte der Setups bleiben gespeichert - sie gelten wieder, sobald "Global" aus ist
        if USE_GLOBAL_R:
            for i in range(len(SETUPS)):
                recalc_setup(SETUPS[i])
                self.update_spinboxes(i)
            self._show_r_values()
            self.main_panel.update_table()
        self.ov.settings_changed()

    def update_r_setup(self, idx, key, val):
        try: v = float(str(val).replace(",", "."))
        except ValueError: return
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

    def set_setup_show(self, idx, key, on):
        # Setup (Hauptschalter) bzw. einzelne Linie an/aus – genau wie die Häkchen im Dashboard
        set_setup_flag(SETUPS[idx], key, on)
        self.main_panel.update_table()  # zieht auch die Häkchen hier im Fenster nach
        self.ov.settings_changed()

    def sync_setup_checks(self):
        # Häkchen an den aktuellen Stand anpassen (nach Dashboard, Automatik, Preset)
        for i, s in enumerate(SETUPS[:len(self.cb_active)]):
            for cb, val in [(self.cb_active[i], s["active"])] + [(self.cb_line[k][i], s[f"show_{k}"]) for k in LINE_KEYS]:
                if cb.isChecked() != bool(val):
                    cb.blockSignals(True); cb.setChecked(bool(val)); cb.blockSignals(False)
            for k in LINE_KEYS:  # Linien eines ausgeschalteten Setups grau - anklickbar bleiben sie
                cb = self.cb_line[k][i]
                if cb.property("dim") != (not s["active"]):
                    cb.setProperty("dim", not s["active"]); cb.style().unpolish(cb); cb.style().polish(cb)

    def set_setup_fill(self, idx, key, on):
        SETUPS[idx][f"fill_{key}"] = on
        self.ov.settings_changed()

    def sync_source(self):
        # Umschalter Setups / Level-Liste und die Hinweise dazu
        if not hasattr(self, "src_setups_box"): return
        src = FIB_STYLE["source"]
        for k, b in self.src_btns.items(): b.setChecked(k == src)
        self.lbl_src_fib.setText("Gerade: die Linien der Setups 1–4 (unten bei „Handels-Setups“ bzw. in der Tabelle im Dashboard). "
                                 "Die Level-Liste weiter unten ist aus – nur die Farben von 0 und 1 gelten für den Rahmen."
                                 if src == "setups" else
                                 "Gerade: die Level-Liste weiter unten, wie bei TradingView. Die Setups werden nicht gezeichnet.")
        self.cb_frame01.setVisible(src == "setups")
        self.src_setups_box.setVisible(src == "levels")

    def pick_color(self, idx, key):
        color = QColorDialog.getColor(SETUPS[idx][f"color_{key}"], self, "Farbe wählen")
        if color.isValid():
            SETUPS[idx][f"color_{key}"] = color
            self.color_btns[key][idx].setStyleSheet(color_btn_css(color))
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
        self.main_panel.set_theme(name)

    def set_fib(self, key, val):
        FIB_STYLE[key] = val
        self.ov.settings_changed()

    def _set_level(self, lv, key, val):
        lv[key] = val
        self.ov.settings_changed()

    def _pick_level_color(self, lv, btn, key="color"):
        color = QColorDialog.getColor(lv[key], self, "Farbe wählen")
        if color.isValid():
            lv[key] = color; btn.setStyleSheet(color_btn_css(color))
            self.ov.settings_changed()

    def restyle(self):
        # beim Design-Wechsel nur die Farben tauschen - das Fenster bleibt offen und an derselben Stelle
        self.t = THEMES[THEME]
        self.setStyleSheet(settings_css(self.t))
        if hasattr(self, "cb_theme"):
            self.cb_theme.blockSignals(True); self.cb_theme.setCurrentText(THEME); self.cb_theme.blockSignals(False)

    def show_section(self, name):
        grp = {"fib": self.grp_fib, "alarm": self.grp_ext}.get(name)
        if grp: QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(grp.y()))

    def set_auto(self, on):
        global AUTO_MODE
        AUTO_MODE = on
        f = self.ov._auto_fib()
        if on and f: self.ov._auto_set(f, f.get("auto_idx", 0))
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
            "Fib wie dein TradingView-Fib einstellen?\n\n"
            "Die Fib zeigt dann die Level-Liste wie bei TradingView: 0 · 0,5 · 0,559 · 0,618 · 0,677 · 0,736 · 1.\n"
            "Die Setups werden dabei nicht gezeichnet – so steht nichts doppelt auf einer Linie.\n"
            "Zurück zu den Setups: Knopf „Setups“ im Dashboard. Deine Setup-Häkchen bleiben, wie sie sind.\n\n"
            "Tipp: Deine jetzigen Einstellungen kannst du vorher in einem Speicherplatz sichern.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply != QMessageBox.Yes: return
        data = settings_to_dict(self.ov)
        data["fib_style"].update({"trend": True, "trend_color": "#c8ffffff", "trend_style": "Dash", "trend_width": 1,
                                  "level_width": 1, "level_style": "Solid", "extend": "none", "background": True,
                                  "bg_opacity": 25, "reverse": False, "prices": True, "level_fmt": "value",
                                  "label_h": "center", "label_v": "middle", "font_size": 10, "label_box": False,
                                  "one_color": False, "source": "levels"})
        data["fib_levels"] = default_fib_levels_json()
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
        self.setWindowTitle(f"Fib Overlay Steuerung – Version {APP_VERSION}")
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

        # Design-Umschalter: Linksklick = nächstes Design, Rechtsklick = voriges
        self.btn_design = QPushButton(); self.btn_design.setObjectName("gear"); self.btn_design.setIconSize(QSize(16, 16))
        self.btn_design.setFixedSize(24, 24)
        self.btn_design.setToolTip("Design wechseln (Linksklick = nächstes, Rechtsklick = voriges)")
        self.btn_design.clicked.connect(lambda: self.cycle_theme(1))
        self.btn_design.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_design.customContextMenuRequested.connect(lambda _: self.cycle_theme(-1))
        btn_layout.addWidget(self.btn_design)  # direkt links neben dem Zahnrad

        self.btn_settings = btn_settings = QPushButton()
        btn_settings.setObjectName("gear"); btn_settings.setIconSize(QSize(16, 16))
        btn_settings.setToolTip("Einstellungen")
        btn_settings.setFixedSize(24, 24)
        btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(btn_settings)

        self.top_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.top_group)

        self.spacer1 = QSpacerItem(0, GAP_1, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.main_layout.addItem(self.spacer1)

        # --- MITTLERER KASTEN (Tabelle) ---
        self.table_group = QGroupBox("Fibonacci-Stufen")
        self.table_group.setObjectName("tableBox")
        table_layout = QVBoxLayout(self.table_group)
        table_layout.setContentsMargins(5, 15, 5, 5)

        # Was die Fib zeigt: die Setups aus der Tabelle oder die Level-Liste wie TradingView - nie beides
        src_row = QHBoxLayout(); src_row.setSpacing(4)
        lbl_src = QLabel("Fib zeigt:"); lbl_src.setObjectName("rules")
        src_row.addWidget(lbl_src)
        self.src_btns = {}
        for key, text, tip in (("setups", "Setups", "Die Fib zeigt die Setups aus der Tabelle – jede Linie einzeln an/aus"),
                               ("levels", "TradingView-Liste", "Die Fib zeigt die Level-Liste wie bei TradingView "
                                                               "(Einstellungen → Fib-Darstellung) – die Setups werden nicht gezeichnet")):
            b = QPushButton(text); b.setObjectName("toggle"); b.setCheckable(True); b.setToolTip(tip)
            b.clicked.connect(lambda checked, k=key: self.set_fib_source(k))
            src_row.addWidget(b, 1); self.src_btns[key] = b
        table_layout.addLayout(src_row)

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
        self.btn_objects = QPushButton(); self.btn_objects.setObjectName("tool"); self.btn_objects.setIconSize(QSize(18, 18))
        self.btn_objects.setFixedHeight(28); self.btn_objects.setToolTip("Objektliste: alle Fibs und Zeichnungen")
        self.btn_objects.clicked.connect(lambda: self.ov.open_object_list())
        self.tool_btns["list"] = self.btn_objects
        tools_row.addWidget(self.btn_objects)
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
        self.btn_design.setIcon(tool_icon("palette", t["icon"]))
        for kind, b in self.tool_btns.items():
            icon = tool_icon(kind, t["icon"])
            # eingeschaltet (z. B. Magnet an): Symbol in der Schriftfarbe des aktiven Knopfs, sonst Gold auf Gold
            icon.addPixmap(tool_icon(kind, t["on_text"]).pixmap(64), QIcon.Normal, QIcon.On)
            b.setIcon(icon)
        self.refresh_rows()  # Grau der ausgeschalteten Linien in der Farbe des Designs
        # neu messen, sobald das Design angewendet ist (Schrift und Kästchen können sich ändern)
        QTimer.singleShot(0, lambda: (self.table.update_natural_widths(), self.fit_to_content()))

    def set_theme(self, name):
        global THEME
        THEME = name
        self.apply_theme()
        self.ov.settings_changed()
        if self.settings_panel: self.settings_panel.restyle()  # nur Farben tauschen - das Fenster bleibt offen
        for dlg in (self.ov.list_dialog, self.ov._dialog):
            if dlg: dlg.setStyleSheet(themed_dialog_css())

    def cycle_theme(self, step):
        names = list(THEMES)
        name = names[(names.index(THEME) + step) % len(names)]
        self.set_theme(name)
        QToolTip.showText(self.btn_design.mapToGlobal(QPoint(0, self.btn_design.height() + 4)), f"Design: {name}", self.btn_design)

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
        self.refresh_rows()
        self.table.blockSignals(False)
        self.table.update_natural_widths()
        QTimer.singleShot(0, self.fit_to_content)
        sp = getattr(self, "settings_panel", None)
        if sp is not None and hasattr(sp, "sync_setup_checks"): sp.sync_setup_checks(); sp.sync_source()

    def refresh_rows(self):
        """Häkchen der Tabelle nach den Setups stellen. Linien eines ausgeschalteten Setups sind grau (bleiben aber
        anklickbar). Zeigt die Fib die Level-Liste, ist die ganze Tabelle grau und gesperrt."""
        setups_on = FIB_STYLE["source"] == "setups"
        muted = QColor(THEMES[THEME]["muted"])
        blocked = self.table.blockSignals(True)
        for i, s in enumerate(SETUPS):
            for col, key in enumerate(["active"] + [f"show_{k}" for k in LINE_KEYS]):
                it = self.table.item(i, col)
                if not it: continue
                it.setCheckState(Qt.Checked if s[key] else Qt.Unchecked)
                it.setData(Qt.ForegroundRole, None if setups_on and (col == 0 or s["active"]) else muted)
        self.table.blockSignals(blocked)
        self.table.setEnabled(setups_on)
        for k, b in self.src_btns.items(): b.setChecked(k == FIB_STYLE["source"])

    def set_fib_source(self, src):
        FIB_STYLE["source"] = src
        self.update_table()  # Tabelle, Knöpfe und die Einstellungen nachziehen
        self.ov.settings_changed()

    def table_item_changed(self, item):
        row = item.row()
        key = item.data(Qt.UserRole)
        if not key or row >= len(SETUPS): return
        s = SETUPS[row]
        checked = (item.checkState() == Qt.Checked)
        if s[key] == checked: return
        # Setup-Häkchen = Hauptschalter, die Linien-Häkchen bleiben, wie sie sind
        set_setup_flag(s, "active" if key == "active" else key[len("show_"):], checked)
        self.refresh_rows()
        if self.settings_panel: self.settings_panel.sync_setup_checks()  # Häkchen in den Einstellungen nachziehen
        self.ov.settings_changed()

    def open_settings(self, fib=False, section=None):
        if not self.settings_panel:
            self.settings_panel = SettingsPanel(self.ov, self)
        bring_window_to_front(self.settings_panel)
        if fib: self.settings_panel.show_fib_section()
        elif section: self.settings_panel.show_section(section)

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
