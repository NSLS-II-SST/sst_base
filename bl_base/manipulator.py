from ophyd import PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument,
                             _to_position_tuple)
from bl_base.sampleholder import dummy_holder
from bl_funcs.geometry.linalg import vec

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

    def __init__(self, holder, origin=vec(0, 0, 0), frame=None, *args, **kwargs):
        """
        Frame takes care of translating manipulator coordinates
        to beam coordinates. Should be just an offset, equal to
        -1*beam origin.
        """
        #self.frame = frame
        self.origin = origin
        if holder is None:
            self.holder = dummy_holder
            self._holder_loaded = False
        super().__init__(*args, **kwargs)

    def manip_to_beam_frame(self, x, y, z, r):
        """
        Converts manipulator coordinates into
        the intermediate frame that can be used by
        the sampleholder (where the beam is at the origin)
        """
        ox, oy, oz = self.origin
        return (x - ox, y - oy, z - oz, r)

    def beam_to_manip_frame(self, x, y, z, r):
        """
        Converts the sampleholder frame into
        manipulator motor coordinates
        """
        ox, oy, oz = self.origin
        return (x + ox, y + oy, z + oz, r)

    def add_holder(self, holder):
        self.holder = holder
        # self.holder.add_parent_frame(self.frame)
        self._holder_loaded = True

    @pseudo_position_argument
    def forward(self, pp):
        rx, ry, rz, rr = self.holder.frame_to_beam(*pp)
        x, y, z, r = self.beam_to_manip_frame(rx, ry, rz, rr)
        return self.RealPosition(x=x, y=y, z=z, r=r)

    @real_position_argument
    def inverse(self, rp):
        x, y, z, r = self.manip_to_beam_frame(*rp)
        sx, sy, sz, sr = self.holder.beam_to_frame(x, y, z, r)
        return self.PseudoPosition(sx=sx, sy=sy, sz=sz, sr=sr)

    def to_pseudo_tuple(self, *args, **kwargs):
        return _to_position_tuple(self.PseudoPosition, *args, **kwargs,
                                  _cur=lambda: self.position)

    def distance_to_beam(self):
        """
        Distance between the beam and the nearest edge of
        the sample holder
        """
        x, y, z, r = self.manip_to_beam_frame(*self.real_position)
        return self.holder.distance_to_beam(x, y, z, r)

    def sample_distance_to_beam(self):
        """
        Distance between the beam and the nearest edge of
        the sample
        """
        x, y, z, r = self.manip_to_beam_frame(*self.real_position)
        return self.holder.sample_distance_to_beam(x, y, z, r)
