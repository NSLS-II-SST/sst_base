import numpy as np        
from .linalg import *
from .polygons import *


class Frame:
    def __init__(self, p1, p2, p3, parent=None):
        self.reset(p1, p2, p3, parent=parent)

    def reset(self, p1, p2, p3, parent=None):
        self.p0 = p1
        self._basis = constructBasis(p1, p2, p3)
        # r_offset
        self.A = changeBasisMatrix(*self._basis)
        self.Ainv = self.A.T
        self.parent = parent
        self.r0 = rad_to_deg(self._roffset())

    def _roffset(self):
        """
        R offset relative to the GLOBAL frame (not the parent frame!)

        Important note! It is a BAKED IN ASSUMPTION that
        these frames are being used for beamline samples, and
        that the z-axis is perpendicular to the sample surface.
        "Rotation" means the angle that the sample z-axis makes
        with respect to the beam in the global x-y plane. This
        makes sense because we only have a 4-axis manipulator.
        If we had, god forbid, a 6-axis manipulator, none of this
        1-axis rotation stuff would make sense, and you would just
        have to specify an exact vector, rather than an angle.
        """

        # we bootstrap the rotation by finding the z-vector in the global
        # frame, even if
        # we have a parent.
        n3 = (self.frame_to_global(vec(0, 0, 1), rotation='global') -
              self.frame_to_global(vec(0, 0, 0), rotation='global'))
        x = n3[0]
        y = n3[1]
        if y == 0:
            return 0
        elif x >= 0 and y >= 0:
            quad = 1
        elif x < 0 and y >= 0:
            quad = 2
        elif x <= 0 and y < 0:
            quad = 3
        else:
            quad = 4
        theta = np.arctan(y/x)
        if quad == 1:
            return theta
        elif quad == 2 or quad == 3:
            return theta + np.pi
        elif quad == 4:
            return theta + 2*np.pi

    def _to_global(self, v):
        return np.dot(self.A, v) + self.p0

    def _to_frame(self, v):
        return np.dot(self.Ainv, v - self.p0)

    def _manip_to_global(self, v_manip, manip, r):
        theta = deg_to_rad(r)
        v_global = rotz(theta, v_manip) + manip
        return v_global

    def _global_to_manip(self, v_global, manip, r):
        theta = deg_to_rad(r)
        v_manip = rotz(-theta, v_global - manip)
        return v_manip

    def frame_to_global(self, v_frame, manip=vec(0, 0, 0), r=0,
                        rotation="frame"):
        """
        Find the global coordinates of a point in the frame, given the
        rotation of the frame, and the manipulator position
        v_frame: frame vector
        manip: current position of manipulator
        r: rotation of the frame (0 = grazing incidence, 90 = normal)
        """
        if rotation == 'frame':
            rg = r - self.r0
        else:
            rg = r
        v_global = self._to_global(v_frame)
        if self.parent is not None:
            return self.parent.frame_to_global(v_global, manip, r=rg,
                                               rotation='global')
        else:
            v_global = self._manip_to_global(v_global, manip, rg)
        return v_global

    def global_to_frame(self, v_global, manip=vec(0, 0, 0), r=0):
        """
        Find the frame coordinates of a point in the global system, 
        given the manipulator position and rotation

        v_global: global vector
        manip: current position of manipulator
        r: rotation of the manipulator
        """
        if self.parent is not None:
            v_manip = self.parent.global_to_frame(v_global, manip, r)
        else:
            v_manip = self._global_to_manip(v_global, manip, r)
        v_frame = self._to_frame(v_manip)
        return v_frame

    def frame_to_beam(self, fx, fy, fz, fr=0):
        """
        Given a frame coordinate, and rotation, find the manipulator position and rotation
        that places the frame coordinate in the beam path
        
        return coordinate tuple
        """
        v_frame = vec(fx, fy, fz)
        v_global = -1*self.frame_to_global(v_frame, r=fr)
        gr = fr - self.r0
        gx, gy, gz = (v_global[0], v_global[1], v_global[2])
        return gx, gy, gz, gr

    def beam_to_frame(self, gx, gy, gz, gr=0):
        """
        Given a manipulator coordinate and rotation, find the beam intersection position and 
        incidence angle in the frame coordinates.

        return coordinate tuple
        """
        manip = vec(gx, gy, gz)
        v_frame = self.origin_to_frame(manip, gr)
        fx, fy, fz = (v_frame[0], v_frame[1], v_frame[2])
        fr = gr + self.r0
        return fx, fy, fz, fr

    def origin_to_frame(self, manip=vec(0, 0, 0), r=0):
        return self.global_to_frame(vec(0, 0, 0), manip, r)

    def project_beam_to_frame_xy(self, manip=vec(0, 0, 0), r=0):
        op = self.origin_to_frame(manip, r)
        theta = deg_to_rad(r)
        Rz_inv = rotzMat(-theta)
        vp = np.dot(self.Ainv, np.dot(Rz_inv, vec(0, 1, 0)))
        a = op[-1]/vp[-1]
        proj = op - a*vp
        return proj

    def distance_to_beam(self, gx, gy, gz, gr=0):
        """
        Given the manipulator coordinate (and rotation, for consistency),
        find the distance from the beam to the coordinate origin, ignoring
        the beam y-axis
        """
        op = self.frame_to_global(vec(0, 0, 0), manip=vec(gx, gy, gz), r=gr)
        distance = np.sqrt(op[0]**2 + op[2]**2)
        return distance


class Panel(Frame):
    """
    A frame that has boundaries, making it a rectangle
    """
    def __init__(self, *args, width=19.5, height=130, parent=None):
        super().__init__(*args, parent=parent)
        self.width = width
        self.height = height
        self.edges = [vec(0, 0, 0), vec(width, 0, 0), vec(width, height, 0),
                      vec(0, height, 0)]

    def real_edges(self, manip, r_manip):
        re = []
        for edge in self.edges:
            real_coord = self.frame_to_global(edge, manip, r_manip,
                                              rotation='global')
            re.append(real_coord)
        return re

    def project_real_edges(self, manip, r_manip):
        re = self.real_edges(manip, r_manip)
        ret = []
        for edge in re:
            ret.append(np.array([edge[0], edge[2]]))
        return ret

    def distance_to_beam(self, x, y, z, r):
        """
        r manipulator
        """
        manip = vec(x, y, z)
        real_edges = self.project_real_edges(manip, r)
        inPoly = isInPoly(vec(0, 0), *real_edges)
        distance = getMinDist(vec(0, 0), *real_edges)
        if inPoly:
            return distance
        else:
            return -1*distance

