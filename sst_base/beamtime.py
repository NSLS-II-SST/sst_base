"""
Tools for setting up a beamtime
"""
import yaml
import os
from os.path import join, exists
from .users import get_user_dictionary, new_user


def get_config_file():
    config_file = join(os.getenv("HOME"), os.getenv('SST_CONFIG_DIR'),
                       "beamtime_md")
    return config_file


def get_config():
    config_file = get_config_file()
    with open(config_file, "r") as f:
        config_md = yaml.load(f)
    return config_md


def save_config(config_md, overwrite=False):
    config_file = get_config_file()
    if exists(config_file) and not overwrite:
        raise FileExistsError
    with open(config_file, "w") as f:
        yaml.dump(config_md, f)


def setup_beamtime(user_folder, overwrite=False):
    beamtime_md = {"user_folder": user_folder}
    save_config(beamtime_md, overwrite=overwrite)
    return beamtime_md


def get_user_md():
    config = get_config()
    user_folder = config['user_folder']
    return get_user_dictionary(user_folder)


def new_experiment(base_folder, gup, saf, name, md={}):
    """
    Create a new user and set up beamline metadata
    """
    user_folder, user_md = new_user(base_folder, gup, saf, name, md={})
    beamtime_md = setup_beamtime(user_folder, overwrite=True)
    return user_folder, user_md, beamtime_md


def switch_experiment(user_folder):
    setup_beamtime(user_folder, overwrite=True)


def print_beamtime_info():
    try:
        user_md = get_user_md()
    except FileNotFoundError:
        print("No Current Beamtime")
        return

    print("Current Beamtime Info:")
    print(f"Name: {user_md['name']}")
    print(f"Start Date: {user_md['start_date']}")
    print(f"GUP: {user_md['gup']}")
    print(f"SAF: {user_md['saf']}")
