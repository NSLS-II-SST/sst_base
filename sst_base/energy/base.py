from ophyd import (
    PVPositioner,
    EpicsSignalRO,
    PseudoPositioner,
    EpicsMotor,
    EpicsSignal,
    PVPositionerPC,
    SoftPositioner,
    Signal,
)
from ophyd import Component as Cpt, Device
import bluesky.plan_stubs as bps
from ophyd.pseudopos import pseudo_position_argument, real_position_argument
import pathlib
import numpy as np
import xarray as xr
from scipy.interpolate import CubicSpline
from nbs_bl.printing import boxed_text, colored
from sst_base.motors import PrettyMotorFMBO, FlyerMixin, PrettyMotorFMBODeadbandFlyer
from nbs_bl.devices import DeadbandEpicsMotor, DeadbandMixin, PseudoSingle
from nbs_bl.devices.motors import DeadbandPVPositioner

import time
from datetime import datetime
from ophyd.status import DeviceStatus, SubscriptionStatus

from queue import Queue, Empty

##############################################################################################


class UndulatorMotor(FlyerMixin, DeadbandEpicsMotor):
    user_setpoint = Cpt(EpicsSignal, "-SP", limits=True)


class EpuMode(PVPositionerPC):
    setpoint = Cpt(EpicsSignal, "-SP", kind="config")
    readback = Cpt(EpicsSignal, "-RB", kind="normal")


