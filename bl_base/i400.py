from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO


class I400(Device):
    exposure_time = Cpt(EpicsSignal, ":PERIOD_MON", write_pv=":PERIOD_SP", kind="config")
    set_range = Cpt(EpicsSignal, ":RANGE_BP")
    range_mon = Cpt(EpicsSignalRO, ":RANGE_MON", kind="config")
    cap_bin = Cpt(EpicsSignal, ":CAP_SP", kind="config")
    err = Cpt(EpicsSignalRO, ":ERR")
    sts = Cpt(EpicsSignalRO, ":STS")
    clrerr = Cpt(EpicsSignal, ":EXECUTE_CLEAR")
    i1 = Cpt(EpicsSignalRO, ":I1_MON")
