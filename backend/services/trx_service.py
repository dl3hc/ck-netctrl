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
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

class TRXService(ABC):
    """Interface for transceiver communication services."""
    
    @abstractmethod
    def list_available_rigs(self) -> List[Tuple[str, int]]:
        """Returns a list of all rigs known to Hamlib."""
        pass
    
    @abstractmethod
    def connect(self, rig_id: Optional[int], port: str, baudrate: int = 9600,
                dtr_state: str = "UNSET", rts_state: str = "UNSET") -> bool:
        """
        Connects to the transceiver.

        Args:
            rig_id: Hamlib rig ID.
            port: COM port (serial) or "host:port" (network).
            baudrate: Serial baud rate. Ignored for network ports.
            dtr_state: DTR line state for serial ports ("ON", "OFF" or "UNSET").
                Some rigs (e.g. Kenwood TS-480) need DTR held high to power
                the serial interface / respond at all.
            rts_state: RTS line state for serial ports ("ON", "OFF" or "UNSET").
        """
        pass
    
    @abstractmethod
    def get_frequency(self) -> Optional[int]:
        """Reads the current frequency from the TRX."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if the TRX is connected."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Closes the connection to the TRX."""
        pass