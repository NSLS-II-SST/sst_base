from nbs_gui.views.status import RedisStatusBox
from nbs_gui.settings import SETTINGS
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QDialog,
    QLineEdit,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QWidget,
    QComboBox,
)
from nbs_gui.models import QtRedisJSONDict
from redis_json_dict import RedisJSONDict
import redis
import warnings
from ldap3 import Server, Connection, NTLM
from ldap3.core.exceptions import LDAPInvalidCredentialsResult, LDAPSocketOpenError
from nslsii.sync_experiment.sync_experiment import (
    validate_proposal,
    should_they_be_here,
    get_current_cycle,
    is_commissioning_proposal,
)
from nbs_bl.redisUtils import open_redis_client_from_settings
from datetime import datetime
import os
import yaml


class AuthorizationError(Exception): ...

config_files = [
    os.path.expanduser("~/.config/n2sn_tools.yml"),
    "/etc/n2sn_tools.yml",
]

def authenticate(username, password):

    config = None
    for fn in config_files:
        try:
            with open(fn) as f:
                config = yaml.safe_load(f)
        except IOError:
            pass
        else:
            break

    if config is None:
        raise RuntimeError("Unable to open a config file")

    server = config.get("common", {}).get("server")

    if server is None:
        raise RuntimeError("Server name not found!")

    auth_server = Server(server, use_ssl=True)

    try:
        connection = Connection(
            auth_server,
            user=f"BNL\\{username}",
            password=password,
            authentication=NTLM,
            auto_bind=True,
            raise_exceptions=True,
        )
        print(f"\nAuthenticated as : {connection.extend.standard.who_am_i()}")

    except LDAPInvalidCredentialsResult:
        raise RuntimeError(f"Invalid credentials for user '{username}'.") from None
    except LDAPSocketOpenError:
        print(f"{server} server connection failed...")


def sync_experiment(proposal_number, beamline, saf, username, password, redis_settings):
    """
    Sync experiment data with Redis.

    Parameters
    ----------
    proposal_number : str
        Proposal number to sync
    beamline : str
        Beamline name
    saf : str
        Safety Approval Form number
    username : str
        Username for authentication
    password : str
        Password for authentication
    redis_settings : dict
        Redis connection settings containing host, port, db, and prefix
    """
    redis_client = open_redis_client_from_settings(redis_settings)

    prefix = redis_settings.get("prefix", "")
    md = RedisJSONDict(redis_client=redis_client, prefix=prefix)

    new_data_session = f"pass-{proposal_number}"

    if (new_data_session == md.get("data_session")) and (username == md.get("username")):
        warnings.warn(f"Experiment {new_data_session} was already started by the same user.")
    else:
        proposal_data = validate_proposal(new_data_session, beamline)
        users = proposal_data.pop("users")

        authenticate(username, password)

        if not should_they_be_here(username, new_data_session, beamline):
            raise AuthorizationError(
                f"User '{username}' is not allowed to take data on proposal {new_data_session}"
            )

        pi_name = ""
        for user in users:
            if user.get("is_pi"):
                pi_name = f'{user.get("first_name", "")} {user.get("last_name", "")}'.strip()

        md["data_session"] = new_data_session
        md["username"] = username
        md["start_datetime"] = datetime.now().isoformat()
        md["cycle"] = (
            "commissioning"
            if is_commissioning_proposal(str(proposal_number), beamline)
            else get_current_cycle()
        )
        md["saf"] = saf
        md["proposal"] = {
            "proposal_id": proposal_data.get("proposal_id"),
            "title": proposal_data.get("title"),
            "type": proposal_data.get("type"),
            "pi_name": pi_name,
        }

        print(f"Started experiment {new_data_session}.")


