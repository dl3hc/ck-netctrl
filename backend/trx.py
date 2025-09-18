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
        Initializes a TRX object for accessing a transceiver.

        Supports real devices via Hamlib (serial or network) or a dummy mode
        for testing purposes.

        Args:
            rig_id (int, optional): Hamlib rig ID. Default: 2048 (FlexRadio/PowerSDR).
            port (str, optional): COM port or network address of the TRX. Default: "localhost:19090".
            baudrate (int, optional): Baud rate for serial connection. Default: 115200.
            databits (int, optional): Number of data bits for serial connection. Default: 8.
            parity (str, optional): Parity for serial connection ('N', 'E', 'O'). Default: 'N'.
            stopbits (int, optional): Number of stop bits for serial connection. Default: 1.
            dummy (bool, optional): Enables dummy mode without real hardware. Default: False.

        Attributes:
            dummy (bool): Indicates if dummy mode is active.
            connected (bool): True if the TRX is connected.
            _freq (int): Current frequency in dummy mode (Hz).
            rig (Hamlib.Rig): Hamlib rig object (only if dummy=False).
            rig_id (int): Hamlib rig ID.
            port (str): Connection port.
        """
        self.dummy = dummy
        self.connected = False
        self._freq = 5351000  # Dummy start frequency 5.351 MHz

        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

        if not self.dummy:
            # Default rig ID to FlexRadio/PowerSDR if None
            self.rig_id = rig_id if rig_id is not None else 2048
            self.rig = Hamlib.Rig(self.rig_id)
            self.port = port
            self.rig.set_conf("rig_pathname", port)
            
            # Serial settings only for real COM ports
            if ":" not in port:  # Network port contains ":"
                self.rig.set_conf("baudrate", str(baudrate))
                self.rig.set_conf("data_bits", str(databits))
                self.rig.set_conf("parity", parity)
                self.rig.set_conf("stop_bits", str(stopbits))

    @staticmethod
    def list_available_rigs():
        """
        Returns a list of all rigs known to Hamlib.

        The prefix 'RIG_MODEL_' is removed from the names.

        Returns:
            list of tuple: List of (name, Hamlib rig ID)
        """
        rig_models = [
            (name.replace("RIG_MODEL_", ""), getattr(Hamlib, name))
            for name in dir(Hamlib)
            if name.startswith("RIG_MODEL_")
        ]
        return rig_models

    def connect(self):
        """
        Opens the connection to the transceiver.

        In dummy mode, the connection is simulated.

        Raises:
            Exception: If connection to a real TRX fails.
        """
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
                print(f"Error connecting to TRX: {e}")

    def get_frequency(self):
        """
        Reads the current frequency from the TRX.

        Returns:
            int: Frequency in Hz (dummy mode: stored dummy frequency)
            None: On error reading frequency.
        
        Raises:
            RuntimeError: If TRX is not connected.
        """
        if self.dummy:
            return self._freq
        else:
            if not self.connected:
                raise RuntimeError("TRX not connected")
            try:
                freq = self.rig.get_freq()
                return freq
            except Exception as e:
                print(f"Error reading frequency: {e}")
                return None

    def close(self):
        """
        Closes the connection to the TRX.

        Does nothing in dummy mode.
        """
        if not self.dummy and self.connected:
            self.rig.close()
            self.connected = False
            print("TRX connection closed")


# def main():
#     """
#     Testet die TRX-Klasse, indem alle verfügbaren Rigs aufgelistet werden.
#     """
#     rigs = TRX.list_available_rigs()
#     print("Gefundene Rigs:")
#     for name, rig_id in rigs:
#         print(f"- {name}: {rig_id}")
# 
# if __name__ == "__main__":
#     main()
# 