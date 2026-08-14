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
from typing import List, Dict, Optional

class SettingsService(ABC):
    """Interface for settings management services."""
    
    @abstractmethod
    def load(self) -> None:
        """Load settings from the JSON file."""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Save current settings to the JSON file."""
        pass
    
    @abstractmethod
    def get_for_frequency(self, freq: float) -> Optional[Dict]:
        """Retrieve the settings entry for a specific frequency."""
        pass
    
    @abstractmethod
    def add_entry(self, min_freq: float, max_freq: float, L: float, C: float, highpass: bool) -> None:
        """Add a new frequency entry to the settings."""
        pass
    
    @abstractmethod
    def delete_entry(self, index: int) -> None:
        """Delete a frequency entry by index."""
        pass
    
    @abstractmethod
    def get_entries(self) -> List[Dict]:
        """Get all frequency entries."""
        pass
    
    @abstractmethod
    def set_sbc_config(self, ip: str, port: int) -> None:
        """Set SBC configuration."""
        pass
    
    @abstractmethod
    def set_trx_config(self, rig_id: Optional[int], port: str, baudrate: int = 9600,
                        dtr_state: str = "UNSET", rts_state: str = "UNSET",
                        conn_type: str = "serial") -> None:
        """Set TRX configuration."""
        pass