import logging
import math
import cv2
import numpy as np
from toolboxClass.miscTools.misc_tools import ncr
from toolboxClass.miscTools.time_tools import chronometer
from toolboxClass.calibration_functions import (run_clustering_calibration,
                                                calculate_projection,
                                                calculate_error)

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def play(self, calib_button):

        calib_button.config(state='disabled')
        self.btn_play.config(relief='sunken')
        self.btn_play.config(state='active')

        self.style_pg.configure('text.Horizontal.TProgressbar', text='0 %')
        self.progbar['value'] = 0

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

        flags_parameters = \
            int(self.p_intrinsics_guess.get())*cv2.CALIB_USE_INTRINSIC_GUESS +\
            int(self.p_fix_point.get()) * cv2.CALIB_FIX_PRINCIPAL_POINT + \
            int(self.p_fix_ratio.get()) * cv2.CALIB_FIX_ASPECT_RATIO + \
            int(self.p_zero_tangent_distance.get())*cv2.CALIB_ZERO_TANGENT_DIST

        logging.debug('%s', self.how_to_calibrate.get())
        if self._(u'Clustering') in self.how_to_calibrate.get():
            c_r = None
            c_k = None

            b_continue = True
            try:
                c_r = self.c_r.get()
                if c_r < 3:
                    self.label_msg[1].configure(
                        text=self._('R parameter must be greater than two'))
                    b_continue = False
                elif c_r > self.n_total.get():
                    self.label_msg[1].configure(
                        text=self.
                        _('R parameter must be smaller or equal than n'))
                    b_continue = False
                else:
                    self.label_msg[1].configure(text='')
            except ValueError:
                self.label_msg[1].configure(
                    text=self._('R parameter can not be empty'))
                b_continue = False
            try:
                c_k = self.c_k.get()
                if c_k < 1:
                    self.label_msg[0].configure(
                        text=self._('K parameter must be greater than zero'))
                    b_continue = False
                else:
                    self.label_msg[0].configure(text='')
            except ValueError:
                self.label_msg[0].configure(
                    text=self._('K parameter can not be empty'))
                b_continue = False
            if not b_continue:
                self.btn_play.config(relief='raised')
                self.btn_play.config(state='normal')
                calib_button.config(state='active')
                return

            # n, number of all images
            max_k = math.comb(self.n_total.get(), c_r)
            k = min(c_k, max_k)

            if k < c_k:
                self.c_k.set(int(k))
                self.label_msg[1].config(
                    text=(self._('Number of groups changed from ')
                          + self._('%d to %d (maximum possible)') % (c_k, k)))
                self.popup.update()  # for updating while running other process

            def clustering_progress(counter, total_k, c_percent, elapsed_time):
                self.progbar['value'] = c_percent * 10.0
                t_left_minutes, t_left_seconds = divmod(elapsed_time * (1 / c_percent - 1), 60)
                if t_left_minutes != 0:
                    self.lb_time.config(text=self._('Estimated time left: %d minutes and %d seconds') % (
                        max(t_left_minutes, 0), max(t_left_seconds, 0)))
                else:
                    self.lb_time.config(text=self._('Estimated time left: %d seconds') % (max(t_left_seconds, 0)))
                self.style_pg.configure('text.Horizontal.TProgressbar',
                                        text='{:g} %'
                                        .format(int(c_percent * 100)))
                self.popup.update()

            result, k = run_clustering_calibration(
                self.objpoints, self.imgpoints, self.size,
                self.n_cameras, self.m_stereo, flags_parameters,
                self.n_total.get(), c_r, c_k,
                progress_callback=clustering_progress)

            self.label_status[1][1].config(text=u'\u2714')
            if result['success']:
                self.label_status[1][2].config(text='%0.5f' % result['elapsed_time_1'])
            self.lb_time.config(text='')

            if result['success']:
                self.camera_matrix = result['camera_matrix']
                self.dev_camera_matrix = result['dev_camera_matrix']
                self.dist_coefs = result['dist_coefs']
                self.dev_dist_coefs = result['dev_dist_coefs']
                self.R_stereo = result['R_stereo']
                self.T_stereo = result['T_stereo']
                self.fx_array = result['fx_array']
                self.fy_array = result['fy_array']
                self.cx_array = result['cx_array']
                self.cy_array = result['cy_array']
                self.k1_array = result['k1_array']
                self.k2_array = result['k2_array']
                self.k3_array = result['k3_array']
                self.k4_array = result['k4_array']
                self.k5_array = result['k5_array']
                self.R_array = result['R_array']
                self.T_array = result['T_array']
                self.RMS_array = result['RMS_array']
                self.samples = result['samples']
            else:
                self.reset_camera_parameters()

            elapsed_time_1 = result.get('elapsed_time_1', 0)
            time_play = chronometer()

            # Time for averaging step (now included in clustering result)
            averaging_time = time_play.gettime()
            self.label_status[2][1].config(text=u'\u2714')
            self.label_status[2][2].config(text='%0.5f' % averaging_time)

            if np.any(self.camera_matrix[:, 0, 0] == 1):
                self.reset_camera_parameters()
                self.reset_error()
            else:
                logging.debug(self._('Correct!'))
                # Camera projections
                self.calculate_projection()
                elapsed_time_3 = time_play.gettime()
                self.label_status[3][1].config(text=u'\u2714')
                self.label_status[3][2].config(text='%0.5f' %
                                               elapsed_time_3)
                # Calculate RMS error
                self.calculate_error()

                elapsed_time_4 = time_play.gettime()
                self.label_status[4][1].config(text=u'\u2714')
                self.label_status[4][2].config(text='%0.5f' %
                                               (elapsed_time_4
                                                - elapsed_time_3))
                self.label_status[5][2].config(text='%0.5f' %
                                               (elapsed_time_1
                                                + elapsed_time_4))
                # enable export parameters buttons
                self.btn_export.config(state='normal')
                self.btn_export2.config(state='normal')
                for e in self.rms:
                    if e == float('inf') or e == float('-inf'):
                        logging.warning(self._('Error is too high'))
                        # mark X for step 3 and 4
                        self.label_status[4][1].config(text=u'\u2718')
                        self.label_status[4][1].config(text=u'\u2718')
                        self.reset_camera_parameters()
                        self.reset_error()
                        # disable export parameters button
                        self.btn_export.config(state='disable')
                        self.btn_export2.config(state='disable')
                        break

        elif self._(u'Load') in self.how_to_calibrate.get():
            b_continue = True
            for j in range(2 * (self.n_cameras - 1) + 1):
                if '.txt' not in self.l_load_files[j].cget('text'):
                    if j == 2:
                        self.l_load_files[j]\
                            .config(text=self._('Missing Extrinsics'),
                                    fg='green')
                        self.label_status_l[3][1].config(text=u'\u2718')
                        if b_continue:
                            # TODO: Adjust for different sizes in Load mode
                            width = max(self.size[0][1], self.size[1][1])
                            height = max(self.size[0][0], self.size[1][0])
                            rms, self.camera_matrix[0], self.dist_coefs[0],\
                                self.camera_matrix[1], self.dist_coefs[1],\
                                R, T, _, _ = cv2.stereoCalibrate(
                                                        self.objpoints,
                                                        self.imgpoints[0],
                                                        self.imgpoints[1],
                                                        self.camera_matrix[0],
                                                        self.dist_coefs[0],
                                                        self.camera_matrix[1],
                                                        self.dist_coefs[1],
                                                        (width, height),
                                                        flags=cv2.
                                                        CALIB_FIX_INTRINSIC +
                                                        flags_parameters)
                            if rms != 0:
                                self.R_stereo = R
                                self.T_stereo = T
                                self.label_status_l[3][0].config(
                                        text=self
                                        ._('3. Calculating Extrinsics'))
                                self.label_status_l[3][1].config(
                                        text=u'\u2714')
                            else:
                                logging.error(self._('Calibration fails'))
                                b_continue = False
                                self.label_status_l[j + 1][1].config(
                                        text=u'\u2718')
                                self.label_status_l[4][1].config(
                                        text=u'\u2718')
                    else:
                        self.l_load_files[j].config(
                                         text=self
                                         ._('File missing, please add'),
                                         fg='red')
                        b_continue = False
                        self.label_status_l[j + 1][1].config(text=u'\u2718')
                        self.label_status_l[4][1].config(text=u'\u2718')

            if b_continue:
                for i in range(self.n_cameras):
                    # Fx is zero only when reset
                    if self.camera_matrix[i][0][0] == 0:
                        logging.debug(self
                                      ._('Data for camera %s not available'),
                                      i + 1)
                        self.reset_camera_parameters()
                        self.reset_error()
                        break
                    if i == self.n_cameras - 1:
                        logging.debug('Correct!')
                        # Camera projections
                        self.calculate_projection()
                        # Calculate RMS error
                        self.calculate_error()
                        # enable export parameters button
                        self.btn_export.config(state='normal')
                        self.btn_export2.config(state='normal')

                for e in self.rms:
                    if e == float('inf') or e == float('-inf'):
                        logging.warning(self._('Error is too high'))
                        self.reset_camera_parameters()
                        self.reset_error()
                        self.label_status_l[4][1].config(text=u'\u2718')
                        # disable export parameters button
                        self.btn_export.config(state='disable')
                        self.btn_export2.config(state='disable')
                        break
                    else:
                        self.label_status_l[4][1].config(text=u'\u2714')

        self.update = True  # Update bool activated

        self.updateCameraParametersGUI()
        self.loadBarError([0, 1])
        calib_button.config(state='normal')
        self.btn_play.config(relief='raised')
        self.btn_play.config(state='normal')

    def calculate_projection(self, r=None, t=None):
        """Function to calculate projections for all cameras."""
        self.projected, self.projected_stereo = calculate_projection(
            self.objpoints, self.imgpoints, self.camera_matrix,
            self.dist_coefs, self.n_cameras, self.m_stereo,
            self.R_stereo, self.T_stereo, r=r, t=t)

    def calculate_error(self):
        """Function to calculate reprojection errors with GUI progress updates."""
        def progress_callback(c_percent):
            self.progbar['value'] = c_percent * 10.0
            self.style_pg.configure('text.Horizontal.TProgressbar',
                                    text='{:g} %'
                                    .format(int(c_percent * 100)))
            self.popup.update()

        self.r_error, self.r_error_p, self.rms = calculate_error(
            self.imgpoints, self.projected, self.projected_stereo,
            self.n_cameras, self.m_stereo,
            progress_callback=progress_callback)
