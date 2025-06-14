from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, FormattedComponent as FCpt
from .detectors.scalar import ophScalar

class RBD9103(Device):
    meas_unit = Cpt(EpicsSignal, "CurrentUnits_RBV", kind="config", string=True)

def RBDFactory(prefix, *args, **kwargs):
    class RBDSignal(ophScalar):
        rbd9103 = Cpt(RBD9103, prefix, add_prefix="", kind="config")

    return RBDSignal(prefix + "Current_RBV", *args, **kwargs)
