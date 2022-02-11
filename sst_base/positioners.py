from ophyd import EpicsMotor, Signal, PositionerBase, Device
from ophyd.pseudopos import PseudoSingle as _PS
from ophyd.pv_positioner import PVPositioner
from ophyd import Component as Cpt
from ophyd.status import wait as status_wait


class DeadbandMixin(Device, PositionerBase):
    """
    Should be the leftmost class in the inheritance list so that it grabs move first!

    Must be combined with either EpicsMotor or PVPositioner, or some other class
    that has a done_value attribute

    An EpicsMotor subclass that has an absolute tolerance for moves.
    If the readback is within tolerance of the setpoint, the MoveStatus
    is marked as finished, even if the motor is still settling.

    This prevents motors with long, but irrelevant, settling times from
    adding overhead to scans.
    """
    tolerance = Cpt(Signal, value=-1, kind='config')

    def move(self, position, wait=True, **kwargs):
        tolerance = self.tolerance.get()
        if tolerance < 0:
            return super().move(position, wait=wait, **kwargs)
        else:
            status = super().move(position, wait=False, **kwargs)
            setpoint = position
            done_value = getattr(self, "done_value", 1)
            def check_deadband(value, timestamp, **kwargs):
                if abs(value - setpoint) < tolerance:                    
                    self._move_changed(timestamp=timestamp, value=done_value)

            def clear_deadband(*args, **kwargs):
                self.clear_sub(check_deadband, event_type=self.SUB_READBACK)

            self.subscribe(check_deadband, event_type=self.SUB_READBACK, run=False)
            self.subscribe(clear_deadband, event_type=self._SUB_REQ_DONE, run=False)
            try:
                if wait:
                    status_wait(status)
            except KeyboardInterrupt:
                self.stop()
                raise

            return status


class DeadbandEpicsMotor(DeadbandMixin, EpicsMotor):
    """
    An EpicsMotor subclass that has an absolute tolerance for moves.
    If the readback is within tolerance of the setpoint, the MoveStatus
    is marked as finished, even if the motor is still settling.

    This prevents motors with long, but irrelevant, settling times from
    adding overhead to scans.

    This class is designed to be subclassed.
    """
    pass


class DeadbandPVPositioner(DeadbandMixin, PVPositioner):
    """
    A PVPositioner subclass that has an absolute tolerance for moves.
    If the readback is within tolerance of the setpoint, the MoveStatus
    is marked as finished, even if the motor is still settling.

    This prevents motors with long, but irrelevant, settling times from
    adding overhead to scans.

    This class is designed to be subclassed.
    """
    pass


class PseudoSingle(_PS):
    def move(self, position, *args, **kwargs):
        return super().move(float(position), *args, **kwargs)
