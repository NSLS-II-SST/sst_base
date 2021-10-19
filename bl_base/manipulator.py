from ophyd import PseudoPositioner, PseudoSingle
from ophyd import Component as Cpt
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument,
                             _to_position_tuple)


class Manipulator1AxBase():
    # Really need a discrete manipulator that can be set to
    # one of several sample positions. May just be a sampleholder
    # Good argument for having sampleholder contain the motors, not
    # the other way around...?
    pass


class Manipulator4AxBase(PseudoPositioner):
    # Find some way to record all motors that moved!
    # Radical thought: Decouple Manipulator4AxBase from bar.
    # Manipulator just has a "frame" that can be set arbitrarily
    # Functions not attached to any class are defined that take
    # both Manipulator and SampleHolder and move samples. 
    sx = Cpt(PseudoSingle)
    sy = Cpt(PseudoSingle)
    sz = Cpt(PseudoSingle)
    sr = Cpt(PseudoSingle)

    def __init__(self, bar, *args, **kwargs):
        self.bar = bar
        super().__init__(*args, **kwargs)

    @pseudo_position_argument
    def forward(self, pp):
        rx, ry, rz, rr = self.bar.frame_to_beam(pp.sx, pp.sy, pp.sz, pp.sr)
        return self.RealPosition(x=rx, y=ry, z=rz, r=rr)

    @real_position_argument
    def inverse(self, rp):
        sx, sy, sz, sr = self.bar.beam_to_frame(rp.x, rp.y, rp.z, rp.r)
        return self.PseudoPosition(sx=sx, sy=sy, sz=sz, sr=sr)

    def to_pseudo_tuple(self, *args, **kwargs):
        return _to_position_tuple(self.PseudoPosition, *args, **kwargs,
                                  _cur=lambda: self.position)

    def distance_to_beam(self):
        x, y, z, r = self.real_position
        return self.bar.distance_to_beam(x, y, z, r)

    def sample_distance_to_beam(self):
        x, y, z, r = self.real_position
        return self.bar.sample_distance_to_beam(x, y, z, r)
