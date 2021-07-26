import pytest

from sst_base.sample_bar import *
from sst_base.linalg import vec

@pytest.fixture
def unit_bar():
    """
    Unit bar with base corners at (0.5, 0.5, 0), (0.5, -0.5, 0), 
    (-0.5, -0.5, 0), (-0.5, 0.5, 0) and height 10
    """
    p1 = vec(0.5, -0.5, 0)
    p2 = vec(0.5, -0.5, 1)
    p3 = vec(0.5, 0.5, 0)
    width = 1
    height=10
    nsides=4
    bar = Bar(p1, p2, p3, width, height, nsides, name='samplebar')
    return bar


def test_bar_edge_distances(unit_bar):
    assert unit_bar.distance_to_beam(-0.5, 0, -1, 0) == 0
    assert unit_bar.distance_to_beam(-0.5, -0.5, -1, 0) == 0
    assert unit_bar.distance_to_beam(0.5, 0, -1, 0) == 0
    assert unit_bar.distance_to_beam(0, 0, -2, 0) == 0.5

def test_bar_subframe(unit_bar):
    x1, y1, x2, y2 = (0, 1, 1, 2)
    sample_id = 1
    side = 0
    unit_bar.add_sample(sample_id, x1, y1, x2, y2, side)
    
    unit_bar.sample.put(1)
    assert np.all(np.isclose(unit_bar.frame_to_beam(0, 0, 0, 90), [-0.5, -0.5, -1, 90]))
