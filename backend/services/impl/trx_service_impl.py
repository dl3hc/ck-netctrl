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
from typing import List, Tuple, Optional
from backend.services.trx_service import TRXService

class TRXServiceImpl(TRXService):
    """Concrete implementation of TRX service using Hamlib."""
    
    def __init__(self):
        self._rig = None
        self._connected = False
        self._freq = 5351000  # Dummy start frequency 5.351 MHz
        
        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
    
    def list_available_rigs(self) -> List[Tuple[str, int]]:
        """Returns a list of all rigs known to Hamlib."""
        rig_models = [
            (name.replace("RIG_MODEL_", ""), getattr(Hamlib, name))
            for name in dir(Hamlib)
            if name.startswith("RIG_MODEL_")
        ]
        return rig_models
    
    def connect(self, rig_id: Optional[int], port: str, baudrate: int = 9600,
                dtr_state: str = "UNSET", rts_state: str = "UNSET") -> bool:
        """Connects to the transceiver."""
        try:
            self._rig = Hamlib.Rig(rig_id if rig_id is not None else 2048)
            self._rig.set_conf("rig_pathname", port)

            # Serial settings only for real COM ports
            if ":" not in port:  # Network port contains ":"
                self._rig.set_conf("serial_speed", str(baudrate))
                self._rig.set_conf("data_bits", "8")
                self._rig.set_conf("serial_parity", "None")
                self._rig.set_conf("stop_bits", "1")
                # Some rigs (e.g. Kenwood TS-480) need DTR/RTS held high to
                # power the serial interface / respond at all.
                if dtr_state != "UNSET":
                    self._rig.set_conf("dtr_state", dtr_state)
                if rts_state != "UNSET":
                    self._rig.set_conf("rts_state", rts_state)

            self._rig.open()
            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            print(f"Error connecting to TRX: {e}")
            return False
    
    def get_frequency(self) -> Optional[int]:
        """Reads the current frequency from the TRX."""
        if not self._connected:
            raise RuntimeError("TRX not connected")
        
        try:
            freq = self._rig.get_freq()
            return freq
        except Exception as e:
            print(f"Error reading frequency: {e}")
            # On error, assume connection is lost and update state
            self._connected = False
            return None
    
    def is_connected(self) -> bool:
        """
        Returns True if the TRX is connected.

        Returns the cached connection state rather than actively probing
        the rig. Liveness is instead verified as a side effect of
        get_frequency(), which clears the cached state on failure - this
        avoids issuing a redundant Hamlib query on every check.
        """
        return self._connected
    
    def close(self) -> None:
        """Closes the connection to the TRX."""
        if self._rig and self._connected:
            self._rig.close()
            self._connected = False