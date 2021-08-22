"""
Tools for setting up user metadata
"""

import bluesky
from os.path import join, dirname, basename, exists
from os import makedirs
import datetime


def interactive_user_directory(base_folder="/tmp"):
    pass


def get_user_directory(base_folder, year, cycle, proposal):
    cycle_folder = f"{year}-{cycle}"
    proposal_folder = f"{proposal}"
    return join(base_folder, cycle_folder, proposal_folder)


def get_user_dictionary(user_directory):
    dictionary_folder = join(user_directory, "user_info")
    user_dict = bluesky.utils.PersistentDict(dictionary_folder)
    return user_dict


def make_user_directory(base_folder, year, cycle, proposal):
    user_directory = get_user_directory(base_folder, year, cycle, proposal)
    makedirs(user_directory, exist_ok=True)
    return user_directory


def make_user_dictionary(user_directory, user_info={}):
    user_dict = get_user_dictionary(user_directory)
    user_dict.update(user_info)
    return user_dict


def new_experiment(base_folder, gup, saf, name, md={}):
    year = datetime.date.today().year
    cycle = 3  # need to automatically set this in some metadata somewhere
    _md = {"name": name,
           "gup": gup,
           "saf": saf}
    _md.update(md)

    user_directory = make_user_directory(base_folder, year, cycle, gup)
    make_user_dictionary(user_directory, user_info=_md)
    return user_directory
