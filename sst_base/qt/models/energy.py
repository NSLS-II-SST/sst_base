from ..views.energy import SST1EnergyControl, SST1EnergyMonitor
from nbs_gui.models import PseudoPositionerModel, PVModel


class GratingModel(PVModel):
    def __init__(self, name, obj, group, long_name, **kwargs):
        super().__init__(name, obj.readback, group, long_name, **kwargs)
        self.grating = obj


# Copied from ucal as an example
class SST1EnergyModel:
    default_controller = SST1EnergyControl
    default_monitor = SST1EnergyMonitor

    def __init__(
        self,
        name,
        obj,
        group,
        long_name,
        **kwargs,
    ):
        print("Initializing Energy")
        self.name = name
        self.obj = obj
        self.energy = PseudoPositionerModel(name, obj, group, name)
        self.grating_motor = GratingModel(
            name=obj.monoen.gratingx.name,
            obj=obj.monoen.gratingx,
            group=group,
            long_name=f"{name} Grating",
        )
        self.cff = PVModel(obj.monoen.cff.name, obj.monoen.cff, group=group, long_name=f"{name} CFF")
        self.group = group
        self.label = long_name
        for key, value in kwargs.items():
            setattr(self, key, value)
        print("Done Initializing Energy")
