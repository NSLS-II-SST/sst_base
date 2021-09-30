from ophyd import Device, Component as Cpt, EpicsSignal, Signal


class I400(Device):
    exposure_time = Cpt(EpicsSignal, ":PERIOD_MON", write_pv=":PERIOD_SP", kind="config")
    curr_range = Cpt(EpicsSignal, ":RANGE_MON", write_pv=":SET_RANGE", kind="config")
    cap_bin = Cpt(EpicsSignal, ":CAP_MON", write_pv=":CAP_SP", kind="config")
    
