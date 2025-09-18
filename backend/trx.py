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

import Hamlib

class TRX:
    def __init__(self, rig_id=None, port="localhost:19090", baudrate=115200,
                 databits=8, parity='N', stopbits=1, dummy=False):
        """
        TRX Interface via Hamlib (seriell oder Netzwerk) oder Dummy-Modus.
        """
        self.dummy = dummy
        self.connected = False
        self._freq = 5351000  # Dummy Start-Frequenz 5.351 MHz

        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

        if not self.dummy:
            # Rig-ID standardmäßig auf FlexRadio/PowerSDR, falls None
            self.rig_id = rig_id if rig_id is not None else 2048
            self.rig = Hamlib.Rig(self.rig_id)
            self.port = port
            self.rig.set_conf("rig_pathname", port)
            
            # Serielle Einstellungen nur bei echten COM-Ports
            if ":" not in port:  # Netzwerkport enthält ":"
                self.rig.set_conf("baudrate", str(baudrate))
                self.rig.set_conf("data_bits", str(databits))
                self.rig.set_conf("parity", parity)
                self.rig.set_conf("stop_bits", str(stopbits))

    @staticmethod
    def list_available_rigs():
        """Gibt eine Liste aller bekannten Hamlib-Rigs zurück,
        wobei der Präfix 'RIG_MODEL_' entfernt wird."""
        rig_models = [
            (name.replace("RIG_MODEL_", ""), getattr(Hamlib, name))
            for name in dir(Hamlib)
            if name.startswith("RIG_MODEL_")
        ]
        return rig_models



    def connect(self):
        """Öffnet die Verbindung zum Transceiver (oder Dummy)"""
        if self.dummy:
            self.connected = True
            print("Dummy TRX connected")
        else:
            try:
                self.rig.open()
                self.connected = True
                print(f"TRX connected: {self.port}")
            except Exception as e:
                self.connected = False
                print(f"Fehler beim TRX connect: {e}")

    def get_frequency(self):
        """Liest die aktuelle Frequenz aus"""
        if self.dummy:
            return self._freq
        else:
            if not self.connected:
                raise RuntimeError("TRX nicht verbunden")
            try:
                freq = self.rig.get_freq()
                return freq
            except Exception as e:
                print(f"Fehler beim Auslesen der Frequenz: {e}")
                return None

    def close(self):
        """Schließt die Verbindung"""
        if not self.dummy and self.connected:
            self.rig.close()
            self.connected = False
            print("TRX connection closed")

def main():
    rigs = TRX.list_available_rigs()
    print("Gefundene Rigs:")
    for name, rig_id in rigs:
        print(f"- {name}: {rig_id}")

if __name__ == "__main__":
    main()
