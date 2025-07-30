from bluesky import plan_stubs as bps
from nbs_bl.beamline import GLOBAL_BEAMLINE
from nbs_bl.plans.plan_stubs import wait_for_signal_equals


def fasstcat_segment(
    temp_sp,
    temp_rate,
    duration,
    gas_flows,
    gas_selections,
    pulse_mode=None,
    line_select=None,
    pulse_params=None,
    md=None,
    wait_for_previous_segment=True,
    wait_for_current_segment=False,
):
    """
    Launch a FASSTCAT segment: set temperature, gas flows, and pulse mode.

    Parameters
    ----------
    temp_sp : float
        Target temperature (degC).
    temp_rate : float
        Temperature ramp rate (degC/min).
    duration : float
        Segment duration (seconds).
    gas_flows : dict
        Mapping of gas flow names to setpoints, e.g. {"input_1_a": 20, ...}
    gas_selections : dict
        Mapping of input names to gas selection, e.g. {"input_1": "H2", ...}
    pulse_mode : str, optional
        Pulse mode ("continuous" or "pulses").
    line_select : str, optional
        Line select ("A" or "B").
    pulse_params : dict, optional
        Additional pulse parameters (e.g. count, time).
    md : dict, optional
        Metadata for the run.
    """
    fasstcat = GLOBAL_BEAMLINE["fasstcat"]

    if wait_for_previous_segment:
        yield from wait_for_fasstcat_segment()

    # Set temperature setpoint and ramp rate
    yield from bps.abs_set(fasstcat.eurotherm.setpoint, temp_sp)
    yield from bps.abs_set(fasstcat.eurotherm.rate, temp_rate)

    # Set gas selections
    for input_name, gas in gas_selections.items():
        input_dev = getattr(fasstcat, input_name)
        yield from bps.abs_set(input_dev.gas_selection, gas)

    # Set gas flows
    for flow_name, value in gas_flows.items():
        # flow_name should be like "input_1_a" or "input_2_b"
        input_idx, line = flow_name.rsplit("_", 1)
        input_dev = getattr(fasstcat, input_idx)
        flow_dev = getattr(input_dev, line)
        yield from bps.abs_set(flow_dev.setpoint, value)

    # Set pulse mode/params if provided
    yield from bps.abs_set(fasstcat.flow_apply, 1)

    if pulse_mode is not None:
        yield from bps.abs_set(fasstcat.pulse.line_mode, pulse_mode)
    if line_select is not None:
        yield from bps.abs_set(fasstcat.pulse.line_select, line_select)
    if pulse_params is not None:
        if "line_select" in pulse_params:
            yield from bps.abs_set(fasstcat.pulse.line_select, pulse_params["line_select"])
        if "count" in pulse_params:
            yield from bps.abs_set(fasstcat.pulse.count, pulse_params["count"])
        if "time" in pulse_params:
            yield from bps.abs_set(fasstcat.pulse.time, pulse_params["time"])
        if pulse_params.get("start", False):
            yield from bps.abs_set(fasstcat.pulse.start, 1)

    yield from bps.mv(fasstcat.eurotherm.start, 1)
    yield from bps.sleep(5)

    if wait_for_current_segment:
        yield from wait_for_fasstcat_segment()


def wait_for_fasstcat_segment():
    fasstcat = GLOBAL_BEAMLINE["fasstcat"]
    yield from wait_for_signal_equals(fasstcat.segment_status, "idle")


def is_fasstcat_running():
    fasstcat = GLOBAL_BEAMLINE["fasstcat"]
    reading = yield from bps.rd(fasstcat.segment_status)
    return reading == "running"
