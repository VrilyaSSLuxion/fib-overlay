# Fib Overlay (SK-System)

Fibonacci-Overlay für Windows, das als durchsichtiges Fenster über jedem Chart liegt – Pocket Option, TradingView,
MetaTrader oder jedes andere Programm. Die Fib wird vom Hoch zum Tief gezogen; die vier Setups des SK-Systems
(Entry, Stop-Loss, Break-Even, TP1–TP3) stehen sofort am Chart. Dazu Zeichenwerkzeuge wie bei TradingView.

**Download:** [neueste Version (Releases)](https://github.com/VrilyaSSLuxion/fib-overlay/releases/latest) – ZIP entpacken und
`FibOverlay.exe` starten, keine Installation nötig. Alle früheren Versionen stehen ebenfalls unter
[Releases](https://github.com/VrilyaSSLuxion/fib-overlay/releases).

Übersicht mit Bildern: https://vrilyassluxion.github.io/fear-greed-v2/tools/#/fib-overlay

## Versionsverlauf

**Version 6**
- Neue Spalte „Fläche“ je Setup-Linie – z. B. rote Fläche nur zwischen Entry und SL, keine Fläche zwischen BE und TP
- Die Version steht jetzt oben im Einstellungsfenster

**Version 5**
- „Setup N anzeigen“ ist ein Hauptschalter: Die Linien-Häkchen bleiben, wie man sie setzt, und lassen sich bei ausgeschaltetem Setup vorbereiten
- Umschalter „Fib zeigt“: die Setups (jede Linie einzeln) oder die Level-Liste wie TradingView – nichts steht mehr doppelt auf einer Linie
- Knopf „Wie mein TradingView-Fib“ schaltet nur noch auf die Level-Liste und lässt die Setups unverändert

**Version 4**
- Setups 1–4 und jede Linie (Entry, SL, BE, TP1–TP3) auch in den Einstellungen an- und ausschalten – synchron mit dem Dashboard und dem Automatikmodus

**Version 3**
- Rechtsklick-Menü wie TradingView: Alarm, Vorlage, Visuelle Reihenfolge, Objektbaum, Klonen, Kopieren/Einfügen, Fixieren, Verbergen, Entfernen
- Eigenschaften-Fenster mit den Reitern Stil, Text und Koordinaten
- Text auf allen Zeichnungen, Rechteck „Verlängern“, Mauszeiger an den Griffen wie bei TradingView
- Fib: Linie 0 gelb, Linie 1 rot, Fläche je Level mit eigener Farbe
- Alarm für Rechtecke und Linien, Automatikmodus (Setups nur vorwärts 1 → 4)
- 50 Designs; Designwechsel ohne dass sich das Einstellungsfenster schließt

**Version 2**
- Rechteck wie bei TradingView mit 8 Griffen und Mittellinie
- Objektliste, Fixieren und Verbergen je Objekt, Vorlagen je Werkzeug
- TradingView-Level-Liste mit 24 Plätzen, 5 Speicherplätze für Einstellungen
- Länge des horizontalen Strahls in Pixel oder Kerzen, 29 Designs

**Version 1**
- Eigenständiges Programm (EXE) mit Dashboard und den Setups 1–4
- Einstellungen und Presets, Hotkeys
- Zeichenwerkzeuge, Magnet, Fib im TradingView-Stil, mehrere Fibs
- Level-Verlängerung mit Alarm, Designs und Matrix-Regen

Jede Version ist ein eigener Commit mit Tag (`v1` … `v6`) – so lässt sich jede Version ansehen und vergleichen.

## Starten ohne EXE

```
pip install -r requirements.txt
python fib_overlay.py
```

## EXE selbst bauen

```
pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean FibOverlay.spec
```

Die fertige Datei liegt danach in `dist\FibOverlay.exe`.

## Gut zu wissen

- Alles steckt in einer Datei: `fib_overlay.py` (Python 3, PyQt5, nur Windows). Getestet mit Python 3.14,
  PyQt5 5.15.11 und PyInstaller 6.22.3 unter Windows 11.
- Einstellungen, Vorlagen und Speicherplätze liegen unter `%APPDATA%\FibOverlay`.
- Das Overlay liegt als Bild über dem Chart: Wird der Chart verschoben oder gezoomt, bleibt die Fib am Bildschirm stehen.
- Alarm, Automatikmodus und Magnet lesen die Kerzen vom Bildschirm ab und sind Test-Funktionen.

Kein Anlagerat – Trading ist mit Risiken verbunden. © VrilyaSS
