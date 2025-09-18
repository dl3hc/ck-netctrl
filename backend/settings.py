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
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.data = []       # Frequenz-Einträge
        self.sbc_ip = "10.1.0.1"
        self.sbc_port = 54123
        self.trx_id = None
        self.trx_port = "localhost:19090"
        self.load()

    def load(self):
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
        if filename:
            self.filename = filename
        self.load()

    def save(self):
        obj = {
            "frequencies": self.data,
            "sbc_ip": self.sbc_ip,
            "sbc_port": self.sbc_port,
            "trx_id": self.trx_id,
            "trx_port": self.trx_port
        }
        print(">>> Speichere nach:", os.path.abspath(self.filename))
        with open(self.filename, "w") as f:
            json.dump(obj, f, indent=2)


    def get_for_frequency(self, freq):
        for entry in self.data:
            if entry["min_freq"] <= freq <= entry["max_freq"]:
                return entry
        return None

    def add_entry(self, min_freq, max_freq, L, C, highpass):
        self.data.append({
            "min_freq": min_freq,
            "max_freq": max_freq,
            "L": L,
            "C": C,
            "highpass": highpass
        })
