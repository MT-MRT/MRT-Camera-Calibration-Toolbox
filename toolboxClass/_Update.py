import logging
import tkinter as tk
from toolboxClass.miscTools.misc_tools import float2StringVar

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def updateSelection(self, event):
        '''
        Function for the click event over the data browser
        '''
        widget = event.widget
        self.zoomhandler = 0
        if widget.curselection():
            self.index.set(widget.curselection()[0])
        if self.r_error[0]:
            self.loadBarError([1])
            self.updateBarError(0)

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

    def updateCameraParametersGUI(self):
        '''
        Function to update all the labels values from the calculated parameters
        in the calibration
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
