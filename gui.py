# -----------------------------------------------------------------------------
# Christian-Koppler Control Software (ck-netctrl)
# Copyright (C) 2025 dl3hc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version, **with the following restriction**:
#
# Non-Commercial Use Only:
# This software may not be used for commercial purposes.
# Commercial purposes include selling, licensing, or using the software
# to provide paid services.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details:
# https://www.gnu.org/licenses/
#
# Additional notes:
# 1. Any modifications or derived works must also be released under
#    this same license (GPLv3 + Non-Commercial).
# 2. Redistribution of modified versions must also make the source code
#    available under this license.
# -----------------------------------------------------------------------------

from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSlider, QVBoxLayout,
    QWidget, QListWidget, QCheckBox, QHBoxLayout, QPushButton,
    QSizePolicy, QLineEdit, QMessageBox, QComboBox, QFileDialog,
    QGroupBox, QTabWidget, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIntValidator
from backend.services.trx_service import TRXService
from backend.services.tuner_service import TunerService
from backend.services.settings_service import SettingsService
from backend.services.impl.trx_service_impl import TRXServiceImpl
from backend.services.impl.tuner_service_impl import TunerServiceImpl
from backend.services.impl.settings_service_impl import SettingsServiceImpl
import time
import Hamlib
from backend.trx import TRX
from backend.utils.sbc65ec import SBC65EC


