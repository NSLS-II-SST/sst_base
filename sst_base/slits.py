from ophyd import EpicsMotor, PseudoPositioner, PseudoSingle, Component as Cpt
from ophyd.pseudopos import pseudo_position_argument, real_position_argument
from nbs_bl.printing import boxed_text
from .motors import FMBOEpicsMotor


class QuadSlitsBase(PseudoPositioner):
    """
    Base class for quad slits.

    Parameters
    ----------
    *args
        Arguments to pass to parent class
    **kwargs
        Keyword arguments to pass to parent class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def where(self):
        print("%s:" % self.name)
        text1 = "      vertical   size   = %7.3f mm\n" % (self.vsize.position)
        text1 += "      vertical   center = %7.3f mm\n" % (self.vcenter.position)
        text2 = "      horizontal size   = %7.3f mm\n" % (self.hsize.position)
        text2 += "      horizontal center = %7.3f mm\n" % (self.hcenter.position)
        return text1 + text2

    def wh(self):
        boxed_text(self.name, self.where(), "cyan")

    # The pseudo positioner axes:

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Run a forward (pseudo -> real) calculation.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position to calculate real positions for

        Returns
        -------
        RealPosition
            The real motor positions
        """
        return self.RealPosition(
            top=pseudo_pos.vcenter + pseudo_pos.vsize / 2,
            bottom=pseudo_pos.vcenter - pseudo_pos.vsize / 2,
            outboard=pseudo_pos.hcenter + pseudo_pos.hsize / 2,
            inboard=pseudo_pos.hcenter - pseudo_pos.hsize / 2,
        )

    @real_position_argument
    def inverse(self, real_pos):
        """
        Run an inverse (real -> pseudo) calculation.

        Parameters
        ----------
        real_pos : RealPosition
            The real positions to calculate pseudo positions for

        Returns
        -------
        PseudoPosition
            The pseudo axis positions
        """
        return self.PseudoPosition(
            hsize=real_pos.outboard - real_pos.inboard,
            hcenter=(real_pos.outboard + real_pos.inboard) / 2,
            vsize=real_pos.top - real_pos.bottom,
            vcenter=(real_pos.top + real_pos.bottom) / 2,
        )


class QuadSlits(QuadSlitsBase):
    """
    Quad slits implementation using standard EpicsMotors.
    """

    vsize = Cpt(PseudoSingle, limits=(-1, 20), kind="hinted")
    vcenter = Cpt(PseudoSingle, limits=(-10, 10), kind="hinted")
    hsize = Cpt(PseudoSingle, limits=(-1, 20), kind="hinted")
    hcenter = Cpt(PseudoSingle, limits=(-10, 10), kind="hinted")

    # The real (or physical) positioners:
    top = Cpt(EpicsMotor, "T}Mtr", kind="hinted")
    bottom = Cpt(EpicsMotor, "B}Mtr", kind="hinted")
    inboard = Cpt(EpicsMotor, "I}Mtr", kind="hinted")
    outboard = Cpt(EpicsMotor, "O}Mtr", kind="hinted")


class FMBOQuadSlits(QuadSlitsBase):
    """
    Quad slits implementation using FMBOEpicsMotors.
    """

    vsize = Cpt(PseudoSingle, limits=(-1, 20), kind="hinted")
    vcenter = Cpt(PseudoSingle, limits=(-10, 10), kind="hinted")
    hsize = Cpt(PseudoSingle, limits=(-1, 20), kind="hinted")
    hcenter = Cpt(PseudoSingle, limits=(-10, 10), kind="hinted")

    # The real (or physical) positioners:
    top = Cpt(FMBOEpicsMotor, "T}Mtr", kind="hinted")
    bottom = Cpt(FMBOEpicsMotor, "B}Mtr", kind="hinted")
    inboard = Cpt(FMBOEpicsMotor, "I}Mtr", kind="hinted")
    outboard = Cpt(FMBOEpicsMotor, "O}Mtr", kind="hinted")


def QuadSlitsLimitFactory(*args, limits={}, **kwargs):
    _limits = {"vsize": (-1, 20), "hsize": (-1, 20), "vcenter": (-10, 10), "hcenter": (-10, 10)}
    _limits.update(limits)

    class QuadSlits(QuadSlitsBase):

        vsize = Cpt(PseudoSingle, limits=_limits["vsize"], kind="hinted")
        vcenter = Cpt(PseudoSingle, limits=_limits["vcenter"], kind="hinted")
        hsize = Cpt(PseudoSingle, limits=_limits["hsize"], kind="hinted")
        hcenter = Cpt(PseudoSingle, limits=_limits["hcenter"], kind="hinted")

        top = Cpt(EpicsMotor, "T}Mtr", kind="hinted")
        bottom = Cpt(EpicsMotor, "B}Mtr", kind="hinted")
        inboard = Cpt(EpicsMotor, "I}Mtr", kind="hinted")
        outboard = Cpt(EpicsMotor, "O}Mtr", kind="hinted")

    return QuadSlits(*args, **kwargs)


def FMBOQuadSlitsLimitFactory(*args, limits={}, **kwargs):
    _limits = {"vsize": (-1, 20), "hsize": (-1, 20), "vcenter": (-10, 10), "hcenter": (-10, 10)}
    _limits.update(limits)

    class FMBOQuadSlits(QuadSlitsBase):

        vsize = Cpt(PseudoSingle, limits=_limits["vsize"], kind="hinted")
        vcenter = Cpt(PseudoSingle, limits=_limits["vcenter"], kind="hinted")
        hsize = Cpt(PseudoSingle, limits=_limits["hsize"], kind="hinted")
        hcenter = Cpt(PseudoSingle, limits=_limits["hcenter"], kind="hinted")

        top = Cpt(FMBOEpicsMotor, "T}Mtr", kind="hinted")
        bottom = Cpt(FMBOEpicsMotor, "B}Mtr", kind="hinted")
        inboard = Cpt(FMBOEpicsMotor, "I}Mtr", kind="hinted")
        outboard = Cpt(FMBOEpicsMotor, "O}Mtr", kind="hinted")

    return FMBOQuadSlits(*args, **kwargs)
