from ophyd import Device, Component as Cpt, EpicsSignal, Signal
from ophyd.status import SubscriptionStatus

class PXITimer(Device):
    integration_time = Cpt(EpicsSignal, "IT:1]Time", name = "Integration Time",kind="config")
    acquire = Cpt(EpicsSignal, ":1]Sts", name="Acquire Status", kind="config")

class PXIScalar(Device):
    timer = PXITimer("XF:07ID-BI[Timer",name="Timer")
    ch1 = Cpt(EpicsSignal, "Ch:1]Cnts", name="Channel 1", kind="hinted")
    ch2 = Cpt(EpicsSignal, "Ch:2]Cnts", name="Channel 2", kind="hinted")
    ch3 = Cpt(EpicsSignal, "Ch:3]Cnts", name="Channel 3", kind="hinted")
    ch4 = Cpt(EpicsSignal, "Ch:4]Cnts", name="Channel 4", kind="hinted")
    ch5 = Cpt(EpicsSignal, "Ch:5]Cnts", name="Channel 5", kind="hinted")
    ch6 = Cpt(EpicsSignal, "Ch:6]Cnts", name="Channel 6", kind="hinted")
    ch7 = Cpt(EpicsSignal, "Ch:7]Cnts", name="Channel 7", kind="hinted")
    update_time = Cpt(Signal,value=0.05,kind="config")

    def trigger(self):
        def check_value(*, old_value, value, **kwargs):
            return (old_value == 1 and value == 0)

        wait_time = self.timer.integration_time.get()+0.2

        status = SubscriptionStatus(self.timer.acquire,check_value,timeout=wait_time,run=False,settle_time=self.update_time.get())
        self.timer.acquire.set(1)
        return status

    def set_integration(self,t):
        self.timer.integration_time.set(t)

pxiScalar = PXIScalar("XF:07ID-BI[Counter:1-",name="PXI Scalar")
