import logging
import os
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import toolboxClass.miscTools.hint_label as hl

logging.basicConfig(level=logging.ERROR)

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240


class Mixin:
    def initializeVariables(self):
        """Function to define variables that has to be reinitialized each time a session is deleted."""
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
        self.index_corner.set(0)
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

        # variable for selecting nearest image per click function
        self.polygons = []

        # variable for importing files
        self.continue_importing = True
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
        # coordinates variable for moving features
        self.new_coord_feature = [[], []]

    def center(self):
        """Function to center popups and disable the main windows."""

        self.master.update_idletasks()
        width = self.popup.winfo_reqwidth()
        height = self.popup.winfo_reqheight()
        x = self.master.winfo_rootx() \
            + (self.master.winfo_width() // 2) \
            - (width // 2)
        y = self.master.winfo_rooty() \
            + (self.master.winfo_height() // 2) \
            - (height // 2)
        self.popup.geometry('+%d+%d' % (x, y))
        if self.master.winfo_viewable():
            self.popup.transient(self.master)
        if self.popup.state() != 'normal':
            self.popup.deiconify()  # become visible now
            self.popup.wait_visibility()
            self.popup.grab_set()  # interact only with popup

    def initialize_GUI_variables(self):
        """Function to initialize GUI related variables at the beginning."""
        # buttons
        self.btn_start = None
        self.btn_add_file = None
        self.btn_add_folder = None
        self.btn_zoom_more = None
        self.btn_zoom_less = None
        self.btn_locate = None
        self.btn_play = None
        self.btn_delete = None
        self.btn_settings = None
        self.btn_export = None
        self.btn_export2 = None
        self.btn_move_feature = None
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
        self.index_corner = tk.IntVar()
        # method for calibration variable
        self.how_to_calibrate = tk.StringVar()
        self.how_to_calibrate.set(self._(u'Clustering calculation'))
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
        self.R_tk = [[tk.StringVar(), tk.StringVar(), tk.StringVar()],
                     [tk.StringVar(), tk.StringVar(), tk.StringVar()],
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
        # Progressbar https://stackoverflow.com/questions/47896881/
        #                    progressbar-with-percentage-label
        self.style_pg = ttk.Style(self.master)
        # add label in the layout
        layout = [('Horizontal.Progressbar.trough',
                   {'children': [('Horizontal.Progressbar.pbar',
                                  {'side': 'left',
                                   'sticky': 'ns'})],
                    'sticky': 'nswe'}),
                  ('Horizontal.Progressbar.label', {'sticky': ''})]
        self.style_pg.layout('text.Horizontal.TProgressbar', layout)

    def add_session(self):
        """Function to add session after the given parameters are correct.

        Creates object_pattern according to the selected pattern type
        Enables and disables the corresponding buttons
        Adjust the GUI for a single/stereo mode.
        """
        if self._(u'Images') in self.pattern_load.get():
            for j in range(3):
                if self.label_msg[j].cget('text'):
                    return
        else:
            for j in range(3, 5):
                if self.label_msg[j].cget('text'):
                    return
            # if 3d points aren't initialized
            if self.object_pattern is None:
                return
            elif not self.object_pattern.any():
                return

        # checks
        if self._(u'Images') in self.pattern_load.get():
            # creates object from Chessboard pattern
            if self._(u'Chessboard') in self.pattern_type.get():
                self.object_pattern = np.zeros((self.p_width
                                                * self.p_height, 3),
                                               np.float32)
                grid = np.mgrid[0:self.p_height, 0:self.p_width] \
                         .T.reshape(-1, 2) * self.f_distance
                self.object_pattern[:, 0] = -grid[:, 1]
                self.object_pattern[:, 1] = grid[:, 0]
            # creates object from Grid pattern
            elif self._(u'Asymmetric Grid') in self.pattern_type.get():
                pattern_size = (self.p_height, self.p_width)
                self.object_pattern = np.zeros((np.prod(pattern_size), 3),
                                               np.float32)
                self.object_pattern[:, :2] = np.fliplr(np.indices(pattern_size)
                                                       .T.reshape(-1, 2))
                for i in range(np.prod(pattern_size)):
                    if self.object_pattern[i, 0] % 2 == 0:
                        self.object_pattern[i, 1] = self.object_pattern[i, 1] \
                                                   * self.f_distance
                        self.object_pattern[i, 0] = self.object_pattern[i, 0] \
                            * self.f_distance / 2
                    else:
                        self.object_pattern[i, 1] = self.object_pattern[i, 1] \
                                                   * self.f_distance \
                                                   + self.f_distance / 2
                        self.object_pattern[i, 0] = self.object_pattern[i, 0] \
                            * self.f_distance / 2
            # returns for led pattern (not yet implemented)
            elif self._(u'Symmetric Grid') in self.pattern_type.get():
                self.object_pattern = np.zeros((self.p_width
                                                * self.p_height, 3),
                                               np.float32)
                grid = np.mgrid[0:self.p_height, 0:self.p_width]\
                         .T.reshape(-1, 2) * self.f_distance
                self.object_pattern[:, 0] = -grid[:, 1]
                self.object_pattern[:, 1] = grid[:, 0]

            # set default image type
            self.valid_files = ['.jpg', '.png']
            self.ftypes = [(self._(u'All image files'),
                            tuple(x + y for x, y in
                                  zip(('*', '*'), tuple(self.valid_files)))), ]
        else:
            self.valid_files = ['.txt']
            self.ftypes = [(self._(u'Text files'), '*.txt')]
            # Disable tab for original image
            self.tabControl[0].tab(0, state='disable')

        self.m_stereo = self.mode_stereo.get()

        self.popup.destroy()

        self.btn_start.config(state='disable', relief='raised')  # disable add session button
        self.btn_add_folder.config(state='normal')  # enable adding images per folder
        self.btn_zoom_more.config(state='disable')  # disable zoom in button
        self.btn_zoom_less.config(state='disable')  # disable zoom out button
        self.btn_locate.config(state='disable')  # disable locate button
        self.btn_play.config(state='disable')  # disable run calibration button
        self.btn_delete.config(state='normal')  # enable delete session button
        self.btn_settings.config(state='normal')  # enable settings button
        self.btn_export.config(state='disable')  # disable export button
        self.btn_export2.config(state='disable')  # disable export button

        if self.m_stereo:
            self.n_cameras = 2
            # disable adding images per file button
            self.btn_add_file.config(state='disable')
            # set GUI for two camera
            # frame for extrinsics
            self.frm[4].grid(row=1, column=3, sticky=tk.N + tk.S)
            # frame for intrinsics second camera
            self.frm[5].grid(row=1, column=4, sticky=tk.N + tk.S)
            # frame for pictures second camera
            self.frm[6].grid(row=1, column=5, sticky=tk.N + tk.S)
            # frame for second grafic first camera
            self.frm[8].grid(row=0, column=1)
            # frame for second grafic second camera
            self.frm[10].grid(row=1, column=1)
            # Enable tab for extrinsic Reprojection
            self.tabControl[0].tab(len(self.list_panel[0])-1, state='normal')
        else:
            self.n_cameras = 1
            # set GUI for one camera
            self.frm[4].grid_forget()
            self.frm[5].grid_forget()
            self.frm[6].grid_forget()
            self.frm[8].grid_forget()
            self.frm[10].grid_forget()
            self.btn_add_file.config(state='normal')  # enable adding per file
            # Disable tab for extrinsic Reprojection
            self.tabControl[0].tab(len(self.list_panel[0])-1, state='disable')

    def traces_GUI(self):
        """Function to trace all the changes in tkinter variables."""
        # link changes in number of poses for updating function
        self.n_total.trace('w', self.update_added_deleted)
        # link changes in width and height to plotting function
        self.pattern_type.trace_id \
            = self.pattern_type.trace('w', self.pattern_default)
        self.image_width.trace_id \
            = self.image_width.trace('w', self.check_errors_and_plot)
        self.image_height.trace_id \
            = self.image_height.trace('w', self.check_errors_and_plot)
        self.pattern_width.trace_id \
            = self.pattern_width.trace('w', self.check_errors_and_plot)
        self.pattern_height.trace_id \
            = self.pattern_height.trace('w', self.check_errors_and_plot)
        self.feature_distance.trace_id \
            = self.feature_distance.trace('w', self.check_errors_and_plot)
        # link changes in selected pose to update GUI
        self.index.trace('w', self.update_index_corner)
        # camera parameters
        self.fx[0].trace('w', self.updatePicture)
        # link changes when selecting index
        self.select_feature.bind('<<ComboboxSelected>>', self.update_index_corner)

    def initUI(self, *args, **kwargs):
        """Function to create toolbar, data browser, panel of tabs of images,error charts and calculated parameters visualization."""
        # frames definition and positioning ##
        self.frm = []
        for i in range(7):
            self.frm.append(tk.Frame(self.master))
            self.frm[-1].rowconfigure(0, weight=1)
            self.frm[-1].columnconfigure(0, weight=1)
            # self.frm[-1].propagate(0)
        # frame for toolbar
        self.frm[0].grid(row=0, column=0, columnspan=6, sticky=tk.W)
        # frame for Listbox
        self.frm[1].grid(row=1, column=0, rowspan=3, sticky='nswe')
        # set frame width 10% of screen width
        self.frm[1].configure(width=self.screen_width * 0.1)

        # frame for pictures first camera
        self.frm[2].grid(row=1, column=1, sticky=tk.N + tk.S)
        # set frame width 28% of screen width
        self.frm[2].configure(width=self.screen_width * 0.28 * 0.9,
                              height=(self.screen_height - 25) / 2)

        # frame for intrinsics first camera
        self.frm[3].grid(row=1, column=2, sticky=tk.N + tk.S)
        # set frame width 15% of screen width
        self.frm[3].configure(width=self.screen_width * 0.15 * 0.9,
                              height=(self.screen_height - 25) / 2)

        # frame for extrinsics
        self.frm[4].grid(row=1, column=3, sticky=tk.N + tk.S)
        # set frame width 14% of screen width
        self.frm[4].configure(width=self.screen_width * 0.14 * 0.9,
                              height=(self.screen_height - 25) / 2)

        # frame for intrinsics second camera
        self.frm[5].grid(row=1, column=4, sticky=tk.N + tk.S)
        # set frame width 15% of screen width
        self.frm[5].configure(width=self.screen_width * 0.15 * 0.9,
                              height=(self.screen_height - 25) / 2)

        # frame for pictures second camera
        self.frm[6].grid(row=1, column=5, sticky=tk.N + tk.S)
        # set frame width 28% of screen width
        self.frm[6].configure(width=self.screen_width * 0.28 * 0.9,
                              height=(self.screen_height - 25) / 2)

        sub_frame_g = tk.Frame(self.master)
        sub_frame_g.grid(row=2, column=1, columnspan=5, sticky=tk.W + tk.E)
        for i in range(4):
            self.frm.append(tk.Frame(sub_frame_g))
            self.frm[-1].rowconfigure(0, weight=1)
            self.frm[-1].columnconfigure(0, weight=1)
            # self.frm[-1].propagate(0)

        # frame for first grafic first camera
        self.frm[7].grid(row=0, column=0)
        # frame for first grafic second camera
        self.frm[8].grid(row=0, column=1)
        # frame for second grafic first camera
        self.frm[9].grid(row=1, column=0)
        # frame for second grafic second camera
        self.frm[10].grid(row=1, column=1)

        self.frm[1].bind('<Enter>', lambda event,
                         message=self._(u'The data browser shows all images '
                                        u'used for calibration. To see an '
                                        u'image on the right, click on its '
                                        u'name in the list.'):
                         self.entry_mouse_enter(event, message))
        self.frm[3].bind('<Enter>', lambda event,
                         message=self._(u'Mean results and the standard '
                                        u'deviation of the first cameras '
                                        u'intrinsics.'):
                         self.entry_mouse_enter(event, message))
        self.frm[4].bind('<Enter>', lambda event,
                         message=self._(u'Mean results and the standard '
                                        u'deviation of the stereo '
                                        u'extrinsics.'):
                         self.entry_mouse_enter(event, message))
        self.frm[5].bind('<Enter>', lambda event,
                         message=self._(u'Mean results and the standard '
                                        u'deviation of the second cameras '
                                        u'intrinsics.'):
                         self.entry_mouse_enter(event, message))
        self.frm[7].bind('<Enter>', lambda event,
                         message=self._(u'RMS Diagramm over all images of the '
                                        u'first camera. To view an image, '
                                        u'select its error block.'):
                         self.entry_mouse_enter(event, message))
        self.frm[8].bind('<Enter>', lambda event,
                         message=self._(u'RMS Diagramm over all images of the '
                                        u'second camera. To view an image, '
                                        u'select its error block.'):
                         self.entry_mouse_enter(event, message))
        self.frm[9].bind('<Enter>', lambda event,
                         message=self._(u'Pixel distance error of the above '
                                        u'selected image over all of its '
                                        u'features. By selecting an error '
                                        u'block, the feature is higlighted in '
                                        u'the intrinsic and extrinsic tab.'):
                         self.entry_mouse_enter(event, message))
        self.frm[10].bind('<Enter>', lambda event,
                          message=self._(u'Pixel distance error of the above '
                                         u'selected image over all of its '
                                         u'features. By selecting an error '
                                         u'block, the feature is higlighted '
                                         u'in the intrinsic and extrinsic '
                                         u'tab.'):
                          self.entry_mouse_enter(event, message))
        self.frm[1].bind('<Leave>', self.entry_mouse_leave)
        self.frm[3].bind('<Leave>', self.entry_mouse_leave)
        self.frm[4].bind('<Leave>', self.entry_mouse_leave)
        self.frm[5].bind('<Leave>', self.entry_mouse_leave)
        self.frm[7].bind('<Leave>', self.entry_mouse_leave)
        self.frm[8].bind('<Leave>', self.entry_mouse_leave)
        self.frm[9].bind('<Leave>', self.entry_mouse_leave)
        self.frm[10].bind('<Leave>', self.entry_mouse_leave)

        # loading icons for toolbar #
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
        path_locate = os.getcwd() + '/icons/locate.png'
        path_move_feature = os.getcwd() + '/icons/movefeature.png'
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
        self.icono_locate = tk.PhotoImage(file=path_locate)
        self.icono_move_feature = tk.PhotoImage(file=path_move_feature)

        # toolbar configuration #
        # icons assignment and trace of functions to the buttons
        self.btn_start = tk.Button(self.frm[0], image=self.icono_plus, command=self.add_session_popup)
        self.btn_add_file = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_open,
                                      command=lambda: self.add_file('p'))
        self.btn_add_folder = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_folder,
                                        command=lambda: self.add_file('f'))
        self.btn_zoom_more = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_zoommore)
        self.btn_zoom_less = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_zoomless)
        self.btn_zoom_more.config(command=lambda: self.toggle_zoom_buttons(self.btn_zoom_more, self.btn_zoom_less))
        self.btn_zoom_less.config(command=lambda: self.toggle_zoom_buttons(self.btn_zoom_less, self.btn_zoom_more))
        self.btn_move_feature = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_move_feature,
                                          command=self.move_feature)
        self.select_feature = ttk.Combobox(self.frm[0], state='readonly', textvariable=self.index_corner,
                                           values=[-1, -2, -3, -4], width=3)
        self.btn_change_feature = tk.Button(self.frm[0], text='Change', command=self.popupmsg_changes)
        self.btn_locate = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_locate, command=self.clickpoint_to_image)
        self.btn_play = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_play, command=self.play_popup)
        self.btn_delete = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_delete,
                                    command=self.popupmsg_deleting)
        self.btn_settings = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_settings,
                                      command=self.popup_configuration)
        self.btn_export = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_export,
                                    command=self.exportCalibrationParameters)
        self.btn_export2 = tk.Button(self.frm[0], state=tk.DISABLED, image=self.icono_export2,
                                     command=self.exportCalibrationParametersIteration)

        # Binding the hint boxes to the buttons
        self.btn_start.bind('<Enter>', lambda event, message=self._(u'Start a new session.'): self.entry_mouse_enter(event, message))
        self.btn_add_file.bind('<Enter>', lambda event, message=self._(u'Adding single image files.'): self.entry_mouse_enter(event, message))
        self.btn_add_folder.bind('<Enter>', lambda event, message=self._(u'Adding image files of a folder.'): self.entry_mouse_enter(event, message))
        self.btn_zoom_more.bind('<Enter>', lambda event, message=self._(u'Activate zoom-in function for ' u'images.'): self.entry_mouse_enter(event, message))
        self.btn_zoom_less.bind('<Enter>', lambda event, message=self._(u'Activate zoom-out function for ' u'images.'): self.entry_mouse_enter(event, message))
        self.btn_locate.bind('<Enter>', lambda event, message=self._(u'Activate locating image by click'): self.entry_mouse_enter(event, message))
        self.btn_play.bind('<Enter>', lambda event, message=self._(u'Start a calibration run.'): self.entry_mouse_enter(event, message))
        self.btn_delete.bind('<Enter>', lambda event, message=self._(u'Delete the active session.'): self.entry_mouse_enter(event, message))
        self.btn_settings.bind('<Enter>', lambda event, message=self._(u'Set different calibration flags.'): self.entry_mouse_enter(event, message))
        self.btn_export.bind('<Enter>', lambda event, message=self._(u'Export the mean parameters.'): self.entry_mouse_enter(event, message))
        self.btn_export2.bind('<Enter>', lambda event, message=self._(u'Export the parameters of every ' u'subsample.'): self.entry_mouse_enter(event, message))

        self.btn_start.bind('<Leave>', self.entry_mouse_leave)
        self.btn_add_file.bind('<Leave>', self.entry_mouse_leave)
        self.btn_add_folder.bind('<Leave>', self.entry_mouse_leave)
        self.btn_zoom_more.bind('<Leave>', self.entry_mouse_leave)
        self.btn_zoom_less.bind('<Leave>', self.entry_mouse_leave)
        self.btn_locate.bind('<Leave>', self.entry_mouse_leave)
        self.btn_play.bind('<Leave>', self.entry_mouse_leave)
        self.btn_delete.bind('<Leave>', self.entry_mouse_leave)
        self.btn_settings.bind('<Leave>', self.entry_mouse_leave)
        self.btn_export.bind('<Leave>', self.entry_mouse_leave)
        self.btn_export2.bind('<Leave>', self.entry_mouse_leave)
        # TODO: Write text for each infobox!

        # buttons positioning
        self.btn_start.grid(row=0, column=0, sticky=tk.W)
        self.btn_add_file.grid(row=0, column=1, sticky=tk.W)
        self.btn_add_folder.grid(row=0, column=2, sticky=tk.W)
        self.btn_zoom_more.grid(row=0, column=3, sticky=tk.W)
        self.btn_zoom_less.grid(row=0, column=4, sticky=tk.W)
        self.btn_move_feature.grid(row=0, column=5, sticky=tk.W)
        self.btn_locate.grid(row=0, column=8, sticky=tk.W)
        self.btn_play.grid(row=0, column=9, sticky=tk.W)
        self.btn_delete.grid(row=0, column=10, sticky=tk.W)
        self.btn_settings.grid(row=0, column=11, sticky=tk.W)
        self.btn_export.grid(row=0, column=12, sticky=tk.W)
        self.btn_export2.grid(row=0, column=13, sticky=tk.W)

        # scrollbar and listbox initialization #
        tk.Label(self.frm[1], text=self._(u'Data Browser')).pack()
        sb = tk.Scrollbar(self.frm[1], orient='vertical')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(self.frm[1], yscrollcommand=sb.set)
        self.listbox.pack(expand=True, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.updateSelection)
        sb.config(command=self.listbox.yview)

        # variables initialization for tabs of images and camera #
        # parameters visualization #
        # tab control for initialization and positioning
        self.tabControl = []
        # list of panels for visualization -
        # - list of panels shape is [camera][images] - -
        # - - where posibles values are for camera: 0 or 1, and for
        # images 0,1,2,3 (original, feature,cloud map, intrinisc, extrinsic)
        self.list_panel = []
        self.list_image_on_panel = []
        self.c_labels = [[], [], []]
        tab_names = [self._(u'Original'),
                     self._(u'Features'),
                     self._(u'Cloud Map'),
                     self._(u'Intrinsic'),
                     self._(u'Extrinsic')]

        # panel for pictures definition
        for j in range(2):
            sub_frame = self.frm[2 + 4 * j]
            self.list_panel.append([])
            self.list_image_on_panel.append([])
            self.tabControl.append(ttk.Notebook(sub_frame))
            # initialization and positioning of
            # labels for visualization of intrinsics
            sub_frame = self.frm[3 + 2 * j]
            for p in range(15):
                for q in range(3):
                    if p == 0 or p == 6 or p == 13:
                        if q == 0:
                            self.c_labels[j].append(tk.Label(sub_frame,
                                                             font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1,
                                                      columnspan=3,
                                                      sticky=tk.N + tk.S)
                    elif p == 14:
                        if q == 0:
                            self.c_labels[j].append(tk.Label(sub_frame,
                                                             font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1 + q,
                                                      sticky=tk.N + tk.S)
                        elif q == 1:
                            self.c_labels[j].append(tk.Label(sub_frame,
                                                             font=('', 8)))
                            self.c_labels[j][-1].grid(row=p, column=1 + q,
                                                      columnspan=3,
                                                      sticky=tk.N + tk.S)
                    else:
                        self.c_labels[j].append(tk.Label(sub_frame,
                                                         font=('', 8)))
                        self.c_labels[j][-1].grid(row=p + 0, column=1 + q,
                                                  sticky=tk.N + tk.S)
            # positioning of images in panels and trace of click event for zoom
            for i in range(5):
                tab = ttk.Frame(self.tabControl[j])
                self.tabControl[j].add(tab, text=tab_names[i])
                self.list_panel[j].append(tk.Canvas(tab,
                                                    width=DEFAULT_WIDTH,
                                                    height=DEFAULT_HEIGHT))
                self.list_panel[j][i].grid(row=0, column=0,
                                           sticky=tk.E + tk.W + tk.N)
                self.list_panel[j][i].bind('<Button-1>', lambda e,a=j: self.click_to_zoom(e, a))
                self.list_panel[j][i].bind('<Button-4>',
                                           lambda e:
                                               self.scroll_to_zoom('m', e))
                self.list_panel[j][i].bind('<Button-5>',
                                           lambda e:
                                               self.scroll_to_zoom('l', e))
                self.list_image_on_panel[j].append(
                    self.list_panel[j][i].create_image(0, 0,
                                                       anchor=tk.N + tk.W,
                                                       image=None))
            self.tabControl[j].grid(row=0, column=0,
                                    rowspan=13, sticky=tk.N + tk.S)

            self.list_panel[j][0]\
                .bind('<Enter>', lambda event,
                      message=self._(u'The original image is shown here.'):
                      self.entry_mouse_enter(event, message))
            self.list_panel[j][1]\
                .bind('<Enter>', lambda event,
                      message=self._(u'The detected calibration target is '
                                     u'shown here.'):
                      self.entry_mouse_enter(event, message))
            self.list_panel[j][2]\
                .bind('<Enter>', lambda event,
                      message=self._(u'The distribution of the features over '
                                     u'all images are shown here. Dark blue '
                                     u'areas mean that the target was never '
                                     u'in this image region.'):
                      self.entry_mouse_enter(event, message))
            self.list_panel[j][3]\
                .bind('<Enter>', lambda event,
                      message=self._(u'The detected calibration target is '
                                     u'shown here. After the calibration, the '
                                     u'target reprojection is drawn in '
                                     u'additionally.'):
                      self.entry_mouse_enter(event, message))
            self.list_panel[j][4]\
                .bind('<Enter>', lambda event,
                      message=self._(u'The detected calibration target is '
                                     u'shown here. After the calibration, the '
                                     u'target reprojection from the view of '
                                     u'the other camera is drawn in '
                                     u'additionally.'):
                      self.entry_mouse_enter(event, message))
            self.list_panel[j][0].bind('<Leave>', self.entry_mouse_leave)
            self.list_panel[j][1].bind('<Leave>', self.entry_mouse_leave)
            self.list_panel[j][2].bind('<Leave>', self.entry_mouse_leave)
            self.list_panel[j][3].bind('<Leave>', self.entry_mouse_leave)
            self.list_panel[j][4].bind('<Leave>', self.entry_mouse_leave)

        # definition of text of labels
        for j in range(2):
            self.c_labels[j][0].config(text=self._(u'CAMERA MATRIX'))
            self.c_labels[j][2].config(text=u'\u03bc')
            self.c_labels[j][3].config(text='SD')
            self.c_labels[j][4].config(text='fx')
            self.c_labels[j][5].config(textvariable=self.fx[j])
            self.c_labels[j][6].config(textvariable=self.sd_fx[j],
                                       fg='#9a1046')
            self.c_labels[j][7].config(text='fy')
            self.c_labels[j][8].config(textvariable=self.fy[j])
            self.c_labels[j][9].config(textvariable=self.sd_fy[j],
                                       fg='#9a1046')
            self.c_labels[j][10].config(text='cx')
            self.c_labels[j][11].config(textvariable=self.cx[j])
            self.c_labels[j][12].config(textvariable=self.sd_cx[j],
                                        fg='#9a1046')
            self.c_labels[j][13].config(text='cy')
            self.c_labels[j][14].config(textvariable=self.cy[j])
            self.c_labels[j][15].config(textvariable=self.sd_cy[j],
                                        fg='#9a1046')
            self.c_labels[j][16].config(text=self
                                        ._(u'DISTORTION COEFFICIENTS'))
            self.c_labels[j][18].config(text=u'\u03bc')
            self.c_labels[j][19].config(text='SD')
            self.c_labels[j][20].config(text='k1')
            self.c_labels[j][21].config(textvariable=self.k1[j])
            self.c_labels[j][22].config(textvariable=self.sd_k1[j],
                                        fg='#9a1046')
            self.c_labels[j][23].config(text='k2')
            self.c_labels[j][24].config(textvariable=self.k2[j])
            self.c_labels[j][25].config(textvariable=self.sd_k2[j],
                                        fg='#9a1046')
            self.c_labels[j][26].config(text='k3')
            self.c_labels[j][27].config(textvariable=self.k3[j])
            self.c_labels[j][28].config(textvariable=self.sd_k3[j],
                                        fg='#9a1046')
            self.c_labels[j][29].config(text='k4')
            self.c_labels[j][30].config(textvariable=self.k4[j])
            self.c_labels[j][31].config(textvariable=self.sd_k4[j],
                                        fg='#9a1046')
            self.c_labels[j][32].config(text='k5')
            self.c_labels[j][33].config(textvariable=self.k5[j])
            self.c_labels[j][34].config(textvariable=self.sd_k5[j],
                                        fg='#9a1046')
            self.c_labels[j][35].config(text=self._(u'REPROJECTION ERROR'))
            self.c_labels[j][36].config(text='RMS')
            self.c_labels[j][37].config(textvariable=self.rms_tk[j])

        # subframe definition and positioning
        sub_frame = self.frm[4]

        # initialization and positioning of
        # labels for visualization of extrinsics
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=1, column=1, columnspan=3,
                                  sticky=tk.N + tk.S)
        for m in range(3):
            for q in range(3):
                self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
                self.c_labels[2][-1].grid(row=m + 2, column=1 + q,
                                          sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=11, column=1, columnspan=3,
                                  sticky=tk.N + tk.S)
        for m in range(3):
            self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
            self.c_labels[2][-1].grid(row=m + 12, column=1, columnspan=3,
                                      sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=15, column=1, columnspan=3,
                                  sticky=tk.N + tk.S)
        self.c_labels[2].append(tk.Label(sub_frame, font=('', 8)))
        self.c_labels[2][-1].grid(row=16, column=1, columnspan=3,
                                  sticky=tk.N + tk.S)
        # definition of text of labels
        self.c_labels[2][0].config(text=self._(u'ROTATION MATRIX'))
        self.c_labels[2][10].config(text=self._(u'TRANSLATIONAL VECTOR'))
        self.c_labels[2][14].config(text=self._(u'REPROJECTION ERROR'))
        for j in range(3):
            self.c_labels[2][11 + j].config(textvariable=self.T_tk[j])
            for i in range(3):
                self.c_labels[2][1 + i + j * 3] \
                    .config(textvariable=self.R_tk[j][i])
        self.c_labels[2][15].config(textvariable=self.rms_tk[2])

        # definition of error bar charts
        # event for the bars bases on:
        # https://matplotlib.org/users/event_handling.html
        # Draggable rectangle exercise
        xlabel_names = [self._(u'Images'), self._(u'Features')]
        title_names = [self._(u'RMS Reprojection Error'),
                       self._(u'Pixel Distance Error')]
        for i in range(2):
            for j in range(2):
                # figure and subplot declaration
                self.f[i].append(Figure(figsize=(
                    self.screen_width
                    / int(self.master.winfo_fpixels('1i'))
                    * 0.45,
                    (self.screen_height - 25)
                    / int(self.master.winfo_fpixels('1i'))
                    * 0.25),
                    dpi=int(self.master.winfo_fpixels('1i'))))
                self.ax[i].append(self.f[i][-1].add_subplot(111))
                # bar chart initialization and definition #
                # adding rectanbles to subplot
                ind = np.arange(5)
                self.ax[i][-1].bar(ind, [1] * len(ind))
                # defining object to handle plot
                # (necessary for connecting the event)
                self.bar[i].append(FigureCanvasTkAgg(self.f[i][-1],
                                                     master=self.
                                                     frm[7 + j + 2 * i]))
                self.bar[i][-1].draw()
                self.bar[i][-1].get_tk_widget().grid(row=0, column=0,
                                                     sticky=tk.W + tk.E)
                # creating click event over the figures
                self.f[i][-1].canvas.mpl_connect('button_press_event',
                                                 lambda e, a=i, b=j:
                                                     self.on_press(e, a, b))

                # clear plot for first loop
                self.ax[i][-1].clear()
                self.ax[i][-1].set_title(title_names[i], fontsize=10)
                self.ax[i][-1].set_xlabel(xlabel_names[i], fontsize=7)
                self.ax[i][-1].set_ylabel(self._(u'Pixels'), fontsize=7)
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
        self.master.bind('<F5>', lambda event: self.btn_play.invoke())
        self.master.bind('<Control-f>', lambda e: self.export_features()) # functionality not in toolbar

    def entry_mouse_enter(self, event, message='I got no message!'):
        """Mouseover event loading hint."""
        self.my_hint_label = hl.MyHintLabel(message)

    def entry_mouse_leave(self, event):
        """Mouseleave event destroying hint."""
        self.my_hint_label.destroy()
