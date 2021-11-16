import gi
import logging

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

from enum import Enum
from gi.repository import GLib, GObject, Gst, Tcam


class SinkFormats(Enum):
    GRAY8 = 0
    GRAY16_LE = 1
    BGRA = 2

    def toString(pf):
        if( pf == SinkFormats.GRAY16_LE ):
            return "GRAY16_LE"

        if( pf == SinkFormats.GRAY8 ):
            return "GRAY8"

        if( pf == SinkFormats.BGRA ):
            return "BGRx"

        return "BGRx"

    def fromString(pf):
        if( pf == "GRAY16_LE"):
            return SinkFormats.GRAY16_LE
        if( pf == "GRAY8"):
            return SinkFormats.GRAY8
      
        return SinkFormats.BGRA


class TIS:
    "The Imaging Source Camera"
    def __init__(self):
        "Constructor of TIS object"
        self.ImageCallback = None
        self.pipeline = None
        self.config = None

        self.gst_debug_level = 1
        Gst.init(["record.py", f"--gst-debug-level={self.gst_debug_level}"])

    def open_device(self):
        # I will fucking remove you 
        ''' Inialize a device, e.g. camera.
        :param serial: Serial number of the camera to be used.
        :param width: Width of the wanted video format
        :param height: Height of the wanted video format
        :param framerate: Numerator of the frame rate. /1 is added automatically
        '''
        self.serialnumber = self.config.general['serial']
        self.height = self.config.general['height']
        self.width = self.config.general['width']
        self.framerate = self.config.general['framerate']
        self.sinkformat = SinkFormats.toString(self.config.general['pixelformat'])

    def createPipeline(self, video_path=None):
        "Creates a Gstreamer pipeline"

        if self.livedisplay:
            p = 'tcambin name=source ! capsfilter name=caps'
            p += " ! tee name=t"
            p += " t. ! videoscale method=0 add-borders=false \
                      ! video/x-raw,width=640,height=360 \
                      ! ximagesink name=xsink"
        elif video_path is not None:
            p = "tcambin name=source"
            # WARNING: Do not change position of identity plugin
            p += " ! identity name=id"
            p += " ! capsfilter name=bayercaps"
            p += " ! bayer2rgb ! videoconvert"
            p += " ! capsfilter name=rawcaps"
            p += " ! videoconvert" 
            p += " ! avimux"
            p += " ! filesink name=fsink"

        logging.debug(f"Gst pipeline: {p}")
        self.pipeline = Gst.parse_launch(p)


        if self.livedisplay:
            self.xsink = self.pipeline.get_by_name("xsink")
            self.xsink.set_property("force-aspect-ratio", True)

        elif video_path is not None:
            bayercaps = self.getcaps(bayer=True)
            self.bayerfilter = self.pipeline.get_by_name("bayercaps")
            self.bayerfilter.set_property("caps", bayercaps)

            rawcaps = self.getcaps(bayer=False)
            self.rawfilter = self.pipeline.get_by_name("rawcaps")
            self.rawfilter.set_property("caps", rawcaps)

            try:
                self.identity = self.pipeline.get_by_name("id")
                self.identity.connect("handoff", self.on_new_buffer)
            except AttributeError:
                logging.warning("No identity detected")

            try:
                self.filesink = self.pipeline.get_by_name("fsink")
                self.filesink.set_property("location", video_path)
            except AttributeError:
                logging.warning("No filesink detected")


        
        self.source = self.pipeline.get_by_name("source")
        self.source.set_property("serial", self.serialnumber)


    def stopPipeline(self):
        "Stops the pipeline"
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.NULL)

    def Set_Image_Callback(self, function, *data):
        "Sets the specific function called when a frame is received"
        self.ImageCallback = function
        self.ImageCallbackData = data

    def on_new_buffer(self, identity, buff):
        "Set the generic ffunction called when a frame is received"
        self.ImageCallback(self, identity, buff, *self.ImageCallbackData);
        return False

    def getcaps(self, bayer=False):
        "Get pixel and sink format and frame rate"
        logging.debug("Creating caps")
        fmt = ""
        if bayer:
            fmt += "video/x-bayer, format=rggb,"
        else:
            fmt += "video/x-raw, format=BGRx,"
            

        fmt += f"""width={self.config.general["width"]},
                   height={self.config.general["height"]},
                   framerate={self.config.general["framerate"]}"""
                   # Maximum accepted framerate, set it high


        caps = Gst.Caps.new_empty()
        structure = Gst.Structure.new_from_string(fmt)
        caps.append_structure(structure)
        structure.free()
        return caps

    def setProperty(self, propertyName, value):
        "Set properties, trying to convert the values to the appropriate types"
        try:
            prop = self.source.get_tcam_property(propertyName)
            if prop.type == 'double':
                value = float(value)
            if prop.type == 'integer':
                value = int(value)
            if prop.type == 'boolean':
                if (value == "True") or (value == "true") or (value is True):
                    value = True 
                elif (value == "False") or (value == "false") or (value is False):
                    value = False 
                else:
                    raise

            result = self.source.set_tcam_property(propertyName, GObject.Value(type(value),value))
            if result is False:
                logging.warning("Failed to set {} to value {}. value type is {} prop type is {}, range is {}-{}".format(
                    propertyName, value,
                    type(value),
                    prop.type,
                    prop.min,
                    prop.max) 
                    )
        except Exception as error:
            logging.error("Error set Property {0}: {1}",propertyName, format(error))
            raise
