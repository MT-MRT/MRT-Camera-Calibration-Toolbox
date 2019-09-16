import logging
import numpy as np

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def reset_error(self):
        '''
        Function to reset error related variables
        '''
        # array of rms error for each pose
        self.r_error = [None, None]
        # array of pixel distance error for each feature
        self.r_error_p = [[], []]
        # projections
        self.projected = [[], []]
        self.projected_stereo = [[], []]

    def reset_camera_parameters(self):
        '''
        Function to reset all intrinsics and extrinsics parameters
        '''
        # camera matrix
        # array of 2 of 3*3 for camera parameters (mean and standard deviation)
        self.camera_matrix = [np.zeros((3, 3),
                              dtype=np.float32),
                              np.zeros((3, 3),
                              dtype=np.float32)]
        self.dev_camera_matrix = [np.zeros((3, 3),
                                  dtype=np.float32),
                                  np.zeros((3, 3),
                                  dtype=np.float32)]
        # array of 2 of 5*1 for distortion parameters (mean and standard dev.)
        self.dist_coefs = [np.zeros((5, 1),
                           dtype=np.float32),
                           np.zeros((5, 1),
                           dtype=np.float32)]
        self.dev_dist_coefs = [np.zeros((5, 1),
                               dtype=np.float32),
                               np.zeros((5, 1),
                               dtype=np.float32)]
        # rotational and translation matrix
        self.R_stereo = np.zeros((3, 3), dtype=np.float32)
        self.T_stereo = np.zeros((3, 1), dtype=np.float32)
        # rms error
        self.rms = [0, 0, 0]

    def del_single(self):
        '''
        Function to delete with Del key one image
        '''
        # get current index
        index = self.listbox.curselection()
        if index:
            self.update = False
            # delete for each selected image the path, original image,
            # features, projections, and erros from the corresponding list
            for j in range(self.n_cameras):
                del self.paths[j][index[0]]
                del self.img_original[j][index[0]]
                del self.detected_features[j][index[0]]
                if self.projected[j]:  # check if projection data exists
                    del self.projected[j][index[0]]
                if j == 1:
                    # check if stereo projection data exists
                    if self.projected_stereo[0]:
                        del self.projected_stereo[0][index[0]]
                        del self.projected_stereo[1][index[0]]
                # barchar
                if self.r_error[j]:  # check if reprojection error data exists
                    del self.r_error[j][index[0]]
                    del self.r_error_p[j][index[0]]
            # update number of total poses
            self.n_total.set(self.n_total.get() - 1)
            # check if there is already a selected image in data browser
            if index[0]:
                # for the case the last image is deleted, update the data
                # browser selection to the penultimate pose
                if index[0] == self.n_total.get():
                    self.index.set(index[0] - 1)
                    self.listbox.select_set(index[0] - 1)
                    self.listbox.yview(index[0] - 1)
                else:
                    self.index.set(index[0])
                    self.listbox.yview(index[0])
            else:
                # if there are images, set the first one as selected
                if self.n_total.get():
                    self.index.set(0)
                else:
                    # disable zoom in button
                    self.bot[3].config(state="disable")
                    self.bot[4].config(state="disable")
                    # disable run calibration button
                    self.bot[5].config(state="disable")
                    self.index.set(-1)
            # uses self.index which is updated in updatepicture
            self.loadBarError([0, 1])

    def del_all(self):
        '''
        Function to delete all the session
        '''
        # enable the add session button
        self.bot[0].config(state="active")
        # disable the other toolbar buttons
        for i in range(1, len(self.bot)):
            self.bot[i].config(state="disable")
        self.popup.destroy()
        # reset variables
        self.reset_camera_parameters()
        self.updateCameraParametersGUI()
        self.reset_error()
        self.loadBarError([0, 1])
        self.initializeVariables()
        self.index.set(-1)
        # set GUI for one camera
        self.frm[4].grid_forget()
        self.frm[5].grid_forget()
        self.frm[6].grid_forget()
        self.frm[8].grid_forget()
        self.frm[10].grid_forget()
