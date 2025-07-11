from nbs_gui.widgets.qt_custom import ScrollingComboBox
from nbs_gui.views.monitors import SIPVMonitor


class CompactRBD9103Monitor(SIPVMonitor):
    """
    Compact monitor for RBD9103 detector.
    Shows a compact range drop-down and value with SI-prefixed units.
    """

    def __init__(self, model, *args, parent_model=None, orientation="h", **kwargs):
        super().__init__(
            model,
            *args,
            parent_model=parent_model,
            orientation=orientation,
            base_unit="A",
            min_prefix="p",
            max_prefix="A",
            **kwargs,
        )
        self.range_combo = ScrollingComboBox(max_visible_items=10)
        self.range_combo.addItems(model.range_ctrl.enum_strs)
        self.range_combo.setCurrentIndex(model.range_ctrl._index_value)
        self.range_combo.currentIndexChanged.connect(self._on_range_changed)
        self.layout().insertWidget(1, self.range_combo)
        # Keep combo in sync with model
        if hasattr(model, "range_ctrl"):
            model.range_ctrl.valueChanged.connect(self._update_range_combo_index)

    def _on_range_changed(self, idx):
        self.model.range_ctrl.set(idx)

    def _update_range_combo_index(self, *args, **kwargs):
        idx = self.model.range_ctrl._index_value
        if self.range_combo.currentIndex() != idx:
            self.range_combo.blockSignals(True)
            self.range_combo.setCurrentIndex(idx)
            self.range_combo.blockSignals(False)
