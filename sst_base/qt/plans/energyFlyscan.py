from nbs_gui.plans.nbsPlan import NBSPlanWidget
from nbs_gui.plans.variableParamGroup import VariableParamGroupBase
from nbs_gui.plans.planParam import LineEditParam, SpinBoxParam
from bluesky_queueserver_api import BPlan

class VariableEnergyStepParam(VariableParamGroupBase):
    def _make_start_param(self):
        start = LineEditParam(
            "start", float, "Energy Start", "Energy Start Position", parent=self
        )
        start.label_text = "Start"
        return start

    def _make_param_pair(self):
        index = (len(self.params) + 1) // 2
        stop = LineEditParam(
            f"stop_{index}", float, f"Energy Stop {index}", "Energy Stop Position", parent=self
        )
        stop.label_text = f"Stop {index}"
        speed = SpinBoxParam(
            f"speed_{index}",
            f"Speed {index}",
            help_text=f"Energy speed between start and end of segment {index} (eV/s)",
            parent=self,
            value_type=float,
            maximum=5,
            minimum=0.01,
        )
        speed.label_text = f"Speed {index}"
        return stop, speed

class EnergyFlyscanWidget(NBSPlanWidget):
    display_name = "Energy Flyscan"

    def __init__(self, model, parent=None):
        print("Initializing Energy Flyscan")
        super().__init__(
            model,
            parent=None,
            plans="nbs_energy_flyscan",
            period={
                "type": "spinbox",
                "args": {"value_type": float, "default": 0.5},
                "label": "Detector Period (s)",
                "help_text": "Read non-flyer detectors every X seconds during flyscan",
            },
            bidirectional={
                "type": "boolean",
                "label": "Bidirectional",
                "help_text": "If true, the scan will be performed up and then down in energy.",
                "default": False,
            },
            sweeps={
                "type": "spinbox",
                "args": {"value_type": int, "default": 1},
                "label": "Sweeps",
                "help_text": "Number of sweeps to perform",
            },
            layout_style=2,
        )
        self.scan_widget.add_param(VariableEnergyStepParam(self), position=0)
        print("Done initializing EnergyFlyScan")

    def create_plan_items(self):
        params = self.get_params()
        samples = params.pop("samples", [{}])
        args = params.pop("args")
        items = []
        for sample in samples:
            item = BPlan(
                self.current_plan,
                *args,
                **params,
                **sample,
            )
            items.append(item)
        return items
