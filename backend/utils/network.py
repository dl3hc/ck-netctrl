import socket
import subprocess
import platform
from shutil import which

def ping_icmp(ip: str, timeout: float = 1.0, attempts: int = 3) -> bool:
    """
    Führt ein klassisches ICMP-Ping durch.
    Windows: ping-Binary oder socket-basiert.
    Linux: /bin/ping Binary, ohne Root funktioniert es, wenn Paketgröße angepasst wird.
    """
    system = platform.system().lower()
    count_flag = "-n" if system == "windows" else "-c"
    timeout_flag = "-w" if system == "windows" else "-W"
    
    # Timeout: Windows -> ms, Linux -> Sekunden (float)
    timeout_value = int(timeout * 1000) if system == "windows" else timeout

    # Ping-Binary finden
    ping_bin = which("ping") or ("/bin/ping" if system != "windows" else "ping")

    # Paketgröße unter Linux anpassen, damit Geräte wie SBC65EC erreichbar sind
    size_flag = "-l" if system == "windows" else "-s"
    packet_size = "32" if system != "windows" else "32"  # Windows standard 32 Bytes

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
    """Sendet ein UDP-Paket, gibt True bei Erfolg zurück."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(data, (ip, port))
        return True
    except Exception:
        return False
