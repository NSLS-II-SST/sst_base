from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.signal import DEFAULT_EPICSSIGNAL_VALUE

class I400MonRO(EpicsSignalRO):
    def set_exposure(self, time):
        self.parent.set_exposure(time)

    def describe(self):
        """
        Temporary override until I can fix PREC in EPICS
        """
        res = super().describe()
        for k in res:
            res[k]['precision'] = 3
        return res

class I400(Device):
    exposure_sp = Cpt(Signal, name="exposure_time", kind="config")
    exposure = Cpt(EpicsSignalRO, ":ITIME_MON")
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
    auto_acquire = Cpt(EpicsSignal, ":TRIGLOOP_RESTART_.DISA", kind="config")
    i1 = Cpt(I400MonRO, ":I1_MON", kind="hinted")
    i2 = Cpt(I400MonRO, ":I2_MON", kind="hinted")
    i3 = Cpt(I400MonRO, ":I3_MON", kind="hinted")
    i4 = Cpt(I400MonRO, ":I4_MON", kind="hinted")
    acquire = Cpt(EpicsSignal, ":COUNT_TRIGGERS", kind="omitted")
    acquire_mode = Cpt(EpicsSignal, ":IC_UPDATE_MODE", kind="omitted")
    accum_mon = Cpt(EpicsSignalRO, ":ACCUM_MON", kind="config")
    accum_sp = Cpt(EpicsSignal, ":ACCUM_SP", kind="omitted")
    disable = Cpt(EpicsSignal, ":ENABLE_IC_UPDATES", kind="omitted")
    
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

    def stage(self):
        self._was_auto_acquiring = (self.auto_acquire.get() == 0)
        self.halt_auto_acquire()
        super().stage()

    def unstage(self):
        if self._was_auto_acquiring:
            self.start_auto_acquire()
        super().unstage()

    def start_auto_acquire(self):
        self.auto_acquire.set(0)
        self.acquire.set(1)
        
    def halt_auto_acquire(self):
        self.auto_acquire.put(1)
        
    def set_exposure(self, exp_time):
        int_time = self.period_mon.get()
        if exp_time < int_time:
            raise ValueError(f"Exposure time {exp_time}s is less than "
                             "integration time of {int_time}s for {self.name}")
        npoints = int(exp_time/int_time)
        self.points.set(f"{npoints:d}")
        self.exposure_sp.set(f"{npoints*int_time}")

    def set_average_mode(self, average_mode):
        """
        accum_mode : 
            0: No averaging
            1: Average with charge interpolation
            2: Average with no-lost-charge method
            3: Average with no charge correction
        """
        self.accum_sp.set(average_mode)

    def trigger(self):
        timeout = float(self.exposure_sp.get())*2
        status = SubscriptionStatus(self.i1, lambda *arg, **kwargs: True, run=False, timeout=timeout)
        self.acquire.set(1)
        return status

