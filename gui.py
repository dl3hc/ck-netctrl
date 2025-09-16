from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSlider, QVBoxLayout,
    QWidget, QListWidget, QCheckBox, QHBoxLayout, QPushButton,
    QSizePolicy, QLineEdit, QMessageBox, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIntValidator
from backend.trx import TRX
from backend.settings import Settings
from backend.utils.sbc65ec import SBC65EC
import time

# --- Heartbeat-Thread ---
class HeartbeatThread(QThread):
    update_signal = pyqtSignal(bool)

    def __init__(self, tuner: SBC65EC, interval=1.0):
        super().__init__()
        self.tuner = tuner
        self.interval = interval
        self.running = True
        self._connected_once = False

    def run(self):
        while self.running:
            try:
                reachable = self.tuner.check_reachability()
            except Exception:
                reachable = False
            self.update_signal.emit(reachable)
            if reachable:
                self._connected_once = True
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.wait()


# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Christian-Koppler Network Control")

        # --- Backend ---
        self.trx = None
        self.settings = Settings()
        self.tuner = SBC65EC(debug=False)

        # --- Modus ---
        self.setup_mode = True
        self._active_entry = None
        self.connected_once = False

        # --- Status Widgets ---
        self.trx_status = QLabel("TRX: ❌")
        self.tuner_status = QLabel("Tuner: ❌")
        self.freq_label = QLabel("Freq: 0 Hz")

        # --- TRX Dropdown + Eingaben ---
        self.trx_combo = QComboBox()
        for rig_name, rig_id in sorted(TRX.list_available_rigs(), key=lambda x: x[0]):
            display_text = f"{rig_name} ({rig_id})"
            self.trx_combo.addItem(display_text, rig_id)
        
        self.trx_port_input = QLineEdit("localhost:19090")
        self.trx_port_input.setPlaceholderText("Port oder COM-Port")
        
        self.trx_connect_button = QPushButton("TRX verbinden")
        self.trx_connect_button.clicked.connect(self.connect_trx)
        
        self.trx_status = QLabel("TRX: ❌ nicht verbunden")  # Startstatus

        trx_layout = QHBoxLayout()
        trx_layout.addWidget(QLabel("TRX Modell"))
        trx_layout.addWidget(self.trx_combo)
        trx_layout.addWidget(QLabel("Port"))
        trx_layout.addWidget(self.trx_port_input)
        trx_layout.addWidget(self.trx_connect_button)

        # --- Toggle Button für Ansicht ---
        self.toggle_button_view = QPushButton("Reduce view")
        self.toggle_button_view.setCheckable(True)
        self.toggle_button_view.setChecked(True)
        self.toggle_button_view.clicked.connect(self.toggle_view)

        # --- Slider / Controls ---
        self.L_slider = QSlider(Qt.Orientation.Horizontal)
        self.L_slider.setRange(0, 127)
        self.C_slider = QSlider(Qt.Orientation.Horizontal)
        self.C_slider.setRange(0, 255)
        self.HP_checkbox = QCheckBox("Highpass")
        self.save_button = QPushButton("Save current values")
        self.delete_button = QPushButton("Delete selected value")
        self.load_json_button = QPushButton("Load values from JSON")
        self.freq_list = QListWidget()

        # --- Setup-Modus Checkbox ---
        self.setup_checkbox = QCheckBox("Setup-Modus aktiv")
        self.setup_checkbox.setChecked(True)
        self.setup_checkbox.toggled.connect(self.toggle_setup_mode)

        # --- Slider Labels ---
        self.L_value_label = QLabel("0")
        self.C_value_label = QLabel("0")
        self.L_slider.valueChanged.connect(lambda val: self.L_value_label.setText(str(val)))
        self.C_slider.valueChanged.connect(lambda val: self.C_value_label.setText(str(val)))

        # --- Frequenz Eingaben ---
        self.freq_min_input = QLineEdit()
        self.freq_min_input.setPlaceholderText("Min freq (Hz)")
        self.freq_min_input.setValidator(QIntValidator(0, 50000000))
        self.freq_max_input = QLineEdit()
        self.freq_max_input.setPlaceholderText("Max freq (Hz)")
        self.freq_max_input.setValidator(QIntValidator(0, 50000000))

        # --- SBC65EC Eingabe ---
        self.sbc_ip_input = QLineEdit("10.1.0.1")
        self.sbc_ip_input.setPlaceholderText("SBC65 IP")
        self.sbc_port_input = QLineEdit("54123")
        self.sbc_port_input.setValidator(QIntValidator(1, 65535))
        self.sbc_port_input.setPlaceholderText("Port")
        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self.connect_to_sbc)

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("SBC IP"))
        ip_layout.addWidget(self.sbc_ip_input)
        ip_layout.addWidget(QLabel("Port"))
        ip_layout.addWidget(self.sbc_port_input)
        ip_layout.addWidget(self.connect_button)

        # --- Erweiterte Ansicht ---
        self.advanced_widget = QWidget()
        adv_layout = QVBoxLayout()
        adv_layout.setSpacing(5)
        adv_layout.insertLayout(0, trx_layout)
        adv_layout.insertLayout(1, ip_layout)
        adv_layout.addWidget(self.setup_checkbox)

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Min Freq"))
        freq_layout.addWidget(self.freq_min_input)
        freq_layout.addWidget(QLabel("Max Freq"))
        freq_layout.addWidget(self.freq_max_input)
        adv_layout.addLayout(freq_layout)

        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel("L"))
        l_layout.addWidget(self.L_slider)
        l_layout.addWidget(self.L_value_label)
        adv_layout.addLayout(l_layout)

        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("C"))
        c_layout.addWidget(self.C_slider)
        c_layout.addWidget(self.C_value_label)
        adv_layout.addLayout(c_layout)

        adv_layout.addWidget(self.HP_checkbox)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.save_button)
        adv_layout.addLayout(hlayout)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(self.delete_button)
        hlayout2.addWidget(self.load_json_button)
        adv_layout.addLayout(hlayout2)

        adv_layout.addWidget(QLabel("Saved Settings"))
        adv_layout.addWidget(self.freq_list)
        self.advanced_widget.setLayout(adv_layout)
        self.advanced_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # --- Status Container ---
        status_widget = QWidget()
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.trx_status)
        status_layout.addWidget(self.tuner_status)
        status_layout.addWidget(self.freq_label)
        status_widget.setLayout(status_layout)

        # --- Hauptlayout ---
        layout = QVBoxLayout()
        layout.addWidget(status_widget)
        layout.addWidget(self.toggle_button_view)
        layout.addWidget(self.advanced_widget)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- Debounce für Slider ---
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._send_tuner_values)

        # --- Heartbeat-Thread ---
        self.heartbeat_thread = HeartbeatThread(self.tuner)
        self.heartbeat_thread.update_signal.connect(self.update_tuner_status)

        # --- Signale ---
        self.L_slider.valueChanged.connect(self.schedule_update)
        self.C_slider.valueChanged.connect(self.schedule_update)
        self.HP_checkbox.stateChanged.connect(self.schedule_update)
        self.save_button.clicked.connect(lambda: print("SAVE CLICKED"))
        self.save_button.clicked.connect(self.save_current)
        self.delete_button.clicked.connect(self.delete_selected)
        self.load_json_button.clicked.connect(self.load_from_json)

        # --- Status-Timer ---
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)

        # --- Initialmodus & gespeicherte Settings ---
        self._apply_mode_settings()
        self.load_list()
        self.load_saved_meta()
        self.update_status()

    # --- TRX Verbindung ---
    def connect_trx(self):
        rig_id = self.trx_combo.currentData()
        port = self.trx_port_input.text().strip()
        if not port:
            QMessageBox.warning(self, "Fehler", "Bitte einen Port oder Host eingeben")
            return

        self.trx = TRX(rig_id=rig_id, port=port)
        self.trx.connect()

        if self.trx.connected:
            self.trx_status.setText(f"TRX: ✅ verbunden ({self.trx_combo.currentText()})")
            self.trx_check_timer = QTimer()
            self.trx_check_timer.timeout.connect(self.check_trx_connection)
            self.trx_check_timer.start(2000)
        else:
            self.trx_status.setText("TRX: ❌ Verbindung fehlgeschlagen")

    def check_trx_connection(self):
        if not self.trx.connected:
            self.trx_status.setText("TRX: ❌ Verbindung zum TRX verloren")
            self.trx_check_timer.stop()

    # --- Status & Frequenzbereich ---
    def update_status(self):
        trx_connected = self.trx.connected if self.trx else False
        self.trx_status.setText(f"TRX: {'✅' if trx_connected else '❌'}")

        freq = self.trx.get_frequency() if self.trx and trx_connected else 0
        self.freq_label.setText(f"Freq: {int(freq)} Hz")


        if not self.setup_mode and trx_connected:
            entry = self.settings.get_for_frequency(freq)
            if entry != self._active_entry:
                self._active_entry = entry
                if entry:
                    self.L_slider.blockSignals(True)
                    self.C_slider.blockSignals(True)
                    self.HP_checkbox.blockSignals(True)
                    self.L_slider.setValue(entry["L"])
                    self.C_slider.setValue(entry["C"])
                    self.HP_checkbox.setChecked(entry["highpass"])
                    self._send_tuner_values()
                    self.L_slider.blockSignals(False)
                    self.C_slider.blockSignals(False)
                    self.HP_checkbox.blockSignals(False)

    # --- Heartbeat GUI Update ---
    def update_tuner_status(self, reachable: bool):
        ip = self.tuner.host
        port = self.tuner.port
        if reachable:
            self.tuner_status.setText(f"Tuner: ✅ Verbindung zu {ip}:{port} hergestellt")
            self.connected_once = True
        else:
            if getattr(self, "connected_once", False):
                self.tuner_status.setText(f"Tuner: ❌ Verbindung zum Tuner verloren")
            else:
                self.tuner_status.setText(f"Tuner: ❌ Verbindung zu {ip}:{port} fehlgeschlagen")

    # --- Setup-Modus ---
    def toggle_setup_mode(self, checked: bool):
        self.setup_mode = checked
        self._apply_mode_settings()

    def _apply_mode_settings(self):
        for w in [self.L_slider, self.C_slider, self.HP_checkbox,
                  self.freq_min_input, self.freq_max_input,
                  self.save_button, self.delete_button,
                  self.load_json_button, self.freq_list]:
            w.setEnabled(self.setup_mode)

        color = "#FFFACD" if self.setup_mode else "#C6F6C6"
        self.setup_checkbox.setText("Setup-Modus aktiv" if self.setup_mode else "Setup-Modus")
        style = f"background-color: {color}; font-weight: bold; border: 1px solid black;"
        self.trx_status.setStyleSheet(style)
        self.tuner_status.setStyleSheet(style)
        self.freq_label.setStyleSheet(style)

    # --- Ansicht ---
    def toggle_view(self):
        if self.toggle_button_view.isChecked():  # ausgeklappt
            self.advanced_widget.show()
            self.setup_checkbox.show()
            self.toggle_button_view.setText("Reduce view")

            self.setMinimumHeight(200)   # Höhe darf nicht kleiner werden
            self.setMaximumHeight(1000)  # Höhe darf nicht größer werden
            self.resize(555, 500)        # volle Größe wiederherstellen
            # Breite NICHT fixieren – Qt passt automatisch an Inhalt

        else:  # reduziert / eingeklappt
            self.advanced_widget.hide()
            self.setup_checkbox.hide()
            self.toggle_button_view.setText("Expand view")

            self.setFixedHeight(125)     # nur Höhe fixieren
            # Breite NICHT fixieren, damit sie beim Expand wieder korrekt wird


    # --- Debounce ---
    def schedule_update(self):
        if self.setup_mode:
            self.debounce_timer.start(50)

    # --- Werte senden ---
    def _send_tuner_values(self):
        if getattr(self.tuner, "reachable", False):
            l_val = self.L_slider.value()
            c_val = self.C_slider.value()
            hp_val = self.HP_checkbox.isChecked()
            self.tuner.send_values(l_val, c_val, hp_val)

    # --- Speichern / Löschen / JSON ---
    def save_current(self):
        if not self.setup_mode:
            return

        min_text = self.freq_min_input.text().strip()
        max_text = self.freq_max_input.text().strip()

        # --- Frequenz-Teil ---
        if min_text or max_text:  # mindestens eins ausgefüllt
            if not (min_text and max_text):
                QMessageBox.warning(self, "Fehler",
                                    "Bitte sowohl Min- als auch Max-Frequenz eingeben "
                                    "oder beide Felder leer lassen.")
                return
            try:
                min_freq = int(min_text)
                max_freq = int(max_text)
            except ValueError:
                QMessageBox.warning(self, "Fehler",
                                    "Min/Max-Frequenz muss eine Zahl sein.")
                return

            self.settings.add_entry(
                min_freq=min_freq,
                max_freq=max_freq,
                L=self.L_slider.value(),
                C=self.C_slider.value(),
                highpass=self.HP_checkbox.isChecked()
            )

        # --- SBC / TRX-Werte ---
        self.settings.sbc_ip = self.sbc_ip_input.text().strip() or self.settings.sbc_ip
        try:
            self.settings.sbc_port = int(self.sbc_port_input.text().strip())
        except ValueError:
            self.settings.sbc_port = 54123

        self.settings.trx_id = self.trx_combo.currentData()
        self.settings.trx_port = self.trx_port_input.text().strip() or self.settings.trx_port

        # --- Speichern & Liste aktualisieren ---
        self.settings.save()
        self.load_list()

        print("Speichern abgeschlossen.")
        print("Aktuelle Frequenzen:", self.settings.data)
        print("SBC:", self.settings.sbc_ip, self.settings.sbc_port)
        print("TRX:", self.settings.trx_id, self.settings.trx_port)


        # --- Alles speichern ---
        self.settings.save()
        print("TRX-ID:", self.settings.trx_id)
        print("TRX-Port:", self.settings.trx_port)
        print("SBC-IP:", self.settings.sbc_ip)
        print("SBC-Port:", self.settings.sbc_port)
        self.load_list()


    def delete_selected(self):
        if not self.setup_mode:
            return
        row = self.freq_list.currentRow()
        if row >= 0:
            del self.settings.data[row]
            self.settings.save()
            self.load_list()

    def load_from_json(self):
        if not self.setup_mode:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "JSON-Datei auswählen", "", "JSON Dateien (*.json)")
        if not file_path:
            return
        self.settings.load_from_json(file_path)
        self.load_list()
        self.load_saved_meta()

    def load_list(self):
        self.freq_list.clear()
        for entry in self.settings.data:
            self.freq_list.addItem(
                f"{entry['min_freq']}-{entry['max_freq']} Hz: L={entry['L']}, C={entry['C']}, HP={entry['highpass']}"
            )

    # --- Verbindung ---
    def connect_to_sbc(self):
        ip = self.sbc_ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Fehler", "Bitte eine IP eingeben")
            return
        try:
            port = int(self.sbc_port_input.text())
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Port muss eine Zahl zwischen 1 und 65535 sein")
            return

        self.tuner.host = ip
        self.tuner.port = port

        reachable = self.tuner.check_reachability(timeout=0.5)
        if reachable:
            self.tuner_status.setText(f"Tuner: ✅ Verbindung zu {ip}:{port} hergestellt")
            self.connected_once = True
            if not self.heartbeat_thread.isRunning():
                self.heartbeat_thread.start()
        else:
            if self.connected_once:
                self.tuner_status.setText("Tuner: ❌ Verbindung zum Tuner verloren")
            else:
                QMessageBox.warning(self, "Fehler", f"SBC65EC unter {ip}:{port} nicht erreichbar")
                self.tuner_status.setText(f"Tuner: ❌ Verbindung zu {ip}:{port} fehlgeschlagen")

    # --- Gespeicherte TRX + SBC Einstellungen laden ---
    def load_saved_meta(self):
        self.sbc_ip_input.setText(self.settings.sbc_ip)
        self.sbc_port_input.setText(str(self.settings.sbc_port))
        index = self.trx_combo.findData(self.settings.trx_id)
        if index >= 0:
            self.trx_combo.setCurrentIndex(index)
        self.trx_port_input.setText(self.settings.trx_port)

