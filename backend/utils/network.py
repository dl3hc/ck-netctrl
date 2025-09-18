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

import socket
import subprocess
import platform
from shutil import which

def ping_icmp(ip: str, timeout: float = 1.0, attempts: int = 3) -> bool:
    """
    Performs a standard ICMP ping to a target IP address.
    
    On Windows, it uses the system ping binary or socket-based approach.
    On Linux, it uses /bin/ping. Works without root privileges if packet size is adjusted.

    Args:
        ip (str): The target IP address to ping.
        timeout (float, optional): Timeout for each ping attempt in seconds. Defaults to 1.0.
        attempts (int, optional): Number of ping attempts. Defaults to 3.

    Returns:
        bool: True if the host responds to ping within the given attempts, False otherwise.
    """
    system = platform.system().lower()
    count_flag = "-n" if system == "windows" else "-c"
    timeout_flag = "-w" if system == "windows" else "-W"
    
    # Timeout: Windows -> ms, Linux -> seconds (float)
    timeout_value = int(timeout * 1000) if system == "windows" else timeout

    # Locate ping binary
    ping_bin = which("ping") or ("/bin/ping" if system != "windows" else "ping")

    # Adjust packet size for Linux to reach certain devices like SBC65EC
    size_flag = "-l" if system == "windows" else "-s"
    packet_size = "32" if system != "windows" else "32"  # Windows default 32 bytes

    for _ in range(attempts):
        try:
            ping_cmd = [
                ping_bin,
                count_flag, "1",
                timeout_flag, str(timeout_value),
                size_flag, packet_size,
                ip
            ]
            result = subprocess.run(
                ping_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                return True
        except Exception:
            continue
    return False

def send_udp(ip: str, port: int, data: bytes, timeout=1.0) -> bool:
    """
    Sends a UDP packet to a specified IP and port.

    Args:
        ip (str): Target IP address.
        port (int): Target UDP port.
        data (bytes): Data payload to send.
        timeout (float, optional): Socket timeout in seconds. Defaults to 1.0.

    Returns:
        bool: True if the packet was sent successfully, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(data, (ip, port))
        return True
    except Exception:
        return False
