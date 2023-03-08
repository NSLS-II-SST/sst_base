from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import DeviceStatus
import threading
import time
import numpy as np


class ScalarBase(Device):
    exposure_time = Cpt(Signal, name="exposure_time", kind="config")
    mean = Cpt(Signal, name="", kind="hinted")
    median = Cpt(Signal, name="median")
    std = Cpt(Signal, name="std")
    npts = Cpt(Signal, name="points")
    sum = Cpt(Signal, name="sum")
    rescale = Cpt(Signal, value=1, name="rescale", kind="config")
    offset = Cpt(Signal, value=0, name="offset", kind="config")

    def __init__(self, *args, **kwargs):
        self._flying = False
        self._flyer_buffer = []
        self._flyer_time_buffer = []
        super().__init__(*args, **kwargs)

    def kickoff(self):
        self._flyer_buffer = []
        self._flyer_time_buffer = []
        self._flyer_timestamp_buffer = []
        kickoff_st = DeviceStatus(device=self)
        kickoff_st.set_finished()
        self._flying = True
        return kickoff_st
        
    def stage(self):
        self._secret_buffer = []
        self._secret_time_buffer = []
        return super().stage()

    def set_exposure(self, exp_time):
        self.exposure_time.set(exp_time)

    def _aggregate(self, value, **kwargs):
        scale_value = value*self.rescale.get() - self.offset.get()
        t = time.time()
        self._buffer.append(scale_value)
        self._time_buffer.append(t)
        if self._flying:
            self._flyer_buffer.append(scale_value)
            self._flyer_time_buffer.append(t)
            self._flyer_timestamp_buffer.append(kwargs.get('timestamp', t))
        
    def _acquire(self, status):
        self._buffer = []
        self._time_buffer = []
        self.target.subscribe(self._aggregate, run=False)
        time.sleep(self.exposure_time.get())
        if len(self._buffer) == 0:
            ntry = 10
            n = 0
            while len(self._buffer) < 1:
                time.sleep(0.1*self.exposure_time.get())
                n += 1
                if n > ntry:
                    break
        self.target.clear_sub(self._aggregate)
        self.mean.put(np.mean(self._buffer))
        self.median.put(np.median(self._buffer))
        self.std.put(np.std(self._buffer))
        self.npts.put(len(self._buffer))
        self.sum.put(np.sum(self._buffer))
        self._secret_buffer.append(np.array(self._buffer))
        self._secret_time_buffer.append(np.array(self._time_buffer))
        status.set_finished()
        return
        
    def trigger(self):
        status = DeviceStatus(self)
        threading.Thread(target=self._acquire, args=(status,), daemon=True).start()
        return status

    def collect(self):
        t = time.time()
        for n in range(len(self._flyer_buffer)):
            v = self._flyer_buffer[n]
            t = self._flyer_time_buffer[n]
            ts = self._flyer_timestamp_buffer[n]
            event = dict()
            event['time'] = t
            event['data'] = dict()
            event['timestamps'] = dict()
            event['data'][self.mean.name + '_raw'] = v
            event['timestamps'][self.mean.name + '_raw'] = ts
            yield event
        return

    def complete(self):
        self._flying = False
        completion_status = DeviceStatus(self)
        completion_status.set_finished()
        return completion_status

    def describe_collect(self):
        dd = dict({self.mean.name + '_raw': {'source': self.target.pvname, 'dtype': 'number', 'shape': []}})
        return {self.name: dd}
        
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
