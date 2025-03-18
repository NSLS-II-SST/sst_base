from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
import threading


class PXITimer(Device):
    integration_time = Cpt(EpicsSignal, "IT:1]Time", name="Integration Time", kind="config")
    acquire = Cpt(EpicsSignal, ":1]Sts", name="Acquire Status", kind="omitted")


class PXIScalar(Device):
    timer = Cpt(PXITimer, "XF:07ID-BI[Timer", add_prefix=(), name="Timer")
    ch1 = Cpt(EpicsSignalRO, "Ch:1]Cnts", name="ch1", kind="hinted")
    ch2 = Cpt(EpicsSignalRO, "Ch:2]Cnts", name="ch2", kind="omitted")
    ch3 = Cpt(EpicsSignalRO, "Ch:3]Cnts", name="ch3", kind="omitted")
    ch4 = Cpt(EpicsSignalRO, "Ch:4]Cnts", name="ch4", kind="omitted")
    ch5 = Cpt(EpicsSignalRO, "Ch:5]Cnts", name="ch5", kind="omitted")
    ch6 = Cpt(EpicsSignalRO, "Ch:6]Cnts", name="ch6", kind="omitted")
    ch7 = Cpt(EpicsSignalRO, "Ch:7]Cnts", name="ch7", kind="omitted")

    # integration_time = timer.integration_time #Cpt(Sig,value=0.1,kind="config")

    def trigger(self):
        def check_value(*, old_value, value, **kwargs):
            return old_value == 1 and value == 0

        def override_status(status):
            print(f"override timer for {self.name}")
            if not status.done:
                status.check_value(old_value=1, value=0)

        wait_time = self.timer.integration_time.get() + 0.5
        timeout_time = wait_time + 1
        # Somehow need a soft timeout that doesn't fail but just goes ahead
        status = SubscriptionStatus(
            self.timer.acquire, check_value, timeout=timeout_time, run=False, settle_time=0.05
        )
        soft_timeout = threading.Timer(wait_time, override_status, args=[status])
        self.timer.acquire.put(1)
        soft_timeout.start()
        return status

    def set_integration(self, t):
        self.timer.integration_time.set(t).wait(timeout=60)

    def set_exposure(self, t):
        self.timer.integration_time.set(t).wait(timeout=60)


# def __init__(self,*args,**kwargs):
#    self.configuration_attrs = ['timer.integration_time']
#    super().__init__(*args,**kwargs)


def PXIScalarBuilder(prefix, *, name, **kwargs):
    class CustomPXIScalar(PXIScalar):
        pass


# pxiScalar = PXIScalar("XF:07ID-BI[Counter:1-",name="PXI Scalar")
