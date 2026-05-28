from ophyd import (
    PVPositioner,
    EpicsSignalRO,
    PseudoPositioner,
    EpicsSignal,
    Signal,
)
from ophyd import Component as Cpt, Device
import bluesky.plan_stubs as bps
from ophyd.pseudopos import pseudo_position_argument, real_position_argument
import pathlib
import numpy as np
import xarray as xr
from scipy.interpolate import CubicSpline
from nbs_bl.printing import boxed_text, colored
from sst_base.motors import FlyerMixin, PrettyMotorFMBODeadbandFlyer
from nbs_bl.devices import DeadbandMixin, PseudoSingle

from .base import EnergyFlyerBase, UndulatorMotor, EpuMode, FlyControl

def format_pv(pv):
    return colored(
        "{:.2f}".format(pv.get()).rstrip("0").rstrip("."),
        "yellow",
    )

class SoftFlyControl(FlyControl):
    readback = Cpt(EpicsSignal, "XF:07ID1-OP{Mono:PGM1-Ax::ENERGY_MON", kind="hinted", add_prefix=[False,False])

class FMB_Mono_Grating_Type(PVPositioner):
    setpoint = Cpt(EpicsSignal, "_TYPE_SP", string=True, kind="config")
    readback = Cpt(EpicsSignal, "_TYPE_MON", string=True, kind="config")
    actuate = Cpt(EpicsSignal, "_DCPL_CALC.PROC")
    enable = Cpt(EpicsSignal, "_ENA_CMD.PROC")
    kill = Cpt(EpicsSignal, "_KILL_CMD.PROC")
    home = Cpt(EpicsSignal, "_HOME_CMD.PROC")
    clear_encoder_loss = Cpt(EpicsSignal, "_ENC_LSS_CLR_CMD.PROC")
    done = Cpt(EpicsSignal, "_AXIS_STS", kind="config")


class Monochromator(FlyerMixin, DeadbandMixin, PVPositioner):
    setpoint = Cpt(EpicsSignal, ":ENERGY_SP", kind="config")
    readback = Cpt(EpicsSignalRO, ":ENERGY_MON", kind="config")
    en_mon = Cpt(EpicsSignalRO, ":READBACK2.A", name="Energy", kind="hinted")

    grating = Cpt(PrettyMotorFMBODeadbandFlyer, "GrtP}Mtr", name="Mono Grating", kind="config")
    mirror2 = Cpt(PrettyMotorFMBODeadbandFlyer, "MirP}Mtr", name="Mono Mirror", kind="config")
    cff = Cpt(EpicsSignal, ":CFF_SP", name="Mono CFF", kind="config", auto_monitor=True)
    vls = Cpt(EpicsSignal, ":VLS_B2.A", name="Mono VLS", kind="config", auto_monitor=True)
    gratingx = Cpt(FMB_Mono_Grating_Type, "GrtX}Mtr", kind="config")
    mirror2x = Cpt(FMB_Mono_Grating_Type, "MirX}Mtr", kind="config")

    scanlock = Cpt(Signal, value=0, name="lock flag for during scans", kind="config")
    done = Cpt(EpicsSignalRO, ":ERDY_STS", kind="config")
    done_value = 1
    stop_signal = Cpt(EpicsSignal, ":ENERGY_ST_CMD")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _setup_move(self, position):
        """Move and do not wait until motion is complete (asynchronous)
        Required so that mono moves do not wait unintentionally, as setpoint
        put will not return until motor has finished moving"""
        self.log.debug("%s.setpoint = %s", self.name, position)
        # copy from pv_positioner, with wait changed to false
        # possible problem with IOC not returning from a set
        self.setpoint.put(position, wait=False)
        if self.actuate is not None:
            self.log.debug("%s.actuate = %s", self.name, self.actuate_value)
            self.actuate.put(self.actuate_value, wait=False)

def EnergySoftFactory(prefix, *, name, beamline=None, rotation_motor_name="manipr", **kwargs):
    if beamline is not None:
        rotation_motor = beamline.devices.get(rotation_motor_name, None)
    else:
        rotation_motor = None
    return EnergySoft(prefix, rotation_motor=rotation_motor, name=name, **kwargs)


