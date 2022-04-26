from ophyd import Device, Component as Cpt, EpicsSignalRO


class F460(Device):
    i1 = Cpt(EpicsSignalRO, "Cur:I0-I", kind="hinted")
    i2 = Cpt(EpicsSignalRO, "Cur:I1-I", kind="hinted")
    i3 = Cpt(EpicsSignalRO, "Cur:I2-I", kind="hinted")
    i4 = Cpt(EpicsSignalRO, "Cur:I3-I", kind="hinted")
    period = Cpt(EpicsSignalRO, "Cur:Per", kind="config")
