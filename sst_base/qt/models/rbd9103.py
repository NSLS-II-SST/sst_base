from nbs_gui.models.base import PVModel, EnumModel
from nbs_gui.models.misc import ScalarModel
from ..views.rbd9103 import CompactRBD9103Monitor


class RBD9103Model(ScalarModel):
    """
    Qt model for RBD9103 picoammeter detector.

    Parameters
    ----------
    name : str
        Name of the detector
    obj : RBD9103
        The ophyd RBD9103 object to model
    group : str
        Group this model belongs to
    long_name : str
        Human readable name for the detector
    """

    default_monitor = CompactRBD9103Monitor
    default_controller = None  # No full controller for now

    def __init__(self, name, obj, group, long_name, **kwargs):
        super().__init__(name, obj, group, long_name, **kwargs)
        self.range_ctrl = EnumModel(
            name=f"{name}_range_ctrl",
            obj=obj.rbd9103.range_ctrl,
            group=group,
            long_name=f"{long_name} Range Control",
        )
        self.range_actual = PVModel(
            name=f"{name}_range_actual",
            obj=obj.rbd9103.range_actual,
            group=group,
            long_name=f"{long_name} Range Actual",
        )
