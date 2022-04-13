import numpy as np
from ophyd import Device, Signal, Component as Cpt
from ophyd.status import StatusBase
from sst_funcs.geometry.frames import Panel, Interval, NullFrame
from sst_funcs.geometry.linalg import vec, deg_to_rad


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
        if md.get('origin', None) is None:
            self.origin.kind = "omitted"
        else:
            self.origin.set(md['origin'])
            self.origin.kind = 'normal'
        status = StatusBase()
        status.set_finished()
        return status


def make_1d_bar(length):
    return [Interval(0, length)]


def make_two_sided_bar(width, height, thickness=0, parent=None):
    y = width/2.0
    x = thickness/2.0
    z = height
    p1 = vec(x, y, z)
    p2 = p1 + vec(0, 0, -1)
    p3 = p1 + vec(0, -1, 0)
    side1 = Panel(p1, p2, p3, width=width, height=height, parent=parent)

    y = -width/2.0
    x = -thickness/2.0
    z = height
    p1 = vec(x, y, z)
    p2 = p1 + vec(0, 0, -1)
    p3 = p1 + vec(0, -1, 0)

    side2 = Panel(p1, p2, p3, width=width, height=height, parent=parent)

    return [side1, side2]


def make_regular_polygon(width, height, nsides, points=None,
                         parent=None, invert=True):
    geometry = []
    interior_angle = deg_to_rad(360.0/nsides)
    if invert:
        az = -1
    else:
        az = 1

    if points is None:
        y = -1*az*width/2.0
        x = width/(2.0*np.tan(interior_angle/2.0))
        if invert:
            z = height
        else:
            z = 0
        p1 = vec(x, y, z)
        p2 = p1 + vec(0, 0, az)
        p3 = p1 + vec(0, az, 0)
    else:
        p1, p2, p3 = points

    def _newSideFromSide(side):
        prev_edges = side.real_edges(vec(0, 0, 0), 0)
        new_vector = vec(np.cos(np.pi - interior_angle), 0,
                         -np.sin(np.pi - interior_angle))
        p1 = prev_edges[1]
        p2 = prev_edges[2]
        p3 = side.frame_to_global(new_vector + side.edges[1], r=0,
                                  rotation="global")
        return Panel(p1, p2, p3, width=width, height=height, parent=parent)

    current_side = Panel(p1, p2, p3, width=width, height=height,
                         parent=parent)
    geometry.append(current_side)
    new_sides = []
    for n in range(1, nsides):
        new_side = _newSideFromSide(current_side)
        new_sides.append(new_side)
        current_side = new_side
    # It is unfortunately easier to generate sides in reverse order
    # due to the coordinate system, so we must reverse them.
    geometry += new_sides[::-1]
    return geometry


class SampleHolder(Device):
    """
    Consider adding manipulator to sampleholder so that
    we can just operate on the SampleHolder...
    """
    sample = Cpt(Sample, kind='config')

    def __init__(self, *args,  manipulator=None, geometry=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_manipulator(manipulator)
        self._reset()
        if geometry is not None:
            self.add_geometry(geometry)

    def add_manipulator(self, manipulator):
        if manipulator is not None:
            manipulator.add_holder(self)
        self.manipulator = manipulator

    def _reset(self):
        self.clear_samples()
        self.sides = []
        self._has_geometry = False


    def clear_samples(self):
        """
        Removes all samples from holder, if any, and re-adds
        the null frame
        """
        self.sample_frames = {}
        self.sample_md = {}
        null_frame = NullFrame()
        self._add_frame(null_frame, "null", "null", -1)
        self.set("null")
                
    @property
    def samples(self):
        return list(self.sample_frames.keys())

    @property
    def current_frame(self):
        return self.sample_frames[self.sample.sample_id.get()]

    def update_side(self, side_num, *args):
        self.sides[side_num].update_basis(*args)

    def set(self, sample_id, **kwargs):
        _md = self.sample_md[f"{sample_id}"]
        md = {}
        md.update(_md)
        md.update(kwargs)
        return self.sample.set(md)

    def _add_frame(self, frame, sample_id, name, side=-1, desc="",
                   origin='edge'):
        md = {"sample_id": sample_id,
              "sample_name": name,
              "side": side,
              "sample_desc": desc}
        self.sample_frames[sample_id] = frame
        self.sample_md[sample_id] = md

    def add_geometry(self, geometry):
        """
        geometry : List of sides
        """
        self._reset()
        self.sides = geometry
        for n, side in enumerate(geometry):
            side_num = n + 1
            sample_id = f"side{side_num}"
            self._add_frame(side, sample_id, sample_id, side_num)
        self._has_geometry = True

    def add_parent_frame(self, frame):
        for s in self.sides:
            s.add_parent_frame(frame)

    def add_sample(self, sample_id, name, position, side, desc="", **kwargs):
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
        s = self.sides[side - 1]
        frame = s.make_sample_frame(position, **kwargs)
        self._add_frame(frame, sample_id, name, side, desc)

    def frame_to_beam(self, *args, **kwargs):
        md = {'origin': self.sample.origin.get()}
        md.update(kwargs)
        return self.current_frame.frame_to_beam(*args, **md)

    def beam_to_frame(self, *args, **kwargs):
        md = {'origin': self.sample.origin.get()}
        md.update(kwargs)
        return self.current_frame.beam_to_frame(*args, **md)

    def distance_to_beam(self, *args, **kwargs):
        if self._has_geometry:
            distances = [side.distance_to_beam(*args)
                         for side in self.sides]
            return np.min(distances)
        else:
            distance = self.current_frame.distance_to_beam(*args)
            return distance

    def sample_distance_to_beam(self, *args):
        return self.current_frame.distance_to_beam(*args)

    def check_value(self, val):
        if val is None:
            # None needs to be allowed so that sample cpt can be instantiated
            # before sample list is populated
            return
        elif val not in self.samples:
            raise ValueError(f"{val} not in sample keys")

    def print_samples(self):
        print(f"Samples loaded on {self.name}:")
        for v in self.sample_md.values():
            print(f"{v['sample_id']}: {v['sample_name']}")
    
dummy_holder = SampleHolder(name="dummy_holder")
dummy_geometry = make_regular_polygon(1, 1, 4)
dummy_holder.add_geometry(dummy_geometry)
