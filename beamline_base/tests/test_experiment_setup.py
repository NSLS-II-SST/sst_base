import pytest
import os
from shutil import rmtree
from os.path import exists
from sst_base.beamtime import (get_config, save_config, get_config_file,
                               get_user_md, print_beamtime_info,
                               new_experiment, switch_experiment)
from sst_base.users import new_user, get_user_dictionary


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
    config_file = get_config_file()
    yield _md
    os.remove(config_file)


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
def user():
    base_folder = "/tmp"
    gup = "1111"
    saf = "2222"
    name = "Test User"
    user_folder, user_md = new_user(base_folder, gup, saf, name)
    yield user_folder, user_md
    rmtree(user_folder)


@pytest.fixture
def experiment(setup):
    base_folder = "/tmp"
    gup = "1111"
    saf = "2222"
    name = "Test User"
    user_folder, user_md, beamtime_md = new_experiment(base_folder, gup, saf,
                                                       name)
    config_file = get_config_file()
    yield (user_folder, user_md, beamtime_md)
    if exists(user_folder):
        rmtree(user_folder)
    if exists(config_file):
        os.remove(config_file)


@pytest.fixture
def experiment2(setup):
    base_folder = "/tmp"
    gup = "1112"
    saf = "2223"
    name = "Test User2"
    user_folder, user_md, beamtime_md = new_experiment(base_folder, gup, saf,
                                                       name)
    config_file = get_config_file()
    yield (user_folder, user_md, beamtime_md)
    if exists(user_folder):
        rmtree(user_folder)
    if exists(config_file):
        os.remove(config_file)


def test_fetch_user(user):
    user_folder, user_md = user
    saved_md = get_user_dictionary(user_folder)
    assert_user_dictionaries_equal(user_md, saved_md)


def test_beamtime_fetch_user(experiment):
    _, user_md, _ = experiment
    saved_user = get_user_md()
    assert_user_dictionaries_equal(saved_user, user_md)


def test_print_user_fails_gracefully(setup):
    print_beamtime_info()


def test_new_beamtime(experiment, experiment2):
    current_user = get_user_md()
    assert_user_dictionaries_equal(current_user, experiment2[1])


def test_switch_beamtime(experiment, experiment2):
    current_user = get_user_md()
    assert_user_dictionaries_equal(current_user, experiment2[1])
    switch_experiment(experiment[0])
    old_user = get_user_md()
    assert_user_dictionaries_equal(old_user, experiment[1])


def assert_user_dictionaries_equal(user1, user2):
    assert user1['gup'] == user2['gup']
    assert user1['saf'] == user2['saf']
    assert user1['name'] == user2['name']
