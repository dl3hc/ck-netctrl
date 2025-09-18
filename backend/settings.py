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

class Settings:
    """
    Manages the configuration settings for the Christian-Koppler Control Software.

    Attributes:
        filename (str): Path to the JSON settings file.
        data (list): List of frequency entries.
        sbc_ip (str): IP address of the SBC (Single Board Computer).
        sbc_port (int): Port of the SBC.
        trx_id (str|None): ID of the transceiver.
        trx_port (str): Address of the transceiver.
    """

    def __init__(self, filename="settings.json"):
        """
        Initializes the Settings object and loads settings from a file.

        Args:
            filename (str): Optional path to the JSON settings file. Defaults to "settings.json".
        """
        self.filename = filename
        self.data = []       # Frequency entries
        self.sbc_ip = "10.1.0.1"
        self.sbc_port = 54123
        self.trx_id = None
        self.trx_port = "localhost:19090"
        self.load()

    def load(self):
        """
        Loads settings from the JSON file. If the file does not exist, defaults are used.
        """
        try:
            with open(self.filename, "r") as f:
                obj = json.load(f)
            self.data = obj.get("frequencies", [])
            self.sbc_ip = obj.get("sbc_ip", self.sbc_ip)
            self.sbc_port = obj.get("sbc_port", self.sbc_port)
            self.trx_id = obj.get("trx_id", self.trx_id)
            self.trx_port = obj.get("trx_port", self.trx_port)
        except FileNotFoundError:
            self.data = []

    def load_from_json(self, filename=None):
        """
        Loads settings from a specified JSON file.

        Args:
            filename (str|None): Optional path to a JSON file. If None, uses the current filename.
        """
        if filename:
            self.filename = filename
        self.load()

    def save(self):
        """
        Saves the current settings to the JSON file.
        """
        obj = {
            "frequencies": self.data,
            "sbc_ip": self.sbc_ip,
            "sbc_port": self.sbc_port,
            "trx_id": self.trx_id,
            "trx_port": self.trx_port
        }
        print(">>> Saving to:", os.path.abspath(self.filename))
        with open(self.filename, "w") as f:
            json.dump(obj, f, indent=2)

    def get_for_frequency(self, freq):
        """
        Retrieves the settings entry corresponding to a specific frequency.

        Args:
            freq (float): The frequency to search for.

        Returns:
            dict|None: The matching frequency entry if found, otherwise None.
        """
        for entry in self.data:
            if entry["min_freq"] <= freq <= entry["max_freq"]:
                return entry
        return None

    def add_entry(self, min_freq, max_freq, L, C, highpass):
        """
        Adds a new frequency entry to the settings.

        Args:
            min_freq (float): Minimum frequency of the entry.
            max_freq (float): Maximum frequency of the entry.
            L (float): Inductance value for the entry.
            C (float): Capacitance value for the entry.
            highpass (bool): Indicates if the entry uses a high-pass filter.
        """
        self.data.append({
            "min_freq": min_freq,
            "max_freq": max_freq,
            "L": L,
            "C": C,
            "highpass": highpass
        })
