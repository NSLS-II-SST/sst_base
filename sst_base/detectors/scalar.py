from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import DeviceStatus
import threading
import time
import numpy as np


class ScalarBase(Device):
    exposure_time = Cpt(Signal, name="exposure_time", kind="config")
    mean = Cpt(Signal, name="", kind="hinted")
    std = Cpt(Signal, name="std")
    npts = Cpt(Signal, name="points")
    sum = Cpt(Signal, name="sum")
    rescale = Cpt(Signal, value=1, name="rescale", kind="config")
    offset = Cpt(Signal, value=0, name="offset", kind="config")

    def set_exposure(self, exp_time):
        self.exposure_time.set(exp_time)

    def _aggregate(self, value, **kwargs):
        self._buffer.append(value*self.rescale.get() - self.offset.get())

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

class I400SingleCh(ScalarBase):
    """Need to give full path to target PV during object creation"""
    
    target = Cpt(EpicsSignal, "", kind="omitted")

testScalar = I400SingleCh("XF:07ID-BI{DM2:I400-1}:IC1_MON", name="i400_scalar")

class ADCBuffer(ScalarBase):
    target = Cpt(EpicsSignal, "Volt", kind="omitted")

testADC = ADCBuffer("XF:07ID-BI[ADC:1-Ch:1]", name='adc_test')

class ophScalar(ScalarBase):
    """Generic Scalar.  Give full path to target PV during object creation """
    target = Cpt(EpicsSignal, "", kind="omitted")
