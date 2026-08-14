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

class TunerService(ABC):
    """Interface for tuner control services."""
    
    @abstractmethod
    def check_reachability(self, timeout: float = 0.5) -> bool:
        """Check if the tuner is reachable."""
        pass
    
    @abstractmethod
    def send_values(self, l_value: int, c_value: int, highpass: bool) -> None:
        """Send tuning values to the tuner."""
        pass
    
    @abstractmethod
    def is_reachable(self) -> bool:
        """Returns True if the tuner is reachable."""
        pass
    
    @abstractmethod
    def set_host_port(self, host: str, port: int) -> None:
        """Set the host and port for communication."""
        pass