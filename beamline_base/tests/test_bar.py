import pytest

from sst_base.sample_bar import SampleHolder
from sst_base.linalg import vec
import numpy as np


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
    height = 10
    nsides = 4
    points = (p1, p2, p3)
    bar = SampleHolder(name='samplebar')
    bar.load_geometry(width, height, nsides, points=points)
    return bar


def test_load_geometry_twice_overwrites(empty_bar):
    width = 1
    height = 10
    nsides = 5
    empty_bar.load_geometry(width, height, nsides + 1)
    assert len(empty_bar.sides) == nsides + 1
    empty_bar.load_geometry(width, height, nsides)
    assert len(empty_bar.sides) == nsides


@pytest.fixture
def empty_bar():
    bar = SampleHolder(name='samplebar')
    return bar


def test_bar_edge_distances(unit_bar):
    assert unit_bar.distance_to_beam(-0.5, 0, -1, 0) == 0
    assert unit_bar.distance_to_beam(-0.5, -0.5, -1, 0) == 0
    assert unit_bar.distance_to_beam(0.5, 0, -1, 0) == 0
    assert unit_bar.distance_to_beam(0, 0, -2, 0) == -0.5
    assert unit_bar.distance_to_beam(0, 0, -0.25, 0) == -0.25
    assert unit_bar.distance_to_beam(0, 0, 2, 0) == 2


def test_bar_subframe(unit_bar):
    position = (0, 1, 1, 2)
    sample_id = 1
    side = 1
    name = "sample"
    unit_bar.add_sample(sample_id, name, position, side)

    unit_bar.set(1)
    assert np.all(np.isclose(unit_bar.frame_to_beam(0, 0, 0, 90),
                             [-0.5, -0.5, -1, 90]))


def test_cant_add_sample_to_empty_bar(empty_bar):
    position = (0, 1, 1, 2)
    sample_id = 1
    side = 1
    name = "sample"
    with pytest.raises(RuntimeError):
        empty_bar.add_sample(sample_id, name, position, side)


def test_empty_bar_has_position(empty_bar):
    assert empty_bar.distance_to_beam(0, 0, 0, 0) == 0
    rng = np.random.default_rng()
    for x in 10*rng.random(5):
        for z in 10*rng.random(5):
            assert np.isclose(empty_bar.distance_to_beam(x, 0, z, 0),
                              np.sqrt(x**2 + z**2))
