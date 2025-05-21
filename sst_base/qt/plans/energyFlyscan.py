from nbs_gui.plans.nbsPlan import NBSPlanWidget
from bluesky_queueserver_api import BPlan


class EnergyFlyscanWidget(NBSPlanWidget):
    display_name = "Energy Flyscan"

    def __init__(self, model, parent=None):
        print("Initializing Energy Flyscan")
        super().__init__(
            model,
            parent=None,
            plans="nbs_energy_flyscan",
            start=float,
            stop=float,
            speed={
                "type": "spinbox",
                "args": {"value_type": float, "maximum": 5},
                "label": "Speed (eV/s)",
                "help_text": "Energy speed between start and stop",
            },
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
        )
        print("Done initializing FlyScan")

    def create_plan_items(self):
        params = self.get_params()
        samples = params.pop("samples", [{}])
        args = [params.pop("start"), params.pop("stop")]
        speed = params.pop("speed", None)
        if speed is not None:
            args.append(speed)
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
