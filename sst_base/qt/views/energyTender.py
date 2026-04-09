from qtpy.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QDialog,
    QComboBox,
    QLineEdit,
    QLabel,
    QFrame,
    QWidget,
)
from qtpy.QtCore import Qt
from qtpy.QtGui import QDoubleValidator
from nbs_gui.views.views import AutoControl, AutoMonitor
from nbs_gui.widgets.utils import execute_plan
from bluesky_queueserver_api import BPlan
from nbs_gui.settings import get_top_level_model


class CrystalSelectionDialog(QDialog):
    """Dialog for selecting crystal settings.

    Parameters
    ----------
    parent : QWidget
        Parent widget
    crystal_model : object
        Model containing crystal settings
    """

    def __init__(self, parent, crystal_model):
        super().__init__(parent)
        self.setWindowTitle("Select Crystal")
        self.crystal_model = crystal_model

        layout = QVBoxLayout()

        self.cb = QComboBox()
        if hasattr(crystal_model, "enum_strs"):
            for s in crystal_model.enum_strs:
                if s != "":
                    self.cb.addItem(s)

        layout.addWidget(self.cb)

        button_box = QHBoxLayout()
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_box.addWidget(self.confirm_button)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def get_selected_crystal(self):
        """Get the selected crystal setting string."""
        return self.cb.currentText()


class SST2EnergyMonitor(QGroupBox):
    """Widget for controlling energy-related components.

    Parameters
    ----------
    energy : object
        Energy model containing energy, gap, and phase attributes
    parent_model : object
        Parent model containing beamline configuration
    orientation : str, optional
        Layout orientation
    *args, **kwargs
        Additional arguments passed to QGroupBox
    """

    def __init__(self, energy, parent_model=None, *args, orientation=None, **kwargs):
        print("Initializing Tender EnergyMonitor")
        super().__init__("Energy Monitor", *args, **kwargs)

        self.model = energy
        self.top_level_model = get_top_level_model()
        self.REClientModel = self.top_level_model.run_engine

        print("Creating Energy monitor layout")
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        ebox = QHBoxLayout()

        print("Adding energy monitor")
        if hasattr(energy, "energy"):
            ebox.addWidget(AutoMonitor(energy.energy))

        vbox.addLayout(ebox)
        vbox.addWidget(AutoMonitor(energy.crystal))
        vbox.addWidget(AutoMonitor(energy.dcm_mode))

        hbox = QHBoxLayout()

        vbox.addLayout(hbox)
        self.setLayout(vbox)
        print("EnergyControl initialization complete")


