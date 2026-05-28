from ophyd import (
    EpicsSignalRO,
    EpicsSignal,
    Signal,
    Component as Cpt,
    PVPositioner,
    Device
)

from .base import UndulatorMotor, FlyControl, EnergyFlyerBase
from nbs_bl.devices.motors import DeadbandEpicsMotor
from sst_base.motors import DeadbandFMBOEpicsMotor
from time import sleep


class TenderFlyControl(FlyControl):
    readback = Cpt(EpicsSignal, "XF:07ID6-OP{Mono:DCM1-Ax::ENERGY_MON", kind="hinted", add_prefix=[False,False])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tolerance.set(0.05)


class DCM_energy(PVPositioner):
    setpoint = Cpt(EpicsSignal,":ENERGY_SP",kind='config')
    readback = Cpt(EpicsSignal,":ENERGY_MON",kind='normal')
    done = Cpt(EpicsSignalRO,":ERDY_STS",kind="config")
    done_value = 1
    stop_signal = Cpt(EpicsSignal, ":ENERGY_ST_CMD.PROC")
    _enable_cmd = Cpt(EpicsSignal, ":ENA_CMD.PROC")


class DCM(Device):
    d = Cpt(EpicsSignalRO, ":XTAL_CONST_MON", kind="config")
    hc = Cpt(EpicsSignalRO, ":HC_SP", kind="config")
    beam_offset = Cpt(EpicsSignalRO, ":BEAM_OFF_SP", kind="config")
    mode = Cpt(EpicsSignal, 
        read_pv="XF:07ID6-OP{MC:08}DCM_MODE_RBV", 
        write_pv="XF:07ID6-OP{MC:08}DCM_MODE", 
        kind="config",
        add_prefix=[False,False],
        string=True
    )
    crystal = Cpt(EpicsSignal, ":XTAL_SEL", string=True, kind="config")

    crystal_move = Cpt(EpicsSignal, ":XTAL_CMD.PROC")
    para_default = Cpt(Signal, value=7.5, kind="config")
    crystalstatus = Cpt(EpicsSignalRO, ":XTAL_STS", kind="config")

    dcm_energy = Cpt(EpicsSignal, ":ENERGY_MON", write_pv=":ENERGY_SP", kind="config")
    # motors:
    bragg = Cpt(DeadbandEpicsMotor, "Bragg}Mtr", kind="normal")
    x2perp = Cpt(DeadbandEpicsMotor, "Per2}Mtr", tolerance=0.001, kind="normal")
    x2para = Cpt(DeadbandEpicsMotor, "Par2}Mtr", tolerance=0.001, kind="normal")
    x2roll = Cpt(DeadbandFMBOEpicsMotor, "R2}Mtr", tolerance=0.001, kind="normal")
    x2pitch = Cpt(DeadbandFMBOEpicsMotor, "P2}Mtr", tolerance=0.001, kind="normal")
    x2perp = Cpt(DeadbandEpicsMotor, "Per2}Mtr", tolerance=0.001, kind="normal")
    x2finepitch = Cpt(DeadbandEpicsMotor, "PF2}Mtr", tolerance=0.001, kind="normal")
    x2fineroll = Cpt(DeadbandEpicsMotor, "RF2}Mtr", tolerance=0.001, kind="normal")


### don't think I need the U42 ###
class U42(UndulatorMotor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    _enabledTU = Cpt(EpicsSignalRO, "SR:C07-ID:G1A{SST2:1-Ax:TU}Sw:AmpEn-Sts", add_prefix=[False],kind='config')
    _enabledTD = Cpt(EpicsSignalRO, "SR:C07-ID:G1A{SST2:1-Ax:TD}Sw:AmpEn-Sts", add_prefix=[False],kind='config')

    def _check_and_enable(self):
        if not self._enabledTU.get() and not self._enabledTD.get():
            print('not enabled')
            current_position = self.position
            self.user_setpoint.put(current_position,wait=False)
            print('U42 not enabled.  Enabling')
            sleep(1.)

    def move(self, position,**kwargs):
        self._check_and_enable()
        super().move(position,**kwargs)
        

class EnergyTender(EnergyFlyerBase, Device):
    speed = Cpt(EpicsSignal,"FlyMove-Speed-RB",write_pv="FlyMove-Speed-SP",kind="config")    
    harmonic = Cpt(
        EpicsSignal,
        "FlyHarmonic-RB",
        write_pv="FlyHarmonic-SP",
        kind="config",
        name="U42 Harmonic",
    )
    mono = Cpt(DCM, "XF:07ID6-OP{Mono:DCM1-Ax:", name="dcm", kind="config",add_prefix=[False,False])
    monoen = Cpt(DCM_energy, "XF:07ID6-OP{Mono:DCM1-Ax:", name = "dcm_energy", kind="config", add_prefix=[False,False])
    u42 = Cpt(
        U42,
        "SR:C07-ID:G1A{SST2:1-Ax:Gap}-Mtr",
        tolerance=0.001,
        kind="config",
        name="U42 Gap",
        add_prefix=[False,False]
    )
    flycontrol = Cpt(TenderFlyControl,"SR:C07-ID:G1A{SST2:1}",add_prefix=[False,False])
    offset_gap = Cpt(EpicsSignal,"EScanIDEnergyOffset-RB",write_pv="EScanIDEnergyOffset-SP",kind='config')

    def set_mono_crystal(self, crystal):
        self.mono.set_crystal(crystal)


    def get_flymove_max_speed(self, start):
        if start < 2150:
            return 1.5
        else:
            return 5.0