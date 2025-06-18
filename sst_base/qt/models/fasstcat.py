"""
Qt model for FASSTCAT gas control and temperature management.
"""

# Import motor models from nbs-gui
from nbs_gui.models.motors import PVPositionerModel, MultiMotorModel
from nbs_gui.models.base import PVModel, EnumModel, PVModelRO
from nbs_gui.models.base import initialize_with_retry
from nbs_gui.views.motor_tuple import MotorTupleMonitor

# Import view widgets
from ..views.fasstcat import (
    EurothermControl,
    EurothermMonitor,
    PulseControl,
    PulseMonitor,
    FasstcatController,
    FasstcatMonitor,
    GasFlowsController,
)


class GasFlowModel(PVPositionerModel):
    """
    Model for a single gas flow control, inheriting from PVPositionerModel.

    This provides all the motor-like functionality (position, setpoint, moving status)
    while adapting it to work with gas flow Ophyd devices that use PVPositionerPC.
    """

    def __init__(self, name, obj, group, long_name, **kwargs):
        # Initialize the parent PVPositionerModel
        super().__init__(name=name, obj=obj, group=group, long_name=long_name)
        self.gas_name = obj.gas_name

    """
        self._initialize()

    @initialize_with_retry
    def _initialize(self):
        print("Initializing GasFlowModel")
        if not super()._initialize():
            return False
        return True
    """

    def _check_moving(self):
        """
        Override to check if gas flow is "moving".
        For PVPositionerPC, motion completion is determined by put completion,
        so we rely on the underlying Ophyd device's moving status.
        """
        try:
            # For PVPositionerPC, the moving status is handled by put completion
            # We can still check if setpoint and readback differ as a fallback
            setpoint = self._obj_setpoint.get(timeout=0.2)
            readback = self._obj_readback.get(timeout=0.2)

            if setpoint is None or readback is None:
                return False

            # For gas flows, consider moving if difference is more than 1% of setpoint or 0.1 sccm
            threshold = max(abs(setpoint) * 0.01, 0.1)
            return abs(setpoint - readback) > threshold

        except Exception:
            return False

    def set(self, value):
        """
        Override to set gas flow setpoint.
        For gas flows, we need to trigger Flow_Apply after setting the setpoint.
        """
        print(f"[{self.gas_name}] Setting gas flow to {value} sccm")
        self._target = value
        self._setpoint = value
        self.setpointChanged.emit(self._setpoint)

        # Set the setpoint
        self._obj_setpoint.put(value)

        # Note: Flow_Apply should be triggered separately to actually apply the flow
        # This is handled by the FasstcatModel.apply_flows() method
        print(f"[{self.gas_name}] Done setting gas flow setpoint")
        return value


class GasFlowsTupleModel(MultiMotorModel):
    """
    Model for a tuple of gas flow controls.

    This model groups all gas flow models together in a compact, tabular layout
    similar to motor tuples, while providing access to individual gas models.
    """

    default_controller = GasFlowsController
    default_monitor = MotorTupleMonitor

    def __init__(self, name, obj, group, long_name, **kwargs):
        # Initialize parent MultiMotorModel
        super().__init__(
            name=name, obj=obj, group=group, long_name=long_name, show_real_motors_by_default=True, **kwargs
        )

        # Store gas names for reference
        self.gas_names = obj.gas_names

        # Create gas flow models directly
        self.real_motors = []
        for gas_name in obj.gas_names:
            print(f"Creating gas flow model for {gas_name}")
            gas_device = getattr(obj, gas_name)
            gas_model = GasFlowModel(gas_name, gas_device, group, f"Gas Flow {gas_name}")
            self.real_motors.append(gas_model)

        # For compatibility with switchable views, we use real_motors as pseudo_motors
        # since they are what we want to show by default
        self.pseudo_motors = self.real_motors

        # Create a mapping from gas names to gas models for easy access
        self.gas_models = {}
        for gas_model in self.real_motors:
            self.gas_models[gas_model.gas_name] = gas_model

    def get_gas_model(self, gas_name):
        """Get gas flow model by name."""
        return self.gas_models.get(gas_name)

    def get_all_gas_models(self):
        """Get all gas flow models."""
        return list(self.gas_models.values())


class EurothermModel:
    """
    Model for Eurotherm temperature control.
    """

    default_controller = EurothermControl
    default_monitor = EurothermMonitor

    def __init__(self, name, obj, group, **kwargs):
        self.obj = obj
        # Create sub-models for each temperature component
        self.setpoint = PVModel(
            name=f"{name}_setpoint", obj=obj.setpoint, group=group, long_name=f"{name} Temperature Setpoint"
        )

        self.rate = PVModel(name=f"{name}_rate", obj=obj.rate, group=group, long_name=f"{name} Temperature Rate")

        self.readback = PVModelRO(
            name=f"{name}_readback", obj=obj.readback, group=group, long_name=f"{name} Temperature Readback"
        )


class PulseModel:
    """
    Model for pulse control.
    """

    default_controller = PulseControl
    default_monitor = PulseMonitor

    def __init__(self, name, obj, group, long_name, **kwargs):
        self.obj = obj
        # Create sub-models for each pulse component
        self.line_select = EnumModel(
            name=f"{name}_line_select", obj=obj.line_select, group=group, long_name=f"{name} Line Select"
        )
        self.line_mode = EnumModel(
            name=f"{name}_line_mode", obj=obj.line_mode, group=group, long_name=f"{name} Line Mode"
        )

        self.count = PVModel(name=f"{name}_count", obj=obj.count, group=group, long_name=f"{name} Pulse Count")

        self.time = PVModel(name=f"{name}_time", obj=obj.time, group=group, long_name=f"{name} Pulse Time")

        self.status = EnumModel(
            name=f"{name}_status", obj=obj.status, group=group, long_name=f"{name} Pulse Status"
        )


class FasstcatModel:
    """
    Qt model for FASSTCAT gas control and temperature management.

    This model follows the modular pattern used in SST1EnergyModel,
    with separate models for each major component.
    """

    default_controller = FasstcatController
    default_monitor = FasstcatMonitor

    def __init__(self, name, obj, group, long_name, **kwargs):
        print("Initializing FasstcatModel")
        self.name = name
        self.obj = obj
        self.group = group
        self.label = long_name

        # Create component models
        self.eurotherm = EurothermModel(
            name=f"{name}_eurotherm", obj=obj.eurotherm, group=group, long_name=f"{name} Eurotherm"
        )

        self.pulse = PulseModel(name=f"{name}_pulse", obj=obj.pulse, group=group, long_name=f"{name} Pulse")

        # Create gas flows tuple model
        self.gas_flows = GasFlowsTupleModel(
            name=f"{name}_gas_flows", obj=obj, group=group, long_name=f"{name} Gas Flows"
        )

        # Store gas names for reference
        self.gas_names = obj.gas_names

        # Set additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

        print("Done Initializing FasstcatModel")

    def start_temperature_ramp(self):
        """Start temperature ramp with current setpoint and rate."""
        setpoint = self.eurotherm.setpoint.value
        rate = self.eurotherm.rate.value
        self.obj.set_temperature_ramp(setpoint, rate)

    def apply_flows(self):
        """Apply all gas flow setpoints."""
        self.obj.apply_flows()

    def get_gas_model(self, gas_name):
        """Get gas flow model by name."""
        return self.gas_flows.get_gas_model(gas_name)

    def get_all_gas_models(self):
        """Get all gas flow models."""
        return self.gas_flows.get_all_gas_models()
