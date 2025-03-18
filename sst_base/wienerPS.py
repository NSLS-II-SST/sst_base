from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO
from ophyd.pv_positioner import PVPositionerComparator
from typing import Dict, Optional
import numpy as np


def sanitize_name(name):
    """
    Convert a channel name to a valid Python identifier.

    Parameters
    ----------
    name : str
        Original channel name

    Returns
    -------
    str
        Sanitized name with spaces and hyphens replaced by underscores
    """
    if name is None:
        return None
    return name.replace("-", "_").replace(" ", "_")


class WienerPSChannel(PVPositionerComparator):
    """
    Ophyd device for a single Wiener Power Supply channel.

    Parameters
    ----------
    prefix : str
        Base PV prefix for the channel
    name : str
        Name for the channel
    """

    # Position signals
    setpoint = Cpt(EpicsSignal, "V-Set", kind="normal")
    readback = Cpt(EpicsSignalRO, "V-Sense", kind="normal")

    # Configuration signals
    vrise = Cpt(EpicsSignal, "V-RiseRate", kind="config")
    vfall = Cpt(EpicsSignal, "V-FallRate", kind="config")
    current = Cpt(EpicsSignalRO, "I-Sense", kind="normal")
    current_limit = Cpt(EpicsSignal, "I-SetLimit", kind="config")
    switch = Cpt(EpicsSignal, "Switch", kind="config")

    # Internal done signal

    def __init__(self, *args, max_voltage=6000, pos_polarity=True, **kwargs):
        if pos_polarity:
            limits = (0, np.abs(max_voltage))
        else:
            limits = (-np.abs(max_voltage), np.abs(max_voltage))
        super().__init__(*args, limits=limits, egu="V", **kwargs)
        self._done = 1
        self._tolerance = 0.01  # 1% tolerance for considering move complete
        self._pos_polarity = pos_polarity
        # Subscribe to readback changes to update done state

    def _setup_move(self, position):
        """Handle switch state and start motion."""
        if not self.switch.get():
            return self.setpoint.put(0, wait=False)
        if not self._pos_polarity:
            position = -np.abs(position)
        return self.setpoint.put(position, wait=False)

    def done_comparator(self, readback, setpoint):
        """Compare readback and setpoint to determine if move is done."""
        sp = np.abs(setpoint)
        rb = np.abs(readback)
        if sp > 0:
            return abs((rb - sp) / sp) < self._tolerance
        else:
            return rb < 0.1  # 0.1V absolute tolerance near zero


class WienerPSBase(Device):
    """
    Base class for Wiener Power Supply.
    """

    pass


def WienerPSFactory(
    prefix: str,
    name: str,
    lvch0: Optional[str] = None,
    lvch1: Optional[str] = None,
    lvch2: Optional[str] = None,
    lvch3: Optional[str] = None,
    lvch4: Optional[str] = None,
    lvch5: Optional[str] = None,
    lvch6: Optional[str] = None,
    lvch7: Optional[str] = None,
    hvch0: Optional[str] = None,
    hvch1: Optional[str] = None,
    hvch2: Optional[str] = None,
    hvch3: Optional[str] = None,
    hvch4: Optional[str] = None,
    hvch5: Optional[str] = None,
    hvch6: Optional[str] = None,
    hvch7: Optional[str] = None,
    **kwargs,
) -> Device:
    """
    Factory function to create a WienerPS device with named channels.

    Parameters
    ----------
    prefix : str
        Base PV prefix
    name : str
        Name for the device
    lvchX : str, optional
        Names for LV channels (X from 0-7)
    hvchX : str, optional
        Names for HV channels (X from 0-7)
    **kwargs : dict
        Additional keyword arguments passed to WienerPS

    Returns
    -------
    Device
        Configured Wiener Power Supply device
    """
    components = {}

    # Add LV channels as components
    for i in range(8):
        ch_name = locals()[f"lvch{i}"]
        if ch_name is not None:
            safe_name = sanitize_name(ch_name)
            components[f"lv_{safe_name}"] = Cpt(WienerPSChannel, f"-LV-u{i}}}", pos_polarity=False, kind="normal")

    # Add HV channels as components
    for i in range(8):
        ch_name = locals()[f"hvch{i}"]
        if ch_name is not None:
            safe_name = sanitize_name(ch_name)
            components[f"hv_{safe_name}"] = Cpt(WienerPSChannel, f"-HV-u30{i}}}", kind="normal")

    # Create a new WienerPS class with the components
    ps = type(
        "WienerPS",
        (WienerPSBase,),
        components,
    )(prefix, name=name, **kwargs)
    ps.position_axes = [getattr(ps, ch_name) for ch_name in components]
    return ps
