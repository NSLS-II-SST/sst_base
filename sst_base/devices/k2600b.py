from ophyd import EpicsSignal, EpicsSignalRO, Signal, Device, Component as Cpt, Kind, DeviceStatus
from sst_base.detectors.scalar import ophScalar

class KeithleySMU(Device):
    """ Keithley 26XXB SMU """
    VLim = Cpt(EpicsSignal, 'SP-LimV', kind='config')
    ILim = Cpt(EpicsSignal, 'SP-LimI', kind='config')
    SourceSelect = Cpt(EpicsSignal, 'Sour:Sts', write_pv='Sour-Sel', kind='config')
    OutputEnable = Cpt(EpicsSignal, 'Sts:Out-Ena', write_pv='Cmd:Out-Ena', kind='config')
    ISource = Cpt(EpicsSignal, 'RB-ILvl', write_pv='SP-ILvl', kind=Kind.config | Kind.hinted)
    VSource = Cpt(EpicsSignal, 'RB-VLvl', write_pv='SP-VLvl', kind=Kind.config | Kind.hinted)
    VMeas = Cpt(ophScalar, 'RB-MeasV', kind='hinted')
    IMeas = Cpt(ophScalar, 'RB-MeasI', kind='hinted')
    IMeasRange = Cpt(EpicsSignal, 'Sts-MeasIRang', write_pv='SP-MeasIRang', kind='config')
    VSourceRange = Cpt(EpicsSignal, 'Sts-SourVRang', write_pv='SP-SourVRang', kind='config')
    ISourceRange = Cpt(EpicsSignal, 'Sts-SourIRang', write_pv='SP-SourIRang', kind='config')
    AutorangeISource = Cpt(EpicsSignal, 'SP-SourAutoRangI', kind='config')
    AutorangeVSource = Cpt(EpicsSignal, 'SP-SourAutoRangV', kind='config')
    AutorangeIMeas = Cpt(EpicsSignal, 'SP-MeasAutoRangI', kind='config')
    AutorangeVMeas = Cpt(EpicsSignal, 'SP-MeasAutoRangV', kind='config')

    def __init__(self, *args, **kwargs):
        """ puts it in DCVolts Source mode, sets source voltage to 0, sets voltage limit to 10 mA """
        super().__init__(*args, **kwargs)
        self._flyers = [self.VMeas, self.IMeas]
        self.SourceSelect.set(1)
        #self.VSource.set(0)
        self.ILim.set(0.01)
        self.OutputEnable.set(1)
    
    def set(self, value):
        if self.SourceSelect.get() == 1:
            return self.VSource.set(value)
        elif self.SourceSelect.get() == 0:
            return self.ISource.set(value)
        else:
            raise ValueError(f"Invalid source select: {self.SourceSelect.get()}")

    def set_exposure(self, exp_time):
        self.VMeas.set_exposure(exp_time)
        self.IMeas.set_exposure(exp_time)

    def set_voltage(self,voltage_level):
        self.VSource.put(voltage_level)

    def disable(self):
        self.VSource.set(0)
        self.OutputEnable.set(0)

    def trigger(self):
        st1 = self.VMeas.trigger()
        st2 = self.IMeas.trigger()
        return st1 & st2

    def kickoff(self):
        st1 = self.VMeas.kickoff()
        st2 = self.IMeas.kickoff()
        return st1 & st2

    def collect(self):
        yield from self.VMeas.collect()
        yield from self.IMeas.collect()

    def complete(self):
        st1 = self.VMeas.complete()
        st2 = self.IMeas.complete()
        return st1 & st2

    def describe_collect(self):
        _collect_dict = {}
        for flyer in self._flyers:
            _collect_dict.update(flyer.describe_collect())
        return _collect_dict

  
#haxSMU = SMU('XF:07ID1{K2601B:1}', name='K2601B')
