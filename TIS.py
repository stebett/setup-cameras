import gi
import logging

gi.require_version("Gst", "1.0")

from gi.repository import GObject, Gst, Tcam


class TIS:
    "The Imaging Source Camera"
    def __init__(self):
        "Constructor of TIS object"
        self.ImageCallback = None
        self.pipeline = None
        self.config = None

        self.gst_debug_level = 1
        Gst.init(["record.py", f"--gst-debug-level={self.gst_debug_level}"])

    def createPipeline(self):
        "Creates a Gstreamer pipeline"
        p = "tcambin name=source ! identity name=id"
        # WARNING: Do not change position of identity plugin

        if self.config.general["color"]:
            p += " ! capsfilter name=bayercaps"
            p += " ! bayer2rgb ! videoconvert"

        p += " ! capsfilter name=rawcaps ! videoconvert"

        if self.livedisplay:
            p += " ! videoscale method=0 add-borders=false"
            p += " ! video/x-raw,width=640,height=360"
            p += " ! ximagesink name=xsink"
        else:
            p += " ! avimux"
            p += " ! filesink name=fsink"

        logging.debug(f"Gst pipeline: {p}")
        self.pipeline = Gst.parse_launch(p)

    def initPipeline(self, video_path):
        "Initializes the Gstreamer pipeline"
        self.source = self.pipeline.get_by_name("source")
        self.source.set_property("serial", self.config.general["serial"])

        self.identity = self.pipeline.get_by_name("id")
        self.identity.connect("handoff", self.on_new_buffer)

        if self.config.general["color"]:
            self.bayerfilter = self.pipeline.get_by_name("bayercaps")
            self.bayerfilter.set_property("caps", self.getcaps(bayer=True))

        self.rawfilter = self.pipeline.get_by_name("rawcaps")
        self.rawfilter.set_property("caps", self.getcaps(bayer=False))

        if self.livedisplay:
            self.xsink = self.pipeline.get_by_name("xsink")
            self.xsink.set_property("force-aspect-ratio", True)
        else:
            self.filesink = self.pipeline.get_by_name("fsink")
            self.filesink.set_property("location", video_path)
        


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
        # TODO rm
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
