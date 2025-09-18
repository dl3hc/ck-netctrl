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

from backend.messages import build_messages
from backend.utils import network

class SBC65EC:
    """
    Controller for the SBC65EC tuner over UDP.

    Provides methods to:
    - Check device reachability
    - Send tuning values (L, C, Highpass)
    """

    def __init__(self, host: str = "10.1.0.1", port: int = 54123, debug: bool = False):
        """
        Initialize the SBC65EC controller.

        Args:
            host (str): IP address of the SBC65EC device. Defaults to "10.1.0.1".
            port (int): UDP port used for communication. Defaults to 54123.
            debug (bool): Enable debug output. Defaults to False.
        """
        self.host = host
        self.port = port
        self.debug = debug

        self.reachable = False
        self.last_l_value = -1
        self.last_c_value = -1
        self.last_hp_value = None

    # --- Check device reachability ---
    def check_reachability(self, timeout: float = 0.5) -> bool:
        """
        Check if the SBC65EC device is reachable via ICMP ping.

        Args:
            timeout (float): Maximum time to wait for a response in seconds. Defaults to 0.5.

        Returns:
            bool: True if the device responds to ping, False otherwise.
        """
        self.reachable = network.ping_icmp(self.host, timeout=timeout)
        if self.debug:
            if self.reachable:
                print(f"[INFO] SBC65EC {self.host}:{self.port} is reachable")
            else:
                print(f"[WARN] SBC65EC {self.host}:{self.port} is not reachable")
        return self.reachable

    # --- Send tuning values ---
    def send_values(self, l_value: int, c_value: int, highpass: bool):
        """
        Send tuning values (L, C, Highpass) to the SBC65EC device over UDP.

        Only sends values if they have changed since the last transmission
        and if the device is reachable.

        Args:
            l_value (int): Inductance value to set.
            c_value (int): Capacitance value to set.
            highpass (bool): Whether the highpass filter is enabled.
        """
        if not self.reachable:
            if self.debug:
                print("[DEBUG] Device not reachable → values not sent")
            return

        # Only send if values have changed
        if (l_value == self.last_l_value and
            c_value == self.last_c_value and
            highpass == self.last_hp_value):
            return

        self.last_l_value = l_value
        self.last_c_value = c_value
        self.last_hp_value = highpass

        # Build messages
        msg_a, msg_b, msg_c1, msg_c2 = build_messages(l_value, c_value, highpass)
        full_msg = msg_a + msg_b + msg_c1 + msg_c2

        if self.debug:
            print(f"[DEBUG] Sending to SBC65EC {self.host}:{self.port}")
            print(f"  Message: {full_msg.decode(errors='ignore')}")

        network.send_udp(self.host, self.port, full_msg)
