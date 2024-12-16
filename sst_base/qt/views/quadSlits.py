from nbs_gui.views.switchable_motors import SwitchableMotorMonitor, SwitchableMotorControl


class QuadSlitsMonitor(SwitchableMotorMonitor):
    """
    Monitor widget for quad slits.
    Shows pseudo motors by default, with option to show real motors.

    Parameters
    ----------
    model : QuadSlitsModel
        The model representing the slits device
    parent_model : object
        Parent model for the widget
    """

    def __init__(self, model, parent_model, *args, **kwargs):
        super().__init__(
            model=model,
            parent_model=parent_model,
            pseudo_title="Slits",
            real_title="Real Motors",
            title=model.label,
            **kwargs
        )


class QuadSlitsControl(SwitchableMotorControl):
    """
    Control widget for quad slits.
    Shows pseudo motors by default, with option to show real motors.

    Parameters
    ----------
    model : QuadSlitsModel
        The model representing the slits device
    parent_model : object
        Parent model for the widget
    """

    def __init__(self, model, parent_model, *args, **kwargs):
        super().__init__(
            model=model,
            parent_model=parent_model,
            pseudo_title="Slits",
            real_title="Real Motors",
            title=model.label,
            **kwargs
        )
