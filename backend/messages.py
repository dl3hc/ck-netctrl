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

def build_messages(val_l: int, val_c: int, highpass: bool):
    """
    Baut alle Nachrichten für den SBC65EC basierend auf L, C und Hoch/Tiefpass.
    val_l: 0–127 (L-Bank)
    val_c: 0–255 (C-Bank)
    highpass: True = Highpass, False = Tiefpass
    """

    # --- msg_a: L-Bank L1-L6 (RA0-RA5) ---
    msg_a = bytearray(6 * 5)  # 6 Kanäle, je 5 Bytes
    for i in range(6):
        msg_a[i * 5] = ord('a')
        msg_a[i * 5 + 1] = ord(str(i))
        msg_a[i * 5 + 2] = ord('=')
        msg_a[i * 5 + 3] = ord('1') if (val_l & (1 << i)) else ord('0')
        msg_a[i * 5 + 4] = ord('&')

    # --- msg_b: letzter L-Wert (RB0) + C0-C4 (RB1-RB5) ---
    msg_b = bytearray(5 * 5)
    # RB0 = letzter L-Wert (L7)
    msg_b[0] = ord('b')
    msg_b[1] = ord('0')
    msg_b[2] = ord('=')
    msg_b[3] = ord('1') if (val_l & (1 << 6)) else ord('0')
    msg_b[4] = ord('&')

    # RB1-RB5 = C0-C4
    for i in range(1, 5):
        msg_b[i * 5] = ord('b')
        msg_b[i * 5 + 1] = ord(str(i))
        msg_b[i * 5 + 2] = ord('=')
        msg_b[i * 5 + 3] = ord('1') if (val_c & (1 << (i - 1))) else ord('0')
        msg_b[i * 5 + 4] = ord('&')

    # --- msg_c1: C5-C7 (RC0-RC2) ---
    msg_c1 = bytearray(3 * 5)
    for j in range(3):
        msg_c1[j * 5] = ord('c')
        msg_c1[j * 5 + 1] = ord(str(j))
        msg_c1[j * 5 + 2] = ord('=')
        msg_c1[j * 5 + 3] = ord('1') if (val_c & (1 << (j + 5))) else ord('0')
        msg_c1[j * 5 + 4] = ord('&')

    # --- msg_c2: Hoch/Tiefpass (RC5) ---
    msg_c2 = bytearray(5)
    msg_c2[0] = ord('c')
    msg_c2[1] = ord('5')  # RC5
    msg_c2[2] = ord('=')
    msg_c2[3] = ord('1') if highpass else ord('0')
    msg_c2[4] = ord('&')

    return bytes(msg_a), bytes(msg_b), bytes(msg_c1), bytes(msg_c2)
