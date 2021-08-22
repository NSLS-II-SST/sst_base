"""
Tools for setting up a beamtime
"""
import yaml
import os
from os.path import join, exists
from .users import get_user_dictionary


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


def get_user_md():
    config = get_config()
    user_directory = config['user_directory']
    return get_user_dictionary(user_directory)
