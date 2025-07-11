"""
FASSTCAT Ophyd device for gas control and temperature management.

This device provides an interface to the FASSTCAT system for Bluesky plans.
"""

from ophyd import Device, Component, PVPositionerPC, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FC


class GasFlowPositioner(PVPositionerPC):
    """
    PVPositionerPC for gas flow control.

    Provides setpoint and readback for individual gas flows.
    Uses put completion to determine when motion is done.
    Prevents setting setpoints when the line is not enabled.
    """

    setpoint = Component(EpicsSignal, "SP", kind="config")
    readback = Component(EpicsSignalRO, "RB")
    enabled = Component(EpicsSignalRO, "ENABLED", kind="config")

    def set(self, value):
        """
        Set the setpoint value, but only if the line is enabled.

        Parameters
        ----------
        value : float
            The setpoint value to set

        Returns
        -------
        Status
            The status of the set operation
        """
        if not self.enabled.get():
            raise ValueError(f"Cannot set gas flow setpoint: line is not enabled")
        return super().set(value)


class InputLine(Device):
    """
    Represents a single input line with A and B gas flows.

    Each input has a gas selection and can have gas flows on both A and B lines.
    The gas selection determines which gas is available for flow control.
    The enabled status indicates whether each line has an MFC configured.
    """

    # Gas flow for line A (if present)
    a = Component(GasFlowPositioner, "A_", name="a")

    # Gas flow for line B (if present)
    b = Component(GasFlowPositioner, "B_", name="b")

    # Gas selection (determines which gas is available)
    gas_selection = Component(EpicsSignal, "Gas_Selection", string=True, kind="config")

    # Gas name (read from PV, reflects current selection)
    gas_name = Component(EpicsSignalRO, "Gas_Name", string=True, kind="config")


class EurothermControl(Device):
    """
    Temperature control for Eurotherm.

    Attributes
    ----------
    setpoint : EpicsSignal
        Temperature setpoint (degC).
    rate : EpicsSignal
        Ramp rate (degC/min).
    start : EpicsSignal
        Trigger to start ramp.
    readback : EpicsSignalRO
        Current temperature (degC).
    hold : EpicsSignal
        Hold at current temperature for a specified time (minutes).
    status : EpicsSignalRO
        Status of the Eurotherm controller (0=idle, 1=running).
    """

    setpoint = Component(EpicsSignal, "Temp_Setpoint", kind="config")
    rate = Component(EpicsSignal, "Temp_Rate", kind="config")
    start = Component(EpicsSignal, "Temp_Trigger", kind="omitted")
    readback = Component(EpicsSignalRO, "Temp_Readback")
    hold = Component(EpicsSignal, "Temp_Hold", kind="config")
    status = Component(EpicsSignalRO, "Status", kind="config", string=True)


class PulseControl(Device):
    """
    Pulse mode control.

    Attributes
    ----------
    line_select : EpicsSignal
        Line selection (A or B).
    line_mode : EpicsSignal
        Mode (continuous or pulses).
    count : EpicsSignal
        Number of pulses.
    time : EpicsSignal
        Time per pulse (seconds).
    start : EpicsSignal
        Trigger to start pulse sequence.
    pulse_status : EpicsSignalRO
        Status of the pulse controller (0=idle, 1=running).
    """

    line_select = Component(EpicsSignal, "Line_Select", string=True, kind="config")
    line_mode = Component(EpicsSignal, "Line_Mode", string=True, kind="config")
    count = Component(EpicsSignal, "Pulse_Count", kind="config")
    time = Component(EpicsSignal, "Pulse_Time", kind="config")
    start = Component(EpicsSignal, "Pulse_Trigger", kind="omitted")
    status = Component(EpicsSignalRO, "Pulse_Status", kind="config", string=True)


