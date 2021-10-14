from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.signal import DEFAULT_EPICSSIGNAL_VALUE

class I400(Device):
    exposure_time = Cpt(EpicsSignal, ":PERIOD_MON", write_pv=":PERIOD_SP", kind="config")
    range_set = Cpt(EpicsSignal, ":RANGE_BP", kind="omitted")
    range_mon = Cpt(EpicsSignalRO, ":RANGE_MON", kind="config")
    period_mon = Cpt(EpicsSignalRO, ":PERIOD_MON", kind="config")
    period_proc = Cpt(EpicsSignal, ":PERIOD_MON.PROC", kind="omitted")
    period_set = Cpt(EpicsSignal, ":PERIOD_SP", kind="config")
    cap_bin = Cpt(EpicsSignal, ":CAP_STS", write_pv=":CAP_SP", kind="config")
    err = Cpt(EpicsSignalRO, ":ERR", kind="config")
    sts = Cpt(EpicsSignalRO, ":STS", kind="config")
    clrerr = Cpt(EpicsSignal, ":EXECUTE_CLEAR.PROC", kind="omitted")
    i1 = Cpt(EpicsSignalRO, ":I1_MON")
    acquire = Cpt(EpicsSignal, ":I1_MON.PROC", kind="omitted")

    def clear_errors(self):
        self.clrerr.set(1)

    def set_range(self, range_exp):
        """
        range_exp : int
            Exponent of desired range, expressed as a positive integer. I.e, for 1e-7 A range,
            enter 7
        """
        ioc_range = int(13 - range_exp)
        min_range = "1e-9" if self.cap_bin.get() else "1e-11"
        if ioc_range <= 1:
            raise ValueError(f"1e-{range_exp%d} current range too low, minimum is {min_range}")
        else:
            self.range_set.set(ioc_range)
            self.period_proc.set(1)

    def trigger(self):
        status = SubscriptionStatus(self.i1, lambda *arg, **kwargs: True, run=False)
        self.acquire.set(1)
        return status

        
    
