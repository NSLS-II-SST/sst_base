from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, FormattedComponent as FCpt
from .detectors.scalar import ophScalar


class RBD9103(Device):
    unit = Cpt(EpicsSignal, "CurrentUnits_RBV", kind="config", string=True)
    range_ctrl = Cpt(EpicsSignal, "Range", kind="omitted")
    range_actual = Cpt(EpicsSignalRO, "RangeActual_RBV", kind="config", string=True)
    sampling_rate_ctrl = Cpt(EpicsSignal, "SamplingRate", kind="omitted")
    sampling_rate = Cpt(EpicsSignalRO, "SamplingRateActual_RBV", kind="config")
    sampling_mode = Cpt(EpicsSignalRO, "SamplingMode_RBV", kind="config", string=True)
    sampling_mode_ctrl = Cpt(EpicsSignal, "SamplingMode", kind="omitted", string=True)
    sampling_status = Cpt(EpicsSignalRO, "Sample_RBV", kind="config", string=True)
    sample = Cpt(EpicsSignal, "Sample", kind="omitted", string=True)
    stable = Cpt(EpicsSignalRO, "Stable_RBV", kind="config", string=True)
    in_range = Cpt(EpicsSignalRO, "InRange_RBV", kind="config", string=True)

    # New PVs for sample counting
    num_samples = Cpt(EpicsSignal, "NumSamples", kind="omitted")
    num_samples_rbv = Cpt(EpicsSignalRO, "NumSamples_RBV", kind="config")
    sample_counter = Cpt(EpicsSignalRO, "SampleCounter_RBV", kind="config")

    def start_sampling(self):
        self.sample.set("Sampling").wait(timeout=5.0)

    def stop_sampling(self):
        self.sample.set("Idle").wait(timeout=5.0)

    def switch_sampling_mode(self, mode):
        if mode not in ["Single", "Multiple", "Continuous"]:
            raise ValueError(f"Invalid sampling mode: {mode}")
        self.stop_sampling()
        self.sampling_mode_ctrl.set(mode).wait(timeout=5.0)
        if mode == "Continuous":
            self.start_sampling()


def RBDFactory(prefix, *args, **kwargs):
    class RBDSignal(ophScalar):
        rbd9103 = Cpt(RBD9103, prefix, add_prefix="", kind="config")

    return RBDSignal(prefix + "Current_RBV", *args, **kwargs)
