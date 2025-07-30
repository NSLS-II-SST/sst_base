"""
FASSTCAT tab for gas control and temperature management.
"""

from qtpy.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QTabWidget
from nbs_gui.views.views import AutoControl
from sst_base.qt.plans.fasstcatSegments import FasstcatPlanWidget


class FasstcatDeviceTab(QWidget):
    name = "Status"

    def __init__(self, model, parent=None):
        print("Initializing FasstcatTab")
        super().__init__(parent)
        self.model = model
        self.layout = QVBoxLayout(self)

        # Check if FASSTCAT device exists in the beamline
        if "fasstcat" not in model.beamline.devices:
            self.show_error_message("FASSTCAT device not found in beamline devices")
            return

        try:
            # Get the FASSTCAT model from the beamline devices
            fasstcat_model = model.beamline.devices["fasstcat"]
            print(f"Found FASSTCAT model: {fasstcat_model}")

            # Create controller tab
            self.controller_widget = AutoControl(fasstcat_model)
            # Add tab widget to layout
            self.layout.addWidget(self.controller_widget)

        except Exception as e:
            error_msg = f"Error initializing FASSTCAT tab: {str(e)}"
            print(error_msg)
            self.show_error_message(error_msg)

    def show_error_message(self, message):
        """Show error message in the tab."""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)

        # Create a simple error display
        error_label = QMessageBox()
        error_label.setIcon(QMessageBox.Warning)
        error_label.setText("FASSTCAT Error")
        error_label.setInformativeText(message)
        error_label.setStandardButtons(QMessageBox.Ok)

        # Add to layout
        error_layout.addWidget(error_label)
        self.layout.addWidget(error_widget)


class FasstcatPlanTab(QWidget):
    name = "Segment Editor"

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.layout = QVBoxLayout(self)
        print("Initializing FasstcatTab")
        # Create segments widget
        self.segments_widget = FasstcatPlanWidget(model)
        self.layout.addWidget(self.segments_widget)


class FasstcatTab(QWidget):
    name = "FASSTCAT"

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.addTab(FasstcatDeviceTab(model), "Device")
        self.tab_widget.addTab(FasstcatPlanTab(model), "Plans")
