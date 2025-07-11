from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
    QGridLayout,
    QCheckBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMenu,
    QAbstractItemView,
    QStyledItemDelegate,
    QComboBox,
)
from qtpy.QtCore import Qt, Slot, QPoint
from bluesky_queueserver_api import BPlan
from nbs_gui.plans.base import PlanWidgetBase, BasicPlanWidget
from nbs_gui.plans.planParam import ParamGroup, SpinBoxParam, ComboBoxParam, ParamGroupBase

print("Loaded fasscatSegments imports")


class SegmentDelegate(QStyledItemDelegate):
    """
    Custom delegate for SegmentViewer that provides combo boxes for enum parameters.
    """

    def __init__(self, editor, table_widget, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.table_widget = table_widget

    def createEditor(self, parent, option, index):
        """
        Create appropriate editor for the cell.

        For enum parameters (Pulse Mode, Pulse Line, Line N Gas), create a combo box.
        For other parameters, use the default editor.
        """
        row = index.row()
        col = index.column()

        # Get the header text to determine parameter type
        header_text = self.table_widget.verticalHeaderItem(row).text()

        # Check if this is an enum parameter
        if header_text == "Pulse Mode":
            # Get options from pulse mode parameter
            options = self.editor.pulse_mode_param.options
            combo = QComboBox(parent)
            combo.addItems(options)
            return combo

        elif header_text == "Pulse Line":
            # Get options from line select parameter
            options = self.editor.line_select_param.options
            combo = QComboBox(parent)
            combo.addItems(options)
            return combo

        elif "Gas" in header_text:
            # Extract line number from header (e.g., "Line 1 Gas" -> "input_1")
            import re

            match = re.match(r"Line (\d+) Gas", header_text)
            if match:
                line_num = match.group(1)
                input_name = f"input_{line_num}"

                # Get gas options for this input line
                if hasattr(self.editor, "gas_group") and hasattr(self.editor.gas_group, "gas_combo_boxes"):
                    gas_combo = self.editor.gas_group.gas_combo_boxes.get(input_name)
                    if gas_combo:
                        options = gas_combo.options
                        combo = QComboBox(parent)
                        combo.addItems(options)
                        return combo

        # Default to standard editor for non-enum parameters
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        """
        Set the current value in the editor.
        """
        if isinstance(editor, QComboBox):
            # For combo boxes, set the current text
            current_value = index.data()
            if current_value:
                # Find the index of the current value in the combo box
                index_in_combo = editor.findText(str(current_value))
                if index_in_combo >= 0:
                    editor.setCurrentIndex(index_in_combo)
                else:
                    editor.setCurrentIndex(0)  # Default to first item
            else:
                editor.setCurrentIndex(0)
        else:
            # For other editors, use default behavior
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """
        Get the value from the editor and set it in the model.
        """
        if isinstance(editor, QComboBox):
            # For combo boxes, get the current text
            value = editor.currentText()
            model.setData(index, value, Qt.EditRole)
        else:
            # For other editors, use default behavior
            super().setModelData(editor, model, index)


class SegmentViewer(QTableWidget):
    """
    Table view for a list of FASSTCAT segment BPlans.
    Each segment is a column; each property is a row.
    Double-clicking a cell allows editing that parameter.
    """

    def __init__(self, segment_list, editor=None, parent=None):
        super().__init__(parent)
        self.segment_list = segment_list  # Reference to the list
        self.editor = editor  # Reference to the editor for enum options
        self.setColumnCount(0)
        self.setRowCount(0)
        self.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.setSelectionBehavior(QAbstractItemView.SelectColumns)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        # Set the custom delegate for enum editing
        if editor:
            self.setItemDelegate(SegmentDelegate(editor, self))

        self.refresh()
        self.cellChanged.connect(self._on_cell_changed)

    def _get_pulse_count(self, seg):
        """Safely get pulse count from segment."""
        if seg is None or not hasattr(seg, "kwargs") or not seg.kwargs:
            return ""
        if seg.kwargs.get("pulse_mode") == "pulses":
            if seg.kwargs.get("pulse_params", None) is not None:
                return seg.kwargs.get("pulse_params", {}).get("count", "")
            else:
                return ""
        return ""

    def _get_pulse_time(self, seg):
        """Safely get pulse time from segment."""
        if seg is None or not hasattr(seg, "kwargs") or not seg.kwargs:
            return ""
        if seg.kwargs.get("pulse_mode") == "pulses":
            if seg.kwargs.get("pulse_params", None) is not None:
                return seg.kwargs.get("pulse_params", {}).get("time", "")
            else:
                return ""
        return ""

    def _get_gas_selection(self, seg, input_name):
        """Safely get gas selection for an input line."""
        if seg is None or not hasattr(seg, "kwargs") or not seg.kwargs:
            return ""
        return seg.kwargs.get("gas_selections", {}).get(input_name, "")

    def _get_gas_flow_a(self, seg, input_name):
        """Safely get gas flow A for an input line."""
        if seg is None or not hasattr(seg, "kwargs") or not seg.kwargs:
            return ""
        return seg.kwargs.get("gas_flows", {}).get(f"{input_name}_a", "")

    def _get_gas_flow_b(self, seg, input_name):
        """Safely get gas flow B for an input line."""
        if seg is None or not hasattr(seg, "kwargs") or not seg.kwargs:
            return ""
        return seg.kwargs.get("gas_flows", {}).get(f"{input_name}_b", "")

    def refresh(self):
        self.blockSignals(True)
        property_names = [
            ("Temperature Setpoint", "temp_sp"),
            ("Ramp Rate", "temp_rate"),
            ("Duration", "duration"),
            ("Pulse Mode", "pulse_mode"),
            ("Pulse Line", "line_select"),
            ("Pulse Count", self._get_pulse_count),
            ("Pulse Time", self._get_pulse_time),
        ]
        all_gas_lines = set()
        for seg in self.segment_list:
            all_gas_lines.update(seg.kwargs.get("gas_selections", {}).keys())
        gas_lines = sorted(all_gas_lines)
        for input_name in gas_lines:
            property_names.append(
                (
                    f"{input_name.replace('input_', 'Line ')} Gas",
                    lambda seg, n=input_name: self._get_gas_selection(seg, n),
                )
            )
            property_names.append(
                (
                    f"{input_name.replace('input_', 'Line ')} A",
                    lambda seg, n=input_name: self._get_gas_flow_a(seg, n),
                )
            )
            property_names.append(
                (
                    f"{input_name.replace('input_', 'Line ')} B",
                    lambda seg, n=input_name: self._get_gas_flow_b(seg, n),
                )
            )
        nrows = len(property_names)
        ncols = len(self.segment_list)
        self.setRowCount(nrows)
        self.setColumnCount(ncols)
        self.setHorizontalHeaderLabels([f"Segment {i+1}" for i in range(ncols)])
        self.setVerticalHeaderLabels([row[0] for row in property_names])
        for col, seg in enumerate(self.segment_list):
            for row, (label, key) in enumerate(property_names):
                if seg is None:
                    value = ""
                else:
                    value = key(seg) if callable(key) else seg.kwargs.get(key, "")
                item = QTableWidgetItem(str(value))
                self.setItem(row, col, item)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.blockSignals(False)

    def get_selected_col(self):
        selected = self.selectedRanges()
        if selected:
            return selected[0].leftColumn()
        return None

    def _on_cell_changed(self, row, col):
        # Update the segment data when a cell is edited
        if col >= len(self.segment_list) or self.segment_list[col] is None:
            return

        seg = self.segment_list[col]
        key = self.verticalHeaderItem(row).text()
        value = self.item(row, col).text()
        # Map header to segment key
        mapping = {
            "Temperature Setpoint": "temp_sp",
            "Ramp Rate": "temp_rate",
            "Duration": "duration",
            "Pulse Mode": "pulse_mode",
            "Pulse Line": "line_select",
        }
        if key in mapping:
            seg.kwargs[mapping[key]] = value
        elif "A" in key or "B" in key or "Gas" in key:
            # Handle gas flows and selections
            import re

            m = re.match(r"Line (\d+) (Gas|A|B)", key)
            if m:
                line = f"input_{m.group(1)}"
                if m.group(2) == "Gas":
                    seg.kwargs.setdefault("gas_selections", {})[line] = value
                elif m.group(2) in ("A", "B"):
                    seg.kwargs.setdefault("gas_flows", {})[f"{line}_{m.group(2).lower()}"] = value
        elif key == "Pulse Count":
            seg.kwargs.setdefault("pulse_params", {})["count"] = value
        elif key == "Pulse Time":
            seg.kwargs.setdefault("pulse_params", {})["time"] = value
        self.refresh()

    def move_left(self):
        col = self.get_selected_col()
        if col is not None and col > 0:
            self.segment_list[col - 1], self.segment_list[col] = (
                self.segment_list[col],
                self.segment_list[col - 1],
            )
            self.selectColumn(col - 1)
            self.refresh()

    def move_right(self):
        col = self.get_selected_col()
        if col is not None and col < len(self.segment_list) - 1:
            self.segment_list[col + 1], self.segment_list[col] = (
                self.segment_list[col],
                self.segment_list[col + 1],
            )
            self.selectColumn(col + 1)
            self.refresh()

    def delete_segment(self):
        col = self.get_selected_col()
        if col is not None and 0 <= col < len(self.segment_list):
            del self.segment_list[col]
            self.clearSelection()
            self.refresh()

    def copy_segment(self):
        col = self.get_selected_col()
        if col is not None and 0 <= col < len(self.segment_list):
            import copy

            self.segment_list.insert(col + 1, copy.deepcopy(self.segment_list[col]))
            self.selectColumn(col + 1)
            self.refresh()


class GasGroup(QWidget, ParamGroupBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.gas_grid = QGridLayout()
        self.gas_grid.setContentsMargins(2, 2, 2, 2)
        self.gas_grid.setHorizontalSpacing(8)
        self.gas_grid.setVerticalSpacing(2)
        # Column headers
        self.gas_grid.addWidget(QLabel("Enable"), 0, 0)
        self.gas_grid.addWidget(QLabel("Gas"), 0, 1)
        self.gas_grid.addWidget(QLabel("Line A Flow (sccm)"), 0, 2)
        self.gas_grid.addWidget(QLabel("Line B Flow (sccm)"), 0, 3)
        self.setLayout(self.gas_grid)
        self.gas_enable_boxes = {}
        self.gas_combo_boxes = {}
        self.gas_a_boxes = {}
        self.gas_b_boxes = {}
        self.input_lines = []

    def add_input_line(self, input_model):
        i = self.gas_grid.rowCount()
        input_name = input_model.name
        self.input_lines.append(input_name)
        # Enable checkbox
        enable_box = QCheckBox()
        enable_box.setChecked(False)
        self.gas_enable_boxes[input_name] = enable_box
        # Gas selection
        try:
            enum_strs = input_model.gas_selection.enum_strs
        except Exception:
            enum_strs = []
        gas_combo = ComboBoxParam(input_name, enum_strs, "", default=enum_strs[0] if enum_strs else None)
        self.gas_combo_boxes[input_name] = gas_combo
        # A/B flows
        a_box = SpinBoxParam(f"{input_name}_a", "", value_type=float, minimum=0, maximum=100, default=0.0)
        b_box = SpinBoxParam(f"{input_name}_b", "", value_type=float, minimum=0, maximum=100, default=0.0)
        self.gas_a_boxes[input_name] = a_box
        self.gas_b_boxes[input_name] = b_box
        # Check if line is available/enabled
        enabled = (
            getattr(input_model, "a_flow", None) is not None or getattr(input_model, "b_flow", None) is not None
        )
        if not enabled:
            enable_box.setEnabled(False)
            gas_combo.setEnabled(False)
            a_box.setEnabled(False)
            b_box.setEnabled(False)
        else:
            self.add_param(gas_combo)
            self.add_param(a_box)
            self.add_param(b_box)
        # Add to grid
        row = i
        self.gas_grid.addWidget(enable_box, row, 0)
        self.gas_grid.addWidget(gas_combo, row, 1)
        self.gas_grid.addWidget(a_box, row, 2)
        self.gas_grid.addWidget(b_box, row, 3)

    def get_params(self):
        params = {"gas_selections": {}, "gas_flows": {}}
        for input_name in self.gas_enable_boxes:
            if not self.gas_enable_boxes[input_name].isChecked():
                continue
            gas_combo = self.gas_combo_boxes[input_name]
            a_box = self.gas_a_boxes[input_name]
            b_box = self.gas_b_boxes[input_name]
            params["gas_selections"].update(gas_combo.get_params())
            params["gas_flows"].update(a_box.get_params())
            params["gas_flows"].update(b_box.get_params())
        return params


class FasstcatSegmentEditor(BasicPlanWidget):
    """
    Qt widget for editing and submitting a FASSTCAT segment using ParamGroups and BasicPlanWidget conventions.
    Includes a pre-submission queue and a SegmentViewer.
    """

    def __init__(self, model, parent=None):
        print("Initializing FasstcatSegmentEditor")
        super().__init__(model, parent, plans="fasstcat_segment")
        # self.setup_widget()

    def _create_temperature_group(self):
        temp_group = ParamGroup(title="Temperature Segment")
        self.temp_sp_param = SpinBoxParam(
            "temp_sp", "Setpoint (°C)", value_type=float, minimum=0, maximum=1200, default=25.0
        )
        self.temp_rate_param = SpinBoxParam(
            "temp_rate", "Ramp Rate (°C/min)", value_type=float, minimum=0.01, maximum=100, default=1.0
        )
        self.duration_param = SpinBoxParam(
            "duration", "Duration (s)", value_type=float, minimum=1, maximum=36000, default=10.0
        )
        temp_group.add_param(self.temp_sp_param)
        temp_group.add_param(self.temp_rate_param)
        temp_group.add_param(self.duration_param)
        return temp_group

    def _create_gas_group(self):
        gas_group = GasGroup()

        input_line_models = self.fasstcat.get_input_line_models()
        for i, input_model in enumerate(input_line_models, 1):
            gas_group.add_input_line(input_model)
        return gas_group

    def _create_pulse_group(self):
        pulse_group = ParamGroup(title="Pulse Control (optional)")
        self.pulse_mode_param = ComboBoxParam("pulse_mode", ["", "continuous", "pulses"], "Mode", default="")
        self.line_select_param = ComboBoxParam("line_select", ["", "A", "B"], "Line", default="")
        self.pulse_count_param = SpinBoxParam(
            "pulse_count", "Count", value_type=int, minimum=1, maximum=1000, default=1
        )
        self.pulse_time_param = SpinBoxParam(
            "pulse_time", "Time (s)", value_type=float, minimum=0.01, maximum=100, default=1.0
        )
        pulse_group.add_param(self.pulse_mode_param)
        pulse_group.add_param(self.line_select_param)
        pulse_group.add_param(self.pulse_count_param)
        pulse_group.add_param(self.pulse_time_param)
        return pulse_group

    def setup_widget(self):
        print("FasstcatSegmentEditor setup_widget")
        super().setup_widget()
        self.beamline = self.model.beamline
        self.fasstcat = self.beamline.misc.get("fasstcat", None)
        print("FasstcatSegmentEditor setup_widget super done")
        # Temperature group
        print("FasstcatSegmentEditor setup_widget adding temp group")
        self.temp_group = self._create_temperature_group()
        print("FasstcatSegmentEditor setup_widget added temp group")
        # Gas flows group (compact grid)
        print("FasstcatSegmentEditor setup_widget adding gas group (compact)")
        self.gas_group = self._create_gas_group()
        print("FasstcatSegmentEditor setup_widget added gas group (compact)")
        # Pulse group
        print("FasstcatSegmentEditor setup_widget adding pulse group")
        self.pulse_group = self._create_pulse_group()
        print("FasstcatSegmentEditor setup_widget added pulse group")
        # Add ParamGroups to params for readiness checks and reset
        print("FasstcatSegmentEditor setup_widget adding params")
        self.params.extend([self.temp_group, self.gas_group, self.pulse_group])
        print("FasstcatSegmentEditor setup_widget added params")
        # Stack all sections vertically
        self.basePlanLayout.addWidget(self.gas_group)
        self.basePlanLayout.addWidget(self.temp_group)
        self.basePlanLayout.addWidget(self.pulse_group)

    def create_plan_items(self):
        """
        Gather all parameters and create a BPlan item for fasstcat_segment.

        Returns
        -------
        list
            List containing a single BPlan item for the queue.
        """
        temp_params = self.temp_group.get_params()
        pulse_params = self.pulse_group.get_params()
        gas_params = self.gas_group.get_params()
        gas_flows = gas_params.get("gas_flows", {})
        gas_selections = gas_params.get("gas_selections", {})
        # Extract gas_selections and gas_flows from gas_params
        pulse_mode = pulse_params.get("pulse_mode") or None
        line_select = pulse_params.get("line_select") or None
        pulse_dict = None
        if pulse_mode == "pulses":
            pulse_dict = {
                "count": pulse_params.get("pulse_count", 1),
                "time": pulse_params.get("pulse_time", 1.0),
            }
        plan_args = dict(
            temp_sp=temp_params.get("temp_sp", 25.0),
            temp_rate=temp_params.get("temp_rate", 1.0),
            duration=temp_params.get("duration", 10.0),
            gas_flows=gas_flows,
            gas_selections=gas_selections,
            pulse_mode=pulse_mode,
            line_select=line_select,
            pulse_params=pulse_dict,
        )
        item = BPlan(
            "fasstcat_segment",
            **plan_args,
        )
        return [item]


class FasstcatPlanWidget(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        print("FasstcatPlanWidget init")
        self.editor = FasstcatSegmentEditor(model, self)
        print("FasstcatSegmentEditor created")
        self.segments = []
        self.viewer = SegmentViewer(self.segments, self.editor)
        print("SegmentViewer created")
        editor_layout = QVBoxLayout()
        # Add global segment control buttons

        editor_layout.addWidget(self.editor)
        viewer_layout = QVBoxLayout()

        button_bar = QHBoxLayout()
        self.btn_left = QPushButton("Left")
        self.btn_right = QPushButton("Right")
        self.btn_delete = QPushButton("Delete")
        self.btn_copy = QPushButton("Copy")
        button_bar.addWidget(self.btn_left)
        button_bar.addWidget(self.btn_right)
        button_bar.addWidget(self.btn_delete)
        button_bar.addWidget(self.btn_copy)
        viewer_layout.addLayout(button_bar)
        viewer_layout.addWidget(self.viewer)
        self.add_segment_btn = QPushButton("Add Segment")
        self.add_segment_btn.clicked.connect(self.on_add_segment)
        editor_layout.addWidget(self.add_segment_btn)

        self.submit_plan_btn = QPushButton("Submit Plan")
        self.submit_plan_btn.clicked.connect(self.on_submit)
        viewer_layout.addWidget(self.submit_plan_btn)
        layout.addLayout(editor_layout)
        layout.addLayout(viewer_layout)
        self.setLayout(layout)
        # Connect buttons to SegmentViewer methods
        self.btn_left.clicked.connect(self.viewer.move_left)
        self.btn_right.clicked.connect(self.viewer.move_right)
        self.btn_delete.clicked.connect(self.viewer.delete_segment)
        self.btn_copy.clicked.connect(self.viewer.copy_segment)

    def on_add_segment(self):
        """
        Add the current segment to the pre-submission queue and update the viewer.
        """
        items = self.editor.create_plan_items()
        if items:
            self.segments.append(items[0])
            self.viewer.refresh()

    def on_submit(self):
        """
        Submit all segments in the pre-submission queue to the main queue.
        """
        for item in self.segments:
            self.editor.submit_plan(item)
        self.segments.clear()
        self.viewer.refresh()
        QMessageBox.information(self, "Plan Submitted", "All FASSTCAT segments submitted.")
