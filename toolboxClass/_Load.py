import logging
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2
import numpy as np

logging.basicConfig(level=logging.ERROR)


class Mixin:
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
    