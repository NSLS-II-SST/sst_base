from ophyd import Device, Signal, EpicsSignal, EpicsSignalRO, PVPositioner
from ophyd import FormattedComponent as FmtCpt, Component as Cpt
from nbs_bl.devices import DeadbandMixin


class HexapodMirror(Device):
    x = Cpt(EpicsSignal, "X}Mtr_MON", write_pv="X}Mtr_SP", kind="hinted")
    y = Cpt(EpicsSignal, "Y}Mtr_MON", write_pv="Y}Mtr_SP", kind="hinted")
    z = Cpt(EpicsSignal, "Z}Mtr_MON", write_pv="Z}Mtr_SP", kind="hinted")
    roll = Cpt(EpicsSignal, "R}Mtr_MON", write_pv="R}Mtr_SP", kind="hinted")
    pitch = Cpt(EpicsSignal, "P}Mtr_MON", write_pv="P}Mtr_SP", kind="hinted")
    yaw = Cpt(EpicsSignal, "Yaw}Mtr_MON", write_pv="Yaw}Mtr_SP", kind="hinted")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_axes = [self.x, self.y, self.z, self.roll, self.pitch, self.yaw]


class FMBHexapodMirrorAxis(PVPositioner):
    readback = Cpt(EpicsSignalRO, "Mtr_MON")
    setpoint = Cpt(EpicsSignal, "Mtr_POS_SP")
    actuate = FmtCpt(EpicsSignal, "{self.parent.prefix}}}MOVE_CMD.PROC", kind="omitted")
    actual_value = 1
    stop_signal = FmtCpt(EpicsSignal, "{self.parent.prefix}}}STOP_CMD.PROC", kind="omitted")
    stop_value = 1
    done = FmtCpt(EpicsSignalRO, "{self.parent.prefix}}}BUSY_STS", kind="omitted")
    done_value = 0


class FMBHexapodMirrorAxisStandAlonePitch(DeadbandMixin, PVPositioner):
    readback = Cpt(EpicsSignalRO, "-Ax:P}Mtr_MON")
    setpoint = Cpt(EpicsSignal, "-Ax:P}Mtr_POS_SP")
    actuate = Cpt(EpicsSignal, "}MOVE_CMD.PROC", kind="omitted")
    actual_value = 1
    stop_signal = Cpt(EpicsSignal, "}STOP_CMD.PROC", kind="omitted")
    stop_value = 1
    done = Cpt(EpicsSignalRO, "}BUSY_STS", kind="omitted")
    done_value = 0


class FMBHexapodMirror(Device):
    z = Cpt(FMBHexapodMirrorAxis, "-Ax:Z}")
    y = Cpt(FMBHexapodMirrorAxis, "-Ax:Y}")
    x = Cpt(FMBHexapodMirrorAxis, "-Ax:X}")
    pitch = Cpt(FMBHexapodMirrorAxis, "-Ax:P}")
    yaw = Cpt(FMBHexapodMirrorAxis, "-Ax:Yaw}")
    roll = Cpt(FMBHexapodMirrorAxis, "-Ax:R}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_axes = [self.x, self.y, self.z, self.roll, self.pitch, self.yaw]
