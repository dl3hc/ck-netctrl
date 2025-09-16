# import hamlib

class TRX:
    def __init__(self, rig_id=2048, port="COM6", baudrate=115200,
                 databits=8, parity='N', stopbits=1, dummy=False):
        """
        TRX Interface via Hamlib (seriell) oder Dummy-Modus.
        
        :param rig_id: Hamlib Rig ID (2048 = FlexRadio/PowerSDR)
        :param port: COM-Port, z.B. "COM3" oder "/dev/ttyUSB0"
        :param baudrate: Baudrate (Default 115200)
        :param databits: Datenbits (Default 8)
        :param parity: Parität ('N'=none, 'E'=even, 'O'=odd)
        :param stopbits: Stopbits (Default 1)
        :param dummy: Wenn True → Dummy-Modus
        """
        self.dummy = dummy
        self.connected = False
        self._freq = 5351000  # Dummy Start-Frequenz 7.1 MHz

        if not self.dummy:
            if port is None:
                raise ValueError("COM port muss angegeben werden, wenn dummy=False")
            self.rig = hamlib.Rig(rig_type=rig_id, device_path=port)
            self.rig.set_conf(hamlib.RIG_CONFIG_BAUDRATE, baudrate)
            self.rig.set_conf(hamlib.RIG_CONFIG_DATABITS, databits)
            self.rig.set_conf(hamlib.RIG_CONFIG_PARITY, parity)
            self.rig.set_conf(hamlib.RIG_CONFIG_STOPBITS, stopbits)

    def connect(self):
        """Öffnet die Verbindung zum Transceiver (oder Dummy)"""
        if self.dummy:
            self.connected = True
            print("Dummy TRX connected")
        else:
            try:
                self.rig.open()
                self.connected = True
                print("TRX connected via COM port")
            except Exception as e:
                self.connected = False
                print(f"Fehler beim TRX connect: {e}")

    def get_frequency(self):
        """Liest die aktuelle Frequenz aus"""
        if self.dummy:
            return self._freq
        else:
            if not self.connected:
                raise RuntimeError("TRX nicht verbunden")
            try:
                return self.rig.get_freq()
            except Exception as e:
                print(f"Fehler beim Auslesen der Frequenz: {e}")
                return None



import Hamlib

Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

RIG_MODEL = Hamlib.RIG_MODEL_POWERSDR   # PowerSDR via Hamlib-Netzwerk
PORT      = "localhost:19090"           # Hamlib-Netzwerkserver von LinHPSDR

rig = Hamlib.Rig(RIG_MODEL)

rig.set_conf("rig_pathname", PORT)
# Serielle Einstellungen nicht nötig bei Netzwerkverbindung
# rig.set_conf("baudrate", "9600")
# rig.set_conf("data_bits", "8")
# rig.set_conf("stop_bits", "1")
# rig.set_conf("parity", "N")

rig.open()

freq = rig.get_freq()
print(f"Aktuelle Frequenz: {freq/1e6:.5f} MHz")

rig.close()


