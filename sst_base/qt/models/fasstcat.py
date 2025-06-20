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
        self.gas_name = obj.gas_name if hasattr(obj, "gas_name") else name

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


class InputLineModel:
    """
    Model for a single input line with gas selection and gas flows.

    This represents the physical input with its gas selection and A/B gas flows.
    """

    def __init__(self, name, obj, group, long_name, **kwargs):
        self.name = name
        self.obj = obj
        self.group = group
        self.label = long_name

        # Create models for gas selection and gas name
        self.gas_selection = EnumModel(
            name=f"{name}_gas_selection", obj=obj.gas_selection, group=group, long_name=f"{name} Gas Selection"
        )

        self.gas_name = PVModelRO(
            name=f"{name}_gas_name", obj=obj.gas_name, group=group, long_name=f"{name} Gas Name"
        )

        # Create models for A and B gas flows
        self.a_flow = GasFlowModel(name=f"{name}_a_flow", obj=obj.a, group=group, long_name=f"{name} A Line Flow")

        self.b_flow = GasFlowModel(name=f"{name}_b_flow", obj=obj.b, group=group, long_name=f"{name} B Line Flow")


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

        # Create input line models
        self.input_lines = []
        self.real_motors = []

        for i in range(1, 8):
            input_name = f"input_{i}"
            input_obj = getattr(obj, input_name, None)

            if input_obj is not None:
                print(f"Creating input line model for {input_name}")
                input_model = InputLineModel(input_name, input_obj, group, f"Input {i}")
                self.input_lines.append(input_model)

                # Add A and B flows to real_motors for motor tuple display
                self.real_motors.append(input_model.a_flow)
                self.real_motors.append(input_model.b_flow)

        # For compatibility with switchable views, we use real_motors as pseudo_motors
        # since they are what we want to show by default
        self.pseudo_motors = self.real_motors

        # Create a mapping from gas names to gas models for easy access
        self.gas_models = {}
        for input_model in self.input_lines:
            # Map by gas name from the PV
            a_gas_name = input_model.gas_name.value or f"{input_model.name}_A"
            b_gas_name = input_model.gas_name.value or f"{input_model.name}_B"

            self.gas_models[a_gas_name] = input_model.a_flow
            self.gas_models[b_gas_name] = input_model.b_flow

    def get_gas_model(self, gas_name):
        """Get gas flow model by name."""
        return self.gas_models.get(gas_name)

    def get_all_gas_models(self):
        """Get all gas flow models."""
        return list(self.gas_models.values())

    def get_line_a_models(self):
        """Get gas flow models for line A."""
        return [input_model.a_flow for input_model in self.input_lines]

    def get_line_b_models(self):
        """Get gas flow models for line B."""
        return [input_model.b_flow for input_model in self.input_lines]

    def get_input_line_models(self):
        """Get all input line models."""
        return self.input_lines


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
        self.gas_names = obj.get_enabled_gas_names()

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

    def get_line_a_models(self):
        """Get gas flow models for line A."""
        return self.gas_flows.get_line_a_models()

    def get_line_b_models(self):
        """Get gas flow models for line B."""
        return self.gas_flows.get_line_b_models()

    def stop_line_a_flows(self):
        """Stop all gas flows on line A."""
        self.obj.stop_line_a_flows()

    def stop_line_b_flows(self):
        """Stop all gas flows on line B."""
        self.obj.stop_line_b_flows()

    def stop_all_flows(self):
        """Stop all gas flows on all lines."""
        self.obj.stop_all_flows()

    def get_input_line_models(self):
        """Get all input line models."""
        return self.gas_flows.get_input_line_models()

    def get_line_a_gases(self):
        """Get list of gas names on line A."""
        return self.obj.get_line_a_gases()

    def get_line_b_gases(self):
        """Get list of gas names on line B."""
        return self.obj.get_line_b_gases()
