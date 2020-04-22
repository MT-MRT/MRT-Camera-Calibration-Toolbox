import logging
# import tkinter as tk
from tkinter import filedialog
import numpy as np
import toolboxClass.miscTools.datastring as datastring

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def export_features(self):
        '''
        Function to export object points and image points
        '''
        if self.object_pattern != None:
            t_choose = self._('Please select a folder for object points')
            path_folder = filedialog.askdirectory(parent=self.master, title=t_choose)
            if path_folder != '':
                np.savetxt(path_folder + '/op.txt', self.object_pattern.reshape(-1), newline=',')
            if self.n_total.get() > 0:
                for j in range(self.n_cameras):
                    t_choose = self._('Please select a folder for image points of each pose for camera ')
                    path_folder = filedialog.askdirectory(parent=self.master, title=t_choose + str(j + 1))
                    if path_folder != '':
                        for index in range(len(self.paths[j])):
                            feature = self.detected_features[j][index]
                            np.savetxt(path_folder + '/f_%d.txt'%index, feature.reshape(-1), newline=',')
                                
    def exportCalibrationParameters(self):
        '''
        Function to export the calibration parameters
        '''
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
                    c_string = datastring\
                               .instrinsic2string(self.camera_matrix[j],
                                                  self.dist_coefs[j])
                    f.write(c_string)
                else:
                    c_string = datastring\
                               .extrinsic2string(self.R_stereo,
                                                 self.T_stereo)
                    f.write(c_string)
                f.close()
            else:
                return

    def exportCalibrationParametersIteration(self):
        '''
        Function to export calibration results per Iteration
        '''
        logging.info(self._('exporting results per calibration'))

        t_choose = self._('Please select a folder')
        path_folder = filedialog.askdirectory(parent=self.master,
                                              title=t_choose)

        if path_folder != '':
            for j in range(self.n_cameras):
                filename = '/fx_cam_' + str(j + 1) + '.txt'
                np.array(self.fx_array[j]).tofile(path_folder + filename, '\n')
                filename = '/fy_cam_' + str(j + 1) + '.txt'
                np.array(self.fy_array[j]).tofile(path_folder + filename, '\n')
                filename = '/cx_cam_' + str(j + 1) + '.txt'
                np.array(self.cx_array[j]).tofile(path_folder + filename, '\n')
                filename = '/cy_cam_' + str(j + 1) + '.txt'
                np.array(self.cy_array[j]).tofile(path_folder + filename, '\n')
                filename = '/k1_cam_' + str(j + 1) + '.txt'
                np.array(self.k1_array[j]).tofile(path_folder + filename, '\n')
                filename = '/k2_cam_' + str(j + 1) + '.txt'
                np.array(self.k2_array[j]).tofile(path_folder + filename, '\n')
                filename = '/k3_cam_' + str(j + 1) + '.txt'
                np.array(self.k3_array[j]).tofile(path_folder + filename, '\n')
                filename = '/k4_cam_' + str(j + 1) + '.txt'
                np.array(self.k4_array[j]).tofile(path_folder + filename, '\n')
                filename = '/k5_cam_' + str(j + 1) + '.txt'
                np.array(self.k5_array[j]).tofile(path_folder + filename, '\n')
                if j == 1:
                    filename = self._('/rotation.txt')
                    f = open(path_folder + filename, 'w')
                    for r in self.R_array:
                        f.write(','.join(str(e) for e in r) + '\n')
                    f.close()
                    filename = self._('/translation.txt')
                    f = open(path_folder + filename, 'w')
                    for t in self.T_array:
                        f.write(','.join(str(e[0]) for e in t) + '\n')
                    f.close()

            filename = self._('/rms') + '.txt'
            np.array(self.RMS_array).tofile(path_folder + filename, '\n')
            filename = self._('/samples') + '.txt'
            f = open(path_folder + filename, 'w')
            for s in self.samples:
                f.write('[')
                for j in range(self.n_cameras):
                    if j == 1:
                        f.write(',')
                    f.write('[')
                    l_paths_s = list(self.paths[j][i] for i in s)
                    f.write(','.join(str(e) for e in l_paths_s))
                    f.write(']')
                f.write(']')
                f.write('\n')
            f.close()
