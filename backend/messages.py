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
