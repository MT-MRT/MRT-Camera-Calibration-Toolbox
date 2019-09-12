import logging
import tkinter as tk
from tkinter import filedialog
import numpy as np
import toolboxClass.miscTools.datastring

logging.basicConfig(level=logging.ERROR)

class Mixin:
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