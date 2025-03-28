import itertools
from pathlib import PurePath

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
    Signal,
    EpicsSignalRO,
)
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite, resource_factory
from ophyd.areadetector.plugins import ImagePlugin_V33
from ophyd import Component as Cpt
from nslsii.ad33 import SingleTriggerV33, StatsPluginV33
from nbs_bl.beamline import GLOBAL_BEAMLINE as bl
from os.path import join
import os
from datetime import datetime


class ExternalFileReference(Signal):
    """
    A pure software signal where a Device can stash a datum_id.
    For example, it can store timestamps from HDF5 files. It needs
    a `shape` because an HDF5 file can store multiple frames which
    have multiple timestamps.
    """
    def __init__(self, *args, shape, **kwargs):
        super().__init__(*args, **kwargs)
        self.shape = shape

    def describe(self):
        res = super().describe()
        res[self.name].update(
            dict(external="FILESTORE:", dtype="array", shape=self.shape)
        )
        return res


class TIFFPluginWithProposalDirectory(TIFFPlugin, FileStoreTIFFIterativeWrite):
    """Add this as a component to detectors that write TIFFs."""

    # Captures the datum id for hte timestamp recorded in the TIFF file
    time_stamp = Cpt(ExternalFileReference, value="", kind="normal", shape=[])

    def __init__(self, *args, md, camera_name, write_path_template="/nsls2/data/sst/proposals", date_template="%Y/%m/%d/", **kwargs):
        super().__init__(*args, write_path_template="", root=write_path_template, **kwargs)
        self.md = md
        self.camera_name = camera_name
        self.date_template = date_template

        # Setup for timestamping using the detector
        self._ts_datum_factory = None
        self._ts_resource_uid = ""
        self._ts_counter = None

    def stage(self):
        # Start the timestamp counter
        self._ts_counter = itertools.count()
        return super().stage()

    def make_filename(self):
        proposal_path = f"{self.md['cycle']}/{self.md['data_session']}/assets/{self.camera_name}"
        write_path = join(self.write_path_template, proposal_path, self.date_template)
        filename = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
        formatter = datetime.now().strftime
        write_path = formatter(write_path)
        read_path = write_path
        return filename, read_path, write_path

    def _generate_resource(self, resource_kwargs):
        super()._generate_resource(resource_kwargs)
        fn = PurePath(self._fn).relative_to(self.reg_root)

        # Update the shape that describe() will report
        # Multiple images will have multiple timestamps
        self.time_stamp.shape = [self.get_frames_per_point()]

        # Query for the AD_TIFF_TS timestamp
        resource, self._ts_datum_factory = resource_factory(
            spec="AD_TIFF_TS",
            root=str(self.reg_root),
            resource_path=str(fn),
            resource_kwargs=resource_kwargs,
            path_semantics=self.path_semantics,
        )

        self._ts_resource_uid = resource["uid"]
        self._asset_docs_cache.append(("resource", resource))

    def generate_datum(self, key, timestamp, datum_kwargs):
        ret = super().generate_datum(key, timestamp, datum_kwargs)
        datum_kwargs = datum_kwargs or {}
        datum_kwargs.update({"point_number": next(self._ts_counter)})
        datum = self._ts_datum_factory(datum_kwargs)
        datum_id = datum["datum_id"]

        self._asset_docs_cache.append(("datum", datum))

        self.time_stamp.put(datum_id)
        return ret

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
    image = Cpt(ImagePlugin_V33, "image1:")
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


def StandardProsilicaWithTIFFFactory(*args, camera_name="", date_template="%Y/%m/%d/", **kwargs):

    class StandardProsilicaWithTIFF(StandardProsilica):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            date_template=date_template,
        )

    return StandardProsilicaWithTIFF(*args, **kwargs)


def StandardProsilicaWithTIFFV33Factory(*args, camera_name="", date_template="%Y/%m/%d/", **kwargs):

    class StandardProsilicaWithTIFFV33(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            date_template=date_template,
        )

    return StandardProsilicaWithTIFFV33(*args, **kwargs)


def ColorProsilicaWithTIFFV33Factory(*args, camera_name="", date_template="%Y/%m/%d/", **kwargs):

    class ColorProsilicaWithTIFFV33(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            date_template=date_template,
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

class StatsWCentroid(StatsPluginV33):
    centroid_total = Cpt(EpicsSignalRO,'CentroidTotal_RBV',kind='hinted')
    profile_avg_x = Cpt(EpicsSignalRO,'ProfileAverageX_RBV',kind='hinted')
    profile_avg_y = Cpt(EpicsSignalRO,'ProfileAverageY_RBV',kind='hinted')

def StandardProsilicawstatsFactory(*args, camera_name="", date_template="%Y/%m/%d", write_path_template="/nsls2/data/sst/proposals", **kwargs):
    class StandardProsilicawstats(StandardProsilicaV33):
        tiff = Cpt(
            TIFFPluginWithProposalDirectory,
            suffix="TIFF1:",
            md=bl.md,
            camera_name=camera_name,
            write_path_template=write_path_template,
            date_template=date_template,
            read_attrs=["time_stamp"],
        )
        stats1 = Cpt(StatsWCentroid, "Stats1:", kind='hinted')
        stats2 = Cpt(StatsWCentroid, "Stats2:", read_attrs=["total"])
        stats3 = Cpt(StatsWCentroid, "Stats3:", read_attrs=["total"])
        stats4 = Cpt(StatsWCentroid, "Stats4:", read_attrs=["total"])
        stats5 = Cpt(StatsWCentroid, "Stats5:", read_attrs=["total","centroid_total", "profile_avg_x", "profile_avg_y"])

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    return StandardProsilicawstats(*args, **kwargs)