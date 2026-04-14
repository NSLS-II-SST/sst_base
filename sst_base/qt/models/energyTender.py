from ..views.energyTender import SST2EnergyControl, SST2EnergyMonitor
from nbs_gui.models import (
    PVPositionerModel,
    MultiMotorModel,
    MotorModel,
    EnumModel,
    PVModel,
)


class SST2EnergyModel:
    default_controller = SST2EnergyControl
    default_monitor = SST2EnergyMonitor

    def __init__(
        self,
        name,
        obj,
        group,
        long_name,
        **kwargs,
    ):
        print("Initializing Tender Energy")
        self.name = name
        self.obj = obj
        self.energy = SST2EnergyAxes(name, obj, group, name)
        self.crystal = EnumModel(
            obj.mono.crystal.name,
            obj.mono.crystal,
            group=group,
            long_name="SST2 Crystal",
        )
        self.dcm_mode = EnumModel(
            obj.mono.mode.name,
            obj.mono.mode,
            group=group,
            long_name="SST2 DCM Mode"
        )
        self.harmonic = PVModel(
            obj.harmonic.name, obj.harmonic, group=group, long_name="Harmonic"
        )
        self.real_motors = self.energy.real_motors
        self.group = group
        self.label = long_name
        for key, value in kwargs.items():
            setattr(self, key, value)
        print("Done Initializing Energy")

    def iter_models(self):
        yield from (self.energy,
                    self.crystal,
                    self.dcm_mode,
                    self.harmonic)
                    


class SST2EnergyAxes(MultiMotorModel):
    """
    Model for pseudo positioners with both real and pseudo motors.

    Parameters
    ----------
    name : str
        Name of the model
    obj : object
        The pseudo positioner object
    group : str
        Group this model belongs to
    long_name : str
        Human readable name
    show_real_motors_by_default : bool, optional
        Whether to show real motors by default instead of pseudo motors
    """

    def __init__(
        self, name, obj, group, long_name, show_real_motors_by_default=False, **kwargs
    ):
        super().__init__(
            name,
            obj,
            group,
            long_name,
            show_real_motors_by_default=show_real_motors_by_default,
            **kwargs,
        )

        # Create models for real motors
        #real_axes = [obj.u42, obj.mono.bragg, obj.mono.x2roll, obj.mono.x2pitch]
        real_axes = [obj.u42, obj.monoen]
        self.real_motors = [
            MotorModel(
                name=real_axis.name,
                obj=real_axis,
                group=group,
                long_name=real_axis.name,
            )
            for real_axis in real_axes
        ]
        pseudo_axes = [obj.flycontrol]
        # Create models for pseudo motors
        self.pseudo_motors = [
            PVPositionerModel(
                name=ps_axis.name,
                obj=ps_axis,
                group=group,
                long_name=ps_axis.name,
            )
            for ps_axis in pseudo_axes
        ]

    def iter_models(self):
        yield from self.real_motors + self.pseudo_motors
        
