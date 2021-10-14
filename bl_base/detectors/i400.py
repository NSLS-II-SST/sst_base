from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.signal import DEFAULT_EPICSSIGNAL_VALUE

class I400(Device):
    exposure_time = Cpt(Signal, name="exposure_time", kind="config")
    range_sp = Cpt(EpicsSignal, ":RANGE", kind="omitted")
    range_set = Cpt(EpicsSignal, ":SET_RANGE.PROC", kind="omitted")
    range_mon = Cpt(EpicsSignalRO, ":RANGE_MON", kind="config")
    period_mon = Cpt(EpicsSignalRO, ":PERIOD_MON", kind="config")
    period_set = Cpt(EpicsSignal, ":PERIOD_SP", kind="omitted")
    points = Cpt(EpicsSignal, ":TRIGPOINTS_MON", write_pv=":TRIGPOINTS_SP", kind="config")
    cap_bin = Cpt(EpicsSignal, ":CAP_STS", write_pv=":CAP_SP", kind="config")
    err = Cpt(EpicsSignalRO, ":ERR", kind="config")
    sts = Cpt(EpicsSignalRO, ":STS", kind="config")
    clrerr = Cpt(EpicsSignal, ":EXECUTE_CLEAR.PROC", kind="omitted")
    i1 = Cpt(EpicsSignalRO, ":I1_MON")
    i2 = Cpt(EpicsSignalRO, ":I2_MON")
    i3 = Cpt(EpicsSignalRO, ":I3_MON")
    i4 = Cpt(EpicsSignalRO, ":I4_MON")
    acquire = Cpt(EpicsSignal, ":COUNT_TRIGGERS", kind="omitted")
    accum_mon = Cpt(EpicsSignalRO, ":ACCUM_MON", kind="config")
    accum_sp = Cpt(EpicsSignal, ":ACCUM_SP", kind="omitted")
    
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
            raise ValueError(f"1e-{range_exp} current range too low, minimum is {min_range}")
        else:
            self.range_sp.set(ioc_range)
            self.range_set.set(1)

    def set_exposure(self, exp_time):
        int_time = self.period_mon.get()
        if exp_time < int_time:
            raise ValueError(f"Exposure time {exp_time}s is less than "
                             "integration time of {int_time}s for {self.name}")
        npoints = int(exp_time/int_time)
        self.points.set(f"{npoints:d}")
        self.exposure_time.set(f"{npoints*int_time}")
        
    def trigger(self):
        status = SubscriptionStatus(self.i1, lambda *arg, **kwargs: True, run=False)
        self.acquire.set(1)
        return status

        
    
