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
    'The Imaging Source Camera'

    def __init__(self):
        ''' Constructor
        :return: none
        '''
        Gst.init([])
        self.serialnumber = ""
        self.height = 0
        self.width = 0
        self.framerate="15/1"
        self.sinkformat = SinkFormats.BGRA
        self.ImageCallback = None
        self.pipeline = None
        self.configs = None

    def open_device(self, configs):
        ''' Inialize a device, e.g. camera.
        :param serial: Serial number of the camera to be used.
        :param width: Width of the wanted video format
        :param height: Height of the wanted video format
        :param framerate: Numerator of the frame rate. /1 is added automatically
        :param color: True = 8 bit color, False = 8 bit mono. ToDo: Y16
        :return: none
        '''
        self.serialnumber = configs['serial']
        self.height = configs['height']
        self.width = configs['width']
        self.framerate = configs['framerate']
        self.sinkformat = SinkFormats.BGRA

    def createPipeline(self, video_path=None):
        p = 'tcambin name=source ! capsfilter name=caps'

        if self.livedisplay:
            logging.info("Testing")
            p += " ! tee name=t"
            p += " t. ! videoscale method=0 add-borders=false \
                      ! video/x-raw,width=640,height=360 \
                      ! ximagesink name=xsink"
        elif video_path is not None:
            logging.info("Not testing")
            p += " ! tee name=t"
            p += " t. ! queue ! appsink name=sink"
            p += " t. ! queue name=queue ! videoconvert ! avimux ! filesink name=fsink"

        logging.debug(f"Gst pipeline: {p}")
        self.pipeline = Gst.parse_launch(p)


        if self.livedisplay:
            self.xsink = self.pipeline.get_by_name("xsink")
            self.xsink.set_property("force-aspect-ratio", True)
            # self.xsink.set_property("pixel-aspect-ratio", "10/5")

        elif video_path is not None: 
            self.filesink = self.pipeline.get_by_name("fsink")
            self.filesink.set_property("location", video_path)

            self.gstqueue = self.pipeline.get_by_name("queue")
            self.gstqueue.set_property("max-size-buffers", 0)
            self.gstqueue.set_property("max-size-time", 0)
            self.gstqueue.set_property("max-size-bytes", int(1.5*10e8))

            self.appsink = self.pipeline.get_by_name("sink")
            self.appsink.set_property("max-buffers", 5)
            self.appsink.set_property("drop",1)
            self.appsink.set_property("emit-signals",1)
            self.appsink.connect('new-sample', self.on_new_buffer)
        
        self.source = self.pipeline.get_by_name("source")
        self.source.set_property("serial", self.serialnumber)

    def stopPipeline(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)
        self.pipeline.set_state(Gst.State.NULL)

    def Set_Image_Callback(self, function, *data):
        self.ImageCallback = function
        self.ImageCallbackData = data

    def on_new_buffer(self, appsink):
        self.ImageCallback(self, *self.ImageCallbackData);
        return False

    def setcaps(self, configs):
        """ 
        Set pixel and sink format and frame rate
        """
        caps = Gst.Caps.new_empty()
        format = 'video/x-raw,format=%s,width=%d,height=%d,framerate=%s' % ( SinkFormats.toString(self.sinkformat),configs["width"],configs["height"],configs["framerate"])
        structure = Gst.Structure.new_from_string(format)

        caps.append_structure(structure)

        structure.free()
        capsfilter = self.pipeline.get_by_name("caps")
        capsfilter.set_property("caps", caps)

    def setProperty(self, PropertyName, value):
        try:
            logging.debug(f"Setting {PropertyName} to value {value}")
            property = self.source.get_tcam_property(PropertyName)
            if property.type == 'double':
                value = float(value)
            if property.type == 'integer':
                value = int(value)
            if property.type == 'boolean':
                value = True if value == "True" else False

            result = self.source.set_tcam_property(PropertyName,GObject.Value(type(value),value))
            if result is False:
                logging.warning("Failed to set {} to value {}. value type is {} Property type is {}, range is {}-{}".format(
                    PropertyName, value,
                    type(value),
                    property.type,
                    property.min,
                    property.max) 
                    )
        except Exception as error:
            logging.error("Error set Property {0}: {1}",PropertyName, format(error))
            raise
