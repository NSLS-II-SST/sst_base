from ophyd import EpicsMotor, EpicsSignal, Signal, PositionerBase, Device
from ophyd.pv_positioner import PVPositioner
from ophyd import Component as Cpt
from ophyd.status import wait as status_wait, DeviceStatus
import bluesky.plan_stubs as bps
from sst_funcs.printing import boxed_text, colored, whisper
from sst_base.positioners import DeadbandMixin
from queue import Queue, Empty
import time
import threading

class FlyerMixin:

    def __init__(self, *args, **kwargs):
        self._ready_to_fly = False
        self._fly_move_st = None
        self._default_time_resolution = 0.1
        self._time_resolution = None
        super().__init__(*args, **kwargs)
        
    # Flyer motor methods
    def preflight(self, start, stop, speed=None, time_resolution=None):
        self._old_velocity = self.velocity.get()
        self._flyer_stop = stop
        st = self.move(start)
        if speed is None:
            speed = self._old_velocity
        self.velocity.set(speed)
        if time_resolution is not None:
            self._time_resolution = time_resolution
        else:
            self._time_resolution = self._default_time_resolution
        self._last_readback_value = start
        self._ready_to_fly = True
        return st

    def fly(self):
        """
        Should be called after all detectors start flying, so that we don't lose data
        """
        if not self._ready_to_fly:
            self._fly_move_st = DeviceStatus(device=self)
            self._fly_move_st.set_finished(success=False)
        else:
            self._fly_move_st = self.move(self._flyer_stop, wait=False)
            self._flying = True
            self._ready_to_fly = False
        return self._fly_move_st

    def land(self):
        if self._fly_move_st.done:
            self.velocity.set(self._old_velocity)
            self._flying = False
            self._time_resolution = None

    # Flyer detector methods for readback
    def kickoff(self):
        kickoff_st = DeviceStatus(device=self)
        self._flyer_queue = Queue()
        self._measuring = True
        self._flyer_buffer = []
        threading.Thread(target=self._aggregate, daemon=True).start()
        #self.user_readback.subscribe(self._aggregate, run=False)
        kickoff_st.set_finished()
        return kickoff_st

    def _aggregate(self):
        name = self.user_readback.name
        while self._measuring:
            t = time.time()
            rb = self.user_readback.read()
            value = rb[name]['value']
            ts = rb[name]['timestamp']
            self._flyer_buffer.append(value)
            event = dict()
            event['time'] = t
            event['data'] = dict()
            event['timestamps'] = dict()
            event['data'][name + '_raw'] = value
            event['timestamps'][name + '_raw'] = ts
            self._flyer_queue.put(event)
            time.sleep(self._time_resolution)
        return

    def collect(self):
        events = []
        while True:
            try:
                e = self._flyer_queue.get_nowait()
                events.append(e)
            except Empty:
                break
        yield from events

    def complete(self):
        if self._measuring:
            # self.user_readback.clear_sub(self._aggregate)
            self._measuring = False
        completion_status = DeviceStatus(self)
        completion_status.set_finished()
        self._time_resolution = None
        return completion_status

    def describe_collect(self):
        dd = dict({self.user_readback.name + '_raw': {'source': self.user_readback.pvname, 'dtype': 'number', 'shape': []}})
        return {self.name: dd}


