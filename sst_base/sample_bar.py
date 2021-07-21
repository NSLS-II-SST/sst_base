import numpy as np
from ophyd import Device, Signal, Component as Cpt
from .frames import Panel
from .linalg import vec, deg_to_rad, rad_to_deg


class Sample(Signal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check_value(self, val):
        if val is None:
            # None needs to be allowed so that sample cpt can be instantiated
            # before sample list is populated
            return
        elif val not in self.parent.samples:
            raise ValueError(f"{val} not in sample keys")
    
class Bar(Device):
    sample = Cpt(Sample, value=None, kind='config')
    
    def __init__(self, p1, p2, p3, width, height, nsides, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interior_angle = 360.0/nsides
        self.width = width
        self.height = height
        self.sides = []
        self.sample_frames = {}
        self.sample_md = {}
        current_side = Panel(p1, p2, p3, width=width, height=height)
        self.add_side(current_side, 1)
        self.sides.append(current_side)
        for n in range(nsides - 1):
            new_side = self._newSideFromSide(current_side, self.interior_angle)
            self.sides.append(new_side)
            self.add_side(new_side, n + 2)
            current_side = new_side
        self.sample.put("side1")

    @property
    def samples(self):
        return list(self.sample_frames.keys())
        
    def _newSideFromSide(self, side, angle):
        prev_edges = side.real_edges(vec(0, 0, 0), 0)
        new_vector = vec(np.cos(np.pi - deg_to_rad(angle)), 0, -np.sin(np.pi - deg_to_rad(angle)))
        p1 = prev_edges[1]
        p2 = prev_edges[2]
        p3 = side.frame_to_global(new_vector + side.edges[1], r=0, rotation="global")
        return Panel(p1, p2, p3, width=self.width, height=self.height)

    def distance_to_beam(self, x, y, z, r):
        distances = [side.distance_to_beam(x, y, z, r) for side in self.sides]
        return np.max(distances)

    def beam_to_frame(self, *args):
        """
        Beam coordinates in basis of current sample
        """
        current_frame = self.sample_frames[self.sample.get()]
        return current_frame.beam_to_frame(*args)

    def frame_to_beam(self, *args):
        """
        Current sample coordinates in beam (global) basis
        """
        current_frame = self.sample_frames[self.sample.get()]
        return current_frame.frame_to_beam(*args)

    def add_side(self, side, side_num):
        sample_id = f"side{side_num}"
        self.sample_frames[sample_id] = side
        self.sample_md[sample_id] = {"sample_name": sample_id}
        
    def add_sample(self, sample_id, x1, y1, x2, y2, side, t=0, **kwargs):
        p1 = vec(x1, y1, t)
        p2 = vec(x1, y2, t)
        p3 = vec(x2, y1, t)
        width = x2 - x1
        height = y2 - y1
        self.sample_frames[sample_id] = Panel(p1, p2, p3, height=height, width=width, parent=self.sides[side])
        self.sample_md[sample_id] = kwargs