class EnergySoft(EnergyFlyerBase, PseudoPositioner):
    """Energy pseudopositioner class.
    Parameters:
    -----------
    """

    # synthetic axis
    energy = Cpt(PseudoSingle, kind="hinted", limits=(71, 2250), name="Beamline Energy")
    polarization = Cpt(PseudoSingle, kind="normal", limits=(-1, 180), name="X-ray Polarization")
    sample_polarization = Cpt(PseudoSingle, kind="hinted", name="Sample X-ray polarization")
    # real motors

    monoen = Cpt(Monochromator, "XF:07ID1-OP{Mono:PGM1-Ax:", kind="hinted", name="Mono Energy")
    epugap = Cpt(
        UndulatorMotor,
        "SR:C07-ID:G1A{SST1:1-Ax:Gap}-Mtr",
        kind="hinted",
        name="EPU Gap",
    )
    epuphase = Cpt(
        UndulatorMotor,
        "SR:C07-ID:G1A{SST1:1-Ax:Phase}-Mtr",
        kind="hinted",
        name="EPU Phase",
    )
    epumode = Cpt(
        EpuMode,
        "SR:C07-ID:G1A{SST1:1-Ax:Phase}Phs:Mode",
        name="EPU Mode",
        kind="config",
    )

    sim_epu_mode = Cpt(Signal, value=0, name="dont interact with the real EPU", kind="config")
    scanlock = Cpt(Signal, value=0, name="Lock Harmonic, Pitch, Grating for scan", kind="config")
    flycontrol = Cpt(SoftFlyControl, "SR:C07-ID:G1A{SST1:1}", name="FlyscanControl", kind="config")
    harmonic = Cpt(Signal, value=1, name="EPU Harmonic", kind="config")
    offset_gap = Cpt(Signal, value=0, name="EPU Gap offset", kind="config")
    rotation_motor = None
    _real = ['monoen', 'epugap', 'epuphase', 'epumode']

    def __init__(
        self,
        a,
        rotation_motor=None,
        configpath=pathlib.Path(__file__).parent.parent.absolute() / "config",
   
        **kwargs,
    ):
        self.gap_fitnew = np.load(configpath / "EPU60_gap_fit.npy")

        # values for the minimum energy as a function of angle polynomial 10th deg
        # 80.934 ± 0.0698
        # -0.91614 ± 0.0446
        # 0.39635 ± 0.00925
        # -0.020478 ± 0.000881
        # 0.00069047 ± 4.54e-05
        # -1.5413e-05 ± 1.37e-06
        # 2.1448e-07 ± 2.49e-08
        # -1.788e-09 ± 2.68e-10
        # 8.162e-12 ± 1.57e-12
        # -1.5545e-14 ± 3.88e-15

        self.polphase = xr.load_dataarray(configpath / "polphase.nc")
        self.phasepol = xr.DataArray(
            data=self.polphase.pol,
            coords={"phase": self.polphase.values},
            dims={"phase"},
        )
        phase_values = self.polphase.values
        pol_values = self.phasepol.values
        self._phase_to_pol_interp = CubicSpline(phase_values, pol_values, bc_type='natural', extrapolate=False)
        self.rotation_motor = rotation_motor
        super().__init__(a, **kwargs)
        self.epugap.tolerance.set(0.5).wait()
        self.epuphase.tolerance.set(10).wait()
        # self.mir3Pitch.tolerance.set(0.01)
        self.monoen.tolerance.set(0.01).wait()

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """Run a forward (pseudo -> real) calculation"""
        ret = self.RealPosition(
            epugap=self.gap(
                pseudo_pos.energy,
                pseudo_pos.polarization,
                self.scanlock.get(),
                self.sim_epu_mode.get(),
            ),
            monoen=pseudo_pos.energy,
            epuphase=abs(self.phase(pseudo_pos.energy, pseudo_pos.polarization, self.sim_epu_mode.get())),
            epumode=self.mode(pseudo_pos.polarization, self.sim_epu_mode.get()),
        )
        return ret

    @real_position_argument
    def inverse(self, real_pos):
        """Run an inverse (real -> pseudo) calculation"""
        # print('in Inverse')
        pol_value = self.pol(real_pos.epuphase, real_pos.epumode)
        ret = self.PseudoPosition(
            energy=real_pos.monoen,
            polarization=pol_value,
            sample_polarization=self.sample_pol(pol_value),
        )
        # print('Finished inverse')
        return ret

    def where_sp(self):

        return (
            f"Beamline Energy Setpoint : {format_pv(self.monoen.setpoint)}"
            f"Monochromator Readback : {format_pv(self.monoen.readback)}"
            f"EPU Gap Setpoint : {format_pv(self.epugap.user_setpoint)}"
            f"EPU Gap Readback : {format_pv(self.epugap.user_readback)}"
            f"EPU Phase Setpoint : {format_pv(self.epuphase.user_setpoint)}"
            f"EPU Phase Readback : {format_pv(self.epuphase.user_readback)}"
            f"EPU Mode Setpoint : {format_pv(self.epumode.setpoint)}"
            f"EPU Mode Readback : {format_pv(self.epumode.readback)}"
            f"Grating Setpoint : {format_pv(self.monoen.grating.user_setpoint)}"
            f"Grating Readback : {format_pv(self.monoen.grating.user_readback)}"
            f"Gratingx Setpoint : {format_pv(self.monoen.gratingx.setpoint)}"
            f"Gratingx Readback : {format_pv(self.monoen.gratingx.readback)}"
            f"Mirror2 Setpoint : {format_pv(self.monoen.mirror2.user_setpoint)}"
            f"Mirror2 Readback : {format_pv(self.monoen.mirror2.user_readback)}"
            f"Mirror2x Setpoint : {format_pv(self.monoen.mirror2x.setpoint)}"
            f"Mirror2x Readback : {format_pv(self.monoen.mirror2x.readback)}"
            f"CFF : {format_pv(self.monoen.cff)}"
            f"VLS : {format_pv(self.monoen.vls)}"
        )

    def where(self):
        return (f"Beamline Energy : {format_pv(self.monoen.readback)}\n"
            f"Polarization : {format_pv(self.polarization.readback)}\n"
            f"Sample Polarization : {format_pv(self.sample_polarization.readback)}"
        )

    def wh(self):
        boxed_text(self.name + " location", self.where_sp(), "green", shrink=True)

    def gap(self, energy, pol, locked, sim=0):
        if sim:
            return self.epugap.get()  # never move the gap if we are in simulated gap mode
            # this might cause problems if someone else is moving the gap, we might move it back
            # but I think this is not a common reason for this mode

        self.harmonic.set(self.choose_harmonic(energy, pol, locked)).wait()
        energy = energy / self.harmonic.get()

        if (pol == -1) or (pol == -0.5):
            encalc = energy
            gap = 6202.6
            gap += 74.094 * encalc**1
            gap += 0.14654 * encalc**2
            gap += -0.001609 * encalc**3
            gap += 5.443e-06 * encalc**4
            gap += -1.0023e-08 * encalc**5
            gap += 1.1005e-11 * encalc**6
            gap += -7.1779e-15 * encalc**7
            gap += 2.5652e-18 * encalc**8
            gap += -3.86e-22 * encalc**9

            return max(14000.0, min(100000.0, gap)) + self.offset_gap.get()
        elif 0 <= pol <= 90:
            return max(14000.0, min(100000.0, self.epu_gap(energy, pol))) + self.offset_gap.get()
        elif 90 < pol <= 180:
            return max(14000.0, min(100000.0, self.epu_gap(energy, 180.0 - pol))) + self.offset_gap.get()
        else:
            return np.nan

    def epu_gap(self, en, pol):
        """
        calculate the epu gap from the energy and polarization, using a 2D polynomial fit
        @param en: energy (valid between ~70 and 1300
        @param pol: polarization (valid between 0 and 90)
        @return: gap in microns
        """
        y = float(en)
        x = float(self.phase(en, pol))
        z = 0.0
        for i in np.arange(self.gap_fitnew.shape[0]):
            for j in np.arange(self.gap_fitnew.shape[1]):
                z += self.gap_fitnew[j, i] * (x**j) * (y**i)
        return z

    def phase(self, en, pol, sim=0):
        if sim:
            return self.epuphase.get()  # never move the gap if we are in simulated gap mode
            # this might cause problems if someone else is moving the gap, we might move it back
            # but I think this is not a common reason for this mode
        if pol == -1:
            return 15000
        elif pol == -0.5:
            return 15000
        elif 90 < pol <= 180:
            return -min(
                29500.0,
                max(0.0, float(self.polphase.interp(pol=180 - pol, method="cubic"))),
            )
        else:
            return min(29500.0, max(0.0, float(self.polphase.interp(pol=pol, method="cubic"))))

    def pol(self, phase, mode):
        if mode == 0:
            return -1
        elif mode == 1:
            return -0.5
        elif mode == 2:
            return float(self._phase_to_pol_interp(np.abs(phase)))
        elif mode == 3:
            return 180 - float(self._phase_to_pol_interp(np.abs(phase)))

    def mode(self, pol, sim=0):
        """
        @param pol:
        @return:
        """
        if sim:
            return self.epumode.get()  # never move the gap if we are in simulated gap mode
            # this might cause problems if someone else is moving the gap, we might move it back
            # but I think this is not a common reason for this mode
        if pol == -1:
            return 0
        elif pol == -0.5:
            return 1
        elif 90 < pol <= 180:
            return 3
        else:
            return 2

    def sample_pol(self, pol):
        if self.rotation_motor is None:
            th = 0
        else:
            th = self.rotation_motor.user_setpoint.get()
        return np.arccos(np.cos(pol * np.pi / 180) * np.sin(th * np.pi / 180)) * 180 / np.pi

    def choose_harmonic(self, energy, pol, locked):
        if locked:
            return self.harmonic.get()
        elif energy < 1200:
            return 1
        else:
            return 3


def base_set_polarization(pol, en):
    yield from bps.mv(en.polarization, pol)
    return 0
