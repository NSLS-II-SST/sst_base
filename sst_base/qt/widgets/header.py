from qtpy.QtWidgets import QWidget, QHBoxLayout, QLabel
from nbs_gui.widgets.header import Header
from .proposal import ProposalStatus

# Use GLOBAL_USER_MD


class NSLSHeader(Header):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the ProposalData widget
        self.proposal_data = ProposalStatus(self.model)

        # Insert the ProposalData widget into the second to last position
        self.layout().insertWidget(self.layout().count() - 1, self.proposal_data)
