import pytest
import os
from shutil import rmtree
from os.path import exists, join
from sst_base.beamtime import get_config, save_config, get_config_file, get_user_md
from sst_base.users import new_experiment, get_user_dictionary

@pytest.fixture(scope="module")
def setup():
    config_dir = "/tmp/sst_config"
    os.environ["SST_CONFIG_DIR"] = config_dir
    os.mkdir(config_dir)
    yield config_dir
    rmtree(config_dir)


def test_setup_fixture(setup):
    assert exists(setup)
    assert os.getenv("SST_CONFIG_DIR") == setup


@pytest.fixture
def arbitrary_md(setup):
    _md = {"test": 5}
    save_config(_md)
    return _md


def test_config_get_before_save(setup):
    with pytest.raises(FileNotFoundError):
        get_config()


def test_config_load(arbitrary_md):
    saved_md = get_config()
    assert saved_md == arbitrary_md


def test_config_overwrite(arbitrary_md):
    new_md = {"test": 10}
    with pytest.raises(FileExistsError):
        save_config(new_md)
    save_config(new_md, overwrite=True)
    saved_md = get_config()
    assert saved_md == new_md


@pytest.fixture
def new_user():
    base_folder = "/tmp"
    gup = "1111"
    saf = "2222"
    name = "Test User"
    directory = new_experiment(base_folder, gup, saf, name)
    user = {"directory": directory, "gup": gup, "saf": saf, "name": name}
    yield user
    rmtree(directory)


def test_fetch_user(new_user):
    user_md = get_user_dictionary(new_user['directory'])
    assert user_md['gup'] == new_user['gup']
    assert user_md['saf'] == new_user['saf']
    assert user_md['name'] == new_user['name']


@pytest.fixture
def beamline_md(setup, new_user):
    _md = {"user_directory": new_user['directory']}
    save_config(_md)
    return new_user


def test_beamtime_fetch_user(beamline_md):
    user_md = get_user_md()
    assert user_md['gup'] == beamline_md['gup']
    assert user_md['saf'] == beamline_md['saf']
    assert user_md['name'] == beamline_md['name']
