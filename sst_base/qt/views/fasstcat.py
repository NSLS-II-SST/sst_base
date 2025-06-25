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
    QLineEdit,
    QComboBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from qtpy.QtCore import Qt, Property, Signal, Slot
from qtpy.QtGui import QFont, QPalette

from nbs_gui.views.views import AutoControl, AutoMonitor
from nbs_gui.views.motor_tuple import MotorTupleControl


class EurothermMonitor(QGroupBox):
    """
    Widget for monitoring Eurotherm temperature control.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
        super().__init__("Temperature Monitor", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add monitors for each component
        layout.addWidget(AutoMonitor(model.setpoint, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.rate, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.readback, parent_model=parent_model))

        self.setLayout(layout)


class EurothermControl(QGroupBox):
    """
    Widget for controlling Eurotherm temperature.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
        super().__init__("Temperature Control", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add controls for each component
        layout.addWidget(AutoControl(model.setpoint, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.readback, parent_model=parent_model))
        layout.addWidget(AutoControl(model.rate, parent_model=parent_model))

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

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
        super().__init__("Pulse Monitor", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add monitors for each component
        layout.addWidget(AutoMonitor(model.line_select, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.line_mode, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.count, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.time, parent_model=parent_model))
        layout.addWidget(AutoMonitor(model.status, parent_model=parent_model))

        self.setLayout(layout)


class PulseControl(QGroupBox):
    """
    Widget for controlling pulse operations.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
        super().__init__("Pulse Control", parent)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()

        # Add controls for each component
        layout.addWidget(AutoControl(model.line_select, parent_model=parent_model))
        layout.addWidget(AutoControl(model.line_mode, parent_model=parent_model))
        layout.addWidget(AutoControl(model.count, parent_model=parent_model))
        layout.addWidget(AutoControl(model.time, parent_model=parent_model))

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


class GasFlowLineWidget(QWidget):
    """
    Compact widget for a single gas flow line (A or B):
    readback, setpoint (current), setpoint entry, set, stop in one row.

    Parameters
    ----------
    gas_flow_model : object
        Model for the gas flow line, providing readback, setpoint, and signals.
    parent_model : object, optional
        The direct parent of the model in the widget/model hierarchy, if any. Defaults to None.
    parent : QWidget, optional
        The Qt parent widget.
    """

    def __init__(self, gas_flow_model, parent_model=None, parent=None):
        super().__init__(parent)
        self.gas_flow_model = gas_flow_model
        self.parent_model = parent_model
        self._last_setpoint = None
        self._last_readback = None
        self.setup_ui()
        self.update_enabled_state()
        self.update_colors()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.readback_label = QLabel("0.0")
        self.readback_label.setFixedWidth(38)
        self.readback_label.setAlignment(Qt.AlignCenter)
        self.readback_label.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 1px solid #ccc; padding: 1px; }"
        )
        layout.addWidget(self.readback_label)

        self.setpoint_label = QLabel("0.0")
        self.setpoint_label.setFixedWidth(38)
        self.setpoint_label.setAlignment(Qt.AlignCenter)
        self.setpoint_label.setStyleSheet(
            "QLabel { background-color: #e8f5e9; border: 1px solid #ccc; padding: 1px; }"
        )
        layout.addWidget(self.setpoint_label)

        self.setpoint_edit = QLineEdit("0.0")
        self.setpoint_edit.setFixedWidth(44)
        self.setpoint_edit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.setpoint_edit)

        self.set_button = QPushButton("Set")
        self.set_button.setFixedWidth(32)
        self.set_button.setFocusPolicy(Qt.NoFocus)
        self.set_button.clicked.connect(self.set_flow)
        layout.addWidget(self.set_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedWidth(38)
        self.stop_button.setFocusPolicy(Qt.NoFocus)
        self.stop_button.clicked.connect(self.stop_flow)
        layout.addWidget(self.stop_button)

        layout.addStretch(1)
        self.setLayout(layout)

        self.setpoint_edit.textChanged.connect(self.update_colors)
        self.gas_flow_model.valueChanged.connect(self.update_readback)
        self.gas_flow_model.setpointChanged.connect(self.update_setpoint)

    def update_enabled_state(self):
        enabled = self.gas_flow_model.line_enabled
        self.setEnabled(enabled)
        if enabled:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("QWidget { background-color: #e0e0e0; }")
            self.readback_label.setText("--")
            self.setpoint_label.setText("")
            self.setpoint_edit.setText("")

    def update_readback(self, value):
        if self.gas_flow_model.line_enabled:
            try:
                if value is not None:
                    formatted_value = f"{float(value):.1f}"
                    self.readback_label.setText(formatted_value)
                    self._last_readback = float(value)
                else:
                    self.readback_label.setText("--")
                    self._last_readback = None
            except (ValueError, TypeError):
                self.readback_label.setText("--")
                self._last_readback = None
        self.update_colors()

    def update_setpoint(self, value):
        if value is not None:
            try:
                formatted_value = f"{float(value):.1f}"
                self.setpoint_label.setText(formatted_value)
                self._last_setpoint = float(value)
            except (ValueError, TypeError):
                self.setpoint_label.setText("")
                self._last_setpoint = None
        self.update_colors()

    @Slot()
    def set_flow(self):
        try:
            value = float(self.setpoint_edit.text())
            self.gas_flow_model.set(value)
        except ValueError:
            pass

    @Slot()
    def stop_flow(self):
        self.setpoint_edit.setText("0.0")
        self.gas_flow_model.set(0.0)

    def update_colors(self):
        """
        Update the background color of the setpoint entry box based on state.

        - Yellow: setpoint entry differs from current setpoint (pending)
        - Green: setpoint matches readback (applied)
        - Default: otherwise
        """
        try:
            entry = float(self.setpoint_edit.text())
        except Exception:
            entry = None
        setpoint = self._last_setpoint
        readback = self._last_readback
        if entry is not None and setpoint is not None and entry != setpoint:
            self.setpoint_label.setStyleSheet("QLabel { background-color: #fff59d; }")
        elif setpoint is not None and readback is not None and setpoint == readback:
            self.setpoint_label.setStyleSheet("QLabel { background-color: #c8e6c9; }")
        else:
            self.setpoint_label.setStyleSheet("")


class CustomGasFlowsWidget(QGroupBox):
    """
    Custom gas flows widget with compact, aligned grid layout.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
        super().__init__("Gas Flows", parent)
        self.model = model
        self.parent_model = parent_model
        self.input_cells = {}
        self.setup_ui()

    def setup_ui(self):
        grid = QGridLayout()
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(2)

        # Header row
        header_font = QFont()
        header_font.setBold(True)
        grid.addWidget(self._header_label("Input", header_font), 0, 0, alignment=Qt.AlignCenter)
        grid.addWidget(self._header_label("Gas", header_font), 0, 1, alignment=Qt.AlignCenter)
        grid.addWidget(self._header_label("A Line", header_font), 0, 2, alignment=Qt.AlignCenter)
        grid.addWidget(self._header_label("B Line", header_font), 0, 3, alignment=Qt.AlignCenter)

        # Input rows
        for i, input_model in enumerate(self.model.get_input_line_models(), 1):
            # Input number
            input_num_label = QLabel(f"Line {str(i)}")
            input_num_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(input_num_label, i, 0)

            gas_layout = QHBoxLayout()
            gas_readback = QLabel(input_model.gas_name.value)
            gas_readback.setFixedWidth(80)
            gas_readback.setAlignment(Qt.AlignCenter)
            input_model.gas_name.valueChanged.connect(lambda value, label=gas_readback: label.setText(value))
            gas_layout.addWidget(gas_readback)

            # Gas selection dropdown
            gas_combo = QComboBox()
            gas_combo.addItems(input_model.gas_selection.enum_strs)
            gas_combo.setCurrentText(input_model.gas_name.value or "")
            gas_combo.setMinimumContentsLength(6)
            gas_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            gas_combo.setFixedWidth(80)
            gas_combo.currentTextChanged.connect(
                lambda text, im=input_model: self.on_gas_selection_changed(im, text)
            )
            gas_layout.addWidget(gas_combo)
            grid.addLayout(gas_layout, i, 1)

            # A line controls
            a_widget = GasFlowLineWidget(input_model.a_flow, self.parent_model)
            self.input_cells[f"input_{i}_a"] = a_widget
            grid.addWidget(a_widget, i, 2, alignment=Qt.AlignCenter)

            # B line controls
            b_widget = GasFlowLineWidget(input_model.b_flow, self.parent_model)
            self.input_cells[f"input_{i}_b"] = b_widget
            grid.addWidget(b_widget, i, 3, alignment=Qt.AlignCenter)

        # Bottom row: Send All/Stop All buttons
        nrows = len(self.model.get_input_line_models()) + 1
        a_send_all = QPushButton("Send All A")
        a_send_all.setFixedWidth(90)
        a_send_all.clicked.connect(self.send_all_a)

        a_stop_all = QPushButton("Stop All A")
        a_stop_all.setFixedWidth(90)
        a_stop_all.clicked.connect(self.stop_all_a)

        a_button_layout = QHBoxLayout()
        a_button_layout.addWidget(a_send_all)
        a_button_layout.addWidget(a_stop_all)
        grid.addLayout(a_button_layout, nrows, 2, alignment=Qt.AlignCenter)

        b_send_all = QPushButton("Send All B")
        b_send_all.setFixedWidth(90)
        b_send_all.clicked.connect(self.send_all_b)

        b_stop_all = QPushButton("Stop All B")
        b_stop_all.setFixedWidth(90)
        b_stop_all.clicked.connect(self.stop_all_b)

        b_button_layout = QHBoxLayout()
        b_button_layout.addWidget(b_send_all)
        b_button_layout.addWidget(b_stop_all)
        grid.addLayout(b_button_layout, nrows, 3, alignment=Qt.AlignCenter)

        self.setLayout(grid)

    def _header_label(self, text, font):
        label = QLabel(text)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        return label

    def on_gas_selection_changed(self, input_model, gas_name):
        try:
            enum_strings = input_model.gas_selection.enum_strs
            if gas_name in enum_strings:
                index = enum_strings.index(gas_name)
                input_model.gas_selection.set(index)
        except Exception as e:
            print(f"Error setting gas selection: {e}")

    @Slot()
    def send_all_a(self):
        a_models = self.model.get_line_a_models()
        for model in a_models:
            if model.line_enabled:
                try:
                    cell_key = f"{model.name.replace('_a_flow', '')}_a"
                    if cell_key in self.input_cells:
                        cell = self.input_cells[cell_key]
                        value = float(cell.setpoint_edit.text())
                        model.set(value)
                except (ValueError, KeyError):
                    pass
        self.parent_model.apply_flows()

    @Slot()
    def stop_all_a(self):
        self.parent_model.stop_line_a_flows()

    @Slot()
    def send_all_b(self):
        b_models = self.model.get_line_b_models()
        for model in b_models:
            if model.line_enabled:
                try:
                    cell_key = f"{model.name.replace('_b_flow', '')}_b"
                    if cell_key in self.input_cells:
                        cell = self.input_cells[cell_key]
                        value = float(cell.setpoint_edit.text())
                        model.set(value)
                except (ValueError, KeyError):
                    pass
        self.parent_model.apply_flows()

    @Slot()
    def stop_all_b(self):
        self.parent_model.stop_line_b_flows()


# Keep the old GasFlowsController for backward compatibility
class GasFlowsController(MotorTupleControl):
    """
    Control widget for gas flows with apply button.

    This extends MotorTupleControl to add an "Apply All Flows" button
    that triggers the flow apply mechanism.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
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

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
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
        left_column.addWidget(EurothermMonitor(self.model.eurotherm, parent_model=self.model))

        # Pulse monitor
        left_column.addWidget(PulseMonitor(self.model.pulse, parent_model=self.model))

        layout.addLayout(left_column)

        # Right column - Gas flow monitor
        right_column = QVBoxLayout()
        right_column.addWidget(AutoMonitor(self.model.gas_flows, parent_model=self.model))

        layout.addLayout(right_column)

        self.setLayout(layout)


class FasstcatController(QWidget):
    """
    Widget for controlling FASSTCAT components.
    """

    def __init__(self, model, parent_model=None, parent=None, **kwargs):
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
        left_column.addWidget(EurothermControl(self.model.eurotherm, parent_model=self.model))

        # Pulse control
        left_column.addWidget(PulseControl(self.model.pulse, parent_model=self.model))

        layout.addLayout(left_column)

        # Right column - Custom gas flow control
        right_column = QVBoxLayout()
        right_column.addWidget(CustomGasFlowsWidget(self.model.gas_flows, parent_model=self.model))

        layout.addLayout(right_column)

        self.setLayout(layout)
