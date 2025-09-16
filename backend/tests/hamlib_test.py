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