from ophyd import EpicsMotor, EpicsSignal, Signal, PositionerBase, Device
from ophyd import Component as Cpt
import bluesky.plan_stubs as bps
from nbs_bl.printing import boxed_text, colored, whisper
from nbs_bl.devices import DeadbandMixin, FlyerMixin


class FMBOEpicsMotor(EpicsMotor):
    resolution = Cpt(EpicsSignal, ".MRES", kind="config")
    encoder = Cpt(EpicsSignal, ".REP", kind="config")
    clr_enc_lss = Cpt(EpicsSignal, "_ENC_LSS_CLR_CMD.PROC", kind="omitted")
    home_cmd = Cpt(EpicsSignal, "_HOME_CMD.PROC", kind="omitted")
    enable = Cpt(EpicsSignal, "_ENA_CMD.PROC", kind="omitted")
    kill = Cpt(EpicsSignal, "_KILL_CMD.PROC", kind="omitted")

    status_list = (
        "MTACT",
        "MLIM",
        "PLIM",
        "AMPEN",
        "LOOPM",
        "TIACT",
        "INTMO",
        "DWPRO",
        "DAERR",
        "DVZER",
        "ABDEC",
        "UWPEN",
        "UWSEN",
        "ERRTAG",
        "SWPOC",
        "ASSCS",
        "FRPOS",
        "HSRCH",
        "SODPL",
        "SOPL",
        "HOCPL",
        "PHSRA",
        "PREFE",
        "TRMOV",
        "IFFE",
        "AMFAE",
        "AMFE",
        "FAFOE",
        "WFOER",
        "INPOS",
        "ENC_LSS",
    )

    ###################################################################
    # this is the complete list of status signals defined in the FMBO #
    # IOC for thier MCS8 motor controllers                            #
    ###################################################################
    mtact = Cpt(EpicsSignal, "_MTACT_STS", kind="omitted")
    mtact_desc = Cpt(EpicsSignal, "_MTACT_STS.DESC", kind="omitted")
    mlim = Cpt(EpicsSignal, "_MLIM_STS", kind="omitted")
    mlim_desc = Cpt(EpicsSignal, "_MLIM_STS.DESC", kind="omitted")
    plim = Cpt(EpicsSignal, "_PLIM_STS", kind="omitted")
    plim_desc = Cpt(EpicsSignal, "_PLIM_STS.DESC", kind="omitted")
    ampen = Cpt(EpicsSignal, "_AMPEN_STS", kind="omitted")
    ampen_desc = Cpt(EpicsSignal, "_AMPEN_STS.DESC", kind="omitted")
    loopm = Cpt(EpicsSignal, "_LOOPM_STS", kind="omitted")
    loopm_desc = Cpt(EpicsSignal, "_LOOPM_STS.DESC", kind="omitted")
    tiact = Cpt(EpicsSignal, "_TIACT_STS", kind="omitted")
    tiact_desc = Cpt(EpicsSignal, "_TIACT_STS.DESC", kind="omitted")
    intmo = Cpt(EpicsSignal, "_INTMO_STS", kind="omitted")
    intmo_desc = Cpt(EpicsSignal, "_INTMO_STS.DESC", kind="omitted")
    dwpro = Cpt(EpicsSignal, "_DWPRO_STS", kind="omitted")
    dwpro_desc = Cpt(EpicsSignal, "_DWPRO_STS.DESC", kind="omitted")
    daerr = Cpt(EpicsSignal, "_DAERR_STS", kind="omitted")
    daerr_desc = Cpt(EpicsSignal, "_DAERR_STS.DESC", kind="omitted")
    dvzer = Cpt(EpicsSignal, "_DVZER_STS", kind="omitted")
    dvzer_desc = Cpt(EpicsSignal, "_DVZER_STS.DESC", kind="omitted")
    abdec = Cpt(EpicsSignal, "_ABDEC_STS", kind="omitted")
    abdec_desc = Cpt(EpicsSignal, "_ABDEC_STS.DESC", kind="omitted")
    uwpen = Cpt(EpicsSignal, "_UWPEN_STS", kind="omitted")
    uwpen_desc = Cpt(EpicsSignal, "_UWPEN_STS.DESC", kind="omitted")
    uwsen = Cpt(EpicsSignal, "_UWSEN_STS", kind="omitted")
    uwsen_desc = Cpt(EpicsSignal, "_UWSEN_STS.DESC", kind="omitted")
    errtg = Cpt(EpicsSignal, "_ERRTG_STS", kind="omitted")
    errtg_desc = Cpt(EpicsSignal, "_ERRTG_STS.DESC", kind="omitted")
    swpoc = Cpt(EpicsSignal, "_SWPOC_STS", kind="omitted")
    swpoc_desc = Cpt(EpicsSignal, "_SWPOC_STS.DESC", kind="omitted")
    asscs = Cpt(EpicsSignal, "_ASSCS_STS", kind="omitted")
    asscs_desc = Cpt(EpicsSignal, "_ASSCS_STS.DESC", kind="omitted")
    frpos = Cpt(EpicsSignal, "_FRPOS_STS", kind="omitted")
    frpos_desc = Cpt(EpicsSignal, "_FRPOS_STS.DESC", kind="omitted")
    hsrch = Cpt(EpicsSignal, "_HSRCH_STS", kind="omitted")
    hsrch_desc = Cpt(EpicsSignal, "_HSRCH_STS.DESC", kind="omitted")
    sodpl = Cpt(EpicsSignal, "_SODPL_STS", kind="omitted")
    sodpl_desc = Cpt(EpicsSignal, "_SODPL_STS.DESC", kind="omitted")
    sopl = Cpt(EpicsSignal, "_SOPL_STS", kind="omitted")
    sopl_desc = Cpt(EpicsSignal, "_SOPL_STS.DESC", kind="omitted")
    hocpl = Cpt(EpicsSignal, "_HOCPL_STS", kind="omitted")
    hocpl_desc = Cpt(EpicsSignal, "_HOCPL_STS.DESC", kind="omitted")
    phsra = Cpt(EpicsSignal, "_PHSRA_STS", kind="omitted")
    phsra_desc = Cpt(EpicsSignal, "_PHSRA_STS.DESC", kind="omitted")
    prefe = Cpt(EpicsSignal, "_PREFE_STS", kind="omitted")
    prefe_desc = Cpt(EpicsSignal, "_PREFE_STS.DESC", kind="omitted")
    trmov = Cpt(EpicsSignal, "_TRMOV_STS", kind="omitted")
    trmov_desc = Cpt(EpicsSignal, "_TRMOV_STS.DESC", kind="omitted")
    iffe = Cpt(EpicsSignal, "_IFFE_STS", kind="omitted")
    iffe_desc = Cpt(EpicsSignal, "_IFFE_STS.DESC", kind="omitted")
    amfae = Cpt(EpicsSignal, "_AMFAE_STS", kind="omitted")
    amfae_desc = Cpt(EpicsSignal, "_AMFAE_STS.DESC", kind="omitted")
    amfe = Cpt(EpicsSignal, "_AMFE_STS", kind="omitted")
    amfe_desc = Cpt(EpicsSignal, "_AMFE_STS.DESC", kind="omitted")
    fafoe = Cpt(EpicsSignal, "_FAFOE_STS", kind="omitted")
    fafoe_desc = Cpt(EpicsSignal, "_FAFOE_STS.DESC", kind="omitted")
    wfoer = Cpt(EpicsSignal, "_WFOER_STS", kind="omitted")
    wfoer_desc = Cpt(EpicsSignal, "_WFOER_STS.DESC", kind="omitted")
    inpos = Cpt(EpicsSignal, "_INPOS_STS", kind="omitted")
    inpos_desc = Cpt(EpicsSignal, "_INPOS_STS.DESC", kind="omitted")
    enc_lss = Cpt(EpicsSignal, "_ENC_LSS_STS", kind="omitted")
    enc_lss_desc = Cpt(EpicsSignal, "_ENC_LSS_STS.DESC", kind="omitted")

    def home(self, *args, **kwargs):
        yield from bps.mv(self.home_cmd, 1)

    def clear_encoder_loss(self):
        yield from bps.mv(self.clr_enc_lss, 1)

    def status(self):
        text = "\n  EPICS PV base : %s\n\n" % (self.prefix)
        for signal in self.status_list:
            if signal.upper() not in self.status_list:
                continue
            suffix = getattr(self, signal).pvname.replace(self.prefix, "")
            if getattr(self, signal).get():
                value_color = "lightgreen"
            else:
                value_color = "lightred"

            text += "  %-26s : %-35s  %s   %s \n" % (
                getattr(self, signal + "_desc").get(),
                colored(
                    getattr(self, signal).enum_strs[getattr(self, signal).get()],
                    value_color,
                ),
                colored(getattr(self, signal).get(), value_color),
                whisper(suffix),
            )
        boxed_text("%s status signals" % self.name, text, "green", shrink=True)


