from qtpy.QtCore import Signal, QTimer
from nbs_gui.models import MotorModel, PseudoSingleModel
from nbs_gui.models.base import BaseModel
from ...slits import QuadSlitsBase
from ..views.quadSlits import QuadSlitsMonitor, QuadSlitsControl


class QuadSlitsModel(BaseModel):
    """
    Qt model for quad slits device.

    Parameters
    ----------
    name : str
        Name of the slits device
    obj : QuadSlitsBase
        The ophyd Slits object to model (either QuadSlits or FMBOQuadSlits)
    group : str
        Group this model belongs to
    long_name : str
        Human readable name for the slits
    """

    default_monitor = QuadSlitsMonitor
    default_controller = QuadSlitsControl

    def __init__(self, name, obj, group, long_name, **kwargs):
        if not isinstance(obj, QuadSlitsBase):
            raise TypeError(f"Expected QuadSlits object, got {type(obj)}")

        super().__init__(name, obj, group, long_name, **kwargs)

        # Create motor models for pseudo motors
        self.vsize = PseudoSingleModel(
            name=f"{name}_vsize", obj=obj.vsize, group=group, long_name=f"{long_name} V Size"
        )

        self.vcenter = PseudoSingleModel(
            name=f"{name}_vcenter", obj=obj.vcenter, group=group, long_name=f"{long_name} V Center"
        )

        self.hsize = PseudoSingleModel(
            name=f"{name}_hsize", obj=obj.hsize, group=group, long_name=f"{long_name} H Size"
        )

        self.hcenter = PseudoSingleModel(
            name=f"{name}_hcenter", obj=obj.hcenter, group=group, long_name=f"{long_name} H Center"
        )

        # Create motor models for real motors
        self.top = MotorModel(name=f"{name}_top", obj=obj.top, group=group, long_name=f"{long_name} Top")

        self.bottom = MotorModel(
            name=f"{name}_bottom", obj=obj.bottom, group=group, long_name=f"{long_name} Bottom"
        )

        self.inboard = MotorModel(
            name=f"{name}_inboard", obj=obj.inboard, group=group, long_name=f"{long_name} Inboard"
        )

        self.outboard = MotorModel(
            name=f"{name}_outboard", obj=obj.outboard, group=group, long_name=f"{long_name} Outboard"
        )

        # Group motors for easy access
        self.pseudo_motors = [self.vsize, self.vcenter, self.hsize, self.hcenter]
        self.real_motors = [self.top, self.bottom, self.inboard, self.outboard]

    def stop(self):
        """Stop all slit motors."""
        self.obj.stop()
