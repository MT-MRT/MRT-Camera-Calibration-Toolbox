import logging

from toolboxClass.delete_functions import (create_empty_error,
                                           create_empty_camera_parameters,
                                           delete_single_image_data)

logging.basicConfig(level=logging.ERROR)


class Mixin:
    def reset_error(self):
        """Function to reset error related variables."""
        (self.r_error, self.r_error_p,
         self.projected, self.projected_stereo) = create_empty_error()

    def reset_camera_parameters(self):
        """Function to reset all intrinsics and extrinsics parameters."""
        (self.camera_matrix, self.dev_camera_matrix,
         self.dist_coefs, self.dev_dist_coefs,
         self.R_stereo, self.T_stereo, self.rms) = \
            create_empty_camera_parameters()

    def del_single(self):
        """Function to delete with Del key one image."""
        # get current index
        index = self.listbox.curselection()
        if index:
            self.update = False
            # delete for each selected image the path, original image,
            # features, projections, and erros from the corresponding list
            delete_single_image_data(
                self.paths, self.img_original, self.detected_features,
                self.projected, self.projected_stereo,
                self.r_error, self.r_error_p, self.n_cameras, index[0])
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
                    self.btn_zoom_more.config(state='disable')
                    self.btn_zoom_less.config(state='disable')
                    self.btn_move_feature.config(state='disable')
                    self.btn_locate.config(state='disable')
                    # disable run calibration button
                    self.btn_play.config(state='disable')
                    self.index.set(-1)
            # uses self.index which is updated in updatepicture
            self.loadBarError([0, 1])

    def del_all(self):
        """Function to delete all the session."""
        # enable the add session button
        self.btn_start.config(state='active')
        # disable the other toolbar buttons
        self.btn_add_file.config(state='disable')
        self.btn_add_folder.config(state='disable')
        self.btn_zoom_more.config(state='disable')
        self.btn_zoom_less.config(state='disable')
        self.btn_move_feature.config(state='disable')
        self.btn_locate.config(state='disable')
        self.btn_play.config(state='disable')
        self.btn_delete.config(state='disable')
        self.btn_settings.config(state='disable')
        self.btn_export.config(state='disable')
        self.btn_export2.config(state='disable')
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
