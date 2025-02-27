from ophyd import (
    ProsilicaDetector,
    SingleTrigger,
    TIFFPlugin,
    ImagePlugin,
    StatsPlugin,
    EpicsSignal,
    ROIPlugin,
    TransformPlugin,
    ProcessPlugin,
    OverlayPlugin,
    ProsilicaDetectorCam,
    ColorConvPlugin,
)
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd import Component as Cpt
from nslsii.ad33 import SingleTriggerV33, StatsPluginV33
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from os.path import join


class TIFFPluginWithProposalDirectory(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""

    def __init__(self, *args, md, camera_name, write_template="%Y/%m/%d/", **kwargs):
        write_path_template = f"/nsls2/data/sst/proposals/{md['cycle']}/{md['data_session']}/assets/{camera_name}"
        write_path_template = join(write_path_template, write_template)
        super().__init__(*args, write_path_template=write_path_template, **kwargs)
        self.md = md
        self.camera_name = camera_name
        self.write_template = write_template

    @property
    def read_path_template(self):
        self._read_path_template = (
            f"/nsls2/data/sst/proposals/{self.md['cycle']}/{self.md['data_session']}/assets/{self.camera_name}"
        )
        self._read_path_template = join(self._read_path_template, self.write_template)
        return super().read_path_template

    @property
    def write_path_template(self):
        self._write_path_template = (
            f"/nsls2/data/sst/proposals/{self.md['cycle']}/{self.md['data_session']}/assets/{self.camera_name}"
        )
        self._write_path_template = join(self._write_path_template, self.write_template)

        return super().write_path_template

    @property
    def reg_root(self):
        self._root = (
            f"/nsls2/data/sst/proposals/{self.md['cycle']}/{self.md['data_session']}/assets/{self.camera_name}/"
        )
        return super().reg_root


class TIFFPluginEnsuredOff(TIFFPlugin):
    """Add this as a component to detectors that do not write TIFFs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([("auto_save", "No")])


class ProsilicaDetectorCamV33(ProsilicaDetectorCam):
    """This is used to update the Standard Prosilica to AD33. It adds the
    process
    """

    wait_for_plugins = Cpt(EpicsSignal, "WaitForPlugins", string=True, kind="hinted")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs["wait_for_plugins"] = "Yes"

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()


class StandardProsilica(SingleTrigger, ProsilicaDetector):
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPlugin, "Stats1:")
    stats2 = Cpt(StatsPlugin, "Stats2:")
    stats3 = Cpt(StatsPlugin, "Stats3:")
    stats4 = Cpt(StatsPlugin, "Stats4:")
    stats5 = Cpt(StatsPlugin, "Stats5:")
    trans1 = Cpt(TransformPlugin, "Trans1:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")
    over1 = Cpt(OverlayPlugin, "Over1:")
    cc1 = Cpt(ColorConvPlugin, "CC1:")

    # This class does not save TIFFs. We make it aware of the TIFF plugin
    # only so that it can ensure that the plugin is not auto-saving.
    tiff = Cpt(TIFFPluginEnsuredOff, suffix="TIFF1:")

    @property
    def hints(self):
        return {"fields": [self.stats1.total.name]}


class StandardProsilicaV33(SingleTriggerV33, ProsilicaDetector):
    cam = Cpt(ProsilicaDetectorCamV33, "cam1:")
    image = Cpt(ImagePlugin, "image1:")
    stats1 = Cpt(StatsPluginV33, "Stats1:")
    stats2 = Cpt(StatsPluginV33, "Stats2:")
    stats3 = Cpt(StatsPluginV33, "Stats3:")
    stats4 = Cpt(StatsPluginV33, "Stats4:")
    stats5 = Cpt(StatsPluginV33, "Stats5:")
    trans1 = Cpt(TransformPlugin, "Trans1:")
    roi1 = Cpt(ROIPlugin, "ROI1:")
    roi2 = Cpt(ROIPlugin, "ROI2:")
    roi3 = Cpt(ROIPlugin, "ROI3:")
    roi4 = Cpt(ROIPlugin, "ROI4:")
    proc1 = Cpt(ProcessPlugin, "Proc1:")
    over1 = Cpt(OverlayPlugin, "Over1:")

    # This class does not save TIFFs. We make it aware of the TIFF plugin
    # only so that it can ensure that the plugin is not auto-saving.
    tiff = Cpt(TIFFPluginEnsuredOff, suffix="TIFF1:")

    @property
    def hints(self):
        return {"fields": [self.stats1.total.name]}


def StandardProsilicaWithTIFFFactory(*args, camera_name="", write_template="%Y/%m/%d/", **kwargs):

    class StandardProsilicaWithTIFF(StandardProsilica):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            write_template=write_template,
        )

    return StandardProsilicaWithTIFF(*args, **kwargs)


def StandardProsilicaWithTIFFV33Factory(*args, camera_name="", write_template="%Y/%m/%d/", **kwargs):

    class StandardProsilicaWithTIFFV33(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            write_template=write_template,
        )

    return StandardProsilicaWithTIFFV33(*args, **kwargs)


def ColorProsilicaWithTIFFV33Factory(*args, camera_name="", write_template="%Y/%m/%d/", **kwargs):

    class ColorProsilicaWithTIFFV33(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            write_template=write_template,
        )

        def describe(self):
            res = super().describe()
            # Patch: device has a color dimension that is not reported correctly
            # by ophyd.
            res["Sample Imager Detector Area Camera_image"]["shape"] = (
                *res["Sample Imager Detector Area Camera_image"]["shape"],
                3,
            )
            res["Sample Imager Detector Area Camera_image"]["dtype_str"] = "|u1"
            return res

    return ColorProsilicaWithTIFFV33(*args, **kwargs)
