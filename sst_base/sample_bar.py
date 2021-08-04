import numpy as np
from ophyd import Device, Signal, Component as Cpt
from .frames import Panel
from .linalg import vec, deg_to_rad, rad_to_deg


class Sample(Device):
    sample_name = Cpt(Signal, value="")
    sample_id   = Cpt(Signal, value=None)
    sample_desc = Cpt(Signal, value="")
    side        = Cpt(Signal, value=0)
    def set(self, md):
        self.sample_name.set(md['sample_name'])
        self.sample_id.set(md['sample_id'])
        self.sample_desc.set(md['sample_desc'])
        self.side.set(md['side'])
            
class SampleHolder(Device):
    sample = Cpt(Sample, kind='config')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reset()
        
    def _reset(self):
        self.sides = []
        self.sample_frames = {}
        self.sample_md = {}
        self.interior_angle = None
        self.width = None
        self.height = None
        
    def load_geometry(self, width, height, nsides, points=None):
        """
        width: Width of side face in mm
        height: Height of side in mm
        nsides: Number of sides on bar (must be regular)
        points: Optional, p1, p2, p3 defining location/orientation of side 1.
        See documentation for sst_base/linalg.py:constructBasis
        """
        # will be inaccurate, need to persist a dictionary with rough defaults
        # currently assuming manipulator attachment point is 0, 0, 0
        self.interior_angle = 360.0/nsides
        self.width = width
        self.height = height

        y = -width/2.0
        x = width/(2.0*np.tan(self.interior_angle/2.0))
        z = -height
        if points is None:
            p1 = vec(x, y, z)
            p2 = p1 + vec(0, 0, 1)
            p3 = p1 + vec(0, 1, 0)
        else:
            p1, p2, p3 = points

        current_side = Panel(p1, p2, p3, width=width, height=height)
        self.add_side(current_side, 1)
        self.sides.append(current_side)
        for n in range(1, nsides):
            new_side = self._newSideFromSide(current_side, self.interior_angle)
            self.sides.append(new_side)
            self.add_side(new_side, n + 1) # sides start at 1, not 0
            current_side = new_side
        self.set("side1")

    def calibrate(self, side_num, p1, p2, p3):
        # have a list of calibrated/uncalibrated sides?
        self.sides[side_num].reset(p1, p2, p3)
        
    def add_side(self, side, side_num):
        sample_id = f"side{side_num}"
        self.sample_frames[sample_id] = side
        md = {"sample_id": sample_id, "sample_name": sample_id, "side": side_num, "sample_desc": ""}
        self.sample_md[sample_id] = md
        
    def add_sample(self, sample_id, name, position, side, t=0, desc=""):
        """
        sample_id: Unique sample identifier
        position: x1, y1, x2, y2 tuple
        side: side number (starting from 1)
        """
        x1, y1, x2, y2 = position
        p1 = vec(x1, y1, t)
        p2 = vec(x1, y2, t)
        p3 = vec(x2, y1, t)
        width = x2 - x1
        height = y2 - y1

        md = {}
        md["sample_id"] = sample_id
        md['sample_name'] = name
        md["sample_desc"] = desc
        md["side"] = side
        
        self.sample_frames[sample_id] = Panel(p1, p2, p3, height=height, width=width, parent=self.sides[side - 1])
        self.sample_md[sample_id] = md

    @property
    def samples(self):
        return list(self.sample_frames.keys())

    @property
    def current_frame(self):
        return self.sample_frames[self.sample.sample_id.get()]
        
    def set(self, sample_id):
        md = self.sample_md[sample_id]
        self.sample.set(md)

    def check_value(self, val):
        if val is None:
            # None needs to be allowed so that sample cpt can be instantiated
            # before sample list is populated
            return
        elif val not in self.samples:
            raise ValueError(f"{val} not in sample keys")

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
        
        return self.current_frame.beam_to_frame(*args)

    def frame_to_beam(self, *args):
        """
        Current sample coordinates in beam (global) basis
        """

        return self.current_frame.frame_to_beam(*args)

