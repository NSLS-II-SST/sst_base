from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
import threading
#from ophyd.utils.epics_pvs import _set_and_wait

class UnreliableEpicsSignal(EpicsSignal):
    def _set_and_wait(self, value, timeout, **kwargs):
        N = 3
        timeout = timeout if timeout is not None else 0.5
        for j in range(N):
            try:
                return epics_pvs._set_and_wait(self, value,
                                               timeout=timeout,
                                               atol=self.tolerance,
                                               rtol=self.rtolerance,
                                               **kwargs)
            except TimeoutError:
                print("I400 signal timed out")
                pass
            else:
                break
        else:
            raise TimeoutError  # or might want to capture and stash the one abev
        
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
    exposure = Cpt(EpicsSignalRO, ":ITIME_MON", kind='config')
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
    acquire = Cpt(EpicsSignal, ":ACQUIRE", kind="omitted")
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
        if getattr(self, "_was_auto_acquiring", False):
            self.start_auto_acquire()
        super().unstage()

    def start_auto_acquire(self):
        self.auto_acquire.put(0)
        self.acquire.put(1)

    def halt_auto_acquire(self):
        self.auto_acquire.set(1)

    def set_exposure(self, exp_time):
        int_time = self.period_mon.get()
        if exp_time < int_time:
            raise ValueError(f"Exposure time {exp_time}s is less than "
                             "integration time of {int_time}s for {self.name}")
        if int_time == 0:
            raise RuntimeError(f"Integration time is 0 for {self.name}, check for communication error")
        npoints = int(exp_time/int_time)
        was_auto_acquiring = (self.auto_acquire.get() == 0)
        self.halt_auto_acquire()
        try:
            self.points.set(f"{npoints:d}", timeout=0.5).wait()
        except TimeoutError:
            self.points.set(f"{npoints:d}", timeout=0.5).wait()
        self.exposure_sp.set(f"{npoints*int_time}")
        if was_auto_acquiring:
            self.start_auto_acquire()
            
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
        def restart_trigger():
            print("Trigger failed, retry once")
            self.acquire.set(0)
            self.acquire.set(1)
        exposure_time = float(self.exposure_sp.get())
        timer = threading.Timer(1.5*exposure_time, restart_trigger)
        def check_value(*, old_value, value, **kwargs):
            success = (old_value == 1 and value == 0)
            if success:
                timer.cancel()
            return success
        status = SubscriptionStatus(self.acquire, check_value, timeout=exposure_time*3, run=False)
        self.acquire.set(1)
        timer.start()
        return status

