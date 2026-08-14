from backend.services.tuner_service import TunerService
from backend.utils.network import ping_icmp, send_udp
from backend.messages import build_messages

class TunerServiceImpl(TunerService):
    """Concrete implementation of tuner service."""
    
    def __init__(self, host: str = "10.1.0.1", port: int = 54123, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        
        self.reachable = False
        self.last_l_value = -1
        self.last_c_value = -1
        self.last_hp_value = None
    
    def check_reachability(self, timeout: float = 0.5) -> bool:
        """Check if the tuner is reachable."""
        self.reachable = ping_icmp(self.host, timeout=timeout)
        if self.debug:
            if self.reachable:
                print(f"[INFO] SBC65EC {self.host}:{self.port} is reachable")
            else:
                print(f"[WARN] SBC65EC {self.host}:{self.port} is not reachable")
        return self.reachable
    
    def send_values(self, l_value: int, c_value: int, highpass: bool) -> None:
        """Send tuning values to the tuner."""
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
        
        send_udp(self.host, self.port, full_msg)
    
    def is_reachable(self) -> bool:
        """Returns True if the tuner is reachable."""
        return self.reachable
    
    def set_host_port(self, host: str, port: int) -> None:
        """Set the host and port for communication."""
        self.host = host
        self.port = port