class Fasstcat(Device):
    """
    FASSTCAT gas control and temperature management device.

    This device provides control over gas flows, temperature ramping,
    and pulse modes for the FASSTCAT system.

    Parameters
    ----------
    prefix : str
        PV prefix for the FASSTCAT IOC
    """

    # Temperature control
    eurotherm = Component(EurothermControl, "eurotherm}")

    # Pulse control
    pulse = Component(PulseControl, "pulse}")

    # Flow apply trigger
    flow_apply = Component(EpicsSignal, "flowsms}Flow_Apply")

    # Segment status
    segment_status = Component(EpicsSignalRO, "}Segment_Status", kind="config", string=True)

    # Input lines - each represents a physical input with valve and gas flows
    input_1 = Component(InputLine, "flowsms}Input_1_", name="input_1")
    input_2 = Component(InputLine, "flowsms}Input_2_", name="input_2")
    input_3 = Component(InputLine, "flowsms}Input_3_", name="input_3")
    input_4 = Component(InputLine, "flowsms}Input_4_", name="input_4")
    input_5 = Component(InputLine, "flowsms}Input_5_", name="input_5")
    input_6 = Component(InputLine, "flowsms}Input_6_", name="input_6")
    input_7 = Component(InputLine, "flowsms}Input_7_", name="input_7")

    def __init__(self, prefix, name="fasstcat", **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)
        self._enabled_gases = set()
        self._update_enabled_gases()

    def _update_enabled_gases(self):
        """Update the set of enabled gases by walking through inputs."""
        enabled_gases = set()

        for i in range(1, 8):
            input_line = getattr(self, f"input_{i}")
            if hasattr(input_line, "gas_selection"):
                # Get the enum strings from the gas selection PV
                try:
                    enum_strings = input_line.gas_selection.enum_strs
                    if enum_strings:
                        enabled_gases.update(enum_strings)
                except Exception as e:
                    print(f"Warning: Could not read gas selection for input {i}: {e}")

        self._enabled_gases = enabled_gases

    def get_enabled_gas_names(self):
        """Get list of enabled gas flow names."""
        self._update_enabled_gases()
        return sorted(list(self._enabled_gases))

    def is_gas_enabled(self, gas_key):
        """Check if a specific gas flow is enabled."""
        self._update_enabled_gases()
        return gas_key in self._enabled_gases

    def apply_flows(self):
        """Apply all gas flow setpoints to readbacks."""
        self.flow_apply.put(1)

    def set_temperature_ramp(self, setpoint, rate):
        """
        Set temperature ramp parameters and start ramp.

        Parameters
        ----------
        setpoint : float
            Target temperature (degC)
        rate : float
            Ramp rate (degC/min)
        """
        self.eurotherm.setpoint.put(setpoint)
        self.eurotherm.rate.put(rate)
        self.eurotherm.start.put(1)

    def set_pulse_sequence(self, line_select, line_mode, count, time):
        """
        Set pulse sequence parameters.

        Parameters
        ----------
        line_select : str
            Line selection ('A' or 'B')
        line_mode : str
            Mode ('continuous' or 'pulses')
        count : int
            Number of pulses
        time : float
            Time per pulse (seconds)
        """
        # Convert strings to enum indices
        line_map = {"A": 0, "B": 1}
        mode_map = {"continuous": 0, "pulses": 1}

        self.pulse.line_select.put(line_map[line_select])
        self.pulse.line_mode.put(mode_map[line_mode])
        self.pulse.count.put(count)
        self.pulse.time.put(time)

    def start_pulses(self):
        """Start the pulse sequence."""
        self.pulse.start.put(1)

    def get_input_lines(self):
        """Get all input line devices."""
        return [getattr(self, f"input_{i}") for i in range(1, 8)]

    def get_line_a_flows(self):
        """Get all A line gas flows."""
        flows = []
        for i in range(1, 8):
            input_line = getattr(self, f"input_{i}")
            if hasattr(input_line, "a"):
                flows.append(input_line.a)
        return flows

    def get_line_b_flows(self):
        """Get all B line gas flows."""
        flows = []
        for i in range(1, 8):
            input_line = getattr(self, f"input_{i}")
            if hasattr(input_line, "b"):
                flows.append(input_line.b)
        return flows

    def stop_line_a_flows(self):
        """Stop all A line gas flows."""
        statuses = []
        for flow in self.get_line_a_flows():
            try:
                status = flow.setpoint.put(0.0)
                statuses.append(status)
            except ValueError as e:
                # Skip disabled lines
                print(f"Warning: {e}")
        return statuses

    def stop_line_b_flows(self):
        """Stop all B line gas flows."""
        statuses = []
        for flow in self.get_line_b_flows():
            try:
                status = flow.setpoint.put(0.0)
                statuses.append(status)
            except ValueError as e:
                # Skip disabled lines
                print(f"Warning: {e}")
        return statuses

    def stop_all_flows(self):
        """Stop all gas flows on all lines."""
        statuses = []
        statuses.extend(self.stop_line_a_flows())
        statuses.extend(self.stop_line_b_flows())
        return statuses
