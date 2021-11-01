import numpy as np
from ophyd import Device, Signal, Component as Cpt
from bl_funcs.geometry.frames import Panel, Frame
from bl_funcs.geometry.linalg import vec, deg_to_rad


class Sample(Device):
    sample_name = Cpt(Signal, value="")
    sample_id = Cpt(Signal, value=None)
    sample_desc = Cpt(Signal, value="")
    side = Cpt(Signal, value=0)
    origin = Cpt(Signal, value="")

    def set(self, md):
        self.sample_name.set(md['sample_name'])
        self.sample_id.set(md['sample_id'])
        self.sample_desc.set(md['sample_desc'])
        self.side.set(md['side'])
        self.origin.set(md['origin'])


class SampleHolderBase(Device):
    sample = Cpt(Sample, kind='config')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reset()

    def _reset(self):
        self.sample_frames = {}
        self.sample_md = {}
        self.set("null")
        self.geometry = None
        self._has_geometry = False

    @property
    def samples(self):
        return list(self.sample_frames.keys())

    @property
    def current_frame(self):
        return self.sample_frames[self.sample.sample_id.get()]

    def set(self, sample_id, **kwargs):
        _md = self.sample_md[sample_id]
        md = {}
        md.update(_md)
        md.update(kwargs)
        self.sample.set(md)


    def add_geometry(self, geometry):
        """
        geometry : List of sides
        """
        self.sides = geometry
        for n, side in enumerate(geometry):
            sample_id = f"side{n + 1}"
        self.add_frame(side, sample_id, sample_id, side_num)
    
    def add_sample(self, sample_id, name, position, side, t=0, desc=""):
        """
        sample_id: Unique sample identifier
        position: x1, y1, x2, y2 tuple
        side: side number (starting from 1)
        """
        if not self._has_geometry:
            raise RuntimeError("Bar has no geometry loaded. "
                               "Call load_geometry first")
        if side > len(self.sides):
            raise ValueError(f"Side {side} too large, bar only has"
                             " {len(self.sides)} sides!")

        x1, y1, x2, y2 = position
        p1 = vec(x1, y1, t)
        p2 = vec(x1, y2, t)
        p3 = vec(x2, y1, t)
        width = x2 - x1
        height = y2 - y1

        frame = Panel(p1, p2, p3, height=height, width=width,
                      parent=self.sides[side - 1])
        self.add_frame(frame, sample_id, name, side, desc)
        return frame

    def get_sample_pos(*args, **kwargs):
        pass
    

class SampleHolder(SampleHolderBase):
    
class SampleHolderOld(Device):
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
        null_frame = Frame(vec(0, 0, 0), vec(0, 0, 1), vec(0, 1, 0))
        self.add_frame(null_frame, "null", "null", -1)
        self.set("null")
        self._has_geometry = False

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
        self._reset()
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
        for n in range(1, nsides):
            new_side = self._newSideFromSide(current_side, self.interior_angle)
            self.add_side(new_side, n + 1)  # sides start at 1, not 0
            current_side = new_side
        self.set("side1")
        self._has_geometry = True

    def calibrate(self, side_num, p1, p2, p3):
        # have a list of calibrated/uncalibrated sides?
        self.sides[side_num].reset(p1, p2, p3)

    def add_side(self, side, side_num):
        sample_id = f"side{side_num}"
        self.sides.append(side)
        self.add_frame(side, sample_id, sample_id, side_num)

    def add_frame(self, frame, sample_id, name, side=-1, desc="",
                  origin='edge'):
        md = {"sample_id": sample_id,
              "sample_name": name,
              "side": side,
              "sample_desc": desc}
        self.sample_frames[sample_id] = frame
        self.sample_md[sample_id] = md

    def add_sample(self, sample_id, name, position, side, t=0, desc=""):
        """
        sample_id: Unique sample identifier
        position: x1, y1, x2, y2 tuple
        side: side number (starting from 1)
        """
        if not self._has_geometry:
            raise RuntimeError("Bar has no geometry loaded. "
                               "Call load_geometry first")
        if side > len(self.sides):
            raise ValueError(f"Side {side} too large, bar only has"
                             " {len(self.sides)} sides!")

        x1, y1, x2, y2 = position
        p1 = vec(x1, y1, t)
        p2 = vec(x1, y2, t)
        p3 = vec(x2, y1, t)
        width = x2 - x1
        height = y2 - y1

        frame = Panel(p1, p2, p3, height=height, width=width,
                      parent=self.sides[side - 1])
        self.add_frame(frame, sample_id, name, side, desc)
        return frame

    def set_frame_sample_edge(self, sample_id):
        self.set(sample_id, "edge")

    def set_frame_sample_center(self, sample_id):
        self.set(sample_id, "center")

    def check_value(self, val):
        if val is None:
            # None needs to be allowed so that sample cpt can be instantiated
            # before sample list is populated
            return
        elif val not in self.samples:
            raise ValueError(f"{val} not in sample keys")

    def _newSideFromSide(self, side, angle):
        prev_edges = side.real_edges(vec(0, 0, 0), 0)
        new_vector = vec(np.cos(np.pi - deg_to_rad(angle)), 0,
                         -np.sin(np.pi - deg_to_rad(angle)))
        p1 = prev_edges[1]
        p2 = prev_edges[2]
        p3 = side.frame_to_global(new_vector + side.edges[1], r=0,
                                  rotation="global")
        return Panel(p1, p2, p3, width=self.width, height=self.height)

    def distance_to_beam(self, x, y, z, r):
        if self._has_geometry:
            distances = [side.distance_to_beam(x, y, z, r)
                         for side in self.sides]
            return np.min(distances)
        else:
            distance = self.current_frame.distance_to_beam(x, y, z, r)
            return distance

    def sample_distance_to_beam(self, x, y, z, r):
        return self.current_frame.distance_to_beam(x, y, z, r)

    def beam_to_frame(self, x, y, z, r):
        """
        Given a manipulator coordinate and rotation, find the beam intersection
        position and incidence angle in the frame coordinates.

        Parameters
        ------------
        x : float
            manipulator x coordinate
        y : float
            manipulator y coordinate
        z : float
            manipulator z coordinate
        r : float, degrees
            manipulator r coordinate

        Returns
        --------
        coordinates : tuple
            The x, y, z, r coordinates of the beam in the frame system
        """
        if self.sample.origin.get() == "edge":
            return self.current_frame.beam_to_frame(x, y, z, r)
        elif self.sample.origin.get() == "center":
            _x, _y, z, r = self.current_frame.beam_to_frame(x, y, z, r)
            x = _x - self.current_frame.width/2.0
            y = _y - self.current_frame.height/2.0
            return x, y, z, r

    def frame_to_beam(self, x, y, z, r):
        """
        Current sample coordinates in beam (global) basis

        Parameters
        ------------
        x : float
            x coordinate in sample frame
        y : float
            y coordinate in sample frame
        z : float
            z coordinate in sample frame
        r : float, degrees
            rotation in sample frame

        Returns
        ---------
        coordinates : tuple
            The x, y, z, r coordinates of the manipulator that put the sample
            spot into the beam path
        """
        if self.sample.origin.get() == "edge":
            return self.current_frame.frame_to_beam(x, y, z, r)
        elif self.sample.origin.get() == "center":
            x0 = self.current_frame.width/2.0
            y0 = self.current_frame.height/2.0
            return self.current_frame.frame_to_beam(x + x0, y + y0, z, r)
