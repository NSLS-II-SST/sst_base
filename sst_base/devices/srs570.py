from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, FormattedComponent as FCpt
from .detectors.scalar import ADCBuffer

class SRS570(Device):
    filter_type = Cpt(EpicsSignal, "filter_type.VAL", kind="config", string=True)
    filter_reset = Cpt(EpicsSignal, "filter_reset.VAL", kind="omitted")
    low_freq = Cpt(EpicsSignal, "low_freq.VAL", kind="config", string=True)
    high_freq = Cpt(EpicsSignal, "high_freq.VAL", kind="config", string=True)
    gain_mode = Cpt(EpicsSignal, "gain_mode.VAL", kind="config", string=True)
    send_all = Cpt(EpicsSignal, "init.PROC", kind="omitted")
    reset = Cpt(EpicsSignal, "reset.PROC", kind="omitted")
    gain_num = Cpt(EpicsSignal, "sens_num.VAL", kind="config", string=True)
    gain_unit = Cpt(EpicsSignal, "sens_unit.VAL", kind="config", string=True)
    invert = Cpt(EpicsSignal, "invert_on.VAL", kind="config", string=True)


def SRSADCFactory(prefix, *args, srs_prefix, **kwargs):
    class SRSADC(ADCBuffer):
        srs570 = Cpt(SRS570, srs_prefix, add_prefix="", kind="config")

    return SRSADC(prefix, *args, **kwargs)
