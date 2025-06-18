"""
Qt view for FASSTCAT gas control and temperature management.
"""

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
)
from qtpy.QtCore import Qt, Property, Signal, Slot
from qtpy.QtGui import QFont

from nbs_gui.views.views import AutoControl, AutoMonitor
from nbs_gui.views.motor_tuple import MotorTupleControl


class EurothermMonitor(QGroupBox):
    """
    Widget for monitoring Eurotherm temperature control.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__("Temperature Monitor", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add monitors for each component
        layout.addWidget(AutoMonitor(model.setpoint, parent_model))
        layout.addWidget(AutoMonitor(model.rate, parent_model))
        layout.addWidget(AutoMonitor(model.readback, parent_model))

        self.setLayout(layout)


class EurothermControl(QGroupBox):
    """
    Widget for controlling Eurotherm temperature.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__("Temperature Control", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add controls for each component
        layout.addWidget(AutoControl(model.setpoint, parent_model))
        layout.addWidget(AutoControl(model.rate, parent_model))

        # Add start ramp button
        self.start_ramp_button = QPushButton("Start Temperature Ramp")
        self.start_ramp_button.clicked.connect(self.start_ramp)
        layout.addWidget(self.start_ramp_button)

        self.setLayout(layout)

    @Slot()
    def start_ramp(self):
        """Start temperature ramp."""
        self.parent_model.start_temperature_ramp()


class PulseMonitor(QGroupBox):
    """
    Widget for monitoring pulse control.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__("Pulse Monitor", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add monitors for each component
        layout.addWidget(AutoMonitor(model.line_select, parent_model))
        layout.addWidget(AutoMonitor(model.line_mode, parent_model))
        layout.addWidget(AutoMonitor(model.count, parent_model))
        layout.addWidget(AutoMonitor(model.time, parent_model))
        layout.addWidget(AutoMonitor(model.status, parent_model))

        self.setLayout(layout)


class PulseControl(QGroupBox):
    """
    Widget for controlling pulse operations.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__("Pulse Control", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add controls for each component
        layout.addWidget(AutoControl(model.line_select, parent_model))
        layout.addWidget(AutoControl(model.line_mode, parent_model))
        layout.addWidget(AutoControl(model.count, parent_model))
        layout.addWidget(AutoControl(model.time, parent_model))

        # Add start pulses button
        self.start_pulses_button = QPushButton("Start Pulses")
        self.start_pulses_button.clicked.connect(self.start_pulses)
        layout.addWidget(self.start_pulses_button)

        self.setLayout(layout)

    @Slot()
    def start_pulses(self):
        """Start pulse sequence."""
        # Trigger the pulse sequence by setting trigger to 1
        self.model.obj.trigger.put(1)


class GasFlowsController(MotorTupleControl):
    """
    Control widget for gas flows with apply button.

    This extends MotorTupleControl to add an "Apply All Flows" button
    that triggers the flow apply mechanism.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__(model=model, parent_model=parent_model, title=model.label, **kwargs)

        # Add apply flows button at the bottom
        self.apply_flows_button = QPushButton("Apply All Flows")
        self.apply_flows_button.clicked.connect(self.apply_flows)
        self.layout.addWidget(self.apply_flows_button)

    @Slot()
    def apply_flows(self):
        """Apply all gas flow setpoints."""
        self.parent_model.apply_flows()


class FasstcatMonitor(QWidget):
    """
    Widget for monitoring FASSTCAT components.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__(parent)
        self.model = model
        self.parent_model = parent_model
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout()

        # Left column - Temperature and Pulse monitors
        left_column = QVBoxLayout()

        # Temperature monitor
        left_column.addWidget(EurothermMonitor(self.model.eurotherm, self.parent_model))

        # Pulse monitor
        left_column.addWidget(PulseMonitor(self.model.pulse, self.parent_model))

        layout.addLayout(left_column)

        # Right column - Gas flow monitor
        right_column = QVBoxLayout()
        right_column.addWidget(AutoMonitor(self.model.gas_flows, self.parent_model))

        layout.addLayout(right_column)

        self.setLayout(layout)


class FasstcatController(QWidget):
    """
    Widget for controlling FASSTCAT components.
    """

    def __init__(self, model, parent_model, parent=None, **kwargs):
        super().__init__(parent)
        self.model = model
        self.parent_model = parent_model
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout()

        # Left column - Temperature and Pulse controls
        left_column = QVBoxLayout()

        # Temperature control
        left_column.addWidget(EurothermControl(self.model.eurotherm, self.parent_model))

        # Pulse control
        left_column.addWidget(PulseControl(self.model.pulse, self.parent_model))

        layout.addLayout(left_column)

        # Right column - Gas flow control
        right_column = QVBoxLayout()
        right_column.addWidget(AutoControl(self.model.gas_flows, self.parent_model))

        layout.addLayout(right_column)

        self.setLayout(layout)
