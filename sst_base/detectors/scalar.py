from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import DeviceStatus
import threading
import time
import numpy as np


class ScalarBase(Device):
    exposure_time = Cpt(Signal, name="exposure_time", kind="config")
    mean = Cpt(Signal, name="mean", kind="hinted")
    std = Cpt(Signal, name="std", kind="hinted")
    npts = Cpt(Signal, name="points", kind="hinted")
    sum = Cpt(Signal, name="sum", kind="hinted")

    def set_exposure(self, exp_time):
        self.exposure_time.set(exp_time)

    def _aggregate(self, value, **kwargs):
        self._buffer.append(value)

    def _acquire(self, status):
        self._buffer = []
        self.target.subscribe(self._aggregate, run=False)
        time.sleep(self.exposure_time.get())
        self.target.clear_sub(self._aggregate)
        self.mean.put(np.mean(self._buffer))
        self.std.put(np.std(self._buffer))
        self.npts.put(len(self._buffer))
        self.sum.put(np.sum(self._buffer))
        status.set_finished()
        return
        
    def trigger(self):
        status = DeviceStatus(self)
        threading.Thread(target=self._acquire, args=(status,), daemon=True).start()
        return status

class I400Buffer(ScalarBase):
    target = Cpt(EpicsSignal, ":I1_MON", kind="omitted")

testScalar = I400Buffer("XF:07ID-BI{DM2:I400-1}", name="i400_scalar")

class ADCBuffer(ScalarBase):
    target = Cpt(EpicsSignal, "Volt", kind="omitted")

testADC = ADCBuffer("XF:07ID-BI[ADC:1-Ch:1]", name='adc_test')
