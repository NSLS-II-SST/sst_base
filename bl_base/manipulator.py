from ophyd import PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument,
                             _to_position_tuple)
from bl_base.sampleholder import dummy_holder

class Manipulator1AxBase():
    # Really need a discrete manipulator that can be set to
    # one of several sample positions. May just be a sampleholder
    # Good argument for having sampleholder contain the motors, not
    # the other way around...?
    pass


class Manipulator4AxBase(PseudoPositioner):
    """
    A manipulator is the top-level class of a three-tiered
    system. A manipulator holds a SampleHolder. The SampleHolder
    holds samples (duh). The manipulator carries the logic for
    coordinating motors. The SampleHolder and Sample have the logic
    for coordinate transformations.
    """
    sx = Cpt(PseudoSingle)
    sy = Cpt(PseudoSingle)
    sz = Cpt(PseudoSingle)
    sr = Cpt(PseudoSingle)

    def __init__(self, holder, *args, **kwargs):
        if holder is None:
            self.holder = dummy_holder
            self._holder_loaded = False
        super().__init__(*args, **kwargs)

    def add_holder(self, holder):
        self.holder = holder
        self._holder_loaded = True
        
    @pseudo_position_argument
    def forward(self, pp):
        rx, ry, rz, rr = self.holder.frame_to_beam(pp.sx, pp.sy, pp.sz, pp.sr)
        return self.RealPosition(x=rx, y=ry, z=rz, r=rr)

    @real_position_argument
    def inverse(self, rp):
        sx, sy, sz, sr = self.holder.beam_to_frame(rp.x, rp.y, rp.z, rp.r)
        return self.PseudoPosition(sx=sx, sy=sy, sz=sz, sr=sr)

    def to_pseudo_tuple(self, *args, **kwargs):
        return _to_position_tuple(self.PseudoPosition, *args, **kwargs,
                                  _cur=lambda: self.position)

    def distance_to_beam(self):
        """
        Distance between the beam and the nearest edge of
        the sample holder
        """
        x, y, z, r = self.real_position
        return self.holder.distance_to_beam(x, y, z, r)

    def sample_distance_to_beam(self):
        """
        Distance between the beam and the nearest edge of
        the sample
        """
        x, y, z, r = self.real_position
        return self.holder.sample_distance_to_beam(x, y, z, r)
