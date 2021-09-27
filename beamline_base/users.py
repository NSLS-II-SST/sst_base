"""
Tools for setting up user metadata
"""

import bluesky
from os.path import join
from os import makedirs
import datetime


def interactive_user_folder(base_folder="/tmp"):
    pass


def get_user_folder(base_folder, year, cycle, proposal):
    cycle_folder = f"{year}-{cycle}"
    proposal_folder = f"{proposal}"
    return join(base_folder, cycle_folder, proposal_folder)


def get_user_dictionary(user_folder):
    dictionary_folder = join(user_folder, "user_info")
    user_dict = bluesky.utils.PersistentDict(dictionary_folder)
    return user_dict


def make_user_folder(base_folder, year, cycle, proposal):
    user_folder = get_user_folder(base_folder, year, cycle, proposal)
    makedirs(user_folder, exist_ok=True)
    return user_folder


def make_user_dictionary(user_folder, user_info={}):
    user_dict = get_user_dictionary(user_folder)
    user_dict.update(user_info)
    return user_dict


def new_user(base_folder, gup, saf, name, md={}):
    """
    Create a new user directory with specified metadata

    Returns
    ---------
    user_folder : str
        Folder where user data will be located
    """
    year = datetime.date.today().year
    start_date = datetime.date.today().isoformat()
    cycle = 3  # need to automatically set this in some metadata somewhere
    user_md = {"name": name,
               "gup": gup,
               "saf": saf,
               "start_date": start_date}
    user_md.update(md)
    user_folder = make_user_folder(base_folder, year, cycle, gup)
    make_user_dictionary(user_folder, user_info=user_md)
    return user_folder, user_md