class ProposalSyncExperiment(QDialog):
    def __init__(self, title, redis_settings, beamline):
        super().__init__()
        self.setWindowTitle(title)
        self.redis_settings = redis_settings
        self.beamline = beamline
        vbox = QVBoxLayout()
        button = QPushButton("Submit")
        button.clicked.connect(self.submit_form)

        form = QFormLayout()
        self.username = QLineEdit()
        self.proposal = QLineEdit()
        self.saf = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        # Add beamline selection if multiple beamlines provided
        self.beamline_combo = None
        if isinstance(beamline, (list, tuple)):
            self.beamline_combo = QComboBox()
            for bl in beamline:
                self.beamline_combo.addItem(str(bl))
            form.addRow("Beamline", self.beamline_combo)

        form.addRow("Username", self.username)
        form.addRow("Proposal ID", self.proposal)
        form.addRow("Safety Approval Form", self.saf)
        form.addRow("Password", self.password)
        vbox.addLayout(form)
        vbox.addWidget(button)
        self.setLayout(vbox)

    def submit_form(self):
        username = self.username.text()
        proposal = self.proposal.text()
        saf = self.saf.text()
        password = self.password.text()

        # Get selected beamline if combo box exists
        selected_beamline = self.beamline_combo.currentText() if self.beamline_combo is not None else self.beamline

        print(f"Authenticating {username} and {proposal}")
        sync_experiment(proposal, selected_beamline, saf, username, password, self.redis_settings)


class RedisProposalBox(RedisStatusBox):
    """
    A proposal status box that displays metadata from Redis.
    Uses its own Redis connection for proposal metadata.
    """

    def __init__(self, user_status, parent=None):
        # Get Redis settings from beamline config
        print("RedisProposalBox init")
        redis_settings = SETTINGS.beamline_config.get("settings", {}).get("redis", {}).get("md", {})
        beamline = SETTINGS.beamline_config.get("settings", {}).get("beamline", "sst1")
        endstation = SETTINGS.beamline_config.get("settings", {}).get("endstation", "nexafs")
        print(f"Got redis settings {redis_settings}")
        if not redis_settings:
            print("Warning: No Redis settings found for proposal metadata")
            super().__init__(user_status, "User Metadata", "USER_MD", parent=parent)
            return

        print("Making Redis Client")
        # Create Redis client and dictionary
        redis_client = open_redis_client_from_settings(redis_settings)
        prefix = redis_settings.get("prefix", "")
        print("Making QtRedisJSONDict")
        redis_dict = QtRedisJSONDict(redis_client, prefix, "")

        # Initialize with our own Redis dictionary
        super().__init__(
            user_status,
            "User Metadata",
            "",
            redis_dict=redis_dict,
            parent=parent,
        )

        # Store settings for proposal sync
        self.redis_settings = redis_settings
        self.beamline = beamline
        print("RedisProposalBox init done")

    def get_display_data(self):
        """Format the proposal data for display"""
        user_md = super().get_display_data()
        print(f"RedisProposalBox got {user_md}")

        cleaned_md = {}
        prop_md = user_md.get("proposal", {})
        full_title = prop_md.get("title", "")
        if len(full_title) > 40:
            title = full_title[:40] + "..."
        else:
            title = full_title
        cleaned_md["Title"] = title
        cleaned_md["Proposal ID"] = prop_md.get("proposal_id", "")
        cleaned_md["SAF"] = user_md.get("saf", "")
        cleaned_md["Type"] = prop_md.get("type", "")
        cleaned_md["PI"] = prop_md.get("pi_name", "")
        cleaned_md["Start Date"] = user_md.get("start_datetime", "")

        return cleaned_md


class ProposalStatus(QWidget):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        print("Init ProposalStatus")
        self.proposal_box = RedisProposalBox(self.model.user_status)

        self.button = QPushButton("New Proposal")
        self.button.clicked.connect(self.push_button)
        vbox = QVBoxLayout()
        vbox.addWidget(self.proposal_box)
        vbox.addWidget(self.button)
        self.setLayout(vbox)

    def push_button(self):
        dlg = ProposalSyncExperiment("New Proposal", self.proposal_box.redis_settings, self.proposal_box.beamline)
        dlg.exec()