class FlyControl(DeadbandPVPositioner):
    macro_enable = Cpt(
        EpicsSignal,
        "MACROControl-RB",
        write_pv="MACROControl-SP",
        name="Enable Undulator Sync",
        kind="config",
    )
    setpoint = Cpt(EpicsSignal, "FlyMove-Mtr-SP-Go", kind="hinted")
    readback = Cpt(EpicsSignal, "FlyMove-Mtr.RBV", kind="hinted")

    flymove_stop_ev = Cpt(EpicsSignal, "FlyMove-Mtr-SP", name="Energy scan stop energy", kind="config")
    flymove_start = Cpt(EpicsSignal, "FlyMove-Mtr-Go.PROC", name="Energy scan start command", kind="config")

    speed = Cpt(EpicsSignal, "FlyMove-Speed-SP", name="Energy scan speed", kind="config")
    stop_signal = Cpt(EpicsSignal, "FlyMove-Mtr.STOP", name="Energy scan stop command", kind="config")
    done = Cpt(EpicsSignalRO, "FlyMove-Mtr.DMOV", name="en_flymove_done", kind="config")
    done_value = 1

    scan_segments_n = Cpt(EpicsSignal, "NScanRegions-SP", name="en_scan_nregions", kind="config")
    scan_segments = Cpt(EpicsSignal, "FlySeg-Energy-SP", name="en_scan_segments", kind="config")
    scan_speed_ev = Cpt(EpicsSignal, "FlySeg-Velo-SP", name="en_scan_speeds", kind="config")
    scan_trigger_width = Cpt(
        EpicsSignal,
        "EScanTriggerWidth-RB",
        write_pv="EScanTriggerWidth-SP",
        name="trigger_width",
        kind="config",
    )
    scan_trigger_n = Cpt(
        EpicsSignal,
        "EScanNTriggers-RB",
        write_pv="EScanNTriggers-SP",
        name="num_triggers",
        kind="config",
    )
    scan_start_go = Cpt(EpicsSignal, "FlyScan-Mtr-Go.PROC", name="scan_start", kind="config")
    scan_type = Cpt(EpicsSignal, "FlyScan-Type-SP", name="scan_type", kind="config")
    num_scans = Cpt(EpicsSignal, "EScanNScans-SP", name="num_scans", kind="config")
    scanning = Cpt(EpicsSignal, "FlyScan-Mtr.MOVN", name="scan_moving", kind="config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.readback.name = self.name

    def _setup_move(self, position):
        print("Flymove initialization")
        self.enable_undulator_sync(wait_for_completion=True)
        super()._setup_move(position)

    def check_macro_status(self):
        if int(self.macro_enable.get()) & 4:
            return "Enabled"
        elif int(self.macro_enable.get()) & 2:
            return "Disabled"
        else:
            return "Unknown"

    def enable_undulator_sync(self, wait_for_completion=False):
        # Read status
        print("Enable undulator sync")

        def check_value(*, old_value, value, **kwargs):
            if int(value) & 4:
                return True
            else:
                return False

        st = SubscriptionStatus(self.macro_enable, check_value, run=True)
        if st.success:
            print("Undulator sync already enabled")
            return st
        else:
            self.macro_enable.put(1)
            if wait_for_completion:
                st.wait(timeout=20)
            print("Enable undulator sync done")
            return st

    def disable_undulator_sync(self, wait_for_completion=False):
        print("Disable undulator sync")

        def check_value(*, old_value, value, **kwargs):
            if int(value) & 2:
                return True
            else:
                return False

        st = SubscriptionStatus(self.macro_enable, check_value, run=True)

        if st.success:
            print("Undulator sync already disabled")
            return st
        else:
            self.macro_enable.put(0)
            if wait_for_completion:
                st.wait(timeout=20)
            print("Disable undulator sync done")
            return st

    def flymove(self, position, speed=5):
        self.speed.set(speed).wait()
        return self.move(position)

    def scan_setup(self, segments, speeds, bidirectional=False, sweeps=1):
        print(f"[{datetime.now().isoformat()}] Flyscan setup")
        self.scan_segments_n.set(len(segments) - 1).wait(timeout=10)
        self.scan_segments.set(segments).wait(timeout=10)
        self.scan_speed_ev.set(speeds).wait(timeout=10)
        start = min(segments)
        stop = max(segments)
        scan_range = stop - start
        self.scan_trigger_width.set(0.1).wait(timeout=10)
        trig_width = self.scan_trigger_width.get(timeout=10)
        # Not relevant yet, but required for scan
        ntrig = np.abs(scan_range // (2 * trig_width))
        print(f"number of triggers : {ntrig}")
        self.scan_trigger_n.set(ntrig).wait(timeout=10)
        self.scan_type.set(1 if bidirectional else 0).wait(timeout=10)
        self.num_scans.set(sweeps).wait(timeout=10)
        print("Flyscan setup done")

    def scan_start(self):
        print(f"[{datetime.now().isoformat()}] Flyscan start")
        self.enable_undulator_sync().wait()
        self.scan_start_go.set(1).wait()
        print(f"[{datetime.now().isoformat()}] Flyscan start done")

        def check_value(*, old_value, value, **kwargs):
            if old_value != 0 and value == 0:
                return True

        fly_move_st = SubscriptionStatus(self.scanning, check_value, run=False)
        return fly_move_st


class EnergyFlyerBase:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready_to_fly = False
        self._fly_move_st = None
        self._default_time_resolution = 0.05
        self._flyer_lag_ev = 0.1
        self._flyer_gap_lead = 0.0
        self._time_resolution = self._default_time_resolution
        self._flying = False
        self._sync_status = None
        
    def get_flymove_max_speed(self, start):
        return 20

    def preflight(
        self, start, stop, speed, *args, time_resolution=None, bidirectional=False, sweeps=1
    ):
        print(f"[{datetime.now().isoformat()}] Energy preflight")
        flight_segments = [start, stop]
        flight_speeds = [speed]
        if len(args) > 0:
            if len(args) % 2 != 0:
                raise ValueError(
                    "args must be start, stop, speed, [stop2, speed2,...]"
                )
            else:
                flight_segments += [args[n] for n in range(len(args)) if n %2 == 0]
                flight_speeds += [args[n] for n in range(len(args)) if n %2 == 1]
        else:
            self.flight_segments = iter(())

        if time_resolution is not None:
            self._time_resolution = time_resolution
        elif self._time_resolution is None:
            self._time_resolution = self._default_time_resolution
        self._sync_status = self.check_macro_status()
        self.flycontrol.scan_setup(flight_segments, flight_speeds, bidirectional=bidirectional, sweeps=sweeps)

        print(f"[{datetime.now().isoformat()}] Setting energy to start")

        self.flycontrol.flymove(start, speed=self.get_flymove_max_speed(start)).wait()
        print(f"[{datetime.now().isoformat()}] Setting energy to start... done")
        self._last_mono_value = start
        self._mono_stop = stop
        self._ready_to_fly = True

    def fly(self):
        """
        Should be called after all detectors start flying, so that we don't lose data
        """
        if not self._ready_to_fly:
            print(f"[{datetime.now().isoformat()}] Energy is not ready to fly")
            self._fly_move_st = DeviceStatus(device=self)
            self._fly_move_st.set_exception(RuntimeError)
        else:
            print(f"[{datetime.now().isoformat()}] Energy is ready to fly")

            def check_value(*, old_value, value, **kwargs):
                if old_value != 0 and value == 0:  # was moving, but not moving anymore
                    print(f"[{datetime.now().isoformat()}] got to stopping point")
                    return True
                else:
                    return False

            # Need our own check_value that will keep flying until there are no more flight segments left
            self._fly_move_st = SubscriptionStatus(self.flycontrol.scanning, check_value, run=False)
            print(f"[{datetime.now().isoformat()}] Calling energy.scan_start()")
            self.flycontrol.scan_start()
            self._flying = True
            self._ready_to_fly = False
        return self._fly_move_st

    def land(self):
        if self._fly_move_st.done:
            self._flying = False
            # self.flycontrol.disable_undulator_sync().wait()
            print(f"[{datetime.now().isoformat()}] Landed")
        else:
            print(f"[{datetime.now().isoformat()}] Trying to land, but fly_move not done. How did we get here??")

        if self._sync_status != "Enabled":
            self.disable_macro().wait()
            self._sync_status = None
        return
    def kickoff(self):
        kickoff_st = DeviceStatus(device=self)
        if self._time_resolution is None:
            self._time_resolution = self._default_time_resolution

        self._flyer_queue = Queue()
        self._measuring = True
        self._flyer_buffer = []
        self._flyer_timestamp_buffer = []

        # Kind of a hack, because flycontrol doesn't have a fast readback yet
        self.monoen.readback.subscribe(self._aggregate, run=False)
        kickoff_st.set_finished()
        return kickoff_st

    def _aggregate(self, value, **kwargs):
        name = "energy_readback"
        if self._measuring:
            t = time()

            ts = kwargs.get("timestamp", t)
            last_timestamp = self._flyer_timestamp_buffer[-1] if len(self._flyer_timestamp_buffer) > 0 else None
            if last_timestamp is None or ts + self._time_resolution > last_timestamp:
                self._flyer_buffer.append(value)
                self._flyer_timestamp_buffer.append(ts)
                event = dict()
                event["time"] = t
                event["data"] = dict()
                event["timestamps"] = dict()
                event["data"][name] = value
                event["timestamps"][name] = ts
                self._flyer_queue.put(event)
            # if abs(self._last_mono_value - value) > self._flyer_lag_ev:
            #    self._last_mono_value = value
            #    self.epugap.set(self.gap(value + self._flyer_gap_lead, self._flyer_pol, False))
            # sleep(self._time_resolution)
        return

    def complete(self):
        if self._measuring:
            self._measuring = False
            self.monoen.readback.clear_sub(self._aggregate)
        completion_status = DeviceStatus(self)
        completion_status.set_finished()
        self._time_resolution = None
        return completion_status

    def collect(self):
        events = []
        while True:
            try:
                e = self._flyer_queue.get_nowait()
                events.append(e)
            except Empty:
                break
        yield from events

    def describe_collect(self):
        dd = dict(
            {
                "energy_readback": {
                    "source": self.monoen.readback.pvname,
                    "dtype": "number",
                    "shape": [],
                }
            }
        )
        return {"energy_readback_monitor": dd}

    def check_macro_status(self):
        return self.flycontrol.check_macro_status()

    def enable_macro(self,wait_for_completion=False):
        return self.flycontrol.enable_undulator_sync(wait_for_completion=wait_for_completion)

    def disable_macro(self,wait_for_completion=False):
        return self.flycontrol.disable_undulator_sync(wait_for_completion=wait_for_completion)


