import re
from nbs_gui.models.misc import ScalarModel
from nbs_gui.models.base import PVModel, EnumModel
from nbs_gui.views.monitors import PVMonitor
from ..views.srs570 import SRS570Monitor, SRS570Control, CompactSRS570Monitor


class SRS570Model(ScalarModel):
    """
    Qt model for SRS570 amplifier/ADC device.

    Parameters
    ----------
    name : str
        Name of the SRS570 device
    obj : SRS570
        The ophyd SRS570 object to model
    group : str
        Group this model belongs to
    long_name : str
        Human readable name for the SRS570
    """

    default_monitor = CompactSRS570Monitor
    default_controller = SRS570Control

    def __init__(self, name, obj, group, long_name, **kwargs):
        super().__init__(name, obj, group, long_name, **kwargs)

        # Create models for filter settings
        self.filter_type = EnumModel(
            name=f"{name}_filter_type",
            obj=obj.srs570.filter_type,
            group=group,
            long_name=f"{long_name} Filter Type",
        )

        self.filter_reset = PVModel(
            name=f"{name}_filter_reset",
            obj=obj.srs570.filter_reset,
            group=group,
            long_name=f"{long_name} Filter Reset",
        )

        self.low_freq = EnumModel(
            name=f"{name}_low_freq", obj=obj.srs570.low_freq, group=group, long_name=f"{long_name} Low Frequency"
        )

        self.high_freq = EnumModel(
            name=f"{name}_high_freq",
            obj=obj.srs570.high_freq,
            group=group,
            long_name=f"{long_name} High Frequency",
        )

        # Create models for gain settings
        self.gain_mode = EnumModel(
            name=f"{name}_gain_mode", obj=obj.srs570.gain_mode, group=group, long_name=f"{long_name} Gain Mode"
        )

        self.gain_num = EnumModel(
            name=f"{name}_gain_num", obj=obj.srs570.gain_num, group=group, long_name=f"{long_name} Gain Number"
        )

        self.gain_unit = EnumModel(
            name=f"{name}_gain_unit", obj=obj.srs570.gain_unit, group=group, long_name=f"{long_name} Gain Unit"
        )

        # Create models for control settings
        self.send_all = PVModel(
            name=f"{name}_send_all", obj=obj.srs570.send_all, group=group, long_name=f"{long_name} Send All"
        )

        self.reset = PVModel(
            name=f"{name}_reset", obj=obj.srs570.reset, group=group, long_name=f"{long_name} Reset"
        )

        self.invert = EnumModel(
            name=f"{name}_invert", obj=obj.srs570.invert, group=group, long_name=f"{long_name} Invert"
        )

        # Group models for easy access
        self.filter_models = [self.filter_type, self.filter_reset, self.low_freq, self.high_freq]
        self.gain_models = [self.gain_mode, self.gain_num, self.gain_unit]
        self.control_models = [self.send_all, self.reset, self.invert]

    @property
    def gain_choices(self):
        """
        List of all possible gain (num, unit) combinations as strings, sorted by total gain.
        Returns
        -------
        list of str
            Each entry is e.g. '500 nA', '1 uA', etc., sorted by numeric value.
        """
        nums = self.gain_num.enum_strs
        units = self.gain_unit.enum_strs
        # Build all pairs and compute numeric value
        gain_pairs = []
        for n in nums:
            for u in units:
                value = self._parse_gain_value(n, u)
                gain_pairs.append(((n, u), value))
        # Sort by value
        gain_pairs.sort(key=lambda x: x[1])
        self._sorted_gain_pairs = [pair[0] for pair in gain_pairs]
        return [f"{n} {u}" for (n, u) in self._sorted_gain_pairs]

    def _parse_gain_value(self, n, u):
        """
        Convert num/unit to a numeric value for sorting.
        """
        # Remove any non-numeric characters from n
        try:
            num = float(re.sub(r"[^0-9.eE+-]", "", n))
        except Exception:
            num = 1.0
        # Map unit to multiplier
        unit_map = {
            "pA/V": 1e-12,
            "nA/V": 1e-9,
            "uA/V": 1e-6,
            "mA/V": 1e-3,
            "pA": 1e-12,
            "nA": 1e-9,
            "uA": 1e-6,
            "mA": 1e-3,
            "pA/V": 1e-12,
            "nA/V": 1e-9,
            "uA/V": 1e-6,
            "mA/V": 1e-3,
        }
        mult = unit_map.get(u, 1.0)
        return num * mult

    @property
    def gain_index(self):
        """
        Index of the current gain (num, unit) combination in gain_choices.
        Returns
        -------
        int
            Index in gain_choices corresponding to current gain_num and gain_unit.
        """
        nums = self.gain_num.enum_strs
        units = self.gain_unit.enum_strs
        try:
            num_idx = self.gain_num._index_value
            unit_idx = self.gain_unit._index_value
            current = (nums[num_idx], units[unit_idx])
            if hasattr(self, "_sorted_gain_pairs"):
                sorted_pairs = self._sorted_gain_pairs
            else:
                # fallback: regenerate
                self.gain_choices
                sorted_pairs = self._sorted_gain_pairs
            return sorted_pairs.index(current)
        except Exception:
            return 0

    @gain_index.setter
    def gain_index(self, idx):
        """
        Set gain_num and gain_unit based on a single index into gain_choices.
        Parameters
        ----------
        idx : int
            Index in gain_choices
        """
        if not hasattr(self, "_sorted_gain_pairs"):
            self.gain_choices
        sorted_pairs = self._sorted_gain_pairs
        n, u = sorted_pairs[idx]
        nums = self.gain_num.enum_strs
        units = self.gain_unit.enum_strs
        num_idx = nums.index(n)
        unit_idx = units.index(u)
        self.set_gain(num_idx, unit_idx)

    def set_gain(self, num_idx, unit_idx):
        """
        Set both gain_num and gain_unit by index.
        Parameters
        ----------
        num_idx : int
            Index in gain_num.enum_strs
        unit_idx : int
            Index in gain_unit.enum_strs
        """
        self.gain_num.set(num_idx)
        self.gain_unit.set(unit_idx)
