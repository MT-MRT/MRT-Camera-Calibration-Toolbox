import logging
import tkinter as tk
from tkinter import ttk
import numpy as np
from toolboxClass.miscTools.misc_tools import validate
from toolboxClass.miscTools.plot_patterns import plot_chessboard,\
                                                 plot_circle_grid

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def popup_configuration(self):
        '''
        Function to create popup for calibration settings button
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Settings calibration'))
        tk.Label(self.popup, text=self._(u'Use intrinsics guess'))\
            .grid(row=0, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_intrinsics_guess)\
            .grid(row=0, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text=self._(u'Fix principal point'))\
            .grid(row=1, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_fix_point)\
            .grid(row=1, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text=self._(u'Fix aspect ratio'))\
            .grid(row=2, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_fix_ratio)\
            .grid(row=2, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Label(self.popup, text=self._(u'Set zero tangent distance'))\
            .grid(row=3, column=0, sticky=tk.W)
        tk.Checkbutton(self.popup, variable=self.p_zero_tangent_distance)\
            .grid(row=3, column=1, sticky=tk.E + tk.W + tk.N)
        tk.Button(self.popup, text=self._(u'Exit'),
                  command=self.popup.destroy)\
            .grid(row=4, column=0, columnspan=2, sticky=tk.E + tk.W + tk.N)
        self.center()

    def pattern_default(self, *args):
        '''
        Function to set default pattern parameters when the pattern type is
        changed
        '''
        self.popup.update()
        if self._(u'Chessboard') in self.pattern_type.get():
            self.feature_distance.set(50)
            self.pattern_width.set(9)
            self.pattern_height.set(6)
        elif self._(u'Asymmetric Grid') in self.pattern_type.get():
            self.feature_distance.set(100)
            self.pattern_width.set(9)
            self.pattern_height.set(4)
        elif self._(u'Symmetric Grid') in self.pattern_type.get():
            self.feature_distance.set(50)
            self.pattern_width.set(7)
            self.pattern_height.set(6)

    def check_errors_and_plot(self, *args):
        '''
        Function for updating the canvas representation of the pattern when
        adding a new session also shows error and warnings depending of the
        range of the parameters
        '''

        # delete grid_line objects
        if self.c_pattern:
            self.c_pattern.delete('grid_line')
            self.c_pattern.delete('grid_oval')
        else:
            logging.error(self._(u'c_pattern does not exist'))
            return

        # Clear warnings
        self.l_error.config(image='', text='', bg='#d9d9d9')
        if self._(u'Images') in self.pattern_load.get():
            # set continue flag in true
            b_continue = True
            # check range of pattern width, update the continue flag and
            # show error if applies
            try:
                self.p_width = self.pattern_width.get()
                if self.p_width < 2:
                    self.label_msg[0].configure(
                        text=self
                        ._(u'width parameter must be greater than one'))
                    b_continue = False
                else:
                    self.label_msg[0].configure(text='')
            except (ValueError, tk.TclError):
                self.label_msg[0].configure(
                        text=self._(u'width parameter can not be empty'))
                b_continue = False
            # check range of pattern height, update the continue flag and show
            # error if applies
            try:
                self.p_height = self.pattern_height.get()
                if self.p_height < 2:
                    self.label_msg[1].configure(
                        text=self
                        ._(u'height parameter must be greater than one'))
                    b_continue = False
                else:
                    self.label_msg[1].configure(text='')
            except (ValueError, tk.TclError):
                self.label_msg[1].configure(
                        text=self._(u'height parameter can not be empty'))
                b_continue = False
            # check range of pattern length and show error if applies
            try:
                self.f_distance = self.feature_distance.get()
                if self.f_distance == 0:
                    self.label_msg[2].configure(
                        text=self
                        ._(u'length parameter must be greater than zero'))
                else:
                    self.label_msg[2].configure(text='')
            except (ValueError, tk.TclError):
                self.label_msg[2].configure(
                        text=self._(u'length parameter can not be empty'))

            if b_continue:
                if self._(u'Chessboard') in self.pattern_type.get():
                    plot_chessboard(self.c_pattern,
                                    self.p_width,
                                    self.p_height,
                                    self.c_pattern.winfo_width(),
                                    self.c_pattern.winfo_height())
                elif self._(u'Asymmetric Grid') in self.pattern_type.get():
                    plot_circle_grid(self.c_pattern,
                                     self.p_width,
                                     self.p_height,
                                     self.c_pattern.winfo_width(),
                                     self.c_pattern.winfo_height(),
                                     symmetric=False)
                elif self._(u'Symmetric Grid') in self.pattern_type.get():
                    plot_circle_grid(self.c_pattern,
                                     self.p_width,
                                     self.p_height,
                                     self.c_pattern.winfo_width(),
                                     self.c_pattern.winfo_height(),
                                     symmetric=True)

                # check if width and height parameters are an odd-even pair
                # and show warnings if applies
                if (self.p_width + self.p_height) % 2 == 0:
                    self.l_error\
                        .config(image='::tk::icons::warning',
                                text=(self._(u'width and height parameters\n')
                                      + self._(u'should be an odd-even pair')),
                                bg='#ffcc0f',
                                fg='black')

        else:
            # check the image size and show error if applies
            try:
                if self.image_width.get() == 0:
                    self.label_msg[3].configure(
                        text=self
                        ._(u'width parameter must be greater than zero'))
                else:
                    self.label_msg[3].configure(text='')
            except ValueError:
                self.label_msg[3].configure(
                        text=self._(u'width parameter can not be empty'))
            # check range of pattern height, update the continue flag and show
            # error if applies
            try:
                if self.image_height.get() == 0:
                    self.label_msg[4].configure(
                         text=self
                         ._(u'height parameter must be greater than zero'))
                else:
                    self.label_msg[4].configure(text='')
            except ValueError:
                self.label_msg[4].configure(
                        text=self._(u'height parameter can not be empty'))

            # load 3D points to object_pattern
            if self.load_files[0]:
                set_3D_points = np.fromfile(self.load_files[0][0],
                                            dtype=np.float32, sep=',')
                n_points = len(set_3D_points) / 3
                self.object_pattern = set_3D_points.reshape((n_points, 1, 3))

    def add_session_popup(self):
        '''
        Function to create popup for add session button
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.grid_columnconfigure(0, weight=1)
        self.popup.grid_rowconfigure(0, weight=1)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Add Session'))

        self.pattern_load.set(self._(u'Images'))

        # struct popup add session popup #
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

        vcmd_int = (self.popup.register(validate), '%d', '%i', '%P', '%s',
                    '%S', '%v', '%V', '%W', '0123456789')
        vcmd_float = (self.popup.register(validate), '%d', '%i', '%P', '%s',
                      '%S', '%v', '%V', '%W', '0123456789.')

        tk.Label(self.m_frm[0], text=self._(u'Select file type to load'))\
            .grid(row=0, column=0, sticky=tk.W + tk.E)
        tk.OptionMenu(self.m_frm[0], self.pattern_load, self._(u'Images'),
                      self._(u'Text'), command=self.modify_add_session_popup)\
            .grid(row=1, column=0, sticky=tk.W + tk.E)

        tk.Label(self.m_frm[3],
                 text=self._(u'Stereo mode?')).grid(row=0, column=0)
        tk.Checkbutton(self.m_frm[3], variable=self.mode_stereo).grid(row=0,
                                                                      column=1)

        self.l_error = tk.Label(self.m_frm[3], compound=tk.LEFT)
        self.l_error.grid(row=1, column=0, columnspan=2)
        tk.Button(self.m_frm[3], text=self._(u'Start'),
                  command=self.add_session).grid(row=2, column=0)
        tk.Button(self.m_frm[3], text=self._(u'Cancel'),
                  command=self.popup.destroy).grid(row=2, column=1)

        # struct Frame add session images (m_frm[1]) #
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

        tk.Label(self.m_frm[1], text=self._(u'Pattern type '))\
            .grid(row=0, column=0, sticky=tk.W)
        tk.OptionMenu(self.m_frm[1], self.pattern_type, self._(u'Chessboard'),
                      self._(u'Asymmetric Grid'),
                      self._(u'Symmetric Grid')).grid(row=1, column=0,
                                                      sticky=tk.W + tk.E)
        self.labelP = tk.Label(self.m_frm[1], text=self._(u'Pattern width '))\
            .grid(row=2, column=0, sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.pattern_width,
                 validate='key', validatecommand=vcmd_int).grid(row=3,
                                                                column=0,
                                                                sticky=tk.W
                                                                + tk.E)

        self.label_msg[0] = tk.Label(self.m_frm[1], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[0].grid(row=4, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1],
                 text=self._(u'Pattern height ')).grid(row=5, column=0,
                                                       sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.pattern_height,
                 validate='key', validatecommand=vcmd_int).grid(row=6,
                                                                column=0,
                                                                sticky=tk.W
                                                                + tk.E)

        self.label_msg[1] = tk.Label(self.m_frm[1], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[1].grid(row=7, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1],
                 text=self._(u'Feature distance (mm) ')).grid(row=8, column=0,
                                                              sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.feature_distance,
                 validate='key', validatecommand=vcmd_float).grid(row=9,
                                                                  column=0,
                                                                  sticky=tk.W
                                                                  + tk.E)

        # struct Frame add session text (m_frm[2]) #
        # ---------------------------------
        # | Image width                   |
        # ---------------------------------
        # | *Text width*                  |
        # ---------------------------------
        # | Label error width             |
        # ---------------------------------
        # | Image height                  |
        # ---------------------------------
        # | *Text height*                 |
        # ---------------------------------
        # | Label error height            |
        # ---------------------------------
        # ||  3D points of pattern (mm)  ||
        # ---------------------------------
        # | Label error 3D points         |
        # ---------------------------------

        self.m_frm[2].grid_forget()
        self.label_msg[2] = tk.Label(self.m_frm[1], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[2].grid(row=10, column=0, sticky=tk.W)

        self.c_pattern = tk.Canvas(self.m_frm[1], height=100, width=100,
                                   bg='white')
        self.c_pattern.grid(row=0, column=1, rowspan=11)
        tk.Label(self.m_frm[1], width=15).grid(row=1, column=1, sticky=tk.W)
        # self.c_pattern.bind('<Configure>', self.check_errors_and_plot)

        tk.Label(self.m_frm[2],
                 text=self._(u'Image width ')).grid(row=0, column=0,
                                                    sticky=tk.W)
        tk.Entry(self.m_frm[2], textvariable=self.image_width, validate='key',
                 validatecommand=vcmd_int).grid(row=1, column=0,
                                                sticky=tk.W + tk.E)
        self.label_msg[3] = tk.Label(self.m_frm[2], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[3].grid(row=2, column=0, sticky=tk.W)

        tk.Label(self.m_frm[2],
                 text=self._(u'Image height ')).grid(row=3, column=0,
                                                     sticky=tk.W)
        tk.Entry(self.m_frm[2], textvariable=self.image_height, validate='key',
                 validatecommand=vcmd_int).grid(row=4, column=0,
                                                sticky=tk.W + tk.E)
        self.label_msg[4] = tk.Label(self.m_frm[2], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[4].grid(row=5, column=0, sticky=tk.W)

        tk.Button(self.m_frm[2], text=self._(u'3D points of pattern (mm)'),
                  command=self.load_3D_points).grid(row=6, column=0)
        self.l_load_files[0] = tk.Label(self.m_frm[2], font='TkDefaultFont 6')
        self.l_load_files[0].grid(row=7, column=0)

        self.m_frm[0]\
            .bind('<Enter>', lambda event,
                  message=self._(u'The toolbox is capable of chessboard, '
                                 u'asymetric and symmetric circle targets '
                                 u'(choose images). If the \nused target is '
                                 u'none of them, please input txt-files with '
                                 u'the given features (see documentation).'):
                  self.entry_mouse_enter(event, message))
        self.m_frm[1]\
            .bind('<Enter>', lambda event,
                  message=self._(u'The parameters of the target must be '
                                 u'entered: The number of features in the '
                                 u'width and height, as well \nas their real '
                                 u'world distance. Examples for the '
                                 u'parameterization are given in the '
                                 u'documentation.'):
                  self.entry_mouse_enter(event, message))
        self.m_frm[2].bind('<Enter>', lambda event,
                           message=self._(u'The width and height of the '
                                          u'images must be entered.'):
                           self.entry_mouse_enter(event, message))
        self.m_frm[3].bind('<Enter>', lambda event,
                           message=self._(u'Setting whether stereo mode '
                                          u'should be used. Starting a new '
                                          u'session.'):
                           self.entry_mouse_enter(event, message))
        self.m_frm[0].bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[1].bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[2].bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[3].bind('<Leave>', self.entry_mouse_leave)

        # Setting pattern feature variables
        self.mode_stereo.set(False)
        self.pattern_type.set(self._(u'Chessboard'))

        self.center()

    def modify_add_session_popup(self, *args):
        '''
        Function to modify add_session popup by changing pattern load
        selection box
        '''
        self.l_load_files[0].config(text='')
        self.load_files[0] = None
        if self._(u'Text') in self.pattern_load.get():
            self.image_width.set(240)
            self.image_height.set(320)
            self.m_frm[2].grid(row=2, column=0)
            self.m_frm[1].grid_forget()
        else:
            self.m_frm[1].grid(row=1, column=0)
            self.m_frm[2].grid_forget()
        self.check_errors_and_plot(None)

    def modify_play_popup(self, *args):
        '''
        Function to adjust the GUI according to the selected calibration method
        '''
        self.btn_export.config(state='disable')  # disable export parameters button
        self.btn_export2.config(state='disable')  # disable export parameters button
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
        self.label_status_l[3][0].config(text=self._(u'3. Loading Extrinsics'))
        self.label_status_l[3][1].config(text='')
        self.label_status_l[4][1].config(text='')

        if self._('Clustering') in self.how_to_calibrate.get():
            # reset progress bar
            self.progbar['value'] = 0
            self.lb_time.config(text='')
            self.style_pg.configure('text.Horizontal.TProgressbar',
                                    text='{:g} %'.format(0))
            # set GUI for clustering
            self.m_frm[1].grid(row=3, column=0, sticky=tk.N + tk.S)
            self.m_frm[0].grid_forget()
        elif self._('Load') in self.how_to_calibrate.get():
            # set GUI for Loading File
            self.m_frm[0].grid(row=2, column=0, sticky=tk.N + tk.S)
            self.m_frm[1].grid_forget()

    def popupmsg(self):
        '''
        Function to show popup with information about the importing images process
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Information imported images'))
        l_msg = tk.Label(self.popup)
        l_msg.grid(row=0, column=0, columnspan=3, sticky=tk.E + tk.W)

        # set initial text progressbar
        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar = ttk.Progressbar(self.popup,
                                       style='text.Horizontal.TProgressbar')
        self.progbar.config(maximum=10, mode='determinate')
        self.progbar.grid(row=1, column=0, columnspan=3, sticky=tk.E + tk.W)

        # text and its scrollbar for additional details
        frm = tk.Frame(self.popup)
        sb = tk.Scrollbar(frm, orient='vertical')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        text_detail = tk.Text(frm, yscrollcommand=sb.set)
        text_detail.pack(expand=True, fill=tk.Y)
        sb.config(command=text_detail.yview)

        # button for getting more or less details
        b_details = tk.Button(self.popup, text=self._(u'\u2b07 more details'))
        b_details.configure(command=lambda: self.show_details(b_details, frm))
        b_details.grid(row=3, column=0, sticky=tk.E + tk.W)
        b_cancel = tk.Button(self.popup, text=self._(u'Cancel'))
        b_cancel.configure(command=lambda: self.cancel_importing(b_cancel))
        b_cancel.grid(row=3, column=1, columnspan=2,sticky=tk.E + tk.W)
        self.center()
        return l_msg, text_detail, b_cancel

    def cancel_importing(self, button):
        '''
        Function to cancel the importing images process and when finished, close the popup
        '''
        if 'Cancel' in button.cget('text'):
            self.continue_importing = False
            button.configure(text=self._('Exit'))
        else:
            self.popup.destroy()

    def show_details(self, button, frm):
        '''
        Function to show more or less details about the rejected, repeated and invalid sized images
        '''
        if '\u2b07' in button.cget('text'):
            frm.grid(row=2, column=0)
            button.configure(text=self._('\u2b06 less details'))
        else:
            frm.grid_forget()
            button.configure(text=self._('\u2b07 more details'))
        self.center()

    def play_popup(self):
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Camera Calibration'))
        self.f_frm = tk.Frame(self.popup)
        self.f_frm.grid(row=0, column=0)

        tk.Label(self.f_frm,
                 text=self
                 ._(u'How to get camera parameters?')).grid(row=0, column=0,
                                                            sticky=tk.E
                                                            + tk.W
                                                            + tk.N)
        tk.OptionMenu(self.f_frm, self.how_to_calibrate,
                      self._(u'Clustering calculation'),
                      self._(u'Load from file'),
                      command=self.modify_play_popup).grid(row=1, column=0,
                                                           sticky=tk.E
                                                           + tk.W
                                                           + tk.N)

        vcmd_int = (self.popup.register(validate), '%d', '%i', '%P', '%s',
                    '%S', '%v', '%V', '%W', '0123456789')

        self.m_frm = []
        for i in range(3):
            self.m_frm.append(tk.Frame(self.popup))
            self.m_frm[-1].grid(row=2 + i, column=0)
        self.m_frm[0].grid_forget()

        # struct popup load from file (m_frm[0]) #
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

        tk.Button(self.m_frm[0], text=self._(u'Intrinsics 1 camera'),
                  command=lambda: self.assign_filename(0)).grid(row=1,
                                                                column=0,
                                                                sticky=tk.E
                                                                + tk.W
                                                                + tk.N)

        if self.m_stereo:
            tk.Button(self.m_frm[0], text=self._(u'Intrinsics 2 camera'),
                      command=lambda: self.assign_filename(1)).grid(row=3,
                                                                    column=0,
                                                                    sticky=tk.E
                                                                    + tk.W
                                                                    + tk.N)
            tk.Button(self.m_frm[0], text=self._(u'Extrinsics'),
                      command=lambda: self.assign_filename(2)).grid(row=5,
                                                                    column=0,
                                                                    sticky=tk.E
                                                                    + tk.W
                                                                    + tk.N)

        self.l_load_files[0] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[0].grid(row=2, column=0, sticky=tk.E + tk.W + tk.N)
        self.l_load_files[1] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[1].grid(row=4, column=0, sticky=tk.E + tk.W + tk.N)
        self.l_load_files[2] = tk.Label(self.m_frm[0], font='TkDefaultFont 6')
        self.l_load_files[2].grid(row=6, column=0, sticky=tk.E + tk.W + tk.N)

        aux_frame = tk.Frame(self.m_frm[0])
        aux_frame.grid(row=7, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # struct for label_status_l #
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
                label = tk.Label(aux_frame)
                label.grid(row=j, column=i, sticky=tk.W)
                self.label_status_l[j].append(label)

        self.label_status_l[0][0].config(text=self._(u'Steps'))
        self.label_status_l[0][1].config(text=self._(u'State'))

        if self.n_cameras == 1:
            # forget grid for labels of errors for stereo mode
            self.l_load_files[1].grid_forget()
            self.l_load_files[2].grid_forget()
            # forget grid of labels for stereo mode
            self.label_status_l[1][0]\
                .config(text=self._(u'1. Loading Intrinsics 1'))
            self.label_status_l[2][0].grid_forget()
            self.label_status_l[3][0].grid_forget()
            self.label_status_l[4][0].config(text=self
                                             ._(u'2. Calculating Error'))
            self.label_status_l[4][0].grid(row=2, column=0)
        else:
            self.label_status_l[1][0]\
                .config(text=self._(u'1. Loading Intrinsics 1'))
            self.label_status_l[2][0]\
                .config(text=self._(u'2. Loading Intrinsics 2'))
            self.label_status_l[3][0]\
                .config(text=self._(u'3. Loading Extrinsics'))
            self.label_status_l[4][0]\
                .config(text=self._(u'4. Calculating Error'))

        # struct popup load from file (m_frm[1]) #
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

        tk.Label(self.m_frm[1],
                 text=self._(u'Number of images (n) ')).grid(row=1, column=0,
                                                             sticky=tk.W)
        tk.Label(self.m_frm[1], text=str(self.n_total.get())).grid(row=2,
                                                                   column=0,
                                                                   sticky=tk.E
                                                                   + tk.W)

        self.c_r.set(self.n_total.get())
        self.c_k.set(1)

        tk.Label(self.m_frm[1],
                 text=self._(u'Number of groups (k) ')).grid(row=3, column=0,
                                                             sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.c_k, validate='key',
                 validatecommand=vcmd_int).grid(row=4, column=0,
                                                sticky=tk.E + tk.W + tk.N)
        self.label_msg[0] = tk.Label(self.m_frm[1], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[0].grid(row=5, column=0, sticky=tk.W)

        tk.Label(self.m_frm[1], text=self
                 ._(u'Number of elements per group (r) ')).grid(row=6,
                                                                column=0,
                                                                sticky=tk.W)
        tk.Entry(self.m_frm[1], textvariable=self.c_r, validate='key',
                 validatecommand=vcmd_int).grid(row=7, column=0,
                                                sticky=tk.E + tk.W + tk.N)
        self.label_msg[1] = tk.Label(self.m_frm[1], font='TkDefaultFont 6',
                                     fg='red')
        self.label_msg[1].grid(row=8, column=0, sticky=tk.W)

        # set initial text progressbar
        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar = ttk.Progressbar(self.m_frm[1],
                                       style='text.Horizontal.TProgressbar')
        self.progbar.config(maximum=10, mode='determinate')
        self.progbar.grid(row=9, column=0, sticky=tk.E + tk.W)

        self.lb_time = tk.Label(self.m_frm[1], font='TkDefaultFont 6')
        self.lb_time.grid(row=10, column=0, sticky=tk.W + tk.E)

        aux_frame = tk.Frame(self.m_frm[1])
        aux_frame.grid(row=11, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # struct for label_status #
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
                label = tk.Label(aux_frame)
                label.grid(row=j, column=i, sticky=tk.W)
                self.label_status[j].append(label)

        self.label_status[0][0].config(text=self._(u'Steps'))
        self.label_status[0][1].config(text=self._(u'State'))
        self.label_status[0][2].config(text=self._(u'Time (s)'))
        self.label_status[1][0].config(text=self._(u'1. Clustering'))
        self.label_status[2][0].config(text=self._(u'2. Averaging'))
        self.label_status[3][0].config(text=self
                                       ._(u'3. Calculating Projections'))
        self.label_status[4][0].config(text=self._(u'4. Calculating Error'))
        self.label_status[5][0].config(text=self._(u'TOTAL'))

        # added reference to disable button while play
        calib_button = tk.Button(self.m_frm[2], text=self._(u'Calibrate'))
        calib_button.config(command=lambda: self.play(calib_button))
        calib_button.grid(row=0, column=0, sticky=tk.E + tk.W + tk.N)
        tk.Button(self.m_frm[2], text=self._(u'Exit'),
                  command=self.popup.destroy).grid(row=0, column=1,
                                                   sticky=tk.E + tk.W + tk.N)

        self.f_frm.bind('<Enter>', lambda event,
                        message=self._(u'Choose between .'):
                        self.entry_mouse_enter(event, message))
        self.m_frm[0].bind('<Enter>', lambda event,
                           message=self._(u'The textfiles with the saved '
                                          u'intrinsic parameters are to be '
                                          u'loaded.'):
                           self.entry_mouse_enter(event, message))
        self.m_frm[1].bind('<Enter>', lambda event,
                           message=self._(u'The parameters for the number of '
                                          u'calibrations and the number of '
                                          u'images per calibration must be '
                                          u'set here. For \na simple '
                                          u'calibration, enter k=1 and the '
                                          u'maximum number of images '
                                          u'(presettings). For a good '
                                          u'calibration, at \nleast r = 10 '
                                          u'images should be selected '
                                          u'usually.'):
                           self.entry_mouse_enter(event, message))
        self.m_frm[2].bind('<Enter>', lambda event,
                           message=self._(u'Start of the calibration.'):
                           self.entry_mouse_enter(event, message))
        self.f_frm.bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[0].bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[1].bind('<Leave>', self.entry_mouse_leave)
        self.m_frm[2].bind('<Leave>', self.entry_mouse_leave)

        self.modify_play_popup()
        self.center()

    def popup_importing_fails(self, message):
        '''
        Function to create error popup when selecting invalid images folders
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Importing error'))
        l_error = tk.Label(self.popup, compound=tk.LEFT, image='::tk::icons::error', text=message)
        l_error.grid(row=0, column=0, sticky=tk.W + tk.E)
        tk.Button(self.popup, text=self._(u'Okay'), command=self.popup.destroy).grid(row=1, column=0,
                                                                                     sticky=tk.W + tk.E)
        self.center()

    def popupmsg_deleting(self):
        '''
        Function to create popup for deleting confirmation
        '''
        self.popup = tk.Toplevel(self.master)
        self.popup.withdraw()

        self.popup.wm_title(self._(u'Delete session'))
        tk.Label(self.popup, text=self
                 ._(u'\nAre you sure you want to delete the session?\n'))\
            .grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E)
        tk.Button(self.popup, text=self._(u'Yes'), command=self.del_all)\
            .grid(row=1, column=0, sticky=tk.W + tk.E)
        tk.Button(self.popup, text=self._(u'Cancel'),
                  command=self.popup.destroy).grid(row=1, column=1,
                                                   sticky=tk.W + tk.E)

        self.center()
