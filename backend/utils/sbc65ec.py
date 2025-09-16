from backend.messages import build_messages
from backend.utils import network

class SBC65EC:
    """
    Steuerung des SBC65EC Tuners über UDP.
    - Erreichbarkeit prüfen
    - Werte (L, C, HP) senden
    """

    def __init__(self, host: str = "10.1.0.1", port: int = 54123, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug

        self.reachable = False
        self.last_l_value = -1
        self.last_c_value = -1
        self.last_hp_value = None

    # --- Erreichbarkeit prüfen ---
    def check_reachability(self, timeout: float = 0.5) -> bool:
        """Prüft, ob der SBC65EC erreichbar ist (per ICMP)."""
        self.reachable = network.ping_icmp(self.host, timeout=timeout)
        if self.debug:
            if self.reachable:
                print(f"[INFO] SBC65EC {self.host}:{self.port} ist erreichbar")
            else:
                print(f"[WARN] SBC65EC {self.host}:{self.port} nicht erreichbar")
        return self.reachable

    # --- Werte senden ---
    def send_values(self, l_value: int, c_value: int, highpass: bool):
        if not self.reachable:
            if self.debug:
                print("[DEBUG] Tuner nicht erreichbar → Werte nicht gesendet")
            return

        # Nur senden, wenn Werte sich geändert haben
        if (l_value == self.last_l_value and
            c_value == self.last_c_value and
            highpass == self.last_hp_value):
            return

        self.last_l_value = l_value
        self.last_c_value = c_value
        self.last_hp_value = highpass

        # Nachrichten aufbauen
        msg_a, msg_b, msg_c1, msg_c2 = build_messages(l_value, c_value, highpass)
        full_msg = msg_a + msg_b + msg_c1 + msg_c2

        if self.debug:
            print(f"[DEBUG] Sende an SBC65EC {self.host}:{self.port}")
            print(f"  Nachricht: {full_msg.decode(errors='ignore')}")

        network.send_udp(self.host, self.port, full_msg)
