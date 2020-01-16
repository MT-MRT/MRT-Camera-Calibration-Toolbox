import logging
import cv2
import numpy as np
from toolboxClass.miscTools.misc_tools import combination
from toolboxClass.miscTools.quaternions import averageMatrix
from toolboxClass.miscTools.time_tools import chronometer

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
            self.samples, k = combination(len(self.objpoints), c_r, c_k)

            if k != c_k:
                self.c_k.set(int(k))
                self.label_msg[1].config(
                    text=(self._('Number of groups changed from ')
                          + self._('%d to %d (maximum possible)') % (c_k, k)))
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
                        logging.debug(self._('Different camera resolution'))
                        ip = np.array(ip)
                        index_min = self.size.index(min(self.size))
                        index_max = self.size.index(max(self.size))
                        w_max, h_max = self.size[index_max]
                        w_min, h_min = self.size[index_min]
                        w_adj = (w_max - w_min) / 2
                        h_adj = (h_max - h_min) / 2
                        n_poses, n_points, _, _ = ip[index_min].shape
                        logging.debug(
                            self._('Transforming coordinates for camera %s'),
                            index_min + 1)
                        for pose in range(n_poses):
                            for point in range(n_points):
                                ip[index_min][pose][point] = \
                                    np.sum([ip[index_min][pose][point],
                                            [[h_adj, w_adj]]],
                                           axis=0)
                    width = max(self.size[0][1], self.size[1][1])
                    height = max(self.size[0][0], self.size[1][0])
                    rms, c[0], d[0], c[1], d[1], R, T, _, _ = \
                        cv2.stereoCalibrate(op, ip[0], ip[1], c[0], d[0], c[1],
                                            d[1], (width, height),
                                            flags=flags_parameters)
                else:
                    width = self.size[0][1]
                    height = self.size[0][0]
                    rms, c[0], d[0], _, _ = \
                        cv2.calibrateCamera(op, ip[0], (width, height),
                                            c[0], d[0], flags=flags_parameters)

                logging.info(self._('this is stereo rms error: %s'), rms)

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

                    # percentage of completion of process
                    c_porcent = counter / float(len(self.samples))
                    self.progbar['value'] = c_porcent * 10.0
                    elapsed_time_1 = time_play.gettime()
                    t_left_minutes, t_left_seconds = divmod(elapsed_time_1 * (1 / c_porcent - 1), 60)
                    if t_left_minutes != 0:
                        self.lb_time.config(text=self._('Estimated time left: %d minutes and %d seconds') % (
                        max(t_left_minutes, 0), max(t_left_seconds, 0)))
                    else:
                        self.lb_time.config(text=self._('Estimated time left: %d seconds') % (max(t_left_seconds, 0)))
                    # update label
                    self.style_pg.configure('text.Horizontal.TProgressbar',
                                            text='{:g} %'
                                            .format(int(c_porcent * 100)))
                    self.popup.update()  # updating while running other process

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
                        logging.debug(self
                                      ._('Correcting cx an cy for camera {0}')
                                      .format(index_min + 1))
                        self.camera_matrix[index_min][0][2] -= h_adj
                        self.camera_matrix[index_min][1][2] -= w_adj
            else:
                self.reset_camera_parameters()

            elapsed_time_2 = time_play.gettime()
            self.label_status[2][1].config(text=u'\u2714')
            self.label_status[2][2].config(text='%0.5f' %
                                           (elapsed_time_2
                                            - elapsed_time_1))

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
                                               (elapsed_time_3
                                                - elapsed_time_2))
                # Calculate RMS error
                self.calculate_error()
                elapsed_time_4 = time_play.gettime()
                self.label_status[4][1].config(text=u'\u2714')
                self.label_status[4][2].config(text='%0.5f' %
                                               (elapsed_time_4
                                                - elapsed_time_3))
                self.label_status[5][2].config(text='%0.5f' % elapsed_time_4)
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
            for i, _ in enumerate(op):
                if not r:
                    _, r1, t1, _ = cv2.solvePnPRansac(op[i],
                                                      ip[j][i],
                                                      c[j],
                                                      d[j])
                else:
                    r1 = r[j][i]
                    t1 = t[j][i]

                imgpoints2, _ = cv2.projectPoints(op[i], r1, t1, c[j], d[j])
                self.projected[j].append(imgpoints2)

                if self.m_stereo:
                    r1 = cv2.Rodrigues(r1)[0]

                    if j == 1:
                        r2 = np.dot(np.linalg.inv(self.R_stereo), r1)
                        t2 = np.dot(np.linalg.inv(self.R_stereo), t1) \
                            - np.dot(np.linalg.inv(self.R_stereo),
                                     self.T_stereo)
                    else:
                        r2 = np.dot(self.R_stereo, r1)
                        t2 = np.dot(self.R_stereo, t1) + self.T_stereo

                    imgpoints2, _ = cv2.projectPoints(op[i], r2, t2,
                                                      c[(j + 1) % 2],
                                                      d[(j + 1) % 2])
                    self.projected_stereo[(j + 1) % 2].append(imgpoints2)

    def calculate_error(self):
        for j in range(self.n_cameras):
            ip = self.imgpoints[j]
            self.r_error_p[j] = []
            self.r_error[j] = []
            for i, _ in enumerate(ip):
                if self.m_stereo:
                    imgpoints2 = self.projected_stereo[j][i]
                else:
                    imgpoints2 = self.projected[j][i]
                self.r_error[j].append(np.sqrt((
                        np.power(np.linalg.norm(ip[i] - imgpoints2, axis=2), 2)
                        .mean())))
                self.r_error_p[j].append(np.linalg.norm(ip[i] - imgpoints2,
                                                        axis=2))
                # Calculated value to update progressbar
                c_porcent = (j * len(ip) + i + 1) \
                    / float(self.n_cameras * len(ip))
                self.progbar['value'] = c_porcent * 10.0
                # update label
                self.style_pg.configure('text.Horizontal.TProgressbar',
                                        text='{:g} %'
                                        .format(int(c_porcent * 100)))
                self.popup.update()  # for updating while running other process
                # update rms when the error for all the images is calculated
                if len(self.r_error[j]) == len(ip):
                    logging.info(self._('Updating RMS for camera %d'), j + 1)
                    self.rms[j] = np.sqrt(np.sum(np.square(self.r_error[j])) /
                                          len(self.r_error[j]))
                    if j == 1:
                        self.rms[2] = np.sqrt(
                            np.sum(np.square(self.r_error[0]
                                             + self.r_error[1]))
                            / len(self.r_error[0] + self.r_error[1]))
