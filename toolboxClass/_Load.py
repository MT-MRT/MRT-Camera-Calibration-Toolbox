import logging
import os
# import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np

from toolboxClass.load_functions import (load_3d_points, detect_features,
                                         parse_intrinsics, parse_extrinsics,
                                         get_file_list)

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def load_3D_points(self):
        """Function to load 3D points from text."""
        self.load_files[0] \
            = filedialog.askopenfilenames(parent=self.popup,
                                          filetypes=[(self._('Text files'),
                                                      '*.txt')])
        if len(self.load_files[0]) == 0:
            self.object_pattern = None
            self.l_load_files[0].config(text=self
                                        ._('File missing, please add'),
                                        fg='red')
        else:
            set_3D_points = load_3d_points(self.load_files[0][0])
            if set_3D_points is None:
                self.l_load_files[0].config(text=self._('No 3D points'),
                                            fg='red')
                self.object_pattern = None
            else:
                self.l_load_files[0].config(text=self.load_files[0][0]
                                                     .rsplit('/', 1)[1],
                                            fg='black')
                self.check_errors_and_plot(None)

    def get_file_names(self, typeof, title_dialog):
        """Function for getting new files."""
        filenames = []
        # this is adding per file
        if typeof == 'p':
            t_choose = self._('Please select a file for ') + title_dialog
            filenames = filedialog.askopenfilenames(parent=self.master,
                                                    title=t_choose,
                                                    filetypes=self.ftypes)
        # this is adding per folder
        else:
            list_path = []
            t_options = [self._(' (first camera)'), self._(' (second camera)')]
            while len(list_path) < self.n_cameras:
                # create dialog for adding folders
                t_choose = self._('Please select a folder for ') \
                            + title_dialog \
                            + t_options[len(list_path)]
                path_folder = filedialog.askdirectory(parent=self.master,
                                                      title=t_choose)
                # checks that the selected folder exists
                if path_folder:
                    list_path.append(path_folder)
                else:
                    break
            for p in list_path:
                filenames.extend(get_file_list(p, self.valid_files))
        return filenames

    def assign_filename(self, j):
        self.load_files[j] \
            = filedialog.askopenfilenames(parent=self.popup,
                                          filetypes=[(self._('Text files'),
                                                      '*.txt')])
        if len(self.load_files[j]) == 0:
            self.l_load_files[j].config(text='', fg='black')
            # clear status check
            self.label_status_l[j + 1][1].config(text='')
            return
        else:
            self.l_load_files[j].config(text=self.load_files[j][0]
                                                 .rsplit('/', 1)[1],
                                        fg='black')
            f = open(self.load_files[j][0], 'r')
            a = f.read()
            if j <= 1:
                self.camera_matrix[j], self.dist_coefs[j] = \
                    parse_intrinsics(a)
            else:
                self.R_stereo, self.T_stereo = parse_extrinsics(a)
            # update status check
            self.label_status_l[j + 1][1].config(text=u'\u2714')
            if j == 2:
                self.label_status_l[3][0]\
                    .config(text=self._('3. Loading Extrinsics'))
            self.rms = [0, 0, 0]
            self.reset_error()
            self.updateCameraParametersGUI()
            self.loadBarError([0, 1])

    def add_file(self, typeof):
        """Function to add files to the session."""
        file_names_2D_points = self.get_file_names(typeof, self._('2D points'))

        if len(file_names_2D_points) == 0:
            if self.m_stereo:
                self.popup_importing_fails(self._(u'\nThe folder has no valid files to import.\n'))
            return
        # for stereo mode, checks if the folders have the same number of valid files
        elif self.m_stereo and len(file_names_2D_points) % 2 != 0:
            self.popup_importing_fails(self._(u'\nThe number of files per folder has to be the same for each camera.\n'))
            return

        l_msg, text_detail, b_cancel = self.popupmsg()

        rejected_images = []
        repeated_images = []
        no_valid_sized_images = []

        self.continue_importing = True
        for i, _ in enumerate(file_names_2D_points):
            if self.continue_importing:
                message = self._('Processing {0} of {1} images\n').format(i + 1, len(file_names_2D_points))
                l_msg.configure(text=message)
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
                        im = cv2.imread(file_name_2D_points, 0)
                        # check if image size is already initialized
                        if self.size[j] is None or len(self.paths[j]) == 0:
                            self.size[j] = im.shape
                            if self.size[j][0] > self.size[j][1]:
                                self.size[j] = (self.size[j][1], self.size[j][0])
                            
                            logging.debug('Initialized image size for camera %d...', j + 1)
                        # check if image size is valid
                        if im.shape == (self.size[j][1], self.size[j][0]):
                            im = cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE)

                        if im.shape == self.size[j]:
                            is_chessboard = self._(u'Chessboard') in self.pattern_type.get()
                            is_chessboard_sb = self._(u'Chessboard SB') in self.pattern_type.get()
                            is_asymmetric = self._(u'Asymmetric Grid') in self.pattern_type.get()
                            is_symmetric = self._(u'Symmetric Grid') in self.pattern_type.get()
                            ret, features = detect_features(
                                im, self.pattern_type.get(),
                                self.p_height, self.p_width,
                                is_chessboard=is_chessboard,
                                is_chessboard_sb=is_chessboard_sb,
                                is_asymmetric=is_asymmetric,
                                is_symmetric=is_symmetric)
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
                            # add image path to no_valid_sized_images
                            no_valid_sized_images.append(file_name_2D_points)
                            # add file path to path
                            self.paths[j].append(None)
                            # add original of image to img_original
                            self.img_original[j].append(None)
                            # add features to detected_features
                            self.detected_features[j].append(None)

                    else:
                        if self.size[j] is None or len(self.paths[j]) == 0:
                            self.size[j] = (self.image_height.get(),self.image_width.get())
                            logging.debug('Initialized image size for camera %d...', j + 1)
                        a = np.fromfile(file_name_2D_points,
                                        dtype=np.float32, sep=',')
                        a = a.reshape((int(len(a) / 2), 1, 2))
                        self.p_height = 1
                        self.p_width = len(a)
                        # add file path to path
                        self.paths[j].append(file_name_2D_points)
                        # add original of image to img_original
                        im = np.zeros(self.size[j])
                        self.img_original[j].append(im)
                        # add features to detected_features
                        self.detected_features[j].append(a)
                else:
                    repeated_images.append(file_name_2D_points)

                # percentage of completion of process
                c_percent = (i + 1) / float(len(file_names_2D_points))
                self.progbar['value'] = c_percent * 10.0
                # update label
                self.style_pg.configure('text.Horizontal.TProgressbar',
                                        text='{:g} %'.format(int(c_percent * 100)))
                # if one or more images failed the importing, add info
                message += self._('Imported: {0}\n').format(i + 1 - len(rejected_images) - len(repeated_images) - len(no_valid_sized_images))
                message += self._('Rejected: {0}\n').format(len(rejected_images))
                message += self._('Repeated: {0}\n').format(len(repeated_images))
                message += self._('Invalid sized: {0}\n').format(len(no_valid_sized_images))
                l_msg.configure(text=message)
                message = ''
                if rejected_images:
                    message += self._('Rejected: \n{0}\n').format('\n'.join(rejected_images))
                if repeated_images:
                    message += self._('Repeated: \n{0}\n').format('\n'.join(repeated_images))
                if no_valid_sized_images:
                    message += self._('Invalid sized images: \n{0}\n').format('\n'.join(no_valid_sized_images))
                text_detail.config(state='normal')
                text_detail.delete(1.0, 'end')
                text_detail.insert(1.0, message)
                text_detail.config(state='disable')

                self.popup.update()
            else:
                message = self._('Processed {0} of {1} images\n').format(i + 1, len(file_names_2D_points))
                message += self._('Imported: {0}\n').format(i + 1 - len(rejected_images) - len(repeated_images) - len(no_valid_sized_images))
                message += self._('Rejected: {0}\n').format(len(rejected_images))
                message += self._('Repeated: {0}\n').format(len(repeated_images))
                message += self._('Invalid sized: {0}\n').format(len(no_valid_sized_images))
                l_msg.configure(text=message)
                l_msg.configure(text=message)
                break

        if self.continue_importing:
            self.cancel_importing(b_cancel)

        index_to_delete = [i for i,
                           v in enumerate(self.paths[0]) if v is None]
        if self.m_stereo:
            index_to_delete = index_to_delete \
                              + [i for i,
                                 v in enumerate(self.paths[1]) if v is None]

        index_to_delete = sorted(set(index_to_delete), reverse=True)
        # delete rejected images
        for j in range(self.n_cameras):
            for i in list(index_to_delete):
                del self.paths[j][i]
                del self.img_original[j][i]
                del self.detected_features[j][i]

        # update total of images
        self.n_total.set(len(self.paths[0]))
        # enable and disable buttons depending of the succeed of the
        # importing process
        if self.n_total.get() > 0:
            self.btn_zoom_more.config(state='normal')  # enable zoom in button
            self.btn_zoom_less.config(state='normal')  # enable zoom out button
            self.btn_move_feature.config(state='normal')  # enable move feature button
            self.btn_locate.config(state='normal')  # enable locate button
            self.btn_play.config(state='normal')  # enable run calib button
        else:
            self.btn_zoom_more.config(state='disable')  # disable zoom in button
            self.btn_zoom_less.config(state='disable')  # disable zoom out button
            self.btn_move_feature.config(state='disable')  # disable move feature button
            self.btn_locate.config(state='disable')  # disable locate button
            self.btn_play.config(state='disable')  # disable run calib button