# --- Application-wide stylesheet ---
# A single, cohesive flat/modern theme (light background, blue accent,
# rounded cards) applied once at the top level - Qt stylesheets cascade to
# all child widgets, so nothing below needs its own per-widget styling
# except the dynamic status colors (setup/active/warning), which stay as
# small, targeted inline overrides.
APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f6f8;
    color: #1f2933;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d9dfe4;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #2b6cb0;
}
QTabWidget::pane {
    border: 1px solid #d9dfe4;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #e8edf2;
    border: 1px solid #d9dfe4;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    font-weight: 600;
    color: #2b6cb0;
}
QPushButton {
    background-color: #2b6cb0;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2c5282;
}
QPushButton:pressed {
    background-color: #1a365d;
}
QPushButton:disabled {
    background-color: #a0aec0;
    color: #edf2f7;
}
QPushButton#secondaryButton {
    background-color: #edf2f7;
    color: #2d3748;
    border: 1px solid #cbd5e0;
}
QPushButton#secondaryButton:hover {
    background-color: #e2e8f0;
}
QPushButton#secondaryButton:pressed {
    background-color: #cbd5e0;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 5px;
    padding: 4px 6px;
    selection-background-color: #2b6cb0;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #2b6cb0;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background-color: #f1f4f7;
    color: #a0aec0;
}
QCheckBox {
    spacing: 6px;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #cbd5e0;
    border-radius: 6px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #cbd5e0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2b6cb0;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:disabled {
    background: #a0aec0;
}
"""

# Status pill colors (semantics preserved from the previous design):
# amber = setup mode, green = active/running, red = warning (blinking).
_STATUS_STYLE = (
    "background-color: {bg}; color: {fg}; font-weight: 600; "
    "border-radius: 6px; padding: 6px 10px;"
)
_COLOR_SETUP = ("#FEF3C7", "#92400E")
_COLOR_ACTIVE = ("#D1FAE5", "#065F46")
_COLOR_WARNING = ("#FEE2E2", "#991B1B")


def _status_style(mode: str) -> str:
    """Returns the stylesheet snippet for a status pill (setup/active/warning)."""
    bg, fg = {"setup": _COLOR_SETUP, "active": _COLOR_ACTIVE, "warning": _COLOR_WARNING}[mode]
    return _STATUS_STYLE.format(bg=bg, fg=fg)


# --- Heartbeat Thread ---
class HeartbeatThread(QThread):
    """
    Thread to periodically check the reachability of a tuner device (SBC65EC).

    Attributes:
        tuner (SBC65EC): The tuner instance to monitor.
        interval (float): Time interval in seconds between checks.
        running (bool): Flag indicating whether the thread is active.
        _connected_once (bool): Indicates if the tuner was ever reachable.
        update_signal (pyqtSignal): Emitted with a boolean indicating reachability.
    """

    update_signal = pyqtSignal(bool)

    def __init__(self, tuner: SBC65EC, interval: float = 1.0):
        """
        Initialize HeartbeatThread.

        Args:
            tuner (SBC65EC): The tuner object to monitor.
            interval (float, optional): Check interval in seconds. Defaults to 1.0.
        """
        super().__init__()
        self.tuner = tuner
        self.interval = interval
        self.running = True
        self._connected_once = False

    def run(self):
        """
        Main loop of the heartbeat thread.
        Checks tuner reachability periodically and emits update_signal.
        """
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
        """
        Stop the heartbeat thread safely.
        """
        self.running = False
        self.wait()


# --- Main Window ---
class MainWindow(QMainWindow):
    """
    Main window for Christian-Koppler Network Control.

    Handles UI, TRX connection, SBC65EC tuner connection,
    setup mode, and user interactions for saving/deleting frequency settings.
    """

    def __init__(self):
        """
        Initialize the main window, UI components, backend objects,
        signals, timers, and load saved settings.
        """
        super().__init__()
        self.setWindowTitle("Christian-Koppler Network Control")
        self.setStyleSheet(APP_STYLESHEET)

        # --- Backend services ---
        self.trx_service: TRXService = TRXServiceImpl()
        self.tuner_service: TunerService = TunerServiceImpl()
        self.settings_service: SettingsService = SettingsServiceImpl()

        # --- Mode ---
        self.setup_mode: bool = True
        self._active_entry: Optional[dict] = None
        self.connected_once: bool = False

        # --- Status Widgets ---
        self.trx_status: QLabel = QLabel("TRX: ❌ not connected")
        self.tuner_status: QLabel = QLabel("Tuner: ❌ not connected")
        self.freq_label: QLabel = QLabel("Freq: 0 Hz")

        # --- Blink timer for "no matching frequency entry" warning ---
        self._blink_state: bool = False
        self._last_freq: int = 0
        self._last_show_warning: bool = False
        self._freq_label_cache_key = None
        self.blink_timer: QTimer = QTimer()
        self.blink_timer.timeout.connect(self._toggle_blink)

        # --- TRX dropdown + input ---
        self.trx_combo: QComboBox = QComboBox()
        for rig_name, rig_id in sorted(TRX.list_available_rigs(), key=lambda x: x[0]):
            display_text = f"{rig_name} ({rig_id})"
            self.trx_combo.addItem(display_text, rig_id)

        # --- Connection type: serial CAT vs. network (netrigctl/rigctld) ---
        # This is the single source of truth for how the port field and the
        # serial-only controls below are interpreted - it replaces guessing
        # the mode from whether the port text happens to contain a ":".
        self.trx_conn_type_combo: QComboBox = QComboBox()
        self.trx_conn_type_combo.addItem("Serial (CAT)", "serial")
        self.trx_conn_type_combo.addItem("Network (netrigctl)", "network")
        self.trx_conn_type_combo.currentIndexChanged.connect(self._on_trx_conn_type_changed)

        self.trx_port_label: QLabel = QLabel("Port:")
        self.trx_port_input: QLineEdit = QLineEdit("COM3")
        self.trx_port_input.setPlaceholderText("COM port, e.g. COM3")

        # --- Serial-only settings (baud rate, DTR/RTS) ---
        self.trx_baudrate_input: QComboBox = QComboBox()
        self.trx_baudrate_input.setEditable(True)
        self.trx_baudrate_input.addItems(
            ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        )
        self.trx_baudrate_input.setCurrentText("9600")
        self.trx_baudrate_input.setToolTip("Baud rate (serial ports only)")

        self.trx_dtr_checkbox: QCheckBox = QCheckBox("DTR")
        self.trx_dtr_checkbox.setToolTip(
            "Hold DTR line high. Required by some rigs, e.g. Kenwood "
            "TS-480, to power the serial interface."
        )
        self.trx_rts_checkbox: QCheckBox = QCheckBox("RTS")
        self.trx_rts_checkbox.setToolTip(
            "Hold RTS line high. Required by some rigs, e.g. Kenwood "
            "TS-480, to power the serial interface."
        )

        self.trx_connect_button: QPushButton = QPushButton("Connect TRX")
        self.trx_connect_button.clicked.connect(self.connect_trx)
        self.trx_disconnect_button: QPushButton = QPushButton("Disconnect TRX")
        self.trx_disconnect_button.setObjectName("secondaryButton")
        self.trx_disconnect_button.clicked.connect(self.disconnect_trx)

        # Row: connection type selector
        conn_type_layout = QHBoxLayout()
        conn_type_layout.addWidget(QLabel("Connection:"))
        conn_type_layout.addWidget(self.trx_conn_type_combo)
        conn_type_layout.addStretch(1)

        # Row: rig model - only meaningful (and shown) in serial mode, since
        # network mode always forces NETRIGCTL.
        self.trx_model_row: QWidget = QWidget()
        model_row_layout = QHBoxLayout()
        model_row_layout.setContentsMargins(0, 0, 0, 0)
        model_row_layout.addWidget(QLabel("TRX model:"))
        model_row_layout.addWidget(self.trx_combo)
        self.trx_model_row.setLayout(model_row_layout)

        # Row: port / host:port - always shown, label text adapts to mode
        port_row_layout = QHBoxLayout()
        port_row_layout.addWidget(self.trx_port_label)
        port_row_layout.addWidget(self.trx_port_input)

        # Row: baud/DTR/RTS - serial only, fully hidden in network mode
        self.trx_serial_extra_row: QWidget = QWidget()
        serial_extra_layout = QHBoxLayout()
        serial_extra_layout.setContentsMargins(0, 0, 0, 0)
        serial_extra_layout.addWidget(QLabel("Baud:"))
        serial_extra_layout.addWidget(self.trx_baudrate_input)
        serial_extra_layout.addWidget(self.trx_dtr_checkbox)
        serial_extra_layout.addWidget(self.trx_rts_checkbox)
        self.trx_serial_extra_row.setLayout(serial_extra_layout)

        # Row: connect/disconnect buttons
        trx_button_layout = QHBoxLayout()
        trx_button_layout.addStretch(1)
        trx_button_layout.addWidget(self.trx_connect_button)
        trx_button_layout.addWidget(self.trx_disconnect_button)

        trx_group = QGroupBox("TRX Connection")
        trx_group_layout = QVBoxLayout()
        trx_group_layout.addLayout(conn_type_layout)
        trx_group_layout.addWidget(self.trx_model_row)
        trx_group_layout.addLayout(port_row_layout)
        trx_group_layout.addWidget(self.trx_serial_extra_row)
        trx_group_layout.addLayout(trx_button_layout)
        trx_group.setLayout(trx_group_layout)

        # --- Toggle button for view ---
        self.toggle_button_view: QPushButton = QPushButton("Reduce view")
        self.toggle_button_view.setObjectName("secondaryButton")
        self.toggle_button_view.setCheckable(True)
        self.toggle_button_view.setChecked(True)
        self.toggle_button_view.clicked.connect(self.toggle_view)

        # --- Sliders / controls ---
        self.L_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.L_slider.setRange(0, 127)
        self.C_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.C_slider.setRange(0, 255)
        self.HP_checkbox: QCheckBox = QCheckBox("High-pass")
        self.save_button: QPushButton = QPushButton("Save current values")
        self.delete_button: QPushButton = QPushButton("Delete selected value")
        self.delete_button.setObjectName("secondaryButton")
        self.load_json_button: QPushButton = QPushButton("Load values from JSON")
        self.load_json_button.setObjectName("secondaryButton")
        self.freq_list: QListWidget = QListWidget()

        # --- Setup mode checkbox ---
        self.setup_checkbox: QCheckBox = QCheckBox("Setup mode active")
        self.setup_checkbox.setChecked(True)
        self.setup_checkbox.toggled.connect(self.toggle_setup_mode)

        # --- L/C numeric entry, synced bidirectionally with the sliders ---
        # Keeps the original slider + live-value display, and additionally
        # allows typing an exact value directly instead of only dragging.
        self.L_value_label: QSpinBox = QSpinBox()
        self.L_value_label.setRange(0, 127)
        self.C_value_label: QSpinBox = QSpinBox()
        self.C_value_label.setRange(0, 255)
        self.L_slider.valueChanged.connect(self.L_value_label.setValue)
        self.L_value_label.valueChanged.connect(self.L_slider.setValue)
        self.C_slider.valueChanged.connect(self.C_value_label.setValue)
        self.C_value_label.valueChanged.connect(self.C_slider.setValue)

        # --- Frequency input ---
        self.freq_min_input: QLineEdit = QLineEdit()
        self.freq_min_input.setPlaceholderText("Min freq (Hz)")
        self.freq_min_input.setValidator(QIntValidator(0, 50000000))
        self.freq_max_input: QLineEdit = QLineEdit()
        self.freq_max_input.setPlaceholderText("Max freq (Hz)")
        self.freq_max_input.setValidator(QIntValidator(0, 50000000))

        # --- SBC65EC input ---
        self.sbc_ip_input: QLineEdit = QLineEdit("10.1.0.1")
        self.sbc_ip_input.setPlaceholderText("SBC65 IP")
        self.sbc_port_input: QLineEdit = QLineEdit("54123")
        self.sbc_port_input.setValidator(QIntValidator(1, 65535))
        self.sbc_port_input.setPlaceholderText("Port")
        self.connect_button: QPushButton = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_sbc)

        sbc_layout = QHBoxLayout()
        sbc_layout.addWidget(QLabel("SBC IP:"))
        sbc_layout.addWidget(self.sbc_ip_input)
        sbc_layout.addWidget(QLabel("Port:"))
        sbc_layout.addWidget(self.sbc_port_input)
        sbc_layout.addWidget(self.connect_button)

        sbc_group = QGroupBox("Tuner Interface (SBC65EC)")
        sbc_group_layout = QVBoxLayout()
        sbc_group_layout.addLayout(sbc_layout)
        sbc_group.setLayout(sbc_group_layout)

        # --- Tab: Connections ---
        connections_tab = QWidget()
        connections_layout = QVBoxLayout()
        connections_layout.addWidget(trx_group)
        connections_layout.addWidget(sbc_group)
        connections_layout.addStretch(1)
        connections_tab.setLayout(connections_layout)

        # --- Tab: Tuner Presets ---
        presets_tab = QWidget()
        presets_layout = QVBoxLayout()

        tuning_group = QGroupBox("Tuning")
        tuning_layout = QVBoxLayout()

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Min freq:"))
        freq_layout.addWidget(self.freq_min_input)
        freq_layout.addWidget(QLabel("Max freq:"))
        freq_layout.addWidget(self.freq_max_input)
        tuning_layout.addLayout(freq_layout)

        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel("L:"))
        l_layout.addWidget(self.L_slider)
        l_layout.addWidget(self.L_value_label)
        tuning_layout.addLayout(l_layout)

        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("C:"))
        c_layout.addWidget(self.C_slider)
        c_layout.addWidget(self.C_value_label)
        tuning_layout.addLayout(c_layout)

        tuning_layout.addWidget(self.HP_checkbox)

        save_layout = QHBoxLayout()
        save_layout.addStretch(1)
        save_layout.addWidget(self.save_button)
        tuning_layout.addLayout(save_layout)

        tuning_group.setLayout(tuning_layout)
        presets_layout.addWidget(tuning_group)

        list_group = QGroupBox("Saved Settings")
        list_layout = QVBoxLayout()
        list_button_layout = QHBoxLayout()
        list_button_layout.addWidget(self.delete_button)
        list_button_layout.addWidget(self.load_json_button)
        list_layout.addLayout(list_button_layout)
        list_layout.addWidget(self.freq_list)
        list_group.setLayout(list_layout)
        presets_layout.addWidget(list_group)

        presets_tab.setLayout(presets_layout)

        # --- Advanced view (collapsible via toggle_button_view) ---
        self.advanced_widget: QWidget = QWidget()
        adv_layout = QVBoxLayout()
        adv_layout.setSpacing(8)
        adv_layout.addWidget(self.setup_checkbox)

        tab_widget = QTabWidget()
        tab_widget.addTab(connections_tab, "Connections")
        tab_widget.addTab(presets_tab, "Tuner Presets")
        adv_layout.addWidget(tab_widget)

        self.advanced_widget.setLayout(adv_layout)
        self.advanced_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # --- Status container ---
        status_widget = QWidget()
        status_layout = QVBoxLayout()
        status_layout.setSpacing(6)
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_row = QHBoxLayout()
        status_row.addWidget(self.trx_status)
        status_row.addWidget(self.tuner_status)
        status_layout.addLayout(status_row)
        status_layout.addWidget(self.freq_label)
        status_widget.setLayout(status_layout)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(status_widget)
        layout.addWidget(self.toggle_button_view)
        layout.addWidget(self.advanced_widget)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- Debounce for sliders ---
        self.debounce_timer: QTimer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._send_tuner_values)

        # --- Heartbeat thread ---
        self.heartbeat_thread: HeartbeatThread = HeartbeatThread(self.tuner_service)
        self.heartbeat_thread.update_signal.connect(self.update_tuner_status)

        # --- Signals ---
        self.L_slider.valueChanged.connect(self.schedule_update)
        self.C_slider.valueChanged.connect(self.schedule_update)
        self.HP_checkbox.stateChanged.connect(self.schedule_update)
        self.save_button.clicked.connect(self.save_current)
        self.delete_button.clicked.connect(self.delete_selected)
        self.load_json_button.clicked.connect(self.load_from_json)

        # --- Status timer ---
        self.status_timer: QTimer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)

        # --- Initial mode & saved settings ---
        self._apply_mode_settings()
        self.load_list()
        self.load_saved_meta()
        self.update_status()
        self.resize(640, 600)

    # --- TRX connection ---
    def _on_trx_conn_type_changed(self):
        """
        Toggle TRX connection UI between serial (CAT) and network
        (netrigctl).

        Network mode locks the rig model to Hamlib's NETRIGCTL backend -
        the only one that speaks the rigctld wire protocol a netrigctl
        server (e.g. openALE) serves - and hides the rig-model and
        baud/DTR/RTS rows entirely, since neither applies to a TCP
        connection.
        """
        is_network = self.trx_conn_type_combo.currentData() == "network"

        self.trx_model_row.setVisible(not is_network)
        self.trx_serial_extra_row.setVisible(not is_network)

        if is_network:
            idx = self.trx_combo.findData(Hamlib.RIG_MODEL_NETRIGCTL)
            if idx >= 0:
                self.trx_combo.setCurrentIndex(idx)
            self.trx_port_label.setText("Host:Port:")
            self.trx_port_input.setPlaceholderText("host:port, e.g. localhost:4532")
        else:
            self.trx_port_label.setText("Port:")
            self.trx_port_input.setPlaceholderText("COM port, e.g. COM3")

    def connect_trx(self):
        """
        Connect to the selected TRX device using the selected model and port.
        Updates TRX status; the periodic status_timer (update_status) then
        picks up frequency and connection-liveness in a single poll.
        """
        rig_id = self.trx_combo.currentData()
        port = self.trx_port_input.text().strip()
        if not port:
            QMessageBox.warning(self, "Error", "Please enter a port or host")
            return

        conn_type = self.trx_conn_type_combo.currentData()
        is_network = conn_type == "network"

        if is_network:
            # Baud/DTR/RTS are meaningless over TCP; Hamlib ignores them for
            # network pathnames anyway, but keep the values inert here too.
            baudrate = 0
            dtr_state = "UNSET"
            rts_state = "UNSET"
        else:
            try:
                baudrate = int(self.trx_baudrate_input.currentText().strip())
            except ValueError:
                QMessageBox.warning(self, "Error", "Baud rate must be a number")
                return

            # Only forced "ON" when requested; otherwise left "UNSET" so Hamlib
            # doesn't touch the line (matches previous behavior for rigs that
            # don't need this).
            dtr_state = "ON" if self.trx_dtr_checkbox.isChecked() else "UNSET"
            rts_state = "ON" if self.trx_rts_checkbox.isChecked() else "UNSET"

        connected = self.trx_service.connect(
            rig_id=rig_id, port=port, baudrate=baudrate,
            dtr_state=dtr_state, rts_state=rts_state
        )

        if connected:
            self.settings_service.set_trx_config(
                rig_id, port, baudrate, dtr_state, rts_state, conn_type
            )
            self.settings_service.save()
            self.trx_status.setText(f"TRX: ✅ connected ({self.trx_combo.currentText()})")
        else:
            self.trx_status.setText("TRX: ❌ connection failed")

    def disconnect_trx(self):
        """
        Closes the current TRX connection (serial or netrigctl/TCP) and
        frees the underlying port so it can be reused, e.g. by another
        application or a new connect attempt with different settings.
        """
        self.trx_service.close()
        self.trx_status.setText("TRX: ❌ not connected")

    # --- Status & frequency range ---
    def _update_freq_label(self, freq: int, show_warning: bool, blink_on: bool = True):
        """
        Update freq_label with current frequency and optional warning icon.

        Warning appears right-aligned inside the same label. Background color
        adapts to setup mode and blinks if the warning is active.

        Skips the actual re-render (HTML rebuild + stylesheet reapply) when
        nothing about the displayed state has changed since the last call,
        to avoid needless work on the 500ms status timer while idle.
        """
        cache_key = (int(freq), show_warning, self._blink_state if show_warning else False, self.setup_mode)
        if self._freq_label_cache_key == cache_key:
            return
        self._freq_label_cache_key = cache_key

        base_text = f"Freq: {int(freq)} Hz"

        if show_warning and self._blink_state:
            style = _status_style("warning")
        else:
            style = _status_style("setup" if self.setup_mode else "active")

        if show_warning and blink_on:
            warning_html = '<span>&#9888; Warning: no corresponding frequency found</span>'
        else:
            warning_html = ""

        html = f"""
        <div style="display:flex; justify-content: space-between; align-items: center;">
            <span>{base_text}</span>
            <span>{warning_html}</span>
        </div>
        """

        self.freq_label.setTextFormat(Qt.TextFormat.RichText)
        self.freq_label.setText(html)
        self.freq_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.freq_label.setStyleSheet(style)

    def _toggle_blink(self):
        """
        Toggle blinking of the warning and background in freq_label.
        """
        self._blink_state = not self._blink_state
        self._update_freq_label(self._last_freq, self._last_show_warning, blink_on=self._blink_state)

    def update_status(self):
        """
        Update the TRX status and currently tuned frequency.
        Applies active tuner settings if not in setup mode.
        Handles connection state changes gracefully.
        Also manages the blinking "no matching frequency entry" warning.

        Issues exactly one Hamlib frequency query per tick. Connection loss
        is detected from that same query (get_frequency() updates the
        service's cached connection state internally on failure) instead of
        a separate, redundant liveness probe.
        """
        trx_connected = False
        freq = 0
        try:
            trx_connected = self.trx_service.is_connected()

            if trx_connected:
                freq = self.trx_service.get_frequency()
                if freq is None:
                    freq = 0
                    trx_connected = self.trx_service.is_connected()

                rig_name = self.trx_combo.currentText()
                self.trx_status.setText(
                    f"TRX: ✅ connected to {rig_name}" if trx_connected
                    else "TRX: ❌ connection lost"
                )
            else:
                self.trx_status.setText("TRX: ❌ not connected")

        except Exception as e:
            print(f"Error updating TRX status: {e}")
            self.trx_status.setText("TRX: ❌ error")

        show_warning = False
        if not self.setup_mode and trx_connected:
            entry = self.settings_service.get_for_frequency(freq)
            if entry != self._active_entry:
                self._active_entry = entry
                if entry:
                    self.L_slider.blockSignals(True)
                    self.C_slider.blockSignals(True)
                    self.HP_checkbox.blockSignals(True)
                    self.L_value_label.blockSignals(True)
                    self.C_value_label.blockSignals(True)
                    self.L_slider.setValue(entry["L"])
                    self.C_slider.setValue(entry["C"])
                    self.HP_checkbox.setChecked(entry["highpass"])
                    self.L_value_label.setValue(entry["L"])
                    self.C_value_label.setValue(entry["C"])
                    self._send_tuner_values()
                    self.L_slider.blockSignals(False)
                    self.C_slider.blockSignals(False)
                    self.HP_checkbox.blockSignals(False)
                    self.L_value_label.blockSignals(False)
                    self.C_value_label.blockSignals(False)
            if not entry:
                show_warning = True

        self._last_freq = freq
        self._last_show_warning = show_warning
        self._update_freq_label(freq, show_warning)

        if show_warning:
            if not self.blink_timer.isActive():
                self._blink_state = True
                self.blink_timer.start(500)
        else:
            self.blink_timer.stop()
            self._blink_state = False

    # --- Common tuner status logic ---
    def _set_tuner_status(self, reachable: bool, ip: Optional[str] = None, port: Optional[int] = None, initial_try: bool = False):
        """
        Update the tuner status label based on reachability.

        Args:
            reachable (bool): Whether the tuner is reachable.
            ip (str, optional): IP address of the tuner. Defaults to tuner's host.
            port (int, optional): Port of the tuner. Defaults to tuner's port.
            initial_try (bool, optional): Indicates if this is the initial connection attempt.
        """
        ip = ip or self.tuner_service.host
        port = port or self.tuner_service.port

        if reachable:
            self.tuner_status.setText(f"Tuner: ✅ reachable at {ip}:{port}")
            self.connected_once = True
        else:
            if self.connected_once:
                self.tuner_status.setText(f"Tuner: ❌ connection to {ip}:{port} lost")
            else:
                if initial_try:
                    self.tuner_status.setText(f"Tuner: ❌ connection to {ip}:{port} failed")
                else:
                    self.tuner_status.setText(f"Tuner: ❌ not reachable")

    def update_tuner_status(self, reachable: bool):
        """
        Update tuner status label from heartbeat thread.

        Args:
            reachable (bool): Whether the tuner is reachable.
        """
        self._set_tuner_status(reachable)

    # --- Setup mode ---
    def toggle_setup_mode(self, checked: bool):
        """
        Enable or disable setup mode.

        Args:
            checked (bool): True if setup mode should be active.
        """
        self.setup_mode = checked
        self._apply_mode_settings()

    def _apply_mode_settings(self):
        """
        Apply UI changes based on setup mode.
        Enables/disables relevant widgets and adjusts style.
        """
        for w in [self.L_slider, self.C_slider, self.HP_checkbox,
                  self.L_value_label, self.C_value_label,
                  self.freq_min_input, self.freq_max_input,
                  self.save_button, self.delete_button,
                  self.load_json_button, self.freq_list]:
            w.setEnabled(self.setup_mode)

        self.setup_checkbox.setText("Setup mode active" if self.setup_mode else "Setup mode")
        style = _status_style("setup" if self.setup_mode else "active")
        self.trx_status.setStyleSheet(style)
        self.tuner_status.setStyleSheet(style)
        # Force freq_label to re-render even if freq/warning didn't change,
        # since the setup-mode color is part of its cache key.
        self._freq_label_cache_key = None
        self._update_freq_label(self._last_freq, self._last_show_warning)

    # --- View toggle ---
    def toggle_view(self):
        """
        Expand or reduce the advanced view section.
        """
        if self.toggle_button_view.isChecked():
            self.advanced_widget.show()
            self.setup_checkbox.show()
            self.toggle_button_view.setText("Reduce view")
            self.setMinimumHeight(200)
            self.setMaximumHeight(1000)
            self.resize(640, 600)
        else:
            self.advanced_widget.hide()
            self.setup_checkbox.hide()
            self.toggle_button_view.setText("Expand view")
            self.setFixedHeight(140)

    # --- Debounce ---
    def schedule_update(self):
        """
        Schedule sending tuner values after a short debounce interval.
        """
        if self.setup_mode:
            self.debounce_timer.start(50)

    # --- Send values ---
    def _send_tuner_values(self):
        """
        Send current L, C, and HP values to tuner if reachable.
        """
        if self.tuner_service.is_reachable():
            l_val = self.L_slider.value()
            c_val = self.C_slider.value()
            hp_val = self.HP_checkbox.isChecked()
            self.tuner_service.send_values(l_val, c_val, hp_val)

    # --- Save / delete / JSON ---
    def save_current(self):
        """
        Save current frequency settings and update TRX/SBC configuration.
        """
        if not self.setup_mode:
            return

        # Get values from GUI
        min_freq = int(self.freq_min_input.text()) if self.freq_min_input.text() else 0
        max_freq = int(self.freq_max_input.text()) if self.freq_max_input.text() else 0
        l_val = self.L_slider.value()
        c_val = self.C_slider.value()
        hp_val = self.HP_checkbox.isChecked()

        # Save to settings service
        self.settings_service.add_entry(min_freq, max_freq, l_val, c_val, hp_val)
        self.settings_service.save()

        # Refresh list
        self.load_list()

    def delete_selected(self):
        """
        Delete currently selected frequency entry.
        """
        if not self.setup_mode:
            return

        current_row = self.freq_list.currentRow()
        if current_row >= 0:
            self.settings_service.delete_entry(current_row)
            self.settings_service.save()
            self.load_list()

    def load_from_json(self):
        """
        Load frequency settings from a JSON file.
        """
        if not self.setup_mode:
            return

        # Implementation remains the same but uses service
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Settings", "", "JSON Files (*.json)"
        )
        if filename:
            self.settings_service.load_from_json(filename)
            self.load_list()

    def load_list(self):
        """
        Refresh the list widget with current frequency entries.
        """
        self.freq_list.clear()
        for entry in self.settings_service.data:
            self.freq_list.addItem(
                f"{entry['min_freq']}-{entry['max_freq']} Hz: L={entry['L']}, C={entry['C']}, HP={entry['highpass']}"
            )


    # --- SBC connection ---
    def connect_to_sbc(self):
        """
        Connect to the SBC65EC device using IP and port input fields.
        Starts heartbeat thread if reachable.
        """
        ip = self.sbc_ip_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Please enter an IP address")
            return
        try:
            port = int(self.sbc_port_input.text())
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Port must be a number between 1 and 65535")
            return

        self.tuner_service.set_host_port(ip, port)

        reachable = self.tuner_service.check_reachability(timeout=0.5)
        self._set_tuner_status(reachable, ip, port, initial_try=True)

        if reachable and not self.heartbeat_thread.isRunning():
            self.heartbeat_thread.start()

    # --- Load saved TRX + SBC settings ---
    def load_saved_meta(self):
        """
        Load saved TRX and SBC settings into UI fields.
        """
        # Use service to get settings
        self.sbc_ip_input.setText(self.settings_service.sbc_ip)
        self.sbc_port_input.setText(str(self.settings_service.sbc_port))

        conn_type = self.settings_service.trx_conn_type
        conn_index = self.trx_conn_type_combo.findData(conn_type)
        if conn_index >= 0:
            self.trx_conn_type_combo.setCurrentIndex(conn_index)
        # Explicit call: setCurrentIndex only emits currentIndexChanged when
        # the index actually changes, so this also covers the default case.
        self._on_trx_conn_type_changed()

        # Network mode always forces rig model to NETRIGCTL (see above), so
        # only restore a saved rig model when in serial mode.
        if conn_type != "network":
            index = self.trx_combo.findData(self.settings_service.trx_id)
            if index >= 0:
                self.trx_combo.setCurrentIndex(index)

        self.trx_port_input.setText(self.settings_service.trx_port)
        self.trx_baudrate_input.setCurrentText(str(self.settings_service.trx_baudrate))
        self.trx_dtr_checkbox.setChecked(self.settings_service.trx_dtr_state == "ON")
        self.trx_rts_checkbox.setChecked(self.settings_service.trx_rts_state == "ON")
