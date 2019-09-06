import logging
import os
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk
from matplotlib import cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import datastring
from misc_tools import combination, validate, float2StringVar
from plot_patterns import plot_chessboard, plot_asymmetric_grid, plot_symmetric_grid, plot_custom
from quaternions import averageMatrix
from time_tools import chronometer

logging.basicConfig(level=logging.ERROR)

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240


class MRTCalibrationToolbox:
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.screen_width = master.winfo_screenwidth()  # For two screens, divide by corresponding factor 2
        self.screen_height = master.winfo_screenheight()
        master.title("MRT Camera Calibration Toolbox")
        self.initialize_GUI_variables()
        self.initializeVariables()
        self.reset_camera_parameters()
        self.reset_error()
        self.initUI()
        self.traces_GUI()
        self.updateCameraParametersGUI()

    def center(self):
        '''
        Function to center popups and disable the main windows
        '''

        self.master.update_idletasks()
        width = self.popup.winfo_reqwidth()
        height = self.popup.winfo_reqheight()
        x = self.master.winfo_rootx() + (self.master.winfo_width() // 2) - (width // 2)
        y = self.master.winfo_rooty() + (self.master.winfo_height() // 2) - (height // 2)
        self.popup.geometry("+%d+%d" % (x, y))
        if self.master.winfo_viewable():
            self.popup.transient(self.master)
        self.popup.deiconify()  # become visible now
        self.popup.wait_visibility()
        self.popup.grab_set()  # interact only with popup

    def initialize_GUI_variables(self):
        '''
        Function to initialize GUI related variables at the beginning
        '''
        # buttons
        self.bot = []
        # total images
        self.n_total = tk.IntVar()
        # pattern feature variables
        self.pattern_type = tk.StringVar()
        self.pattern_load = tk.StringVar()
        self.pattern_width = tk.IntVar()
        self.pattern_height = tk.IntVar()
        self.feature_distance = tk.DoubleVar()
        self.mode_stereo = tk.BooleanVar()
        # image features variables
        self.image_width = tk.IntVar()
        self.image_height = tk.IntVar()
        # trace for update picture
        self.index = tk.IntVar()
        # method for calibration variable
        self.how_to_calibrate = tk.StringVar()
        self.how_to_calibrate.set("Clustering calculation")
        # loading parameters from file variables
        self.load_files = [None, None, None]
        self.l_load_files = [None, None, None]
        # calculation from clusters variables
        self.c_r = tk.IntVar()
        self.c_k = tk.IntVar()
        # bar chart variables
        self.f = [[], []]
        self.ax = [[], []]
        self.bar = [[], []]
        # flags for camera calibrations
        self.p_intrinsics_guess = tk.BooleanVar()
        self.p_fix_point = tk.BooleanVar()
        self.p_fix_ratio = tk.BooleanVar()
        self.p_zero_tangent_distance = tk.BooleanVar()
        # Variables for intrinsic and extrinsic parameters visualization
        # camera parameters
        self.fx = [tk.StringVar(), tk.StringVar()]
        self.fy = [tk.StringVar(), tk.StringVar()]
        self.cx = [tk.StringVar(), tk.StringVar()]
        self.cy = [tk.StringVar(), tk.StringVar()]
        # distortion parameters
        self.k1 = [tk.StringVar(), tk.StringVar()]
        self.k2 = [tk.StringVar(), tk.StringVar()]
        self.k3 = [tk.StringVar(), tk.StringVar()]
        self.k4 = [tk.StringVar(), tk.StringVar()]
        self.k5 = [tk.StringVar(), tk.StringVar()]
        # Rotation and translation matrix
        self.R_tk = [[tk.StringVar(), tk.StringVar(), tk.StringVar()], [tk.StringVar(), tk.StringVar(), tk.StringVar()],
                     [tk.StringVar(), tk.StringVar(), tk.StringVar()]]
        self.T_tk = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        # rms error
        self.rms_tk = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        # standard deviations
        # camera parameters
        self.sd_fx = [tk.StringVar(), tk.StringVar()]
        self.sd_fy = [tk.StringVar(), tk.StringVar()]
        self.sd_cx = [tk.StringVar(), tk.StringVar()]
        self.sd_cy = [tk.StringVar(), tk.StringVar()]
        # distortion parameters
        self.sd_k1 = [tk.StringVar(), tk.StringVar()]
        self.sd_k2 = [tk.StringVar(), tk.StringVar()]
        self.sd_k3 = [tk.StringVar(), tk.StringVar()]
        self.sd_k4 = [tk.StringVar(), tk.StringVar()]
        self.sd_k5 = [tk.StringVar(), tk.StringVar()]
        # variable for data browsing
        self.listbox = None
        # progress bar layout
        # Progressbar https://stackoverflow.com/questions/47896881/progressbar-with-percentage-label
        self.style_pg = ttk.Style(self.master)
        # add label in the layout
        layout = [('Horizontal.Progressbar.trough', {'children': [('Horizontal.Progressbar.pbar',
                                                                   {'side': 'left', 'sticky': 'ns'})],
                                                     'sticky': 'nswe'}),
                  ('Horizontal.Progressbar.label', {'sticky': ''})]
        self.style_pg.layout('text.Horizontal.TProgressbar', layout)

    def traces_GUI(self):
        '''
        Function to trace all the changes in tkinter variables
        '''
        # link changes in number of poses for updating function
        self.n_total.trace('w', self.update_added_deleted)
        # link changes in width and height to plotting function
        self.pattern_type.trace_id = self.pattern_type.trace('w', self.pattern_default)
        self.image_width.trace_id = self.image_width.trace('w', self.check_errors_and_plot)
        self.image_height.trace_id = self.image_height.trace('w', self.check_errors_and_plot)
        self.pattern_width.trace_id = self.pattern_width.trace('w', self.check_errors_and_plot)
        self.pattern_height.trace_id = self.pattern_height.trace('w', self.check_errors_and_plot)
        self.feature_distance.trace_id = self.feature_distance.trace('w', self.check_errors_and_plot)
        # link changes in selected pose to update GUI
        self.index.trace('w', self.updatePicture)
        # camera parameters
        self.fx[0].trace('w', self.updatePicture)

    def reset_error(self):
        '''
        Function to reset error related variables
        '''
        # array of rms error for each pose
        self.r_error = [None, None]
        # array of pixel distance error for each feature
        self.r_error_p = [[], []]
        # projections
        self.projected = [[], []]
        self.projected_stereo = [[], []]

    def reset_camera_parameters(self):
        '''
        Function to reset all intrinsics and extrinsics parameters
        '''
        # camera matrix
        # array of 2 of 3*3 for camera parameters (mean and standard deviation)
        self.camera_matrix = [np.zeros((3, 3), dtype=np.float32), np.zeros((3, 3), dtype=np.float32)]
        self.dev_camera_matrix = [np.zeros((3, 3), dtype=np.float32), np.zeros((3, 3), dtype=np.float32)]
        # array of 2 of 5*1 for distortion parameters (mean and standard deviation)
        self.dist_coefs = [np.zeros((5, 1), dtype=np.float32), np.zeros((5, 1), dtype=np.float32)]
        self.dev_dist_coefs = [np.zeros((5, 1), dtype=np.float32), np.zeros((5, 1), dtype=np.float32)]
        # rotational and translation matrix
        self.R_stereo = np.zeros((3, 3), dtype=np.float32)
        self.T_stereo = np.zeros((3, 1), dtype=np.float32)
        # rms error
        self.rms = [0, 0, 0]

    def initializeVariables(self):
        '''
        Function to define variables that has to be reinitialized each time a session is deleted
        '''
        # total number of cameras
        self.n_cameras = 0
        # size for each camera, used for internal functions
        self.size = [None, None]
        # 3d points in real world space
        self.objpoints = [[], []]
        # 2d points in image plane
        self.imgpoints = [[], []]
        # 3d points for pattern type
        self.object_pattern = None

        # bool to indicate if any image was deleted after calibration
        self.update = False

        # GUI related variables
        self.imscale = 1.0
        self.delta = 0.75
        self.scale = 1.0
        self.x = None
        self.y = None
        self.zoomhandler = 0

        # popup related variables
        self.popup = None
        self.l_error = None  # label for input errors
        self.label_msg = [None, None, None, None, None]
        self.label_filenames = [None, None, None]
        self.lb_time = None  # label for time
        self.c_pattern = None  # canvas

        # process variables
        self.heat_map = [None, None]
        self.img = [[[], [], [], [], [], []], [[], [], [], [], [], []]]
        self.index.set(-1)
        self.index_corner = 0
        self.paths = [[], []]
        self.img_original = [[], []]
        self.detected_features = [[], []]
        # total number of images (couple of images for the stereo mode)
        self.n_total.set(0)

        self.p_width = None
        self.p_height = None
        self.p_length = None
        self.m_stereo = True

        # bar chart variables
        self.dr = [[], []]

        # variable for importing files
        self.ftypes = None
        self.valid_files = None

        # array for all calibrations
        self.fx_array = []
        self.fy_array = []
        self.cx_array = []
        self.cy_array = []
        self.k1_array = []
        self.k2_array = []
        self.k3_array = []
        self.k4_array = []
        self.k5_array = []
        self.R_array = []
        self.T_array = []
        self.RMS_array = []
        self.samples = None

    def initUI(self, *args, **kwargs):
        '''
        Function to create toolbar, data browser, panel of tabs of images, error charts and calculated parameters visualization
        '''
        ## frames definition and positioning ##
        self.frm = []
        for i in range(7):
            self.frm.append(tk.Frame(self.master))
            self.frm[-1].rowconfigure(0, weight=1)
            self.frm[-1].columnconfigure(0, weight=1)
            # self.frm[-1].propagate(0)
        self.frm[0].grid(row=0, column=0, columnspan=6, sticky=tk.W)  # frame for toolbar
        self.frm[1].grid(row=1, column=0, rowspan=3, sticky='nswe')  # frame for Listbox
        self.frm[1].configure(width=self.screen_width * 0.1)  # set frame width 10% of screen width

        self.frm[2].grid(row=1, column=1, sticky=tk.N + tk.S)  # frame for pictures first camera
        self.frm[2].configure(width=self.screen_width * 0.28 * 0.9,
                              height=(self.screen_height - 25) / 2)  # set frame width 28% of screen width

        self.frm[3].grid(row=1, column=2, sticky=tk.N + tk.S)  # frame for intrinsics first camera
        self.frm[3].configure(width=self.screen_width * 0.15 * 0.9,
                              height=(self.screen_height - 25) / 2)  # set frame width 15% of screen width

        self.frm[4].grid(row=1, column=3, sticky=tk.N + tk.S)  # frame for extrinsics
        self.frm[4].configure(width=self.screen_width * 0.14 * 0.9,
                              height=(self.screen_height - 25) / 2)  # set frame width 14% of screen width

        self.frm[5].grid(row=1, column=4, sticky=tk.N + tk.S)  # frame for intrinsics second camera
        self.frm[5].configure(width=self.screen_width * 0.15 * 0.9,
                              height=(self.screen_height - 25) / 2)  # set frame width 15% of screen width

        self.frm[6].grid(row=1, column=5, sticky=tk.N + tk.S)  # frame for pictures second camera
        self.frm[6].configure(width=self.screen_width * 0.28 * 0.9,
                              height=(self.screen_height - 25) / 2)  # set frame width 28% of screen width

        sub_frame_g = tk.Frame(self.master)
        sub_frame_g.grid(row=2, column=1, columnspan=5, sticky=tk.W + tk.E)
        for i in range(4):
            self.frm.append(tk.Frame(sub_frame_g))
            self.frm[-1].rowconfigure(0, weight=1)
            self.frm[-1].columnconfigure(0, weight=1)
            # self.frm[-1].propagate(0)
        self.frm[7].grid(row=0, column=0)  # frame for first grafic first camera
        self.frm[8].grid(row=0, column=1)  # frame for second grafic first camera
        self.frm[9].grid(row=1, column=0)  # frame for first grafic second camera
        self.frm[10].grid(row=1, column=1)  # frame for second grafic second camera

        ## loading icons for toolbar ##
        # defining icons path
        path_open = os.getcwd() + '/icons/open.png'
        path_zoommore = os.getcwd() + '/icons/zoommore.png'
        path_zoomless = os.getcwd() + '/icons/zoomless.png'
        path_play = os.getcwd() + '/icons/play.png'
        path_folder = os.getcwd() + '/icons/folder.png'
        path_delete = os.getcwd() + '/icons/delete.png'
        path_plus = os.getcwd() + '/icons/plus.png'
        path_export = os.getcwd() + '/icons/export.png'
        path_settings = os.getcwd() + '/icons/settings.png'
        path_export2 = os.getcwd() + '/icons/exportall.png'
        # loading tk object for the icons
        self.icono_open = tk.PhotoImage(file=path_open)
        self.icono_zoommore = tk.PhotoImage(file=path_zoommore)
        self.icono_zoomless = tk.PhotoImage(file=path_zoomless)
        self.icono_play = tk.PhotoImage(file=path_play)
        self.icono_folder = tk.PhotoImage(file=path_folder)
        self.icono_delete = tk.PhotoImage(file=path_delete)
        self.icono_plus = tk.PhotoImage(file=path_plus)
        self.icono_export = tk.PhotoImage(file=path_export)
        self.icono_settings = tk.PhotoImage(file=path_settings)
        self.icono_export2 = tk.PhotoImage(file=path_export2)
        ## toolbar configuration ##
        # icons assigment and trace of functions to the buttons
        self.bot.append(tk.Button(self.frm[0], image=self.icono_plus, command=self.add_session_popup))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_open, command=lambda: self.add_file('p')))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_folder, command=lambda: self.add_file('f')))
        self.bot.append(tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_zoommore,
                                  command=lambda: self.toggle_zoom_buttons(3, 4)))
        self.bot.append(tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_zoomless,
                                  command=lambda: self.toggle_zoom_buttons(4, 3)))
        self.bot.append(tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_play, command=self.play_popup))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_delete, command=self.popupmsg_deleting))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_settings, command=self.popup_configuration))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_export,
                      command=self.exportCalibrationParameters))
        self.bot.append(
            tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_export2,
                      command=self.exportCalibrationParametersIteration))

        # buttons positioning
        for i in range(len(self.bot)):
            self.bot[i].grid(row=0, column=i, sticky=tk.W)

        ## scrollbar and listbox initialization ##
        tk.Label(self.frm[1], text="Data Browser").pack()
        sb = tk.Scrollbar(self.frm[1], orient="vertical")
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(self.frm[1], yscrollcommand=sb.set)
        self.listbox.pack(expand=True, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.updateSelection)
        sb.config(command=self.listbox.yview)
        ## variables initialization for tabs of images and camera parameters visualization ##
        # tab control for initialization and positioning
        self.tabControl = []
        # list of panels for visualization -
        # - list of panels shape is [camera][images] - -
        # - - where posibles values are for camera: 0 or 1, and for images 0,1,2,3 (original, feature,cloud map, intrinisc, extrinsic)
        self.list_panel = []
        self.list_image_on_panel = []
        self.c_labels = [[], [], []]
        tab_names = ['Original', 'Features', 'Cloud Map', 'Intrinsic', 'Extrinsic']
        # panel for pictures definition
        for j in range(2):
            sub_frame = self.frm[2 + 4 * j]
            self.list_panel.append([])
            self.list_image_on_panel.append([])
            self.tabControl.append(ttk.Notebook(sub_frame))
            # initialization and positioning of labels for visualization of intrinsics
            sub_frame = self.frm[3 + 2 * j]
            for p in range(15):
                for q in range(3):
                    if p == 0 or p == 6 or p == 13:
                        if q == 0:
                            self.c_labels[j].append(tk.Label(sub_frame, font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1, columnspan=3, sticky=tk.N + tk.S)
                    elif p == 14:
                        if q == 0:
                            self.c_labels[j].append(tk.Label(sub_frame, font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1 + q, sticky=tk.N + tk.S)
                        elif q == 1:
                            self.c_labels[j].append(tk.Label(sub_frame, font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1 + q, columnspan=3, sticky=tk.N + tk.S)
                    else:
                        self.c_labels[j].append(tk.Label(sub_frame, font=('', 8)))
                        self.c_labels[j][-1].grid(row=p + 0, column=1 + q, sticky=tk.N + tk.S)
            # positioning of images in panels and trace of click event for zoom
            for i in range(5):
                tab = ttk.Frame(self.tabControl[j])
                self.tabControl[j].add(tab, text=tab_names[i])
                self.list_panel[j].append(tk.Canvas(tab, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT))
                self.list_panel[j][i].grid(row=0, column=0, sticky=tk.E + tk.W + tk.N)
                self.list_panel[j][i].bind('<Button-1>', self.click_to_zoom)
                self.list_panel[j][i].bind('<Button-4>', lambda e: self.scroll_to_zoom('m', e))
                self.list_panel[j][i].bind('<Button-5>', lambda e: self.scroll_to_zoom('l', e))
                self.list_image_on_panel[j].append(
                    self.list_panel[j][i].create_image(0, 0, anchor=tk.N + tk.W, image=None))
            self.tabControl[j].grid(row=0, column=0, rowspan=13, sticky=tk.N + tk.S)
        # definition of text of labels
        for j in range(2):
            self.c_labels[j][0].config(text='CAMERA MATRIX')
            self.c_labels[j][2].config(text=u'\u03bc')
            self.c_labels[j][3].config(text='SD')
            self.c_labels[j][4].config(text='fx')
            self.c_labels[j][5].config(textvariable=self.fx[j])
            self.c_labels[j][6].config(textvariable=self.sd_fx[j], fg='green')
            self.c_labels[j][7].config(text='fy')
            self.c_labels[j][8].config(textvariable=self.fy[j])
            self.c_labels[j][9].config(textvariable=self.sd_fy[j], fg='green')
            self.c_labels[j][10].config(text='cx')
            self.c_labels[j][11].config(textvariable=self.cx[j])
            self.c_labels[j][12].config(textvariable=self.sd_cx[j], fg='green')
            self.c_labels[j][13].config(text='cy')
            self.c_labels[j][14].config(textvariable=self.cy[j])
            self.c_labels[j][15].config(textvariable=self.sd_cy[j], fg='green')
            self.c_labels[j][16].config(text='DISTORTION COEFFICIENTS')
            self.c_labels[j][18].config(text=u'\u03bc')
            self.c_labels[j][19].config(text='SD')
            self.c_labels[j][20].config(text='k1')
            self.c_labels[j][21].config(textvariable=self.k1[j])
            self.c_labels[j][22].config(textvariable=self.sd_k1[j], fg='green')
            self.c_labels[j][23].config(text='k2')
            self.c_labels[j][24].config(textvariable=self.k2[j])
            self.c_labels[j][25].config(textvariable=self.sd_k2[j], fg='green')
            self.c_labels[j][26].config(text='k3')
            self.c_labels[j][27].config(textvariable=self.k3[j])
            self.c_labels[j][28].config(textvariable=self.sd_k3[j], fg='green')
            self.c_labels[j][29].config(text='k4')
            self.c_labels[j][30].config(textvariable=self.k4[j])
            self.c_labels[j][31].config(textvariable=self.sd_k4[j], fg='green')
            self.c_labels[j][32].config(text='k5')
            self.c_labels[j][33].config(textvariable=self.k5[j])
            self.c_labels[j][34].config(textvariable=self.sd_k5[j], fg='green')
            self.c_labels[j][35].config(text='REPROJECTION ERROR')
            self.c_labels[j][36].config(text='RMS')
            self.c_labels[j][37].config(textvariable=self.rms_tk[j])
        # subframe definition and positioning
        sub_frame = self.frm[4]
        # initialization and positioning of labels for visualization of extrinsics
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=1, column=1, columnspan=3, sticky=tk.N + tk.S)
        for m in range(3):
            for q in range(3):
                self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
                self.c_labels[2][-1].grid(row=m + 2, column=1 + q, sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=11, column=1, columnspan=3, sticky=tk.N + tk.S)
        for m in range(3):
            self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
            self.c_labels[2][-1].grid(row=m + 12, column=1, columnspan=3, sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=15, column=1, columnspan=3, sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=16, column=1, columnspan=3, sticky=tk.N + tk.S)
        # definition of text of labels
        self.c_labels[2][0].config(text='ROTATION MATRIX')
        self.c_labels[2][10].config(text='TRANSLATIONAL VECTOR')
        self.c_labels[2][14].config(text='REPROJECTION ERROR')
        for j in range(3):
            self.c_labels[2][11 + j].config(textvariable=self.T_tk[j])
            for i in range(3):
                self.c_labels[2][1 + i + j * 3].config(textvariable=self.R_tk[j][i])
        self.c_labels[2][15].config(textvariable=self.rms_tk[2])

        # definition of error bar charts
        # event for the bars bases on: https://matplotlib.org/users/event_handling.html Draggable rectangle exercise
        xlabel_names = ['Images', 'Features']
        title_names = ['RMS Reprojection Error', 'Pixel Distance Error']
        for i in range(2):
            for j in range(2):
                # figure and subplot declaration
                self.f[i].append(Figure(figsize=(
                    self.screen_width / int(self.master.winfo_fpixels('1i')) * 0.45,
                    (self.screen_height - 25) / int(self.master.winfo_fpixels('1i')) * 0.25),
                    dpi=int(self.master.winfo_fpixels('1i'))))
                self.ax[i].append(self.f[i][-1].add_subplot(111))
                ## bar chart initialization and definition ##
                # adding rectanbles to subplot
                ind = np.arange(5)
                self.ax[i][-1].bar(ind, [1] * len(ind))
                # defining object to handle plot (necessary for connecting the event)
                self.bar[i].append(FigureCanvasTkAgg(self.f[i][-1], master=self.frm[7 + j + 2 * i]))
                self.bar[i][-1].draw()
                self.bar[i][-1].get_tk_widget().grid(row=0, column=0, sticky=tk.W + tk.E)
                # creating click event over the figures
                self.f[i][-1].canvas.mpl_connect('button_press_event', lambda e, a=i, b=j: self.on_press(e, a,
                                                                                                         b))
                # clear plot for first loop
                self.ax[i][-1].clear()
                self.ax[i][-1].set_title(title_names[i], fontsize=10)
                self.ax[i][-1].set_xlabel(xlabel_names[i], fontsize=7)
                self.ax[i][-1].set_ylabel('Pixels', fontsize=7)
                self.f[i][-1].tight_layout()  # Adjust size

        # set GUI for one camera
        self.frm[4].grid_forget()
        self.frm[5].grid_forget()
        self.frm[6].grid_forget()
        self.frm[8].grid_forget()
        self.frm[10].grid_forget()
        # Binding keyboard events with toolbar functions
        self.master.bind('<Delete>', lambda e: self.del_single())
        self.master.bind('<Alt-F4>', self.master.quit)
        self.master.bind("<F5>", lambda event: self.bot[5].invoke())

    def pattern_default(self, *args):
        '''
        Function to set default pattern parameters when the pattern type is changed
        '''
        self.popup.update()
        if "Chessboard" in self.pattern_type.get():
            self.feature_distance.set(50)
            self.pattern_width.set(9)
            self.pattern_height.set(6)
        elif "Asymmetric Grid" in self.pattern_type.get():
            self.feature_distance.set(100)
            self.pattern_width.set(9)
            self.pattern_height.set(4)
        elif "Symmetric Grid" in self.pattern_type.get():
            self.feature_distance.set(50)
            self.pattern_width.set(7)
            self.pattern_height.set(6)

    def check_errors_and_plot(self, *args):
        '''
        Function for updating the canvas representation of the pattern when adding a new session
        also shows error and warnings depending of the range of the parameters
        '''
        # delete grid_line objects
        try:
            self.c_pattern.delete('grid_line')
        except:
            logging.error('c_pattern does not exist')
            return
        # Clear warnings
        self.l_error.config(image='', text='', bg='#d9d9d9')
        if "Image" in self.pattern_load.get():
            # set continue flag in true
            b_continue = True
            # check range of pattern width, update the continue flag and show error if applies
            try:
                self.p_width = self.pattern_width.get()
                if self.p_width < 2:
                    self.label_msg[0].configure(text='width parameter muss be greater than one')
                    b_continue = False
                else:
                    self.label_msg[0].configure(text='')
            except ValueError:
                self.label_msg[0].configure(text='width parameter can not be empty')
                b_continue = False
            # check range of pattern height, update the continue flag and show error if applies
            try:
                self.p_height = self.pattern_height.get()
                if self.p_height < 2:
                    self.label_msg[1].configure(text='height parameter muss be greater than one')
                    b_continue = False
                else:
                    self.label_msg[1].configure(text='')
            except ValueError:
                self.label_msg[1].configure(text='height parameter can not be empty')
                b_continue = False
            # check range of pattern length and show error if applies
            try:
                self.f_distance = self.feature_distance.get()
                if self.f_distance == 0:
                    self.label_msg[2].configure(text='length parameter muss be greater than zero')
                else:
                    self.label_msg[2].configure(text='')
            except ValueError:
                self.label_msg[2].configure(text='length parameter can not be empty')

            if b_continue:
                if "Chessboard" in self.pattern_type.get():
                    plot_chessboard(self.c_pattern, self.p_width, self.p_height, self.c_pattern.winfo_width(),
                                    self.c_pattern.winfo_height())
                elif "Asymmetric Grid" in self.pattern_type.get():
                    plot_asymmetric_grid(self.c_pattern, self.p_width, self.p_height, self.c_pattern.winfo_width(),
                                         self.c_pattern.winfo_height())
                elif "Symmetric Grid" in self.pattern_type.get():
                    plot_symmetric_grid(self.c_pattern, self.p_width, self.p_height, self.c_pattern.winfo_width(),
                                        self.c_pattern.winfo_height())

                # check if width and height parameters are an odd-even pair and show warnings if applies
                if (self.p_width + self.p_height) % 2 == 0:
                    self.l_error.config(image='::tk::icons::warning',
                                        text='width and height parameters \n should be an odd-even pair', bg='#ffcc0f',
                                        fg='black')

        else:
            # check the image size and show error if applies
            try:
                if self.image_width.get() == 0:
                    self.label_msg[3].configure(text='width parameter muss be greater than zero')
                else:
                    self.label_msg[3].configure(text='')
            except ValueError:
                self.label_msg[3].configure(text='width parameter can not be empty')
            # check range of pattern height, update the continue flag and show error if applies
            try:
                if self.image_height.get() == 0:
                    self.label_msg[4].configure(text='height parameter muss be greater than zero')
                else:
                    self.label_msg[4].configure(text='')
            except ValueError:
                self.label_msg[4].configure(text='height parameter can not be empty')

            # load 3D points to object_pattern
            if self.load_files[0]:
                set_3D_points = np.fromfile(self.load_files[0][0], dtype=np.float32, sep=',')
                n_points = len(set_3D_points) / 3
                self.object_pattern = set_3D_points.reshape((n_points, 1, 3))

    def popup_configuration(self):
        '''
        Function to create popup for calibration settings button
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title("Settings calibration")
        tk.Label(self.popup, text='Use intrinsics guess').grid(row=0, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_intrinsics_guess).grid(row=0, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text='Fix principal point').grid(row=1, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_fix_point).grid(row=1, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text='Fix aspect ratio').grid(row=2, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_fix_ratio).grid(row=2, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text='Set zero tangent distance').grid(row=3, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_zero_tangent_distance).grid(row=3, column=1,
                                                                               sticky=tk.E + tk.W + tk.N)
        tk.Button(self.popup, text="Exit", command=self.popup.destroy).grid(row=4, column=0, columnspan=2,
                                                                            sticky=tk.E + tk.W + tk.N)
        self.center()

    def add_session_popup(self):
        '''
        Function to create popup for add session button
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.grid_columnconfigure(0, weight=1)
        self.popup.grid_rowconfigure(0, weight=1)
        self.popup.withdraw()

        self.popup.wm_title("Add Session")

        self.pattern_load.set('Images')

        ## struct popup add session popup ##
        # ---------------------------------
        # | Select file type to load      |
        # ---------------------------------
        # | Option Menu file type  |*|    |
        # ---------------------------------
        # |    Frame add image files      |
        # ---------------------------------
        # |    Frame add text files       |
        # ---------------------------------
        # | Stereo mode? | checkbox [+]   |
        # ---------------------------------
        # |    !  Label warning           |
        # ---------------------------------
        # ||   Start   || ||   Exit      ||
        # ---------------------------------
        self.m_frm = []
        for i in range(4):
            self.m_frm.append(tk.Frame(self.popup))
            self.m_frm[-1].grid(row=i, column=0, columnspan=1 + i % 2)

        vcmd_int = (self.popup.register(validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W', '0123456789')
        vcmd_float = (self.popup.register(validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W', '0123456789.')

        tk.Label(self.m_frm[0], text='Select file type to load').grid(row=0, column=0, sticky=tk.W + tk.E)
        tk.OptionMenu(self.m_frm[0], self.pattern_load, "Images", "Text",
                      command=self.modify_add_session_popup).grid(row=1, column=0, sticky=tk.W + tk.E)

        tk.Label(self.m_frm[3], text='Stereo mode?').grid(row=0, column=0)
        tk.Checkbutton(self.m_frm[3], variable=self.mode_stereo).grid(row=0, column=1)

        self.l_error = tk.Label(self.m_frm[3], compound=tk.LEFT)
        self.l_error.grid(row=1, column=0, columnspan=2)
        tk.Button(self.m_frm[3], text="Start", command=self.add_session).grid(row=2, column=0)
        tk.Button(self.m_frm[3], text="Cancel", command=self.popup.destroy).grid(row=2, column=1)

        ## struct Frame add session images (m_frm[1]) ##
        # -------------------------------------------------------------
        # | Pattern type                  |                           |
        # ---------------------------------                           |
        # | Option Menu pattern type  |*| |                           |
        # ---------------------------------                           |
        # | Pattern width                 |                           |
        # ---------------------------------                           |
        # | *Text width*                  |                           |
        # ---------------------------------                           |
        # | Label error width             |                           |
        # ---------------------------------      canvas pattern       |
        # | Pattern height                |                           |
        # ---------------------------------                           |
        # | *Text height*                 |                           |
        # ---------------------------------                           |
        # | Label error height            |                           |
        # ---------------------------------                           |
        # | Feature distance (mm)         |                           |
        # ---------------------------------                           |
        # | Label error distance          |                           |
        # ---------------------------------                           |
        # | *Text distance*               |                           |
        # -------------------------------------------------------------

        tk.Label(self.m_frm[1], text='Pattern type ').grid(row=0, column=0, sticky=tk.W)
        tk.OptionMenu(self.m_frm[1], self.pattern_type, "Chessboard", "Asymmetric Grid", "Symmetric Grid").grid(
            row=1, column=0, sticky=tk.W + tk.E)
        tk.Label(self.m_frm[1], text='Pattern width ').grid(row=2, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.pattern_width, validate='key', validatecommand=vcmd_int).grid(
            row=3,
            column=0, sticky=tk.W + tk.E)

        self.label_msg[0] = tk.Label(self.m_frm[1], font='TkDefaultFont 6', fg='red')
        self.label_msg[0].grid(row=4, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1], text='Pattern height ').grid(row=5, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.pattern_height, validate='key', validatecommand=vcmd_int).grid(
            row=6,
            column=0, sticky=tk.W + tk.E)

        self.label_msg[1] = tk.Label(self.m_frm[1], font='TkDefaultFont 6', fg='red')
        self.label_msg[1].grid(row=7, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1], text='Feature distance (mm) ').grid(row=8, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.feature_distance, validate='key',
                 validatecommand=vcmd_float).grid(
            row=9, column=0, sticky=tk.W + tk.E)

        ## struct Frame add session text (m_frm[2]) ##
        # -----------------------------
        # | Image width               |
        # -----------------------------
        # | *Text width*              |
        # -----------------------------
        # | Label error width         |
        # -----------------------------
        # | Image height              |
        # -----------------------------
        # | *Text height*             |
        # -----------------------------
        # | Label error height        |
        # -----------------------------
        # ||  3D points of pattern   ||
        # -----------------------------
        # | Label error 3D points     |
        # -----------------------------

        self.m_frm[2].grid_forget()
        self.label_msg[2] = tk.Label(self.m_frm[1], font='TkDefaultFont 6', fg='red')
        self.label_msg[2].grid(row=10, column=0, sticky=tk.W)

        self.c_pattern = tk.Canvas(self.m_frm[1], height=100, width=100, bg='white')
        self.c_pattern.grid(row=0, column=1, rowspan=11)
        tk.Label(self.m_frm[1], width=15).grid(row=1, column=1, sticky=tk.W)
        # self.c_pattern.bind('<Configure>', self.check_errors_and_plot)

        tk.Label(self.m_frm[2], text='Image width ').grid(row=0, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[2], textvariable=self.image_width, validate='key', validatecommand=vcmd_int).grid(row=1,
                                                                                                              column=0,
                                                                                                              sticky=tk.W + tk.E)
        self.label_msg[3] = tk.Label(self.m_frm[2], font='TkDefaultFont 6', fg='red')
        self.label_msg[3].grid(row=2, column=0, sticky=tk.W)

        tk.Label(self.m_frm[2], text='Image height ').grid(row=3, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[2], textvariable=self.image_height, validate='key', validatecommand=vcmd_int).grid(
            row=4, column=0, sticky=tk.W + tk.E)
        self.label_msg[4] = tk.Label(self.m_frm[2], font='TkDefaultFont 6', fg='red')
        self.label_msg[4].grid(row=5, column=0, sticky=tk.W)

        tk.Button(self.m_frm[2], text="3D points of pattern", command=self.load_3D_points).grid(row=6, column=0)
        self.l_load_files[0] = tk.Label(self.m_frm[2], font='TkDefaultFont 6')
        self.l_load_files[0].grid(row=7, column=0)

        # Setting pattern feature variables
        self.mode_stereo.set(False)
        self.pattern_type.set('Chessboard')

        self.center()

    def modify_add_session_popup(self, *args):
        '''
        Function to modify add_session popup by changing pattern load selection box
        '''
        self.l_load_files[0].config(text='')
        self.load_files[0] = None
        if "Text" in self.pattern_load.get():
            self.image_width.set(240)
            self.image_height.set(320)
            self.m_frm[2].grid(row=2, column=0)
            self.m_frm[1].grid_forget()
        else:
            self.m_frm[1].grid(row=1, column=0)
            self.m_frm[2].grid_forget()
        self.check_errors_and_plot(None)

    def load_3D_points(self):
        '''
        Function to load 3D points from text
        '''
        self.load_files[0] = tk.filedialog.askopenfilenames(parent=self.popup,
                                                            filetypes=[('Text files', '*.txt')])  # , multiple = False)
        if len(self.load_files[0]) == 0:
            self.object_pattern = None
            self.l_load_files[0].config(text='File missing, please add', fg='red')
        else:
            set_3D_points = np.fromfile(self.load_files[0][0], dtype=np.float32, sep=',')
            if len(set_3D_points) % 3 != 0:
                self.l_load_files[0].config(text='No 3D points', fg='red')
                self.object_pattern = None
            else:
                self.l_load_files[0].config(text=self.load_files[0][0].rsplit('/', 1)[1], fg='black')
                self.check_errors_and_plot(None)

    def add_session(self):
        '''
        Function to add session after the given parameters are correct
        Creates object_pattern according to the selected pattern type
        Enables and disables the corresponding buttons
        Adjust the GUI for a single/stereo mode
        '''
        if 'Images' in self.pattern_load.get():
            for j in range(3):
                print(self.label_msg[j].cget('text'))
                if self.label_msg[j].cget('text'):
                    return
        else:
            for j in range(3, 5):
                print(self.label_msg[j].cget('text'))
                if self.label_msg[j].cget('text'):
                    return
            # if 3d points aren't initialized
            if self.object_pattern is None:
                return
            elif not self.object_pattern.any():
                return

        # checks
        if 'Images' in self.pattern_load.get():
            # creates object from Chessboard pattern
            if "Chessboard" in self.pattern_type.get():
                self.object_pattern = np.zeros((self.p_width * self.p_height, 3), np.float32)
                grid = np.mgrid[0:self.p_height, 0:self.p_width].T.reshape(-1, 2) * self.f_distance
                self.object_pattern[:, 0] = -grid[:, 1]
                self.object_pattern[:, 1] = grid[:, 0]
            # creates object from Grid pattern
            elif "Asymmetric Grid" in self.pattern_type.get():
                pattern_size = (self.p_height, self.p_width)
                self.object_pattern = np.zeros((np.prod(pattern_size), 3), np.float32)
                self.object_pattern[:, :2] = np.fliplr(np.indices(pattern_size).T.reshape(-1, 2))
                for i in range(np.prod(pattern_size)):
                    if self.object_pattern[i, 0] % 2 == 0:
                        self.object_pattern[i, 1] = self.object_pattern[i, 1] * self.f_distance
                        self.object_pattern[i, 0] = self.object_pattern[i, 0] * self.f_distance / 2
                    else:
                        self.object_pattern[i, 1] = self.object_pattern[i, 1] * self.f_distance + self.f_distance / 2
                        self.object_pattern[i, 0] = self.object_pattern[i, 0] * self.f_distance / 2
            # returns for led pattern (not yet implemented)
            elif "Symmetric Grid" in self.pattern_type.get():
                self.object_pattern = np.zeros((self.p_width * self.p_height, 3), np.float32)
                grid = np.mgrid[0:self.p_height, 0:self.p_width].T.reshape(-1, 2) * self.f_distance
                self.object_pattern[:, 0] = -grid[:, 1]
                self.object_pattern[:, 1] = grid[:, 0]

            # set default image type
            self.valid_files = [".jpg", ".png"]
            self.ftypes = [('All image files', tuple(x + y for x, y in zip(('*', '*'), tuple(self.valid_files)))), ]
        else:
            self.valid_files = [".txt"]
            self.ftypes = [('Text files', '*.txt')]
            self.tabControl[0].tab(0, state="disable")  # Disable tab for original image

        self.m_stereo = self.mode_stereo.get()

        self.popup.destroy()

        self.bot[0].config(state="disable")  # disable add session button
        self.bot[0].config(relief="raised")  # change to raise add session button
        self.bot[3].config(state="disable")  # disable zoom in button
        self.bot[4].config(state="disable")  # disable zoom out button
        self.bot[5].config(state="disable")  # disable run calibration button
        self.bot[8].config(state="disable")  # disable export button
        self.bot[9].config(state="disable")  # disable export button

        self.bot[2].config(state="normal")  # enable adding images per folder button
        self.bot[6].config(state="normal")  # enable delete session button
        self.bot[7].config(state="normal")  # settings button

        if self.m_stereo:
            self.n_cameras = 2
            self.bot[1].config(state="disable")  # disable adding images per file button
            # set GUI for two camera
            self.frm[4].grid(row=1, column=3, sticky=tk.N + tk.S)  # frame for extrinsics
            self.frm[5].grid(row=1, column=4, sticky=tk.N + tk.S)  # frame for intrinsics second camera
            self.frm[6].grid(row=1, column=5, sticky=tk.N + tk.S)  # frame for pictures second camera
            self.frm[8].grid(row=0, column=1)  # frame for second grafic first camera
            self.frm[10].grid(row=1, column=1)  # frame for second grafic second camera
            self.tabControl[0].tab(4, state="normal")  # Enable tab for extrinsic Reprojection
        else:
            self.n_cameras = 1
            # set GUI for one camera
            self.frm[4].grid_forget()
            self.frm[5].grid_forget()
            self.frm[6].grid_forget()
            self.frm[8].grid_forget()
            self.frm[10].grid_forget()
            self.bot[1].config(state="normal")  # enable adding per file
            self.tabControl[0].tab(4, state="disable")  # Disable tab for extrinsic Reprojection

    def get_file_names(self, typeof, title_dialog):
        '''
        Function for getting new files
        '''
        filenames = []
        # this is adding per file
        if typeof == 'p':
            t_choose = 'Please select a file for ' + title_dialog
            filenames = tk.filedialog.askopenfilenames(parent=self.master, title=t_choose, filetypes=self.ftypes)
        # this is adding per folder
        else:
            list_path = []
            t_options = [' (first camera)', ' (second camera)']
            while len(list_path) < self.n_cameras:
                # create dialog for adding folders
                t_choose = 'Please select a folder for ' + title_dialog + t_options[len(list_path)]
                path_folder = tk.filedialog.askdirectory(parent=self.master, title=t_choose)
                # checks that the selected folder exists
                if path_folder:
                    list_path.append(path_folder)
                else:
                    break
            for p in list_path:
                file_no_path = []
                for f in os.listdir(p):
                    ext = os.path.splitext(f)[1]
                    if ext.lower() not in self.valid_files:
                        continue
                    file_no_path.append(f)
                try:
                    # sorting files, based on: https://stackoverflow.com/questions/33159106/sort-filenames-in-directory-in-ascending-order
                    file_no_path.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))
                except ValueError:
                    logging.warning('non-indexable filenames')
                for f in file_no_path:
                    filenames.append(os.path.join(p, f))
        return filenames

    def add_file(self, typeof):
        '''
        Function to add files to the session
        '''
        file_names_2D_points = self.get_file_names(typeof, '2D points')

        if len(file_names_2D_points) == 0:
            return

        l_msg = self.popupmsg()

        rejected_images = []
        repeated_images = []

        for i in range(len(file_names_2D_points)):
            file_name_2D_points = file_names_2D_points[i]
            j = 0
            if self.m_stereo:
                # this corresponds to the right camera
                if i >= len(file_names_2D_points) / 2:
                    j = 1
            # checks if images isn't repeated
            if file_name_2D_points not in self.paths[j]:
                if '.txt' not in self.valid_files:
                    # read image file
                    im = np.float32(cv2.imread(file_name_2D_points, 0))
                    # original: normalized read image
                    im = (255.0 * (im - im.min()) / (im.max() - im.min())).astype(np.uint8)
                    ret = False
                    features = None

                    # creates copy of im, performance test found in https://stackoverflow.com/questions/48106028/python-copy-an-array-array
                    im2 = im * 1
                    for cycle in range(2):
                        logging.debug('Cycle... %d', cycle + 1)
                        if cycle == 1:
                            logging.debug('Inverting image')
                            im2 = 255 - im2
                        # find features for chessboard pattern type
                        if 'Chessboard' in self.pattern_type.get():
                            ret, features = cv2.findChessboardCorners(im2, (self.p_height, self.p_width))
                            if ret:
                                # improve feature detection
                                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 130,
                                            0.25)  ### EPS realistisch einstellen je nach Bildaufloesung (z.B fuer (240x320) 0.1, 0.25)
                                cv2.cornerSubPix(im2, features, (3, 3), (-1, -1), criteria)
                                break
                        # find features for asymmetric grid pattern type
                        elif 'Asymmetric Grid' in self.pattern_type.get():
                            features = np.array([], np.float32)
                            ret, features = cv2.findCirclesGrid(im2, (self.p_height, self.p_width), features,
                                                                cv2.CALIB_CB_ASYMMETRIC_GRID)
                            if ret:
                                break
                        # find features for asymmetric grid pattern type
                        elif 'Symmetric Grid' in self.pattern_type.get():
                            features = np.array([], np.float32)
                            '''
                            Since the findCirclesGrid algorithm for symmetric grid usually fails for a wrong height - width configuration,
                            we invert here those parameters 
                            '''
                            for inner_cycle in range(2):
                                if inner_cycle == 0:
                                    logging.debug('height - width')
                                    ret, features = cv2.findCirclesGrid(im2, (self.p_height, self.p_width),
                                                                        features,
                                                                        cv2.CALIB_CB_SYMMETRIC_GRID)
                                    if ret:
                                        break
                                else:
                                    logging.debug('width - height')
                                    ret, features = cv2.findCirclesGrid(im2, (self.p_width, self.p_height),
                                                                        features,
                                                                        cv2.CALIB_CB_SYMMETRIC_GRID)

                                    if ret:
                                        # trasform the detected features configuration to match the original (height, width)
                                        features = features.reshape(self.p_height, self.p_width, 1, 2)
                                        features = np.transpose(features, (1, 0, 2, 3))
                                        features = features.reshape(self.p_width * self.p_height, 1, 2)
                                        break
                            if ret:
                                break

                    # checks if the detection of features succeed
                    if ret:
                        # add file path to path
                        self.paths[j].append(file_name_2D_points)
                        # add original of image to img_original
                        self.img_original[j].append(im)
                        # add features to detected_features
                        self.detected_features[j].append(features)
                    else:
                        # add image path to rejected_images
                        rejected_images.append(file_name_2D_points)
                        # add file path to path
                        self.paths[j].append(None)
                        # add original of image to img_original
                        self.img_original[j].append(None)
                        # add features to detected_features
                        self.detected_features[j].append(None)

                else:
                    a = np.fromfile(file_name_2D_points, dtype=np.float32, sep=',')
                    a = a.reshape((len(a) / 2, 1, 2))
                    self.p_height = 1
                    self.p_width = len(a)
                    # add file path to path
                    self.paths[j].append(file_name_2D_points)
                    # add original of image to img_original
                    im = np.zeros((self.image_height.get(), self.image_width.get()))
                    self.img_original[j].append(im)
                    # add features to detected_features
                    self.detected_features[j].append(a)
            else:
                repeated_images.append(file_name_2D_points)

            c_porcent = (i + 1) / float(len(file_names_2D_points))  # percentage of completion of process
            self.progbar["value"] = c_porcent * 10.0
            self.style_pg.configure('text.Horizontal.TProgressbar',
                                    text='{:g} %'.format(c_porcent * 100.0))  # update label
            # if one or more images failed the importing, show info popup
            message = 'Imported images: {0} of {1}\n'.format(i + 1 - len(rejected_images) - len(repeated_images),
                                                             len(file_names_2D_points))
            if rejected_images or repeated_images:
                # message += 'A total of {0} images could not be loaded\n'.format(len(rejected_images) + len(repeated_images))
                message += 'Rejected images: {0}\n'.format(len(rejected_images))
                message += 'Repeated images: {0}\n'.format(len(repeated_images))
                if rejected_images:
                    message += 'Rejected: \n {0}\n'.format('\n'.join(rejected_images))
                if repeated_images:
                    message += 'Repeated: \n {0}'.format('\n'.join(repeated_images))
            l_msg.configure(text=message)

            self.popup.update()

        index_to_delete = [i for i, v in enumerate(self.paths[0]) if v == None]
        if self.m_stereo:
            index_to_delete = index_to_delete + [i for i, v in enumerate(self.paths[1]) if v == None]

        index_to_delete = sorted(set(index_to_delete), reverse=True)
        # delete rejected images
        for j in range(self.n_cameras):
            for i in list(index_to_delete):
                del self.paths[j][i]
                del self.img_original[j][i]
                del self.detected_features[j][i]

        # update total of images
        self.n_total.set(len(self.paths[0]))
        # enable and disable buttons depending of the succeed of the importing process
        if self.n_total.get() > 0:
            self.bot[3].config(state="normal")  # enable zoom in button
            self.bot[4].config(state="normal")  # enable zoom in button
            self.bot[5].config(state="normal")  # enable run calibration button
        else:
            self.bot[3].config(state="disable")  # disable zoom in button
            self.bot[4].config(state="disable")  # disable zoom in button
            self.bot[5].config(state="disable")  # disable run calibration button

    def popupmsg(self):
        '''
        Function to create popup for failure in importing images
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title("Information imported images")
        l_msg = tk.Label(self.popup)
        l_msg.grid(row=0, column=0, columnspan=2, sticky=tk.E + tk.W)

        # set initial text progressbar
        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar = ttk.Progressbar(self.popup, style='text.Horizontal.TProgressbar')
        self.progbar.config(maximum=10, mode='determinate')
        self.progbar.grid(row=1, column=0, columnspan=2, sticky=tk.E + tk.W)

        tk.Button(self.popup, text="Okay", command=self.popup.destroy).grid(row=2, column=0, columnspan=2,
                                                                            sticky=tk.E + tk.W)
        self.center()
        return l_msg

    def updateSelection(self, event):
        '''
        Function for the click event over the data browser
        '''
        widget = event.widget
        self.zoomhandler = 0
        self.index.set(widget.curselection()[0])
        if self.r_error[0]:
            self.loadBarError([1])
            self.updateBarError(0)

    def updateSelectionperclick(self, selection, i):
        '''
        Function for the click event over the error bars
        '''
        # This corresponds to a click over the RMS reprojection error chart
        if i == 0:
            self.zoomhandler = 0
            self.listbox.selection_clear(0, tk.END)
            self.index.set(selection - 1)
            self.listbox.select_set(selection - 1)  # This make sense for update by click in bar chart
            self.listbox.yview(selection - 1)
            self.loadBarError([1])
            self.updateBarError(0)
        # This corresponds to a click over the Pixel error chart
        else:
            self.index_corner = selection - 1
            self.updatePicture(None)
            self.updateBarError(1)

    def click_to_zoom(self, event):
        '''
        Function for the click event with a zoom sunken button
        Detects the x,y click position and calculate the scale for the image resizing
        '''
        self.scale = 1.0
        self.x = event.x
        self.y = event.y
        # check if the zoom in button is sunken and current zoom is less than maximum
        if self.bot[3].config('relief')[-1] == 'sunken' and self.zoomhandler < 10:
            self.scale /= self.delta
            self.imscale /= self.delta
            self.zoomhandler += 1
        # check if the zoom out button is sunken and current zoom is less than minimum
        elif self.bot[4].config('relief')[-1] == 'sunken' and self.zoomhandler > 0:
            self.scale *= self.delta
            self.imscale *= self.delta
            self.zoomhandler -= 1
        self.updatePicture()

    def scroll_to_zoom(self, type, event):
        self.scale = 1.0
        self.x = event.x
        self.y = event.y
        if type == 'm' and self.zoomhandler < 10:
            self.scale /= self.delta
            self.imscale /= self.delta
            self.zoomhandler += 1
        elif self.zoomhandler > 0:
            self.scale *= self.delta
            self.imscale *= self.delta
            self.zoomhandler -= 1
        self.updatePicture()

    def toggle_zoom_buttons(self, button1, button2):
        '''
        Function to keep only one zoom button enable
        '''
        if self.bot[button1].config('relief')[-1] == 'sunken':
            self.bot[button1].config(relief="raised")
        else:
            self.bot[button1].config(relief="sunken")
            self.bot[button2].config(relief="raised")

    def updatePicture(self, *args):
        '''
        Function to update pictures in panel of tabs
        '''
        selection = self.index.get()
        # checks for a valid selection
        if selection >= 0:
            # update selection in data browser
            self.listbox.activate(selection)
            images = []
            for j in range(self.n_cameras):
                images.append([])
                images[j].append(Image.fromarray(self.img_original[j][selection]))  # get original of the selected image
                images[j].append(Image.fromarray(
                    self.image_features(j, selection)))  # get images with marked features of the selected image
                images[j].append(Image.fromarray(self.heat_map[j]))  # get heat_map for all the images in camera
                images[j].append(Image.fromarray(self.project_detected_features(j,
                                                                                selection)))  # get projection image with intrinsic parameters of the selected image
                images[j].append(Image.fromarray(self.project_detected_features(j, selection,
                                                                                forExtrinsics=True)))  # get projection image with the intrinsics of the other camera and extrinsics between the cameras of the selected image
            # scale image if zoom applies and update panel of tabs
            if self.zoomhandler != 0:
                width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
                new_size = int(self.imscale * width), int(self.imscale * height)
                for j in range(self.n_cameras):
                    for i in range(5):
                        self.list_panel[j][i].scale('all', self.x, self.y, self.scale, self.scale)
                        self.img[j][i] = ImageTk.PhotoImage(images[j][i].resize(new_size))
                        self.list_panel[j][i].itemconfig(self.list_image_on_panel[j][i], image=self.img[j][i])
            # Update panel of tabs
            else:
                self.imscale = 1
                width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
                new_size = int(self.imscale * width), int(self.imscale * height)
                for j in range(self.n_cameras):
                    for i in range(5):
                        self.list_panel[j][i].scale('all', 0, 0, 1, 1)
                        self.list_panel[j][i].coords(self.list_image_on_panel[j][i], 0, 0)
                        self.img[j][i] = ImageTk.PhotoImage(images[j][i].resize(new_size))
                        self.list_panel[j][i].itemconfig(self.list_image_on_panel[j][i], image=self.img[j][i])
            self.scale = 1

        # for no valid selection, update with empty picture the panel of tabs
        else:
            for j in range(self.n_cameras):
                for i in range(5):
                    self.list_panel[j][i].delete("all")
                    self.list_image_on_panel[j][i] = self.list_panel[j][i].create_image(0, 0, anchor=tk.N + tk.W,
                                                                                        image=None)

    # self.panel1.itemconfig(self.image_on_panel1, image = None)

    def image_features(self, camera, index):
        '''
        Function to create an picture with the original one and its detected features with markers
        '''
        # get the features for the selected image
        features = self.detected_features[camera][index]
        # get original of the selected image
        im = self.img_original[camera][index]
        if features.any():
            im2 = np.uint8(np.zeros(im.shape + (3,)))
            im2[:, :, 0] = im
            im2[:, :, 1] = im
            im2[:, :, 2] = im
            # draw markers over the image representing the features
            cv2.drawChessboardCorners(im2, (self.p_height, self.p_width), features, True)
        else:
            im2 = im
        return im2

    def update_added_deleted(self, *args):
        '''
        Function to update heat map when a new image is added or an image is deleted
        '''
        self.zoomhandler = 0
        if self.n_total.get() > 0:
            for j in range(self.n_cameras):
                if self.size[j] is None:
                    self.size[j] = self.img_original[j][0].shape
                # recalculate heat_map
                self.heat_map[j] = self.density_cloud_heat_map(j)
        # update data browser
        self.loadImagesBrowser()

    def loadImagesBrowser(self):
        '''
        Function to update items in data browser
        '''
        # checks if listbox object exists
        if self.listbox:
            self.listbox.delete(0, tk.END)
            if self.n_total.get() > 0:
                for i in self.paths[0]:
                    self.listbox.insert(tk.END, str(i.rsplit('/', 1)[1]))
                if self.index.get() == -1:
                    self.listbox.select_set(0)
                    self.index.set(0)
                else:
                    self.listbox.select_set(self.index.get())

    def density_cloud_heat_map(self, camera):
        '''
        Function to calculate a density cloud map of all the images using its detected features
        '''
        # initialize picture with image size
        width = self.size[camera][1]
        height = self.size[camera][0]
        grid = np.zeros((height, width))
        # get detected features for the camera
        list_features = self.detected_features[camera]
        ## create circle matrix for each pattern ##
        # calculate number of pixel as the radius of the circle for each feature depending of the width
        L = int(round(0.006 * width + 8))
        step = 1.0 / L
        # initialize grid for the circle matrix
        grid_circle = np.zeros((L * 2 + 1, L * 2 + 1))
        # Assign values to the grid from 1.0 to 0.0 as a circle representation, where the center gets 1.0 and the radius gets 0.0
        for k in range(L):
            for i in range(L - k, L + k + 1):
                for j in range(L - k, L + k + 1):
                    r = ((i - L) ** 2 + (j - L) ** 2) ** 0.5
                    if r <= k:
                        grid_circle[i, j] += step
        # for each point in the list of features overlay the circle matrix, considering the width and height of the image
        for k in list_features:
            for c in k:
                x = int(c[0][1])
                y = int(c[0][0])
                x_min = 0
                x_max = height
                y_min = 0
                y_max = width
                x_min_g = 0
                x_max_g = L * 2 + 1
                y_min_g = 0
                y_max_g = L * 2 + 1

                if x - L < 0:
                    x_min_g -= x - L
                else:
                    x_min += x - L
                if x + L + 1 > height:
                    x_max_g = x_max - x_min
                else:
                    x_max = x + L + 1
                if y - L < 0:
                    y_min_g -= y - L
                else:
                    y_min += y - L
                if y + L + 1 > width:
                    y_max_g = y_max - y_min
                else:
                    y_max = y + L + 1

                # TODO: Show errors
                grid[x_min:x_max, y_min:y_max] += grid_circle[x_min_g:x_max_g, y_min_g:y_max_g]

        # normalized the picture
        grid = ((grid - grid.min()) / (grid.max() - grid.min()))
        '''
        for k in list_features: 
            for c in k: 
                grid[int(c[0][1]),int(c[0][0])]=1.0 
        '''
        # create heatmap of the normalized picture. Check: https://stackoverflow.com/questions/10965417/how-to-convert-numpy-array-to-pil-image-applying-matplotlib-colormap
        im = np.uint8(cm.jet(grid) * 255)
        return im

    def project_detected_features(self, camera, index, forExtrinsics=False):
        '''
        Function to get the images comparing the original in green and its projection in red
        The current selected feature index is represented by a circle over the point
        '''
        # create RGB picture with the image size
        im3 = np.uint8(np.zeros(self.size[camera] + (3,)))
        im = self.img_original[camera][index]
        im3[:, :, 0] = im
        im3[:, :, 1] = im
        im3[:, :, 2] = im
        # check if the projection is from intrinsics or from intrinsics and extrinsics (from the other camera)
        if forExtrinsics:
            projections = self.projected_stereo
        else:
            projections = self.projected

        # plot projection mesh of features using  red lines
        if projections[camera]:
            for i in range(self.p_height):
                for j in range(self.p_width):
                    a = projections[camera][index][j * self.p_height + i]
                    if j * self.p_height + i == self.index_corner:
                        cv2.circle(im3, (a[0][0], a[0][1]), 5, (255, 0, 0))
                    if i < self.p_height - 1:
                        b = projections[camera][index][j * self.p_height + i + 1]
                        cv2.line(im3, (a[0][0], a[0][1]), (b[0][0], b[0][1]), (255, 0, 0))
                    if j < self.p_width - 1:
                        c = projections[camera][index][(j + 1) * self.p_height + i]
                        cv2.line(im3, (a[0][0], a[0][1]), (c[0][0], c[0][1]), (255, 0, 0))

        # plot original mesh of features using green lines
        for i in range(self.p_height):
            for j in range(self.p_width):
                a = self.detected_features[camera][index][j * self.p_height + i]
                if j * self.p_height + i == self.index_corner:
                    cv2.circle(im3, (a[0][0], a[0][1]), 5, (0, 255, 0))
                if i < self.p_height - 1:
                    b = self.detected_features[camera][index][j * self.p_height + i + 1]
                    cv2.line(im3, (a[0][0], a[0][1]), (b[0][0], b[0][1]), (0, 255, 0))
                if j < self.p_width - 1:
                    c = self.detected_features[camera][index][(j + 1) * self.p_height + i]
                    cv2.line(im3, (a[0][0], a[0][1]), (c[0][0], c[0][1]), (0, 255, 0))

        return im3

    def modify_play_popup(self, *args):
        '''
        Function to adjust the GUI according to the selected calibration method
        '''
        self.bot[8].config(state="disable")  # enable export parameters button
        self.bot[9].config(state="disable")  # enable export parameters button
        # reset all values
        self.reset_camera_parameters()
        self.reset_error()
        self.updateCameraParametersGUI()
        self.loadBarError([0, 1])
        self.load_files = [None, None, None]
        for j in range(3):
            self.l_load_files[j].config(text='', fg='black')

        # reset values status for clustering
        self.label_status[1][1].config(text='')
        self.label_status[1][2].config(text='')
        self.label_status[2][1].config(text='')
        self.label_status[2][2].config(text='')
        self.label_status[3][1].config(text='')
        self.label_status[3][2].config(text='')
        self.label_status[4][1].config(text='')
        self.label_status[4][2].config(text='')
        self.label_status[5][2].config(text='')

        # reset values status for loading
        # update status check
        self.label_status_l[1][1].config(text='')
        self.label_status_l[2][1].config(text='')
        self.label_status_l[3][0].config(text='3. Loading Extrinsics')
        self.label_status_l[3][1].config(text='')
        self.label_status_l[4][1].config(text='')

        if "Clustering" in self.how_to_calibrate.get():
            # reset progress bar
            self.progbar["value"] = 0
            self.lb_time.config(text='')
            self.style_pg.configure('text.Horizontal.TProgressbar', text='{:g} %'.format(0))
            # set GUI for clustering
            self.m_frm[1].grid(row=3, column=0, sticky=tk.N + tk.S)
            self.m_frm[0].grid_forget()
        elif "Load" in self.how_to_calibrate.get():
            # set GUI for Loading File
            self.m_frm[0].grid(row=2, column=0, sticky=tk.N + tk.S)
            self.m_frm[1].grid_forget()

    def assign_filename(self, j):
        self.load_files[j] = tk.filedialog.askopenfilenames(parent=self.popup, filetypes=[
            ('Text files', '*.txt')])  # , multiple = False,)
        if len(self.load_files[j]) == 0:
            self.l_load_files[j].config(text='', fg='black')
            # clear status check
            self.label_status_l[j + 1][1].config(text='')
            return
        else:
            self.l_load_files[j].config(text=self.load_files[j][0].rsplit('/', 1)[1], fg='black')
            f = open(self.load_files[j][0], 'r')
            a = f.read()
            if j <= 1:
                self.camera_matrix[j], self.dist_coefs[j] = datastring.string2intrinsic(a)
            else:
                self.R_stereo, self.T_stereo = datastring.string2extrinsic(a)
            # update status check
            self.label_status_l[j + 1][1].config(text=u'\u2714')
            if j == 2:
                self.label_status_l[3][0].config(text='3. Loading Extrinsics')
            self.rms = [0, 0, 0]
            self.reset_error()
            self.updateCameraParametersGUI()
            self.loadBarError([0, 1])

    def play_popup(self):
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title("Camera Calibration")

        tk.Label(self.popup, text='How to get camera parameters?').grid(row=0, column=0,
                                                                        sticky=tk.E + tk.W + tk.N)
        tk.OptionMenu(self.popup, self.how_to_calibrate, "Clustering calculation", "Load from file",
                      command=self.modify_play_popup).grid(row=1, column=0, sticky=tk.E + tk.W + tk.N)

        vcmd_int = (self.popup.register(validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W', '0123456789')

        self.m_frm = []
        for i in range(3):
            self.m_frm.append(tk.Frame(self.popup))
            self.m_frm[-1].grid(row=2 + i, column=0)
        self.m_frm[0].grid_forget()

        ## struct popup load from file (m_frm[0]) ##
        # ------------------------------
        # How to get camera parameters |
        # ------------------------------
        # | Load from file         |*| |
        # ------------------------------
        # || Intrinsics 1 camera      ||
        # ------------------------------
        # || Intrinsics 2 camera      ||
        # ------------------------------
        # || Extrinsics               ||
        # ------------------------------
        # |  (label_status_l)          |
        # ------------------------------
        # || Calibrate || ||Exit      ||
        # ------------------------------

        tk.Button(self.m_frm[0], text="Intrinsics 1 camera", command=lambda: self.assign_filename(0)).grid(row=1,
                                                                                                           column=0,
                                                                                                           sticky=tk.E + tk.W + tk.N)

        if self.m_stereo:
            tk.Button(self.m_frm[0], text="Intrinsics 2 camera", command=lambda: self.assign_filename(1)).grid(row=3,
                                                                                                               column=0,
                                                                                                               sticky=tk.E + tk.W + tk.N)
            tk.Button(self.m_frm[0], text="Extrinsics", command=lambda: self.assign_filename(2)).grid(row=5, column=0,
                                                                                                      sticky=tk.E + tk.W + tk.N)

        self.l_load_files[0] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[0].grid(row=2, column=0, sticky=tk.E + tk.W + tk.N)
        self.l_load_files[1] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[1].grid(row=4, column=0, sticky=tk.E + tk.W + tk.N)
        self.l_load_files[2] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[2].grid(row=6, column=0, sticky=tk.E + tk.W + tk.N)

        aux_frame = tk.Frame(self.m_frm[0])
        aux_frame.grid(row=7, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        ## struct for label_status_l ##
        # ---------------------------------------------
        # | Steps                             | State |
        # ---------------------------------------------
        # | 1. Loading Intrinsics 1           |       |
        # ---------------------------------------------
        # | 2. Loading Intrinsics 2           |       |
        # ---------------------------------------------
        # | 3. Loading/Calculating Extrinsics |       |
        # ---------------------------------------------
        # | 2/4. Calculating Error            |       |
        # ---------------------------------------------
        self.label_status_l = []
        for j in range(5):
            self.label_status_l.append([])
            for i in range(2):
                l = tk.Label(aux_frame)
                l.grid(row=j, column=i, sticky=tk.W)
                self.label_status_l[j].append(l)

        self.label_status_l[0][0].config(text='Steps')
        self.label_status_l[0][1].config(text='State')

        if self.n_cameras == 1:
            # forget grid for labels of errors for stereo mode
            self.l_load_files[1].grid_forget()
            self.l_load_files[2].grid_forget()
            # forget grid of labels for stereo mode
            self.label_status_l[1][0].config(text='1. Loading Intrinsics 1')
            self.label_status_l[2][0].grid_forget()
            self.label_status_l[3][0].grid_forget()
            self.label_status_l[4][0].config(text='2. Calculating Error')
            self.label_status_l[4][0].grid(row=2, column=0)
        else:
            self.label_status_l[1][0].config(text='1. Loading Intrinsics 1')
            self.label_status_l[2][0].config(text='2. Loading Intrinsics 2')
            self.label_status_l[3][0].config(text='3. Loading Extrinsics')
            self.label_status_l[4][0].config(text='4. Calculating Error')

        ## struct popup load from file (m_frm[1]) ##
        # ------------------------------------
        # How to get camera parameters       |
        # ------------------------------------
        # | Clustering calculation       |*| |
        # ------------------------------------
        # | Number of groups (k)             |
        # ------------------------------------
        # |              (c_k)               |
        # ------------------------------------
        # | Number of elements per group (r) |
        # ------------------------------------
        # |              (c_r)               |
        # ------------------------------------
        # |         >>>>(progbar)>>>>        |
        # ------------------------------------
        # |            (lb_time)             |
        # ------------------------------------
        # |          (label_status)          |
        # ------------------------------------
        # || Calibrate ||       ||Exit      ||
        # ------------------------------------

        tk.Label(self.m_frm[1], text='Number of images (n) ').grid(row=1, column=0, sticky=tk.W)
        tk.Label(self.m_frm[1], text=str(self.n_total.get())).grid(row=2, column=0, sticky=tk.E + tk.W)

        self.c_r.set(self.n_total.get())
        self.c_k.set(1)

        tk.Label(self.m_frm[1], text='Number of groups (k) ').grid(row=3, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.c_k, validate='key', validatecommand=vcmd_int).grid(row=4, column=0,
                                                                                                      sticky=tk.E + tk.W + tk.N)
        self.label_msg[0] = tk.Label(self.m_frm[1], font='TkDefaultFont 6', fg='red')
        self.label_msg[0].grid(row=5, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1], text='Number of elements per group (r) ').grid(row=6, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.c_r, validate='key', validatecommand=vcmd_int).grid(row=7, column=0,
                                                                                                      sticky=tk.E + tk.W + tk.N)
        self.label_msg[1] = tk.Label(self.m_frm[1], font='TkDefaultFont 6', fg='red')
        self.label_msg[1].grid(row=8, column=0, sticky=tk.W)

        # set initial text progressbar
        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar = ttk.Progressbar(self.m_frm[1], style='text.Horizontal.TProgressbar')
        self.progbar.config(maximum=10, mode='determinate')
        self.progbar.grid(row=9, column=0, sticky=tk.E + tk.W)

        self.lb_time = tk.Label(self.m_frm[1], font='TkDefaultFont 6')
        self.lb_time.grid(row=10, column=0, sticky=tk.W + tk.E)

        aux_frame = tk.Frame(self.m_frm[1])
        aux_frame.grid(row=11, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        ## struct for label_status ##
        # -------------------------------------------------
        # | Steps                      | State | Time (s) |
        # -------------------------------------------------
        # | 1. Clustering              |       |          |
        # -------------------------------------------------
        # | 2. Averaging               |       |          |
        # -------------------------------------------------
        # | 3. Calculating Projections |       |          |
        # -------------------------------------------------
        # | 4. Calculating Error       |       |          |
        # -------------------------------------------------
        # | TOTAL                      |       |          |
        # -------------------------------------------------
        self.label_status = []
        for j in range(6):
            self.label_status.append([])
            for i in range(3):
                l = tk.Label(aux_frame)
                l.grid(row=j, column=i, sticky=tk.W)
                self.label_status[j].append(l)

        self.label_status[0][0].config(text='Steps')
        self.label_status[0][1].config(text='State')
        self.label_status[0][2].config(text='Time (s)')
        self.label_status[1][0].config(text='1. Clustering')
        self.label_status[2][0].config(text='2. Averaging')
        self.label_status[3][0].config(text='3. Calculating Projections')
        self.label_status[4][0].config(text='4. Calculating Error')
        self.label_status[5][0].config(text='TOTAL')

        calib_button = tk.Button(self.m_frm[2], text="Calibrate")  # added reference to disable button while play
        calib_button.config(command=lambda: self.play(calib_button))
        calib_button.grid(row=0, column=0, sticky=tk.E + tk.W + tk.N)
        tk.Button(self.m_frm[2], text="Exit", command=self.popup.destroy).grid(row=0, column=1,
                                                                               sticky=tk.E + tk.W + tk.N)

        self.modify_play_popup()

        self.center()

    def play(self, calib_button):

        calib_button.config(state="disabled")
        self.bot[5].config(relief="sunken")
        self.bot[5].config(state="active")

        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar["value"] = 0

        # reset values status for clustering
        self.label_status[1][1].config(text='')
        self.label_status[1][2].config(text='')
        self.label_status[2][1].config(text='')
        self.label_status[2][2].config(text='')
        self.label_status[3][1].config(text='')
        self.label_status[3][2].config(text='')
        self.label_status[4][1].config(text='')
        self.label_status[4][2].config(text='')
        self.label_status[5][2].config(text='')

        self.popup.update()

        self.imgpoints = [[], []]
        self.objpoints = []

        for j in range(self.n_cameras):
            for feature in self.detected_features[j]:
                self.imgpoints[j].append(feature)
                if j == 0:
                    self.objpoints.append(self.object_pattern)

        flags_parameters = int(self.p_intrinsics_guess.get()) * cv2.CALIB_USE_INTRINSIC_GUESS + \
                           int(self.p_fix_point.get()) * cv2.CALIB_FIX_PRINCIPAL_POINT + \
                           int(self.p_fix_ratio.get()) * cv2.CALIB_FIX_ASPECT_RATIO + \
                           int(self.p_zero_tangent_distance.get()) * cv2.CALIB_ZERO_TANGENT_DIST

        logging.debug('%s', self.how_to_calibrate.get())

        if "Clustering" in self.how_to_calibrate.get():
            c_r = None
            c_k = None

            b_continue = True
            try:
                c_r = self.c_r.get()
                if c_r == 0:
                    self.label_msg[1].configure(text='R parameter muss be greater than zero')
                    b_continue = False
                elif c_r > self.n_total.get():
                    self.label_msg[1].configure(text='R parameter muss be smaller or equal than n')
                    b_continue = False
                else:
                    self.label_msg[1].configure(text='')
            except ValueError:
                self.label_msg[1].configure(text='R parameter can not be empty')
                b_continue = False
            try:
                c_k = self.c_k.get()
                if c_k == 0:
                    self.label_msg[0].configure(text='K parameter muss be greater than zero')
                    b_continue = False
                else:
                    self.label_msg[0].configure(text='')
            except ValueError:
                self.label_msg[0].configure(text='K parameter can not be empty')
                b_continue = False
            if not b_continue:
                self.bot[5].config(relief="raised")
                self.bot[5].config(state="normal")
                calib_button.config(state="active")
                return

            # n, number of all images
            self.samples, k = combination(len(self.objpoints), c_r, c_k)

            if k != c_k:
                self.c_k.set(k)
                self.label_msg[1].config(text='Number of groups changed from %d to %d (maximum possible)' % (c_k, k))
                self.popup.update()  # for updating while running other process

            time_play = chronometer()
            counter = 0

            C_array = []
            D_array = []
            self.R_array = []
            self.T_array = []

            self.fx_array = [[], []]
            self.fy_array = [[], []]
            self.cx_array = [[], []]
            self.cy_array = [[], []]
            self.k1_array = [[], []]
            self.k2_array = [[], []]
            self.k3_array = [[], []]
            self.k4_array = [[], []]
            self.k5_array = [[], []]
            self.RMS_array = []

            for s in self.samples:
                op = list(self.objpoints[i] for i in s)
                ip, c, d = [], [], []
                for j in range(self.n_cameras):
                    ip.append(list(self.imgpoints[j][i] for i in s))
                    c.append(np.eye(3, dtype=np.float32))
                    d.append(np.zeros((5, 1), dtype=np.float32))

                R = None
                T = None

                if self.m_stereo:
                    # move coordinates when images size are different
                    if self.size[0] != self.size[1]:
                        logging.debug('Different camera resolution')
                        ip = np.array(ip)
                        index_min = self.size.index(min(self.size))
                        index_max = self.size.index(max(self.size))
                        w_adj, h_adj = self.size[index_max]
                        w, h = self.size[index_min]
                        n_poses, n_points, _, _ = ip[index_min].shape
                        logging.debug('Transforming coordinates for camera %s', index_min + 1)
                        for pose in range(n_poses):
                            for point in range(n_points):
                                ip[index_min][pose][point] = np.sum(
                                    [ip[index_min][pose][point], [[(h_adj - h) / 2, (w_adj - w) / 2]]], axis=0)
                    width = max(self.size[0][1], self.size[1][1])
                    height = max(self.size[0][0], self.size[1][0])
                    rms, c[0], d[0], c[1], d[1], R, T, E, F = cv2.stereoCalibrate(op, ip[0], ip[1], c[0], d[0], c[1],
                                                                                  d[1], (width, height),
                                                                                  flags=flags_parameters)
                else:
                    width = self.size[0][1]
                    height = self.size[0][0]
                    rms, c[0], d[0], r, t = cv2.calibrateCamera(op, ip[0], (width, height), c[0], d[0],
                                                                flags=flags_parameters)
                logging.info('this is stereo rms error: %s', rms)

                if rms != 0:
                    counter += 1
                    # add to matrices
                    C_array.append(c)
                    D_array.append(d)
                    # add to iteration array
                    self.fx_array[0].append(c[0][0][0])
                    self.fy_array[0].append(c[0][1][1])
                    self.cx_array[0].append(c[0][0][2])
                    self.cy_array[0].append(c[0][1][2])
                    self.k1_array[0].append(d[0][0][0])
                    self.k2_array[0].append(d[0][1][0])
                    self.k3_array[0].append(d[0][2][0])
                    self.k4_array[0].append(d[0][3][0])
                    self.k5_array[0].append(d[0][4][0])
                    self.RMS_array.append(rms)
                    if self.m_stereo:
                        self.R_array.append(R)
                        self.T_array.append(T)
                        # add to iteration array
                        self.fx_array[1].append(c[1][0][0])
                        self.fy_array[1].append(c[1][1][1])
                        self.cx_array[1].append(c[1][0][2])
                        self.cy_array[1].append(c[1][1][2])
                        self.k1_array[1].append(d[1][0][0])
                        self.k2_array[1].append(d[1][1][0])
                        self.k3_array[1].append(d[1][2][0])
                        self.k4_array[1].append(d[1][3][0])
                        self.k5_array[1].append(d[1][4][0])

                    c_porcent = counter / float(len(self.samples))  # percentage of completion of process
                    self.progbar["value"] = c_porcent * 10.0
                    elapsed_time_1 = time_play.gettime()
                    self.lb_time.config(
                        text='Estimated time left: %0.5f seconds' % max(elapsed_time_1 * (1 / c_porcent - 1), 0))
                    self.style_pg.configure('text.Horizontal.TProgressbar',
                                            text='{:g} %'.format(c_porcent * 100.0))  # update label
                    self.popup.update()  # for updating while running other process

            self.label_status[1][1].config(text=u'\u2714')
            self.label_status[1][2].config(text='%0.5f' % elapsed_time_1)
            self.lb_time.config(text='')

            if len(C_array) > 0:
                self.camera_matrix = np.mean(np.array(C_array), axis=0)
                self.dist_coefs = np.mean(np.array(D_array), axis=0)
                self.dev_camera_matrix = np.std(np.array(C_array), axis=0)
                self.dev_dist_coefs = np.std(np.array(D_array), axis=0)
                if self.m_stereo:
                    self.R_stereo = averageMatrix(self.R_array)
                    self.T_stereo = np.mean(np.array(self.T_array), axis=0)
                    # Correction for cx and cy parameters
                    if self.size[0] != self.size[1]:
                        logging.debug('Correcting cx an cy for camera {0}'.format(index_min + 1))
                        self.camera_matrix[index_min][0][2] -= (h_adj - h) / 2
                        self.camera_matrix[index_min][1][2] -= (w_adj - w) / 2
            else:
                self.reset_camera_parameters()

            elapsed_time_2 = time_play.gettime()
            self.label_status[2][1].config(text=u'\u2714')
            self.label_status[2][2].config(text='%0.5f' % (elapsed_time_2 - elapsed_time_1))

            if np.any(self.camera_matrix[:, 0, 0] == 1):
                self.reset_camera_parameters()
                self.reset_error()
            else:
                logging.debug('Correct!')
                # Camera projections
                self.calculate_projection()
                elapsed_time_3 = time_play.gettime()
                self.label_status[3][1].config(text=u'\u2714')
                self.label_status[3][2].config(text='%0.5f' % (elapsed_time_3 - elapsed_time_2))
                # Calculate RMS error
                self.calculate_error()
                elapsed_time_4 = time_play.gettime()
                self.label_status[4][1].config(text=u'\u2714')
                self.label_status[4][2].config(text='%0.5f' % (elapsed_time_4 - elapsed_time_3))
                self.label_status[5][2].config(text='%0.5f' % elapsed_time_4)
                self.bot[8].config(state="normal")  # enable export parameters button
                self.bot[9].config(state="normal")  # enable export parameters button
                for e in self.rms:
                    if e == float("inf") or e == float("-inf"):
                        logging.warning('Error is too high')
                        # mark X for step 3 and 4
                        self.label_status[4][1].config(text=u'\u2718')
                        self.label_status[4][1].config(text=u'\u2718')
                        self.reset_camera_parameters()
                        self.reset_error()
                        self.bot[8].config(state="disable")  # enable export parameters button
                        self.bot[9].config(state="disable")  # enable export parameters button
                        break

        elif "Load" in self.how_to_calibrate.get():
            b_continue = True
            for j in range(2 * (self.n_cameras - 1) + 1):
                if '.txt' not in self.l_load_files[j].cget('text'):
                    if j == 2:
                        self.l_load_files[j].config(text='Missing Extrinsics', fg='green')
                        self.label_status_l[3][1].config(text=u'\u2718')
                        if b_continue:
                            # TODO: Adjust for different sizes in Load mode
                            width = max(self.size[0][1], self.size[1][1])
                            height = max(self.size[0][0], self.size[1][0])
                            rms, self.camera_matrix[0], self.dist_coefs[0], self.camera_matrix[1], self.dist_coefs[
                                1], R, T, E, F = cv2.stereoCalibrate(self.objpoints, self.imgpoints[0],
                                                                     self.imgpoints[1], self.camera_matrix[0],
                                                                     self.dist_coefs[0], self.camera_matrix[1],
                                                                     self.dist_coefs[1], (width, height),
                                                                     flags=cv2.CALIB_FIX_INTRINSIC + flags_parameters)
                            if rms != 0:
                                self.R_stereo = R
                                self.T_stereo = T
                                self.label_status_l[3][0].config(text='3. Calculating Extrinsics')
                                self.label_status_l[3][1].config(text=u'\u2714')
                            else:
                                logging.error('Calibration fails')
                                b_continue = False
                                self.label_status_l[j + 1][1].config(text=u'\u2718')
                                self.label_status_l[4][1].config(text=u'\u2718')
                    else:
                        self.l_load_files[j].config(text='File missing, please add', fg='red')
                        b_continue = False
                        self.label_status_l[j + 1][1].config(text=u'\u2718')
                        self.label_status_l[4][1].config(text=u'\u2718')

            if b_continue:
                for i in range(self.n_cameras):
                    if self.camera_matrix[i][0][0] == 0:  # Fx is zero only when reset
                        logging.debug('Data for camera %s not available', i + 1)
                        self.reset_camera_parameters()
                        self.reset_error()
                        break
                    if i == self.n_cameras - 1:
                        logging.debug('Correct!')
                        # Camera projections
                        self.calculate_projection()
                        # Calculate RMS error
                        self.calculate_error()
                        self.bot[8].config(state="normal")  # enable export parameters button
                        self.bot[9].config(state="normal")  # enable export parameters button

                for e in self.rms:
                    if e == float("inf") or e == float("-inf"):
                        logging.warning('Error is too high')
                        self.reset_camera_parameters()
                        self.reset_error()
                        self.label_status_l[4][1].config(text=u'\u2718')
                        self.bot[8].config(state="disable")  # enable export parameters button
                        self.bot[9].config(state="disable")  # enable export parameters button
                        break
                    else:
                        self.label_status_l[4][1].config(text=u'\u2714')

        self.update = True  # Update bool activated

        self.updateCameraParametersGUI()
        self.loadBarError([0, 1])
        calib_button.config(state="normal")
        self.bot[5].config(relief="raised")
        self.bot[5].config(state="normal")

    def calculate_projection(self, r=None, t=None):
        if t is None:
            t = []
        if r is None:
            r = []
        op = self.objpoints
        ip = self.imgpoints
        c = self.camera_matrix
        d = self.dist_coefs

        for j in range(self.n_cameras):
            self.projected[j] = []
            self.projected_stereo[(j + 1) % 2] = []
            for i in range(len(op)):
                if not r:
                    _, r1, t1, _ = cv2.solvePnPRansac(op[i], ip[j][i], c[j], d[j])
                else:
                    r1 = r[j][i]
                    t1 = t[j][i]

                imgpoints2, _ = cv2.projectPoints(op[i], r1, t1, c[j], d[j])
                self.projected[j].append(imgpoints2)

                if self.m_stereo:
                    r1 = cv2.Rodrigues(r1)[0]

                    if j == 1:
                        r2 = np.dot(np.linalg.inv(self.R_stereo), r1)
                        t2 = np.dot(np.linalg.inv(self.R_stereo), t1) - np.dot(np.linalg.inv(self.R_stereo),
                                                                               self.T_stereo)
                    else:
                        r2 = np.dot(self.R_stereo, r1)
                        t2 = np.dot(self.R_stereo, t1) + self.T_stereo

                    imgpoints2, _ = cv2.projectPoints(op[i], r2, t2, c[(j + 1) % 2], d[(j + 1) % 2])
                    self.projected_stereo[(j + 1) % 2].append(imgpoints2)

    def calculate_error(self):
        for j in range(self.n_cameras):
            ip = self.imgpoints[j]
            self.r_error_p[j] = []
            self.r_error[j] = []
            for i in range(len(ip)):
                if self.m_stereo:
                    imgpoints2 = self.projected_stereo[j][i]
                else:
                    imgpoints2 = self.projected[j][i]
                self.r_error[j].append(np.sqrt((np.power(np.linalg.norm(ip[i] - imgpoints2, axis=2), 2).mean())))
                self.r_error_p[j].append(np.linalg.norm(ip[i] - imgpoints2, axis=2))
                # Calculated value to update progressbar
                c_porcent = (j * len(ip) + i + 1) / float(self.n_cameras * len(ip))
                self.progbar["value"] = c_porcent * 10.0
                self.style_pg.configure('text.Horizontal.TProgressbar',
                                        text='{:g} %'.format(c_porcent * 100.0))  # update label
                self.popup.update()  # for updating while running other process
                # update rms when the error for all the images is calculated
                if len(self.r_error[j]) == len(ip):
                    logging.info("Updating RMS for camera %d", j + 1)
                    self.rms[j] = np.sqrt(np.sum(np.square(self.r_error[j])) / len(self.r_error[j]))
                    if j == 1:
                        self.rms[2] = np.sqrt(
                            np.sum(np.square(self.r_error[0] + self.r_error[1])) / len(
                                self.r_error[0] + self.r_error[1]))

    def updateBarError(self, k):
        '''
        Function to update the color of the bars in the bar charts
        depending of the selection
        The selected bar is red, the others are blue
        '''
        if k == 0:
            index = self.index.get()
        else:
            index = self.index_corner
        for j in range(self.n_cameras):
            # TODO maybe save old index?
            if self.r_error[j]:
                for i in range(len(self.dr[k][j])):
                    if i == index:
                        self.dr[k][j][i].set_color('r')
                    else:
                        self.dr[k][j][i].set_color('b')
                self.bar[k][j].draw()

    def loadBarError(self, r_up):
        '''
        Function to update error bar chart
        '''
        xlabel_names = ['Images', 'Features']
        title_names = ['RMS Reprojection Error', 'Pixel Distance Error']
        factor_width = [10, 7]
        for k in r_up:
            self.dr[k] = []
            for j in range(self.n_cameras):
                self.ax[k][j].clear()
                data = None
                m_error = None
                index = None
                # getting error data depending of the chart type (RMS reprojection error or pixel distance error)
                if k == 0:
                    if self.r_error[j]:
                        data = self.r_error[j]
                        m_error = np.mean(data)
                        index = self.index.get()
                else:
                    if self.r_error_p[j]:
                        data = self.r_error_p[j][self.index.get()].T[0]  # converted to size-1 arrays
                        index = self.index_corner

                if data is not None:
                    ## defining bars of the chart##
                    ind = np.arange(len(data))
                    # height of bars correspond to the list of data errors
                    rects = self.ax[k][j].bar(ind, data, align='center')
                    self.dr[k].append([])
                    # set bars color according to index of selected image
                    for rect, i in zip(rects, ind):
                        rect.set_label(i + 1)
                        if i == index:
                            rect.set_color('r')
                        else:
                            rect.set_color('b')
                        self.dr[k][j].append(rect)
                    # set tick of labels for the x and y axes
                    self.ax[k][j].set_xticks(ind)
                    if self.ax[k][j].patches:
                        self.ax[k][j].set_xticklabels(tuple(ind + 1), rotation=65,
                                                      size=self.ax[k][j].patches[0].get_width() * factor_width[k])
                        # draw to update, necessary to keep changes
                        self.bar[k][j].draw()
                        self.ax[k][j].set_yticklabels([item.get_text() for item in self.ax[k][j].get_yticklabels()],
                                                      size=10)
                    # create dashed line for RMS reprojection mean
                    if k == 0:
                        self.ax[k][j].axhline(y=m_error, color='k', linestyle='--', label="z")
                        handles, _ = self.ax[k][j].get_legend_handles_labels()
                        self.ax[k][j].legend(handles[0:1], ['Mean RMS Reprojection Error is: %.5f' % m_error],
                                             loc='lower center',
                                             prop={'size': self.ax[k][j].patches[0].get_width() * 15})
                    # inform about the not updated of the chart when applies
                    if self.update:
                        self.ax[k][j].set_title(title_names[k], fontsize=10)
                    else:
                        self.ax[k][j].set_title(title_names[k] + ' (Not Updated)', color='r', fontsize=10)
                # for empty error data, only set the chart titles
                else:
                    self.ax[k][j].set_title(title_names[k], fontsize=10)
                # set names of labels for the x and y axes
                self.ax[k][j].set_xlabel(xlabel_names[k], fontsize=7)
                self.ax[k][j].set_ylabel('Pixels', fontsize=7)
                # set size chart and re draw the bars
                self.ax[k][j].autoscale(tight=True)
                self.f[k][j].tight_layout()  # Adjust size
                self.bar[k][j].draw()

    def on_press(self, event, i, j):
        '''
        Function to handle the event of pressing over one of the bar in the chart to update selected pose
        j is camera, i is graphic #TODO: Maybe change logic? (easier to understand...)
        '''
        # checks if a calibration has already succeed
        if self.camera_matrix[0][0][0] != 0:  # Fx is zero only when reset
            b_continue = False
            for rect in self.dr[i][j]:
                if event.inaxes == rect.axes:
                    b_continue = True
                    break
            if b_continue:
                # compares if the click is inside the bar, for each bar in the chart
                for rect in self.dr[i][j]:
                    contains, attrd = rect.contains(event)
                    # update for the selected bar
                    if contains:
                        self.updateSelectionperclick(int(rect.get_label()), i)
                        break

    def updateCameraParametersGUI(self):
        '''
        Function to update all the labels values from the calculated parameters in the calibration
        '''
        if self.n_cameras == 0:
            r_cameras1 = 2
            r_cameras2 = 3
        else:
            r_cameras1 = self.n_cameras
            r_cameras2 = int(self.m_stereo) * 3
        for j in range(r_cameras1):
            float2StringVar(self.fx[j], self.camera_matrix[j][0][0])
            float2StringVar(self.fy[j], self.camera_matrix[j][1][1])
            float2StringVar(self.cx[j], self.camera_matrix[j][0][2])
            float2StringVar(self.cy[j], self.camera_matrix[j][1][2])
            float2StringVar(self.sd_fx[j], self.dev_camera_matrix[j][0][0])
            float2StringVar(self.sd_fy[j], self.dev_camera_matrix[j][1][1])
            float2StringVar(self.sd_cx[j], self.dev_camera_matrix[j][0][2])
            float2StringVar(self.sd_cy[j], self.dev_camera_matrix[j][1][2])
            float2StringVar(self.k1[j], self.dist_coefs[j][0][0])
            float2StringVar(self.k2[j], self.dist_coefs[j][1][0])
            float2StringVar(self.k3[j], self.dist_coefs[j][2][0])
            float2StringVar(self.k4[j], self.dist_coefs[j][3][0])
            float2StringVar(self.k5[j], self.dist_coefs[j][4][0])
            float2StringVar(self.sd_k1[j], self.dev_dist_coefs[j][0][0])
            float2StringVar(self.sd_k2[j], self.dev_dist_coefs[j][1][0])
            float2StringVar(self.sd_k3[j], self.dev_dist_coefs[j][2][0])
            float2StringVar(self.sd_k4[j], self.dev_dist_coefs[j][3][0])
            float2StringVar(self.sd_k5[j], self.dev_dist_coefs[j][4][0])
            float2StringVar(self.rms_tk[j], self.rms[j])
        for j in range(r_cameras2):
            if j == 2:
                float2StringVar(self.rms_tk[j], self.rms[j])
            float2StringVar(self.T_tk[j], self.T_stereo[j][0])
            for i in range(3):
                float2StringVar(self.R_tk[i][j], self.R_stereo[i][j])

    def del_single(self):
        '''
        Function to delete with Del key one image
        '''
        # get current index
        index = self.listbox.curselection()
        if index:
            self.update = False
            # delete for each selected image the path, original image, features, projections, and erros from the corresponding list
            for j in range(self.n_cameras):
                del self.paths[j][index[0]]
                del self.img_original[j][index[0]]
                del self.detected_features[j][index[0]]
                if self.projected[j]:  # check if projection data exists
                    del self.projected[j][index[0]]
                if j == 1:
                    if self.projected_stereo[0]:  # check if stereo projection data exists
                        del self.projected_stereo[0][index[0]]
                        del self.projected_stereo[1][index[0]]
                # barchar
                if self.r_error[j]:  # check if reprojection error data exists
                    del self.r_error[j][index[0]]
                    del self.r_error_p[j][index[0]]
            # update number of total poses
            self.n_total.set(self.n_total.get() - 1)
            # check if there is already a selected image in data browser
            if index[0]:
                # for the case the last image is deleted, update the data browser selection to the penultimate pose
                if index[0] == self.n_total.get():
                    self.index.set(index[0] - 1)
                    self.listbox.select_set(index[0] - 1)
                    self.listbox.yview(index[0] - 1)
                else:
                    self.index.set(index[0])
                    self.listbox.yview(index[0])
            else:
                # if there are images, set the first one as selected
                if self.n_total.get():
                    self.index.set(0)
                else:
                    self.bot[3].config(state="disable")  # disable zoom in button
                    self.bot[4].config(state="disable")  # disable zoom in button
                    self.bot[5].config(state="disable")  # disable run calibration button
                    self.index.set(-1)
            self.loadBarError([0, 1])  # uses self.index which is updated in updatepicture

    def del_all(self):
        '''
        Function to delete all the session
        '''
        # enable the add session button
        self.bot[0].config(state="active")
        # disable the other toolbar buttons
        for i in range(1, len(self.bot)):
            self.bot[i].config(state="disable")
        self.popup.destroy()
        # reset variables
        self.reset_camera_parameters()
        self.updateCameraParametersGUI()
        self.reset_error()
        self.loadBarError([0, 1])
        self.initializeVariables()
        self.index.set(-1)
        # set GUI for one camera
        self.frm[4].grid_forget()
        self.frm[5].grid_forget()
        self.frm[6].grid_forget()
        self.frm[8].grid_forget()
        self.frm[10].grid_forget()

    def popupmsg_deleting(self):
        '''
        Function to create popup for deleting confirmation
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title("Delete session")
        tk.Label(self.popup, text='\nAre you sure you want to delete the session?\n').grid(row=0, column=0,
                                                                                           columnspan=2,
                                                                                           sticky=tk.W + tk.E)
        tk.Button(self.popup, text="Yes", command=self.del_all).grid(row=1, column=0, sticky=tk.W + tk.E)
        tk.Button(self.popup, text="Cancel", command=self.popup.destroy).grid(row=1, column=1, sticky=tk.W + tk.E)

        self.center()

    def exportCalibrationParameters(self):
        '''
        Function to export the calibration parameters
        '''
        default_filenames = ['intrinsics_first_camera', 'intrinsics_second_camera', 'extrinsics']
        for j in range(2 * int(self.m_stereo) + 1):
            filename = tk.filedialog.asksaveasfilename(initialfile=default_filenames[j], defaultextension='.txt',
                                                       filetypes=[('Text files', '*.txt')])
            if filename != '':
                f = open(filename, 'w')
                if j < 2:
                    c_string = datastring.instrinsic2string(self.camera_matrix[j], self.dist_coefs[j])
                    f.write(c_string)
                else:
                    c_string = datastring.extrinsic2string(self.R_stereo, self.T_stereo)
                    f.write(c_string)
                f.close()
            else:
                return

    def exportCalibrationParametersIteration(self):
        '''
        Function to export calibration results per Iteration
        '''
        logging.info('exporting results per calibration')

        t_choose = 'Please select a folder'
        path_folder = tk.filedialog.askdirectory(parent=self.master, title=t_choose)

        if path_folder != '':
            for j in range(self.n_cameras):
                filename = '/fx_cam_' + str(j + 1) + '.txt'
                np.array(self.fx_array[j]).tofile(path_folder + filename, "\n")
                filename = '/fy_cam_' + str(j + 1) + '.txt'
                np.array(self.fy_array[j]).tofile(path_folder + filename, "\n")
                filename = '/cx_cam_' + str(j + 1) + '.txt'
                np.array(self.cx_array[j]).tofile(path_folder + filename, "\n")
                filename = '/cy_cam_' + str(j + 1) + '.txt'
                np.array(self.cy_array[j]).tofile(path_folder + filename, "\n")
                filename = '/k1_cam_' + str(j + 1) + '.txt'
                np.array(self.k1_array[j]).tofile(path_folder + filename, "\n")
                filename = '/k2_cam_' + str(j + 1) + '.txt'
                np.array(self.k2_array[j]).tofile(path_folder + filename, "\n")
                filename = '/k3_cam_' + str(j + 1) + '.txt'
                np.array(self.k3_array[j]).tofile(path_folder + filename, "\n")
                filename = '/k4_cam_' + str(j + 1) + '.txt'
                np.array(self.k4_array[j]).tofile(path_folder + filename, "\n")
                filename = '/k5_cam_' + str(j + 1) + '.txt'
                np.array(self.k5_array[j]).tofile(path_folder + filename, "\n")
                if j == 1:
                    filename = '/rotation.txt'
                    f = open(path_folder + filename, 'w')
                    for r in self.R_array:
                        f.write(','.join(str(e) for e in r) + '\n')
                    f.close()
                    filename = '/translation.txt'
                    f = open(path_folder + filename, 'w')
                    for t in self.T_array:
                        f.write(','.join(str(e[0]) for e in t) + '\n')
                    f.close()

            filename = '/rms' + '.txt'
            np.array(self.RMS_array).tofile(path_folder + filename, "\n")
            filename = '/samples' + '.txt'
            f = open(path_folder + filename, 'w')
            for s in self.samples:
                f.write("[")
                for j in range(self.n_cameras):
                    if j == 1:
                        f.write(",")
                    f.write("[")
                    l_paths_s = list(self.paths[j][i] for i in s)
                    f.write(','.join(str(e) for e in l_paths_s))
                    f.write("]")
                f.write("]")
                f.write("\n")
            f.close()
