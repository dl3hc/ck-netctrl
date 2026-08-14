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
import json
import os
from typing import List, Dict, Optional
from backend.services.settings_service import SettingsService

class SettingsServiceImpl(SettingsService):
    """Concrete implementation of settings service."""
    
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.data = []       # Frequency entries
        self.sbc_ip = "10.1.0.1"
        self.sbc_port = 54123
        self.trx_id = None
        self.trx_port = "localhost:19090"
        self.trx_baudrate = 9600
        self.trx_dtr_state = "UNSET"
        self.trx_rts_state = "UNSET"
        self.load()
    
    def load(self) -> None:
        """Load settings from the JSON file."""
        try:
            with open(self.filename, "r") as f:
                obj = json.load(f)
            self.data = obj.get("frequencies", [])
            self.sbc_ip = obj.get("sbc_ip", self.sbc_ip)
            self.sbc_port = obj.get("sbc_port", self.sbc_port)
            self.trx_id = obj.get("trx_id", self.trx_id)
            self.trx_port = obj.get("trx_port", self.trx_port)
            self.trx_baudrate = obj.get("trx_baudrate", self.trx_baudrate)
            self.trx_dtr_state = obj.get("trx_dtr_state", self.trx_dtr_state)
            self.trx_rts_state = obj.get("trx_rts_state", self.trx_rts_state)
        except FileNotFoundError:
            self.data = []

    def save(self) -> None:
        """Save current settings to the JSON file."""
        obj = {
            "frequencies": self.data,
            "sbc_ip": self.sbc_ip,
            "sbc_port": self.sbc_port,
            "trx_id": self.trx_id,
            "trx_port": self.trx_port,
            "trx_baudrate": self.trx_baudrate,
            "trx_dtr_state": self.trx_dtr_state,
            "trx_rts_state": self.trx_rts_state
        }
        print(">>> Saving to:", os.path.abspath(self.filename))
        with open(self.filename, "w") as f:
            json.dump(obj, f, indent=2)
    
    def get_for_frequency(self, freq: float) -> Optional[Dict]:
        """Retrieve the settings entry for a specific frequency."""
        for entry in self.data:
            if entry["min_freq"] <= freq <= entry["max_freq"]:
                return entry
        return None
    
    def add_entry(self, min_freq: float, max_freq: float, L: float, C: float, highpass: bool) -> None:
        """Add a new frequency entry to the settings."""
        self.data.append({
            "min_freq": min_freq,
            "max_freq": max_freq,
            "L": L,
            "C": C,
            "highpass": highpass
        })
    
    def delete_entry(self, index: int) -> None:
        """Delete a frequency entry by index."""
        if 0 <= index < len(self.data):
            self.data.pop(index)
    
    def get_entries(self) -> List[Dict]:
        """Get all frequency entries."""
        return self.data
    
    def set_sbc_config(self, ip: str, port: int) -> None:
        """Set SBC configuration."""
        self.sbc_ip = ip
        self.sbc_port = port
    
    def set_trx_config(self, rig_id: int, port: str, baudrate: int = 9600,
                        dtr_state: str = "UNSET", rts_state: str = "UNSET") -> None:
        """Set TRX configuration."""
        self.trx_id = rig_id
        self.trx_port = port
        self.trx_baudrate = baudrate
        self.trx_dtr_state = dtr_state
        self.trx_rts_state = rts_state