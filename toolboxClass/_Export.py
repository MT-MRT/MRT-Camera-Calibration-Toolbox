import logging
# import tkinter as tk
from tkinter import filedialog

from toolboxClass.export_functions import (export_features_to_folder,
                                           format_intrinsics,
                                           format_extrinsics,
                                           save_calibration_iteration)

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def export_features(self):
        """Function to export object points and image points."""
        if self.object_pattern is not None:
            t_choose = self._('Please select a folder for object points')
            op_folder = filedialog.askdirectory(parent=self.master,
                                                title=t_choose)
            ip_folders = []
            if self.n_total.get() > 0:
                for j in range(self.n_cameras):
                    t_choose = self._('Please select a folder for image '
                                      'points of each pose for camera ')
                    folder = filedialog.askdirectory(parent=self.master,
                                                     title=t_choose
                                                     + str(j + 1))
                    ip_folders.append(folder)
            else:
                ip_folders = [''] * self.n_cameras

            export_features_to_folder(
                self.object_pattern, self.detected_features,
                self.paths, self.n_cameras, op_folder, ip_folders)

    def exportCalibrationParameters(self):
        """Function to export the calibration parameters."""
        default_filenames = [self._('intrinsics_first_camera'),
                             self._('intrinsics_second_camera'),
                             self._('extrinsics')]
        for j in range(2 * int(self.m_stereo) + 1):
            filename = filedialog\
                       .asksaveasfilename(initialfile=default_filenames[j],
                                          defaultextension='.txt',
                                          filetypes=[(self._('Text files'),
                                                      '*.txt')])
            if filename != '':
                f = open(filename, 'w')
                if j < 2:
                    c_string = format_intrinsics(self.camera_matrix[j],
                                                 self.dist_coefs[j])
                    f.write(c_string)
                else:
                    c_string = format_extrinsics(self.R_stereo,
                                                 self.T_stereo)
                    f.write(c_string)
                f.close()
            else:
                return

    def exportCalibrationParametersIteration(self):
        """Function to export calibration results per Iteration."""
        logging.info(self._('exporting results per calibration'))

        t_choose = self._('Please select a folder')
        path_folder = filedialog.askdirectory(parent=self.master,
                                              title=t_choose)

        save_calibration_iteration(
            self.fx_array, self.fy_array, self.cx_array, self.cy_array,
            self.k1_array, self.k2_array, self.k3_array, self.k4_array,
            self.k5_array, self.R_array, self.T_array, self.RMS_array,
            self.samples, self.paths, self.n_cameras, path_folder,
            translate=self._)

