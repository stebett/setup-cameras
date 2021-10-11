import tkinter
from tkinter import *
from tkinter import simpledialog
from PIL import Image, ImageTk
import serial.tools.list_ports
import gi
import pandas as pd
from pandastable import Table, TableModel
import re
from enum import Enum
from gi.repository import GLib, GObject, Gst, Tcam, GstVideo
import cam_management
import protocols

gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "0.1")

app = None
mwin_id = None


class StatusInfo(Frame):
    def __init__(self, parent=None):
        global mwin_id
        self.parent = parent
        Frame.__init__(self)
        self.main = self.master
        self.main.geometry('1920x1080+0+0')
        self.main.title('Table app')
        self.main.rowconfigure(7, weight=1)
        self.main.columnconfigure(6, weight=1)
        f = Frame(self.parent, width=450, height=500)
        f.grid(row=0, column=0, sticky="ew", columnspan=4, rowspan=5)
        self.df = self.get_info_df()
        print(self.df)
        self.table = pt = Table(f, dataframe=self.df,
                                showtoolbar=False, showstatusbar=True, width=1000, height=150)

        #f2 = Frame(self.parent)
        #f2.pack(fill='both', expand=True)
        #self.table2 = pt2 = Table(f2, dataframe=df_contact, showtoolbar=False, showstatusbar=True, width=200)
        pt.show()
        #pt2.show()

        init_button = Button(self.parent, text="Initialization", command=self.init_cam)
        init_button.grid(row=0, column=4, sticky="nsew", columnspan=1)
        rename_button = Button(self.parent, text="Rename", command=self.rename)
        rename_button.grid(row=0, column=5, sticky="nsew", columnspan=1)
        trig_button = Button(self.parent, text="Trigger Mode", command=self.trigger_mode)
        trig_button.grid(row=1, column=4, sticky="nsew", columnspan=2)
        prep_button = Button(self.parent, text="Preparation", command=self.prep_cam)
        prep_button.grid(row=2, column=4, sticky="nsew", columnspan=2)
        run_button = Button(self.parent, text="Capture", command=self.capture)
        run_button.grid(row=3, column=4, sticky="nsew", columnspan=2)
        stop_button = Button(self.parent, text="Stop", command=self.stop)
        stop_button.grid(row=4, column=4, sticky="nsew", columnspan=2)

        if protocols.protocol is not None:
            self.init_cam_windows(n_cam=protocols.protocol.n_camera)
            #self.init_cam_windows(n_cam=4)
        else:
            self.init_cam_windows(n_cam=1)
        window.after(1000, self.update_window)


    def init_cam_windows(self, n_cam):
        global mwin_id
        mwin_id = {}
        if n_cam == 1:
            movie_window = Frame(self.parent, bg='#000000', width=1440, height=900)
            movie_window.grid(row=5, column=0, sticky="nesw", rowspan=1, columnspan=3)
            mwin_id[0] = movie_window.winfo_id()
        elif n_cam == 2:
            movie_window = Frame(self.parent, bg='#000000', width=800, height=700)
            movie_window_2 = Frame(self.parent, bg='#000000', width=800, height=700)
            movie_window.grid(row=5, column=0, sticky="nesw", rowspan=1, columnspan=3)
            movie_window_2.grid(row=5, column=3, sticky="nesw", rowspan=1, columnspan=3)
            mwin_id[0] = movie_window.winfo_id()
            mwin_id[1] = movie_window_2.winfo_id()
        elif n_cam <= 4:
            movie_window = Frame(self.parent, bg='#000000', width=800, height=450)
            movie_window_2 = Frame(self.parent, bg='#000000', width=800, height=450)
            movie_window_3 = Frame(self.parent, bg='#000000', width=800, height=450)
            movie_window_4 = Frame(self.parent, bg='#000000', width=800, height=450)
            movie_window.grid(row=5, column=0, sticky="nesw", rowspan=1, columnspan=3)
            movie_window_2.grid(row=5, column=3, sticky="nesw", rowspan=1, columnspan=3)
            movie_window_3.grid(row=6, column=0, sticky="nesw", rowspan=1, columnspan=3)
            movie_window_4.grid(row=6, column=3, sticky="nesw", rowspan=1, columnspan=3)
            mwin_id[0] = movie_window.winfo_id()
            mwin_id[1] = movie_window_2.winfo_id()
            mwin_id[2] = movie_window_3.winfo_id()
            mwin_id[3] = movie_window_4.winfo_id()



    def get_status(self, cam_index=0):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                if protocols.protocol.cameras[cam_index].callback is not None:
                    if protocols.protocol.cameras[cam_index].callback.capture:
                        return "Capturing:  "+str(protocols.protocol.cameras[cam_index].callback.frame_count) + " frames"
                    else:
                        return "Camera ready"
                else:
                    return "Stream not ready"
            else:
                return "Stream not ready"
        else:
            return "Stream not ready"

    def get_info_df(self):
        df_header = ["Label", "Value"]
        df_buffer = []
        labels = ["Model:", "ID:", "Dimension:", "Format:", "Trigger:", "Status:"]
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                df_header = ["Label"]
                row_1 = [labels[0]]
                row_2 = [labels[1]]
                row_3 = [labels[2]]
                row_4 = [labels[3]]
                row_5 = [labels[4]]
                row_6 = [labels[5]]
                for i in range(0,protocols.protocol.n_camera):
                    df_header.append(protocols.protocol.cameras[i].name)
                    dimensions = str(protocols.protocol.cameras[i].width)+"x"+str(protocols.protocol.cameras[i].height)
                    row_1.append(protocols.protocol.cameras[i].model)
                    row_2.append(protocols.protocol.cameras[i].serialnumber)
                    row_3.append(dimensions)
                    row_4.append(str(protocols.protocol.cameras[i].sinkformat))
                    row_5.append(protocols.protocol.cameras[i].trigger)
                    row_6.append(self.get_status(cam_index=i))
                df_buffer.append(row_1)
                df_buffer.append(row_2)
                df_buffer.append(row_3)
                df_buffer.append(row_4)
                df_buffer.append(row_5)
                df_buffer.append(row_6)

        else:
            df_buffer.append([labels[0], None])
            df_buffer.append([labels[1], None])
            df_buffer.append([labels[2], None])
            df_buffer.append([labels[3], None])
            df_buffer.append([labels[4], None])
            df_buffer.append([labels[5], None])
        return pd.DataFrame(df_buffer, columns=df_header)

    def update_window(self):
        self.table.model.df = self.get_info_df()
        self.table.adjustColumnWidths()
        self.table.redraw()
        window.after(200, self.update_window)

    def init_cam(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                for i in range(0, protocols.protocol.n_camera):
                    protocols.protocol.cameras[i].initialize_cam()

    def prep_cam(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                for i in range(0, protocols.protocol.n_camera):
                    protocols.protocol.cameras[i].prepare()

    def capture(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                for i in range(0, protocols.protocol.n_camera):
                    if not protocols.protocol.cameras[i].callback.capture:
                        protocols.protocol.cameras[i].callback.capture = True
                        protocols.protocol.cameras[i].start_capture()

    def stop(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                for i in range(0, protocols.protocol.n_camera):
                    if protocols.protocol.cameras[i].callback.capture:
                        protocols.protocol.cameras[i].callback.capture = False
                        protocols.protocol.cameras[i].stop_capture()
                        protocols.protocol.cameras[i].callback.close_stream()
                        protocols.protocol.cameras[i].callback = None
                self.init_cam()

    def rename(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                name = protocols.protocol.cameras[0].file_name
                new_name = simpledialog.askstring("Video prefix", "Choose the video prefix", initialvalue=name)
                for i in range(0, protocols.protocol.n_camera):
                    protocols.protocol.cameras[i].file_name = new_name


    def trigger_mode(self):
        if protocols.protocol is not None:
            if protocols.protocol.cameras is not None:
                for i in range(0, protocols.protocol.n_camera):
                    if protocols.protocol.cameras[i].trigger:
                        protocols.protocol.cameras[i].setProperty("Trigger Mode", False)
                        protocols.protocol.cameras[i].trigger = False
                    else:
                        protocols.protocol.cameras[i].setProperty("Trigger Mode", True)
                        protocols.protocol.cameras[i].trigger = True



def createWindow(window):
    menu_bar = Menu(window)
    window.config(menu=menu_bar)

    # Configures Device menu
    data_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Device", menu=data_menu)
    data_menu.add_command(label="Initialize Camera", command=serialCOMWindow)
    #data_menu.add_command(label="Dismiss Camera", command=rotarod.dismiss_rtrd)
    #data_menu.add_separator()

    '''# Configures Protocol menu
    device_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Protocol", menu=device_menu)
    device_menu.add_command(label="Select Protocol", command=rotarod.select_protocol)
    device_menu.add_command(label="Dismiss Protocol", command=rotarod.dismiss_protocol)
    # data_menu.add_separator()

    # Configures FSR menu
    fsr_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="FSR", menu=fsr_menu)
    fsr_menu.add_command(label="0 rpm", command=lambda: rotarod.fsr(0))
    fsr_menu.add_command(label="5 rpm", command=lambda:rotarod.fsr(5))
    fsr_menu.add_command(label="10 rpm", command=lambda: rotarod.fsr(10))
    fsr_menu.add_command(label="15 rpm", command=lambda: rotarod.fsr(15))
    fsr_menu.add_command(label="20 rpm", command=lambda: rotarod.fsr(20))
    fsr_menu.add_command(label="25 rpm", command=lambda: rotarod.fsr(25))
    fsr_menu.add_command(label="Dismiss Protocol", command=rotarod.dismiss_protocol)
    # data_menu.add_separator()'''


def getCams():
    source = Gst.ElementFactory.make("tcamsrc")
    serials = source.get_device_serials()
    list_cams = []
    models = []
    ids = []
    for single_serial in serials:
        (return_value, model, identifier, connection_type) = source.get_device_info(single_serial)
        if return_value:
            models.append(model)
            ids.append(single_serial)
            list_cams.append("Model: {} Serial: {} ".format(model, single_serial))
    return models, ids, list_cams, serials

def serialCOMWindow():
    top = tkinter.Toplevel()
    top.title("Serial COM selection")
    listbox = Listbox(top, selectmode=SINGLE)
    listbox.pack()
    models, ids, list_cams, serials = getCams()

    def select(listbox, window, serials, list_cams, models):
        selection = listbox.get(listbox.curselection())
        index = list_cams.index(selection)
        serial = ids[index]
        model = models[index]
        cam_management.cam = cam_management.Cam(serial, model)
        window.destroy()

    for item in list_cams:
        listbox.insert(END, item)

    cancel_button = Button(top, text="Validate",command=lambda x=listbox: select(x, top, serials, list_cams, models))
    cancel_button.pack()
    cancel_button = Button(top, text="Cancel", command=lambda x=top: x.destroy())
    cancel_button.pack()


window = Tk()
window.title("TISbuntu")