class SST2EnergyControl(QGroupBox):
    """Widget for controlling energy-related components.

    Parameters
    ----------
    energy : object
        Energy model containing energy, gap, and phase attributes
    parent_model : object
        Parent model containing beamline configuration
    orientation : str, optional
        Layout orientation
    *args, **kwargs
        Additional arguments passed to QGroupBox
    """

    def __init__(self, energy, parent_model=None, *args, orientation=None, **kwargs):
        print("Initializing Tender EnergyControl")
        super().__init__("Energy Control", *args, **kwargs)

        self.model = energy
        self.top_level_model = get_top_level_model()
        self.REClientModel = self.top_level_model.run_engine

        print("Creating Tender Energy Control layout")
        mainBox = QHBoxLayout()
        motorBox = QVBoxLayout()
        settingBox = QVBoxLayout()
        harmonicBox = QVBoxLayout()
        
        
        
        print("Adding tender energy control")
        if hasattr(energy, "energy"):
            motorBox.addWidget(AutoControl(energy.energy))

        settingBox.addWidget(AutoMonitor(energy.crystal))
        settingBox.addWidget(AutoMonitor(energy.dcm_mode))

        buttonBox = QHBoxLayout()

        print("Adding tune button")
        self.tuneButton = QPushButton("Tune X2 Pitch")
        self.tuneButton.clicked.connect(self.tune_x2pitch)
        buttonBox.addWidget(self.tuneButton)

        print("Adding crystal selection button")
        self.crystalButton = QPushButton("Set Crystal")
        self.crystalButton.clicked.connect(self.show_crystal_dialog)
        buttonBox.addWidget(self.crystalButton)
        
        print("Adding mode selection button")
        self.modeButton = QPushButton("Set DCM Mode")
        self.modeButton.clicked.connect(self.show_mode_dialog)
        buttonBox.addWidget(self.modeButton)

        settingBox.addLayout(buttonBox)
        
        harmonicBox.addWidget(AutoControl(energy.harmonic))
        self.optimizeButton = OptimizeEnergy(self.top_level_model)
        harmonicBox.addWidget(self.optimizeButton)
        

        mainBox.addLayout(motorBox)
        mainBox.addLayout(settingBox)
        mainBox.addLayout(harmonicBox)
        self.setLayout(mainBox)
        print("EnergyControl initialization complete")

    def show_crystal_dialog(self):
        """Show crystal selection dialog."""
        print("Opening crystal selection dialog")
        if hasattr(self.model, "crystal"):
            dialog = CrystalSelectionDialog(self, self.model.crystal)
            if dialog.exec_() == QDialog.Accepted:
                crystal_setting = dialog.get_selected_crystal()
                print(f"Selected crystal setting: {crystal_setting}")
                msg = f"Are you sure you want to change to {crystal_setting}?"
                if self.confirm_dialog(msg):
                    plan = BPlan("set_crystal", crystal_setting)
                    execute_plan(self, self.REClientModel, plan)

    def show_mode_dialog(self):
        print("Opening mode selection dialog")
        dialog = QDialog()
        dialog.setWindowTitle("DCM Mode Selection")
        vbox = QVBoxLayout()
        vbox.addWidget(AutoControl(self.model.dcm_mode))
        dialog.setLayout(vbox)
        dialog.exec_()
        
    def tune_x2pitch(self):
        """Execute x2pitch tuning plan."""
        print("Initiating x2pitch tune")
        msg = "Are you sure you want to tune the X2 pitch?"
        if self.confirm_dialog(msg):
            plan = BPlan("tune_x2pitch")
            execute_plan(self, self.REClientModel, plan)

    def confirm_dialog(self, confirm_message):
        """Show a confirmation dialog.

        Parameters
        ----------
        confirm_message : str
            Message to display in the dialog

        Returns
        -------
        bool
            True if user confirmed, False otherwise
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText(confirm_message)
        msg.setStyleSheet("button-layout: 1")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        ret = msg.exec_()
        return ret == QMessageBox.Yes


class OptimizeEnergy(QWidget):
    """Widget for optimizing photon energy.

    Parameters
    ----------
    parent_model : object
        Parent model containing beamline configuration
    """

    def __init__(self, parent_model, **kwargs):
        super().__init__(**kwargs)
        self.parent_model = parent_model
        self.REClientModel = parent_model.run_engine

        box = QHBoxLayout()
        box.setContentsMargins(2, 1, 2, 1)
        box.setSpacing(2)

        # Label with expanding space after it
        self.label = QLabel("Target Energy")
        self.label.setFixedHeight(20)
        box.addWidget(self.label)
        box.addStretch()

        # Fixed-width input field with validation
        self.edit = QLineEdit()
        self.edit.setFixedWidth(100)
        self.edit.setFixedHeight(20)
        self.edit.setAlignment(Qt.AlignRight)
        self.edit.setValidator(QDoubleValidator())

        # Fixed-width optimize button
        optimize_text = "Optimize Photon Energy"
        self.optimizeButton = QPushButton(optimize_text)
        self.optimizeButton.setFixedHeight(20)
        self.optimizeButton.clicked.connect(self.optimize_energy)

        box.addWidget(self.edit)
        box.addWidget(self.optimizeButton)

        self.setLayout(box)

    def optimize_energy(self):
        """Execute the set_photon_energy plan with the entered value."""
        try:
            energy = float(self.edit.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a valid energy value.",
                QMessageBox.Ok,
            )
        msg = f"Are you sure you want to optimize to {energy} eV?"
        if self.confirm_dialog(msg):
            plan = BPlan("set_photon_energy", energy)
            execute_plan(self, self.REClientModel, plan)

    def confirm_dialog(self, confirm_message):
        """Show a confirmation dialog.

        Parameters
        ----------
        confirm_message : str
            Message to display in the dialog

        Returns
        -------
        bool
            True if user confirmed, False otherwise
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText(confirm_message)
        msg.setStyleSheet("button-layout: 1")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        ret = msg.exec_()
        return ret == QMessageBox.Yes
