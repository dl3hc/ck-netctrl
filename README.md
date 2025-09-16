# Christian-Koppler Control Software

## Projektübersicht

Die Christian-Koppler-Control-Software ist eine Desktopanwendung zur Steuerung eines Christian-Kopplers (Antennen-Tuner) über ein LAN-Interface in Verbindung mit einem Transceiver (TRX), der über CAT angesprochen wird.

Die Software erlaubt das **automatische Einstellen des Tuners** auf die vom TRX aktuell empfangene Frequenz sowie das **manuelle Setzen und Speichern von L-, C- und Hoch-/Tiefpass-Werten** für bestimmte Frequenzbereiche.

Ziel ist es, sowohl **manuelle Feinabstimmung** als auch **automatisches Arbeiten im Live-Betrieb** komfortabel zu ermöglichen.

> **Hinweis:** Das Programm ist aktuell **nur unter Linux getestet und lauffähig**, da Hamlib bisher noch nicht erfolgreich unter Windows kompiliert werden konnte.

---

## Schnellstart-Anleitung

### Voraussetzungen
- Python 3.10+  
- PyQt6
- [Hamlib](https://github.com/Hamlib/Hamlib) (nur unter Linux getestet)

### Repository klonen
```bash
git clone https://github.com/dl3hc/ck-netctrl.git
cd ck-netctrl
````

### Virtuelle Umgebung

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows (nicht getestet)
```

### Python-Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install PyQt6
```
---

### Hamlib installieren / kompilieren

* TRX-Kommunikation erfolgt über Hamlib.
* Linux: Kompilieren von Hamlib mit aktivierten Python-Bindings.
* Windows: Aktuell noch nicht möglich.

Die TRX-Kommunikation erfolgt über Hamlib.
Hier die vollständige Anleitung für Linux (mit Python-Bindings):


#### Systemabhängige Pakete installieren

```bash
sudo apt update
sudo apt install git build-essential autoconf automake libtool pkg-config libusb-1.0-0-dev libhamlib-dev swig python3-dev
```

**Erklärung:**

* `libhamlib-dev` → Hamlib-Header und Bibliothek
* `swig` → erzeugt die Python-Bindings aus C-Code
* `python3-dev` → Header-Dateien für Python-Entwicklung

---

#### Hamlib-Quellcode herunterladen

```bash
git clone https://github.com/Hamlib/Hamlib
cd Hamlib
```

Falls direkt aus Git geklont: Build-System initialisieren:

```bash
./bootstrap
```

> Bei Source-Releases entfällt dieser Schritt.

#### Aktiviere deine virtuelle Umgebung:

```bash
source .venv/bin/activate
which python3   # sollte VIRTUAL_ENV/bin/python3 anzeigen
```
---

#### Hamlib konfigurieren (Out-of-Tree Build)

```bash
mkdir ../hamlib-build
cd ../hamlib-build
../Hamlib/configure --with-python-binding PYTHON="$VIRTUAL_ENV/bin/python3" --prefix="$VIRTUAL_ENV"
```

> `PYTHON=$(which python3)` nutzt die aktuelle Python-Version.
> `--prefix=$VIRTUAL_ENV` installiert alles in der aktiven venv (kein Root nötig).

---

#### Build & Installation

```bash
make -j$(nproc)
make install
```

Wechsle anschließend in den `bindings`-Ordner:

```bash
cd ../Hamlib/bindings
make
make install
```

Danach sollten in deiner virtuellen Umgebung erscheinen:

```
$VIRTUAL_ENV/lib/python3.12/site-packages/Hamlib.py
$VIRTUAL_ENV/lib/python3.12/site-packages/_Hamlib.so
```

---

#### Testen der Installation

```bash
(.venv)python3 -c "import Hamlib; print(Hamlib)"
```

Wenn keine Fehlermeldung erscheint, sind die Python-Bindings korrekt installiert.

---



### Anwendung starten

```bash
python main.py
```

* TRX und SBC-IP/Port können direkt eingegeben werden.
* Setup-Modus aktivieren → Werte eintragen → Speichern.
* Setup-Modus deaktivieren → automatische Übernahme der Werte.

---

## Hauptfunktionen

1. **TRX-Status**
   - Anzeige, ob eine Verbindung zum TRX besteht.
   - Auslesen der aktuellen Frequenz.

2. **Tuner-Status**
   - Anzeige, ob der Koppler über LAN erreichbar ist.
   - Einstellung von L-, C- und Hoch-/Tiefpass-Werten über GUI-Slider und Checkbox.

3. **Setup-Modus**
   - Ermöglicht das **manuelle Einstellen und Speichern** von Werten für definierte Frequenzbereiche.
   - Aktiviert die Eingabefelder für Min/Max Frequenz und die Slider/Checkboxen.
   - Deaktiviert automatische Updates durch den Live-Modus.

4. **Live-Modus**
   - Übernimmt automatisch die gespeicherten Werte aus der Frequenzliste entsprechend der aktuell vom TRX ausgelesenen Frequenz.
   - Slider und Checkboxen werden gesperrt, um unbeabsichtigte Änderungen zu verhindern.

5. **Frequenzbereiche / Settings**
   - Speicherung von unterer und oberer Frequenz, L-Wert, C-Wert und Hoch-/Tiefpass.
   - Automatisches Laden der Werte, wenn die Frequenz in einem gespeicherten Bereich liegt.
   - Visualisierung in einer Liste mit Hervorhebung des aktuell aktiven Eintrags.
   - Speicherung der TRX-Port/Host und SBC-IP/Port Einstellungen.

6. **Reduzierte / Erweiterte Ansicht**
   - Reduzierte Ansicht: Zeigt nur TRX-Verbindung, Tuner-Verbindung und aktuelle Frequenz.
   - Erweiterte Ansicht: Zusätzlich Steuerung der Slider, Checkbox, Frequenzbereichseingaben und gespeicherte Einstellungen.

7. **Live-Visualisierung**
   - Farbige Hervorhebung der aktiven Frequenzbereichs-Einträge.
   - Anzeige des aktiven Modus (Setup / Live) über visuelle Indikatoren.

---

## Software-Architektur / Modularität

Die Software ist **modular aufgebaut**, um zukünftige Erweiterungen einfach zu ermöglichen:

### Backend
- `trx.py`: Schnittstelle zum Transceiver (über Hamlib oder CAT-DLL).
- `messages.py`: Nachrichtenerzeugung für L-, C- und HP-Werte.
- `settings.py`: Verwaltung der Frequenzbereiche, L-, C- und HP-Werte sowie TRX/SBC-Einstellungen.
- `utils/`
  - `network.py`: Ping, send_udp
  - `sbc65ec.py`: SBC65-spezifische Logik

### Frontend (GUI)
- `gui.py`: Hauptfenster der Anwendung mit PyQt6.
  - Statusanzeigen (TRX, Tuner, Frequenz)
  - Slider für L/C, Checkbox für HP
  - Eingabefelder für Frequenzbereiche
  - Liste der gespeicherten Einstellungen
  - Setup / Live Modus
  - Reduzierte / Erweiterte Ansicht

---



## Projektstruktur

```
cknetctrl/
├─ gui.py
├─ main.py
├─ backend/
│  ├─ messages.py
│  ├─ trx.py
│  ├─ settings.py
│  └─ utils/
│     ├─ network.py
│     └─ sbc65ec.py
├─ docs/
│  ├─ lc_matrix_tuner.pdf    
│  └─ pin_matrix_sbc65ec.pdf
```

---

# Klassen und Funktionen

| Modul                      | Klasse / Funktion                                                     | Beschreibung / Zweck                                                                                                                             |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `main.py`                  | `QApplication`                                                        | Startet die Qt-Anwendung.                                                                                                                        |
|                            | `MainWindow`                                                          | Initialisiert das Hauptfenster der Christian-Koppler-Software.                                                                                   |
|                            | `app.exec()`                                                          | Startet die Qt-Event-Schleife.                                                                                                                   |
| `gui.py`                   | `HeartbeatThread`                                                     | Thread zur periodischen Überprüfung der Erreichbarkeit des Tuners.                                                                               |
|                            | `__init__(tuner, interval=1.0)`                                       | Initialisiert den Heartbeat-Thread mit Referenz auf den Tuner und Intervall.                                                                     |
|                            | `run()`                                                               | Hauptschleife des Threads, prüft die Erreichbarkeit und sendet Signal.                                                                           |
|                            | `stop()`                                                              | Stoppt den Thread sicher.                                                                                                                        |
| `gui.py`                   | `MainWindow`                                                          | Hauptfenster der Anwendung, enthält GUI-Elemente, Statusanzeigen und Backend-Logik.                                                              |
|                            | `__init__()`                                                          | Initialisiert GUI, Backend, Timer, Heartbeat-Thread und verbindet Signale.                                                                       |
|                            | `connect_trx()`                                                       | Baut Verbindung zum TRX auf, aktualisiert Statusanzeige und Timer.                                                                               |
|                            | `check_trx_connection()`                                              | Prüft periodisch die Verbindung zum TRX und aktualisiert Anzeige.                                                                                |
|                            | `update_status()`                                                     | Aktualisiert TRX-Status, Frequenzanzeige und lädt Werte im Live-Modus.                                                                           |
|                            | `update_tuner_status(reachable)`                                      | Aktualisiert GUI-Statusanzeige für Tuner je nach Erreichbarkeit.                                                                                 |
|                            | `toggle_setup_mode(checked)`                                          | Schaltet Setup-Modus ein/aus und passt GUI entsprechend an.                                                                                      |
|                            | `_apply_mode_settings()`                                              | Aktiviert oder deaktiviert Widgets abhängig vom aktuellen Modus.                                                                                 |
|                            | `toggle_view()`                                                       | Umschalten zwischen reduzierter und erweiterter Ansicht.                                                                                         |
|                            | `schedule_update()`                                                   | Debounced Update der Tuner-Werte bei Slider/Checkbox-Änderungen.                                                                                 |
|                            | `_send_tuner_values()`                                                | Sendet aktuelle L-, C- und HP-Werte an den Tuner.                                                                                                |
|                            | `save_current()`                                                      | Speichert aktuelle Frequenzbereichs- und TRX/SBC-Einstellungen.                                                                                  |
|                            | `delete_selected()`                                                   | Löscht den aktuell ausgewählten Eintrag aus der Frequenzliste.                                                                                   |
|                            | `load_from_json()`                                                    | Lädt Frequenz- und Tuner-Einstellungen aus einer JSON-Datei.                                                                                     |
|                            | `load_list()`                                                         | Lädt die GUI-Liste der gespeicherten Frequenzbereiche.                                                                                           |
|                            | `connect_to_sbc()`                                                    | Baut Verbindung zum SBC65EC auf, prüft Erreichbarkeit, startet Heartbeat.                                                                        |
|                            | `load_saved_meta()`                                                   | Lädt gespeicherte SBC- und TRX-Einstellungen in die GUI.                                                                                         |
| `backend/trx.py`           | `TRX`                                                                 | Schnittstelle zum Transceiver via Hamlib oder Dummy-Modus.                                                                                       |
|                            | `__init__(rig_id, port, baudrate, databits, parity, stopbits, dummy)` | Initialisiert TRX-Objekt, wählt Hamlib-Rig oder Dummy.                                                                                           |
|                            | `list_available_rigs()`                                               | Gibt alle bekannten Hamlib-Rigs als Liste zurück.                                                                                                |
|                            | `connect()`                                                           | Öffnet die Verbindung zum TRX oder Dummy.                                                                                                        |
|                            | `get_frequency()`                                                     | Liest die aktuelle Frequenz aus dem TRX oder Dummy.                                                                                              |
|                            | `close()`                                                             | Schließt die Verbindung zum TRX.                                                                                                                 |
| `backend/settings.py`      | `Settings`                                                            | Verwaltung der Frequenzbereiche, TRX- und SBC-Einstellungen.                                                                                     |
|                            | `__init__(filename="settings.json")`                                  | Initialisiert die Settings, lädt gespeicherte Werte.                                                                                             |
|                            | `load()`                                                              | Lädt Settings aus der JSON-Datei.                                                                                                                |
|                            | `load_from_json(filename=None)`                                       | Lädt Settings aus einer optional angegebenen JSON-Datei.                                                                                         |
|                            | `save()`                                                              | Speichert aktuelle Frequenzen und TRX/SBC-Einstellungen in JSON.                                                                                 |
|                            | `get_for_frequency(freq)`                                             | Gibt den gespeicherten Eintrag für die gegebene Frequenz zurück.                                                                                 |
|                            | `add_entry(min_freq, max_freq, L, C, highpass)`                       | Fügt einen neuen Frequenzbereich mit L/C/HP-Werten hinzu.                                                                                        |
| `backend/messages.py`      | `build_messages(val_l, val_c, highpass)`                              | Baut alle Nachrichten für den SBC65EC basierend auf L-, C- und Hoch-/Tiefpass-Werten. Liefert vier Bytearrays: msg\_a, msg\_b, msg\_c1, msg\_c2. |
| `backend/utils/sbc65ec.py` | `SBC65EC`                                                             | Steuerung des SBC65EC Tuners über UDP; prüft Erreichbarkeit und sendet L-, C- und HP-Werte.                                                      |
|                            | `__init__(host, port, debug)`                                         | Initialisiert Tuner mit IP, Port und optional Debug-Modus.                                                                                       |
|                            | `check_reachability(timeout)`                                         | Prüft, ob der Tuner erreichbar ist (per ICMP) und setzt `reachable`.                                                                             |
|                            | `send_values(l_value, c_value, highpass)`                             | Sendet Werte an den Tuner, nur wenn sich Werte geändert haben; Debug-Ausgabe optional.                                                           |
| `backend/utils/network.py` | `ping_icmp(ip, timeout=1.0, attempts=3)`                              | Führt ein klassisches ICMP-Ping durch; unterstützt Windows und Linux.                                                                            |
|                            | `send_udp(ip, port, data, timeout=1.0)`                               | Sendet ein UDP-Paket an die angegebene IP/Port und gibt True bei Erfolg zurück.

---

## Lizenz

Dieses Projekt ist **Open Source**, lizenziert unter **GPLv3 + Non-Commercial**.  

- **Non-Commercial:** Die Software darf nicht für kommerzielle Zwecke verwendet werden.  
  Kommerzielle Zwecke schließen den Verkauf, die Lizenzierung oder die Nutzung der Software für bezahlte Dienstleistungen ein.
- **Copyleft:** Änderungen oder abgeleitete Werke müssen ebenfalls unter dieser Lizenz veröffentlicht werden.
- **Haftungsausschluss:** Die Software wird ohne jegliche Garantie bereitgestellt.

Für die vollständigen Lizenzbedingungen siehe die [LICENSE-Datei](./LICENSE) im Repository.