class DeadbandFMBOEpicsMotor(DeadbandMixin, FMBOEpicsMotor):
    pass


class PrettyMotor(EpicsMotor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_attrs = ["user_readback", "user_setpoint"]

    def where(self):
        return ("{} : {}").format(
            colored(self.name, "lightblue"),
            colored(
                "{:.2f}".format(self.user_readback.get()).rstrip("0."),
                "yellow",
            ),
        )

    def where_sp(self):
        return ("{} Setpoint : {}\n{} Readback : {}").format(
            colored(self.name, "lightblue"),
            colored(
                "{:.2f}".format(self.user_readback.get()).rstrip("0."),
                "yellow",
            ),
            colored(self.name, "lightblue"),
            colored(
                "{:.2f}".format(self.user_setpoint.get()).rstrip("0."),
                "yellow",
            ),
        )

    def wh(self):
        boxed_text(self.name + " location", self.where_sp(), "green", shrink=True)

    def status_or_rel_move(self, line):
        try:
            loc = float(line)
        except:
            if len(line) > 0:
                if line[0] == "s":
                    self.status()  # followed by an s, display status
                elif line[0] == "a":
                    try:
                        loc = float(line[1:])
                    except:
                        # followed by an a but not a number, just display location
                        boxed_text(self.name, self.where_sp(), "lightgray", shrink=True)
                    else:
                        # followed by an a and a number, do absolute move
                        yield from bps.mv(self, loc)
                        boxed_text(self.name, self.where_sp(), "lightgray", shrink=True)
                else:
                    # followed by something besides a number, a or s, just show location
                    boxed_text(self.name, self.where_sp(), "lightgray", shrink=True)
            else:
                # followed by something besides a number, a or s, just show location
                boxed_text(self.name, self.where_sp(), "lightgray", shrink=True)
        else:
            # followed by a number - relative move
            yield from bps.mvr(self, loc)
            boxed_text(self.name, self.where(), "lightgray", shrink=True)


class PrettyMotorFMBO(FMBOEpicsMotor, PrettyMotor):
    pass


class PrettyMotorFMBODeadband(DeadbandMixin, PrettyMotorFMBO):
    pass


class PrettyMotorDeadband(DeadbandMixin, PrettyMotor):
    pass


class PrettyMotorFMBODeadbandFlyer(FlyerMixin, PrettyMotorFMBODeadband):
    pass


class PrettyMotorDeadbandFlyer(FlyerMixin, PrettyMotorDeadband):
    pass
