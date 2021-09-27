from ophyd import Device, Signal, EpicsSignal, EpicsSignalRO, PVPositioner
from ophyd import FormattedComponent as FmtCpt, Component as Cpt
from ophyd.signal import SignalRO

class HexapodMirror(Device):
    X = Cpt(EpicsSignal, 'X}Mtr_MON',write_pv='X}Mtr_SP',kind='hinted')
    Y = Cpt(EpicsSignal, 'Y}Mtr_MON',write_pv='Y}Mtr_SP',kind='hinted')
    Z = Cpt(EpicsSignal, 'Z}Mtr_MON',write_pv='Z}Mtr_SP',kind='hinted')
    Roll = Cpt(EpicsSignal, 'R}Mtr_MON',write_pv='R}Mtr_SP',kind='hinted')
    Pitch = Cpt(EpicsSignal, 'P}Mtr_MON',write_pv='P}Mtr_SP',kind='hinted')
    Yaw = Cpt(EpicsSignal, 'Yaw}Mtr_MON',write_pv='Yaw}Mtr_SP',kind='hinted')
#    def read(self):
#        self.X.read()
#        self.Y.read()
#        self.Z.read()
#        self.Roll.read()
#        self.Pitch.read()
#        self.Yaw.read()

class SimHexapodMirror(Device):
    X = Cpt(Signal, kind='hinted')
    Y = Cpt(Signal, kind='hinted')
    Z = Cpt(Signal, kind='hinted')
    Roll = Cpt(Signal, kind='hinted')
    Pitch = Cpt(Signal, kind='hinted')
    Yaw = Cpt(Signal, kind='hinted')

class FMBHexapodMirrorAxis(PVPositioner):
    readback = Cpt(EpicsSignalRO, 'Mtr_MON')
    setpoint = Cpt(EpicsSignal, 'Mtr_POS_SP')
    actuate = FmtCpt(EpicsSignal, '{self.parent.prefix}}}MOVE_CMD.PROC')
    actual_value = 1
    stop_signal = FmtCpt(EpicsSignal, '{self.parent.prefix}}}STOP_CMD.PROC')
    stop_value = 1
    done = FmtCpt(EpicsSignalRO, '{self.parent.prefix}}}BUSY_STS')
    done_value = 0

class SimFMBHexapodMirrorAxis(PVPositioner):
    #readback = Cpt(SignalRO, 'Mtr_MON')
    setpoint = Cpt(Signal)
    readback = setpoint
    actuate = Cpt(Signal)
    actual_value = 1
    stop_signal = Cpt(Signal)
    stop_value = 1
    done = FmtCpt(SignalRO, value=0)
    done_value = 0
    
    
class FMBHexapodMirror(Device):
    z = Cpt(FMBHexapodMirrorAxis, '-Ax:Z}')
    Y = Cpt(FMBHexapodMirrorAxis, '-Ax:Y}')
    X = Cpt(FMBHexapodMirrorAxis, '-Ax:X}')
    Pitch = Cpt(FMBHexapodMirrorAxis, '-Ax:P}')
    Yaw = Cpt(FMBHexapodMirrorAxis, '-Ax:Yaw}')
    Roll = Cpt(FMBHexapodMirrorAxis, '-Ax:R}')

class SimFMBHexapodMirror(Device):
    z     = Cpt(SimFMBHexapodMirrorAxis)
    Y     = Cpt(SimFMBHexapodMirrorAxis)
    X     = Cpt(SimFMBHexapodMirrorAxis)
    Pitch = Cpt(SimFMBHexapodMirrorAxis)
    Yaw   = Cpt(SimFMBHexapodMirrorAxis)
    Roll  = Cpt(SimFMBHexapodMirrorAxis)
    
