import Hamlib

rig_models = [(name, getattr(Hamlib, name)) for name in dir(Hamlib) if name.startswith("RIG_MODEL_")]

for rig_id, rig_name in rig_models:
    print(rig_id, rig_name)