class FMBOEpicsMotor(EpicsMotor):
    resolution = Cpt(EpicsSignal, ".MRES")
    encoder = Cpt(EpicsSignal, ".REP")
    clr_enc_lss = Cpt(EpicsSignal, "_ENC_LSS_CLR_CMD.PROC")
    home_cmd = Cpt(EpicsSignal, "_HOME_CMD.PROC")
    enable = Cpt(EpicsSignal, "_ENA_CMD.PROC")
    kill = Cpt(EpicsSignal, "_KILL_CMD.PROC")

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
    mtact = Cpt(EpicsSignal, "_MTACT_STS")
    mtact_desc = Cpt(EpicsSignal, "_MTACT_STS.DESC")
    mlim = Cpt(EpicsSignal, "_MLIM_STS")
    mlim_desc = Cpt(EpicsSignal, "_MLIM_STS.DESC")
    plim = Cpt(EpicsSignal, "_PLIM_STS")
    plim_desc = Cpt(EpicsSignal, "_PLIM_STS.DESC")
    ampen = Cpt(EpicsSignal, "_AMPEN_STS")
    ampen_desc = Cpt(EpicsSignal, "_AMPEN_STS.DESC")
    loopm = Cpt(EpicsSignal, "_LOOPM_STS")
    loopm_desc = Cpt(EpicsSignal, "_LOOPM_STS.DESC")
    tiact = Cpt(EpicsSignal, "_TIACT_STS")
    tiact_desc = Cpt(EpicsSignal, "_TIACT_STS.DESC")
    intmo = Cpt(EpicsSignal, "_INTMO_STS")
    intmo_desc = Cpt(EpicsSignal, "_INTMO_STS.DESC")
    dwpro = Cpt(EpicsSignal, "_DWPRO_STS")
    dwpro_desc = Cpt(EpicsSignal, "_DWPRO_STS.DESC")
    daerr = Cpt(EpicsSignal, "_DAERR_STS")
    daerr_desc = Cpt(EpicsSignal, "_DAERR_STS.DESC")
    dvzer = Cpt(EpicsSignal, "_DVZER_STS")
    dvzer_desc = Cpt(EpicsSignal, "_DVZER_STS.DESC")
    abdec = Cpt(EpicsSignal, "_ABDEC_STS")
    abdec_desc = Cpt(EpicsSignal, "_ABDEC_STS.DESC")
    uwpen = Cpt(EpicsSignal, "_UWPEN_STS")
    uwpen_desc = Cpt(EpicsSignal, "_UWPEN_STS.DESC")
    uwsen = Cpt(EpicsSignal, "_UWSEN_STS")
    uwsen_desc = Cpt(EpicsSignal, "_UWSEN_STS.DESC")
    errtg = Cpt(EpicsSignal, "_ERRTG_STS")
    errtg_desc = Cpt(EpicsSignal, "_ERRTG_STS.DESC")
    swpoc = Cpt(EpicsSignal, "_SWPOC_STS")
    swpoc_desc = Cpt(EpicsSignal, "_SWPOC_STS.DESC")
    asscs = Cpt(EpicsSignal, "_ASSCS_STS")
    asscs_desc = Cpt(EpicsSignal, "_ASSCS_STS.DESC")
    frpos = Cpt(EpicsSignal, "_FRPOS_STS")
    frpos_desc = Cpt(EpicsSignal, "_FRPOS_STS.DESC")
    hsrch = Cpt(EpicsSignal, "_HSRCH_STS")
    hsrch_desc = Cpt(EpicsSignal, "_HSRCH_STS.DESC")
    sodpl = Cpt(EpicsSignal, "_SODPL_STS")
    sodpl_desc = Cpt(EpicsSignal, "_SODPL_STS.DESC")
    sopl = Cpt(EpicsSignal, "_SOPL_STS")
    sopl_desc = Cpt(EpicsSignal, "_SOPL_STS.DESC")
    hocpl = Cpt(EpicsSignal, "_HOCPL_STS")
    hocpl_desc = Cpt(EpicsSignal, "_HOCPL_STS.DESC")
    phsra = Cpt(EpicsSignal, "_PHSRA_STS")
    phsra_desc = Cpt(EpicsSignal, "_PHSRA_STS.DESC")
    prefe = Cpt(EpicsSignal, "_PREFE_STS")
    prefe_desc = Cpt(EpicsSignal, "_PREFE_STS.DESC")
    trmov = Cpt(EpicsSignal, "_TRMOV_STS")
    trmov_desc = Cpt(EpicsSignal, "_TRMOV_STS.DESC")
    iffe = Cpt(EpicsSignal, "_IFFE_STS")
    iffe_desc = Cpt(EpicsSignal, "_IFFE_STS.DESC")
    amfae = Cpt(EpicsSignal, "_AMFAE_STS")
    amfae_desc = Cpt(EpicsSignal, "_AMFAE_STS.2ESC")
    amfe = Cpt(EpicsSignal, "_AMFE_STS")
    amfe_desc = Cpt(EpicsSignal, "_AMFE_STS.DESC")
    fafoe = Cpt(EpicsSignal, "_FAFOE_STS")
    fafoe_desc = Cpt(EpicsSignal, "_FAFOE_STS.DESC")
    wfoer = Cpt(EpicsSignal, "_WFOER_STS")
    wfoer_desc = Cpt(EpicsSignal, "_WFOER_STS.DESC")
    inpos = Cpt(EpicsSignal, "_INPOS_STS")
    inpos_desc = Cpt(EpicsSignal, "_INPOS_STS.DESC")
    enc_lss = Cpt(EpicsSignal, "_ENC_LSS_STS")
    enc_lss_desc = Cpt(EpicsSignal, "_ENC_LSS_STS.DESC")

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


class DeadbandEpicsMotor(DeadbandMixin, EpicsMotor):
    pass

class FlyableMotor(EpicsMotor, FlyerMixin):
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
        boxed_text(self.name + " location", self.where_sp(), "green",
                   shrink=True)

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
