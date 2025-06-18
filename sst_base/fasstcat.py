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
    """

    setpoint = Component(EpicsSignal, "SP", kind="config")
    readback = Component(EpicsSignalRO, "RB")

    def __init__(self, prefix, gas_name, **kwargs):
        self.gas_name = gas_name
        super().__init__(prefix, **kwargs)


class EurothermControl(Device):
    """
    Temperature control for Eurotherm.
    """

    setpoint = Component(EpicsSignal, "Temp_Setpoint", kind="config")
    rate = Component(EpicsSignal, "Temp_Rate", kind="config")
    start = Component(EpicsSignal, "Temp_Trigger", kind="omitted")
    readback = Component(EpicsSignalRO, "Temp_Readback")


class PulseControl(Device):
    """
    Pulse mode control.
    """

    line_select = Component(EpicsSignal, "Line_Select", kind="config")
    line_mode = Component(EpicsSignal, "Line_Mode", kind="config")
    count = Component(EpicsSignal, "Pulse_Count", kind="config")
    time = Component(EpicsSignal, "Pulse_Time", kind="config")
    start = Component(EpicsSignal, "Pulse_Trigger", kind="omitted")
    status = Component(EpicsSignalRO, "Pulse_Status", kind="config")


def create_fasstcat_class(gases=None):
    """
    Create Fasstcat device class with gas flow components.

    Parameters
    ----------
    gases : list, optional
        List of gas names to create flow controllers for.
        If None, uses default gas list.

    Returns
    -------
    type
        Fasstcat device class with all gas components defined.
    """
    if gases is None:
        # Default gases from the system
        gases = [
            "H2_A",
            "H2_B",
            "D2_A",
            "D2_B",
            "O2_A",
            "O2_B",
            "CO_AH",
            "CO_AL",
            "CO_BH",
            "CO_BL",
            "CO2_AH",
            "CO2_AL",
            "CO2_BH",
            "CO2_BL",
            "CH4_A",
            "CH4_B",
            "C2H6_A",
            "C2H6_B",
            "C3H8_A",
            "C3H8_B",
            "He_A",
            "He_B",
            "Ar_A",
            "Ar_B",
            "N2_A",
            "N2_B",
        ]

    # Start with base class attributes
    class_attrs = {
        "__doc__": """
        FASSTCAT gas control and temperature management device.

        This device provides control over gas flows, temperature ramping,
        and pulse modes for the FASSTCAT system.

        Parameters
        ----------
        prefix : str
            PV prefix for the FASSTCAT IOC
        """,
        # Temperature control
        "eurotherm": Component(EurothermControl, "eurotherm}"),
        # Pulse control
        "pulse": Component(PulseControl, "pulse}"),
        # Flow apply trigger
        "flow_apply": Component(EpicsSignal, "flowsms}Flow_Apply"),
        # Store gas names for reference
        "gas_names": gases,
    }

    # Add gas flow positioners
    for gas in gases:
        class_attrs[gas] = Component(GasFlowPositioner, f"flowsms}}{gas}_", gas_name=gas)

    # Create the class
    Fasstcat = type("Fasstcat", (Device,), class_attrs)

    # Add methods
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

    # Add methods to the class
    Fasstcat.apply_flows = apply_flows
    Fasstcat.set_temperature_ramp = set_temperature_ramp
    Fasstcat.set_pulse_sequence = set_pulse_sequence
    Fasstcat.start_pulses = start_pulses

    return Fasstcat


# Create default Fasstcat class
Fasstcat = create_fasstcat_class()
