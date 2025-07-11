from qtpy.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel, QSplitter
from ..views.srs570 import SRS570Monitor, SRS570Control
from nbs_gui.views.views import AutoControlCombo


class TestingTab(QWidget):
    """
    Testing tab for development and debugging of components.

    This tab provides a space for testing various components including:
    - SRS570 amplifier/ADC controls
    - Other experimental components
    - Debugging tools

    Parameters
    ----------
    model : object
        The main application model
    """

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.name = "Testing"

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create main splitter for organization
        splitter = QSplitter()
        layout.addWidget(splitter)

        # Create left panel for monitor
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Add SRS570 testing section
        srs570_group = QGroupBox("SRS570 Amplifier/ADC Testing")
        srs570_layout = QVBoxLayout()

        # Check if SRS570 device exists in the beamline
        if "i0" in model.beamline.devices:
            srs570_model = model.beamline.devices["i0"]
            # Create monitor widget
            print("Creating SRS570 monitor")
            srs570_monitor = SRS570Monitor(srs570_model)

            # Add to layout
            srs570_layout.addWidget(QLabel("Monitor:"))
            srs570_layout.addWidget(srs570_monitor)

        else:
            srs570_layout.addWidget(QLabel("SRS570 device not found in beamline configuration"))
            srs570_layout.addWidget(QLabel("Add SRS570 to devices.toml to enable testing"))

        srs570_group.setLayout(srs570_layout)
        left_layout.addWidget(srs570_group)

        # Create right panel for control
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Add detector controls section
        detector_controls_group = QGroupBox("Detector Controls")
        detector_controls_layout = QVBoxLayout()

        # Get all detector devices from the beamline
        detector_models = model.beamline.detectors

        if detector_models:
            print("Creating AutoControlCombo for detectors")
            # Create AutoControlBox for all detectors
            detector_control_box = AutoControlCombo(detector_models, "Detector Controls")
            detector_controls_layout.addWidget(detector_control_box)
        else:
            detector_controls_layout.addWidget(QLabel("No detector devices found in beamline configuration"))
            detector_controls_layout.addWidget(QLabel("Add detectors to devices.toml to enable testing"))

        detector_controls_group.setLayout(detector_controls_layout)
        right_layout.addWidget(detector_controls_group)

        # Add to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([600, 600])
