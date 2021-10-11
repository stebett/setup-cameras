import GUI
import cam_management
import tkinter
from tkinter import *
import protocols
from gi.repository import GLib, GObject, Gst, Tcam, GstVideo
GObject.threads_init()
Gst.init([])

protocols.protocol_init()


GUI.createWindow(GUI.window)
status = tkinter.Label(GUI.window, text="COM Port:")
status2 = tkinter.Label(GUI.window, text="Protocol:")
#status.pack()
#status2.pack()
GUI.app = GUI.StatusInfo(GUI.window)
#window.after(1, StatusInfo)


while True:
    GUI.app.update()
