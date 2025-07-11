from qtpy.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QWidget,
    QComboBox,
)
from nbs_gui.views.views import AutoControl, AutoMonitor
from nbs_gui.views.monitors import PVMonitor, SIPVMonitor
from nbs_gui.widgets.qt_custom import ScrollingComboBox


class CompactSRS570Monitor(SIPVMonitor):
    """
    Compact monitor for SRS570 amplifier/ADC.
    Shows combined gain control and signal monitor only (no label).

    Parameters
    ----------
    model : SRS570Model
        The model representing the SRS570 device
    parent_model : object, optional
        Parent model for the widget
    orientation : str, optional
        'h' for horizontal (default), 'v' for vertical
    """

    def __init__(self, model, *args, parent_model=None, orientation="h", **kwargs):
        print("Initializing CompactSRS570Monitor")
        super().__init__(
            model,
            *args,
            parent_model=parent_model,
            orientation=orientation,
            base_unit="V",
            min_prefix="",
            max_prefix="",
            **kwargs,
        )
        self.model = model
        self.gain_combo = ScrollingComboBox(max_visible_items=10)
        self.gain_combo.addItems(model.gain_choices)
        self.gain_combo.setCurrentIndex(model.gain_index)
        self.gain_combo.currentIndexChanged.connect(self._on_gain_changed)
        self.layout().insertWidget(1, self.gain_combo)
        # Connect to gain_num and gain_unit valueChanged signals
        if hasattr(model, "gain_num") and hasattr(model, "gain_unit"):
            model.gain_num.valueChanged.connect(self._update_gain_combo_index)
            model.gain_unit.valueChanged.connect(self._update_gain_combo_index)

    def _on_gain_changed(self, idx):
        # Block signals to avoid feedback loop
        self.gain_combo.blockSignals(True)
        self.model.gain_index = idx
        self.gain_combo.blockSignals(False)

    def _update_gain_combo_index(self, *args, **kwargs):
        # Update the combo box to reflect the current gain
        idx = self.model.gain_index
        if self.gain_combo.currentIndex() != idx:
            self.gain_combo.blockSignals(True)
            self.gain_combo.setCurrentIndex(idx)
            self.gain_combo.blockSignals(False)


class SRS570Monitor(QWidget):
    """
    Monitor widget for SRS570 amplifier/ADC.
    Shows all SRS570 parameters organized in logical groups.

    Parameters
    ----------
    model : SRS570Model
        The model representing the SRS570 device
    parent_model : object
        Parent model for the widget
    """

    def __init__(self, model, *args, parent_model=None, **kwargs):
        print("Initializing SRS570Monitor")
        super().__init__(*args, **kwargs)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create filter settings group
        print("Creating filter settings group")
        filter_group = QGroupBox("Filter Settings")
        filter_layout = QGridLayout()

        filter_layout.addWidget(QLabel("Filter Type:"), 0, 0)
        filter_layout.addWidget(AutoMonitor(model.filter_type), 0, 1)

        filter_layout.addWidget(QLabel("Low Frequency:"), 1, 0)
        filter_layout.addWidget(AutoMonitor(model.low_freq), 1, 1)

        filter_layout.addWidget(QLabel("High Frequency:"), 2, 0)
        filter_layout.addWidget(AutoMonitor(model.high_freq), 2, 1)

        filter_layout.addWidget(QLabel("Filter Reset:"), 3, 0)
        filter_layout.addWidget(AutoMonitor(model.filter_reset), 3, 1)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Create gain settings group
        print("Creating gain settings group")
        gain_group = QGroupBox("Gain Settings")
        gain_layout = QGridLayout()

        gain_layout.addWidget(QLabel("Gain Mode:"), 0, 0)
        gain_layout.addWidget(AutoMonitor(model.gain_mode), 0, 1)

        gain_layout.addWidget(QLabel("Gain Number:"), 1, 0)
        gain_layout.addWidget(AutoMonitor(model.gain_num), 1, 1)

        gain_layout.addWidget(QLabel("Gain Unit:"), 2, 0)
        gain_layout.addWidget(AutoMonitor(model.gain_unit), 2, 1)

        gain_layout.addWidget(QLabel("Invert:"), 3, 0)
        gain_layout.addWidget(AutoMonitor(model.invert), 3, 1)

        gain_group.setLayout(gain_layout)
        layout.addWidget(gain_group)

        # Create control settings group
        print("Creating control settings group")
        control_group = QGroupBox("Control Settings")
        control_layout = QGridLayout()

        control_layout.addWidget(QLabel("Send All:"), 0, 0)
        control_layout.addWidget(AutoMonitor(model.send_all), 0, 1)

        control_layout.addWidget(QLabel("Reset:"), 1, 0)
        control_layout.addWidget(AutoMonitor(model.reset), 1, 1)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Add scalar value display
        print("Adding scalar value display")
        scalar_group = QGroupBox("Signal Value")
        scalar_layout = QVBoxLayout()
        scalar_layout.addWidget(PVMonitor(model))
        scalar_group.setLayout(scalar_layout)
        layout.addWidget(scalar_group)


class SRS570Control(QWidget):
    """
    Control widget for SRS570 amplifier/ADC.
    Shows all SRS570 parameters organized in logical groups.

    Parameters
    ----------
    model : SRS570Model
        The model representing the SRS570 device
    parent_model : object
        Parent model for the widget
    """

    def __init__(self, model, *args, parent_model=None, orientation=None, **kwargs):
        print("Initializing SRS570Control")
        super().__init__(*args, **kwargs)
        self.model = model
        self.parent_model = parent_model

        layout = QVBoxLayout()
        self.setLayout(layout)

        print("Adding scalar value display")
        scalar_group = QGroupBox("Signal Value")
        scalar_layout = QVBoxLayout()
        scalar_layout.addWidget(PVMonitor(model))
        scalar_group.setLayout(scalar_layout)
        layout.addWidget(scalar_group)

        settings_layout = QHBoxLayout()

        # Create filter settings group
        print("Creating filter settings group")
        filter_group = QGroupBox("Filter Settings")
        filter_layout = QVBoxLayout()

        filter_layout.addWidget(AutoControl(model.filter_type))
        filter_layout.addWidget(AutoControl(model.low_freq))
        filter_layout.addWidget(AutoControl(model.high_freq))
        filter_layout.addWidget(AutoControl(model.filter_reset))

        filter_group.setLayout(filter_layout)
        settings_layout.addWidget(filter_group)

        # Create gain settings group
        print("Creating gain settings group")
        gain_group = QGroupBox("Gain Settings")
        gain_layout = QVBoxLayout()

        gain_layout.addWidget(AutoControl(model.gain_mode))
        gain_layout.addWidget(AutoControl(model.gain_num))
        gain_layout.addWidget(AutoControl(model.gain_unit))
        gain_layout.addWidget(AutoControl(model.invert))

        gain_group.setLayout(gain_layout)
        settings_layout.addWidget(gain_group)
        layout.addLayout(settings_layout)
        # Create control settings group

        # Add scalar value display
