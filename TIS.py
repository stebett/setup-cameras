import gi
import logging

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

from gi.repository import GObject, Gst, Tcam


class TIS:
    "The Imaging Source Camera"
    def __init__(self, gst_debug_level):
        "Constructor of TIS object"
        self.gst_debug_level = gst_debug_level
        Gst.init(["record.py", f"--gst-debug-level={self.gst_debug_level}"])

    def create_pipeline(self):
        "Creates a Gstreamer pipeline"
        p = "tcambin name=source ! identity name=id"
        # WARNING: Do not change position of identity plugin

        if self.config.general["color"] == "true":
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

    def init_pipeline(self, video_path):
        "Initializes the Gstreamer pipeline"
        self.source = self.pipeline.get_by_name("source")
        self.source.set_property("serial", self.config.general["serial"])

        self.identity = self.pipeline.get_by_name("id")
        self.identity.connect("handoff", self.on_new_buffer)

        if self.config.general["color"] == "true":
            self.bayerfilter = self.pipeline.get_by_name("bayercaps")
            self.bayerfilter.set_property("caps", self.get_caps(bayer=True))

        self.rawfilter = self.pipeline.get_by_name("rawcaps")
        self.rawfilter.set_property("caps", self.get_caps(bayer=False))

        if self.livedisplay:
            self.xsink = self.pipeline.get_by_name("xsink")
            self.xsink.set_property("force-aspect-ratio", True)
        else:
            self.filesink = self.pipeline.get_by_name("fsink")
            self.filesink.set_property("location", video_path)
        
    def stop_pipeline(self):
        "Stops the pipeline"
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.NULL)

    def set_image_callback(self, function, *data):
        "Sets the specific function called when a frame is received"
        self.image_callback = function
        self.image_callback_data = data

    def on_new_buffer(self, *args):
        "Set the generic ffunction called when a frame is received"
        self.image_callback(self, *self.image_callback_data);
        return False

    def get_caps(self, bayer=False):
        "Get pixel and sink format and frame rate"
        logging.debug("Creating caps")
        if bayer:
            fmt = "video/x-bayer, format=rggb,"
        else:
            fmt = "video/x-raw, format=BGRx,"
            

        fmt += f"""width={self.config.general["width"]},
                   height={self.config.general["height"]},
                   framerate={self.config.general["framerate"]}/1"""
                   # Maximum accepted framerate, set it high

        caps = Gst.Caps.new_empty()
        structure = Gst.Structure.new_from_string(fmt)
        caps.append_structure(structure)
        structure.free()
        return caps

    def set_property(self, property_name, value):
        "Set properties, trying to convert the values to the appropriate types"
        try:
            prop = self.source.get_tcam_property(property_name)
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

            result = self.source.set_tcam_property(property_name, GObject.Value(type(value),value))
            if result is False:
                logging.warning("Failed to set {} to value {}. value type is {} prop type is {}, range is {}-{}".format(property_name, value, type(value), prop.type, prop.min, prop.max))
        except Exception as error:
            logging.error("Error set Property {0}: {1}",property_name, format(error))
            raise
