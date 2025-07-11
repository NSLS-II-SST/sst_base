from nbs_bl.plans.scans import nbs_fly_scan
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from nbs_bl.utils import merge_func
from nbs_bl.help import add_to_scan_list, add_to_plan_time_dict


@add_to_scan_list
@merge_func(nbs_fly_scan, omit_params=["motor"], use_func_name=False)
def nbs_energy_flyscan(start, stop, speed, period=None, bidirectional=False, sweeps=1, **kwargs):
    """
    Parameters
    ----------
    bidirectional : bool
        If True, the scan will be performed up and then down in energy.
    sweeps : int
        The number of sweeps to perform.
    """
    # Energy is probably the pseudosingle, so we need to get the parent
    en = bl.energy
    if bl.energy.parent is not None:
        en = bl.energy.parent
    return (
        yield from nbs_fly_scan(
            en, start, stop, speed, period=period, bidirectional=bidirectional, sweeps=sweeps, **kwargs
        )
    )


add_to_plan_time_dict(nbs_energy_flyscan, "fly_scan_estimate", fixed=5)
