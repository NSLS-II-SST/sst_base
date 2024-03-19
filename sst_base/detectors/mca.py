from ophyd import Device, Component as Cpt, EpicsSignal, Signal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
import numpy as np


class EpicsMCABase(Device):
    exposure_time = Cpt(EpicsSignal, "COUNT_TIME", name="exposure_time", kind="config")
    counts = Cpt(EpicsSignalRO, "COUNTS", name="counts", kind="hinted")
    acquire = Cpt(EpicsSignal, "ACQUIRE", name="acquire", kind="omitted")
    spectrum = Cpt(EpicsSignalRO, "SPECTRUM", name="spectrum", kind="normal")
    llim = Cpt(EpicsSignal, "LLIM", name="llim", kind="config")
    ulim = Cpt(EpicsSignal, "ULIM", name="ulim", kind="config")
    nbins = Cpt(EpicsSignal, "NBINS", name="nbins", kind='config')
    energies = Cpt(EpicsSignalRO, "CENTERS", name="energies", kind='config')
    rois = {}
    roi_hints = set()

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.rois = {}

    @property
    def hints(self):
        return {'fields': [f"{self.name}_{roi}" for roi in self.rois] + [self.counts.name]}

    def get_plot_hints(self):
        h = [{"signal": ['data', self.spectrum.name],
              "axes": [['config', self.name, self.energies.name]]}]
        if len(self.roi_hints) > 0:
            h += [f"{self.name}_{roi}" for roi in self.roi_hints]
        else:
            h += [self.counts.name]
        return h

    def set_roi(self, label, llim, ulim, plot=False):
        self.rois[label] = (llim, ulim)
        if plot:
            self.roi_hints.add(label)

    def clear_roi(self, label):
        self.rois.pop(label)
        if label in self.roi_hints:
            self.roi_hints.remove(label)

    def clear_all_rois(self):
        self.rois = {}
        self.roi_hints = set()

    def set_exposure(self, exp_time):
        self.exposure_time.set(exp_time)

    def trigger(self):

        def check_value(*, old_value, value, **kwargs):
            success = (old_value == 1 and value == 0)
            return success

        status = SubscriptionStatus(self.acquire, check_value, run=False)
        self.acquire.set(1)
        return status

    def set_resolution(self, res, llim=None, ulim=None):
        if llim is not None:
            self.llim.set(llim)
        if ulim is not None:
            self.ulim.set(ulim)

        nbins = int((self.ulim.get() - self.llim.get()) / res)
        self.nbins.set(nbins)

    def describe(self):
        d = super().describe()
        k = self.spectrum.name
        d[k]['shape'] = [self.nbins.get()]
        d[k]['dtype'] = 'array'
        for k in self.rois:
            key = self.name + "_" + k
            d[key] = {"dtype": "number", "shape": [], "source": key,
                      "llim": self.rois[k][0], "ulim": self.rois[k][1]}
        return d

    def read(self):
        r = super().read()
        k = self.spectrum.name
        partialval = r[k]['value']
        full_len = self.nbins.get()
        if len(partialval) > full_len:
            partialval = partialval[:full_len]
        fullval = np.zeros(full_len)
        fullval[:len(partialval)] = partialval
        r[k]['value'] = fullval
        e = self.energies.get()
        for roi, (llim, ulim) in self.rois.items():
            i1 = e.searchsorted(llim, 'left')
            i2 = e.searchsorted(ulim, 'right')
            key = self.name + "_" + roi
            r[key] = {"value": np.sum(fullval[i1:i2]), "timestamp": r[k]['timestamp']}
        return r
