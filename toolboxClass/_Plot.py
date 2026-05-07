import logging
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

from toolboxClass.plot_functions import (create_feature_image,
                                         create_heat_map,
                                         create_moving_features_image,
                                         create_projection_image)

logging.basicConfig(level=logging.ERROR)

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240


class Mixin:
    def updateSelectionperclick(self, selection, i):
        """Function for the click event over the error bars."""
        # This corresponds to a click over the RMS reprojection error chart
        if i == 0:
            self.zoomhandler = 0
            self.listbox.selection_clear(0, tk.END)
            self.index.set(selection - 1)
            # This make sense for update by click in bar chart
            self.listbox.select_set(selection - 1)
            self.listbox.yview(selection - 1)
            self.loadBarError([1])
            self.updateBarError(0)
        # This corresponds to a click over the Pixel error chart
        else:
            self.index_corner.set(selection - 1)
            self.updatePicture(None)
            self.updateBarError(1)

    def click_to_zoom(self, event, camera):
        """Function for the click event with a zoom sunken button.

        Detects the x,y click position and calculates the image resizing scale.
        """
        self.scale = 1.0
        self.x = event.x
        self.y = event.y
        # check if the zoom in button is sunken and current zoom is less than
        # maximum
        if self.btn_zoom_more.config('relief')[-1] == 'sunken' \
                and self.zoomhandler < 10:
            self.scale /= self.delta
            self.imscale /= self.delta
            self.zoomhandler += 1
        # check if the zoom out button is sunken and current zoom is less than
        # minimum
        elif self.btn_zoom_less.config('relief')[-1] == 'sunken' \
                and self.zoomhandler > 0:
            self.scale *= self.delta
            self.imscale *= self.delta
            self.zoomhandler -= 1
        # check if there are loaded images and if the locate button in enable
        elif self.paths[camera] and self.btn_locate.config('relief')[-1] == 'sunken':
            selection = 1
            for poly in self.polygons:
                contains, _ = poly.contains(event)
                if contains:
                    self.listbox.selection_clear(0, tk.END)
                    self.index.set(selection - 1)
                    # This make sense for update by click in bar chart
                    self.listbox.select_set(selection - 1)
                    self.listbox.yview(selection - 1)
                    self.loadBarError([1])
                    self.updateBarError(0)
                    break
                selection += 1
        elif self.paths[camera] and self.btn_move_feature.config('relief')[-1] == 'sunken' and self.tabControl[
            camera].index(self.tabControl[camera].select()) == 1:
            width = self.size[camera][1]
            height = self.size[camera][0]
            x_offset, y_offset = self.list_panel[camera][0].coords('all')
            x_image = (self.x - x_offset) / self.imscale * width / DEFAULT_WIDTH
            y_image = (self.y - y_offset) / self.imscale * width / DEFAULT_WIDTH
            if 0 <= x_image <= width and 0 <= y_image <= height:
                self.new_coord_feature[camera] = [[x_image, y_image]]
        self.updatePicture()

    def scroll_to_zoom(self, ztype, event):
        self.scale = 1.0
        self.x = event.x
        self.y = event.y
        if ztype == 'm' and self.zoomhandler < 10:
            self.scale /= self.delta
            self.imscale /= self.delta
            self.zoomhandler += 1
        elif self.zoomhandler > 0:
            self.scale *= self.delta
            self.imscale *= self.delta
            self.zoomhandler -= 1
        self.updatePicture()

    def toggle_zoom_buttons(self, button1, button2):
        """Function to keep only one zoom button enable."""
        if button1.config('relief')[-1] == 'sunken':
            button1.config(relief='raised')
        else:
            button1.config(relief='sunken')
            button2.config(relief='raised')
        # disable locate button
        self.btn_locate.config(relief='raised')
        self.btn_move_feature.config(relief='raised')
        self.select_feature.grid_forget()
        self.btn_change_feature.grid_forget()

    def clickpoint_to_image(self):
        """Function to select image with clicked point in canvas."""
        if self.btn_locate.config('relief')[-1] == 'sunken':
            self.btn_locate.config(relief='raised')
        else:
            self.btn_locate.config(relief='sunken')
        # disable zoom buttons
        self.btn_zoom_more.config(relief='raised')
        self.btn_zoom_less.config(relief='raised')
        self.btn_move_feature.config(relief='raised')
        self.select_feature.grid_forget()
        self.btn_change_feature.grid_forget()

    def change_position_feature(self):
        """Function to change feature position."""
        for camera in range(self.n_cameras):
            if self.new_coord_feature[camera]:
                self.detected_features[camera][self.index.get()][self.index_corner.get()] = self.new_coord_feature[
                    camera]
        self.popup.destroy()
        self.updatePicture()

    def move_feature(self):
        """Function to select a coordinate point by clicking."""
        if self.btn_move_feature.config('relief')[-1] == 'sunken':
            self.btn_move_feature.config(relief='raised')
            self.select_feature.grid_forget()
            self.btn_change_feature.grid_forget()
        else:
            self.btn_move_feature.config(relief='sunken')
            self.new_coord_feature = [[], []]
            self.select_feature['values'] = list(range(self.p_height*self.p_width))
            self.select_feature.grid(row=0, column=6, sticky=tk.W)
            self.btn_change_feature.grid(row=0, column=7, sticky=tk.W)
        # disable zoom buttons
        self.btn_zoom_more.config(relief='raised')
        self.btn_zoom_less.config(relief='raised')
        self.btn_locate.config(relief='raised')
        self.updatePicture()

    def update_index_corner(self, *args):
        self.new_coord_feature = [[], []]
        self.updatePicture()

    def updatePicture(self, *args):
        """Function to update pictures in panel of tabs."""
        selection = self.index.get()
        # checks for a valid selection
        if selection >= 0:
            # update selection in data browser
            self.listbox.activate(selection)
            images = []
            for j in range(self.n_cameras):
                images.append([])
                # get original of the selected image
                images[j].append(Image.fromarray(
                        self.img_original[j][selection]))
                # get images with marked features of the selected image
                if self.paths[j] and self.btn_move_feature.config('relief')[-1] == 'sunken':
                    images[j].append(Image.fromarray(self.show_moving_features(j, selection)))
                else:
                    images[j].append(Image.fromarray(self.image_features(j, selection)))
                # get heat_map for all the images in camera
                images[j].append(Image.fromarray(
                        self.heat_map[j]))
                # get projection image with intrinsic parameters of the
                # selected image
                images[j].append(Image.fromarray(
                        self.project_detected_features(j, selection)))
                # get projection image with the intrinsics of the other camera
                # and extrinsics between the cameras of the selected image
                images[j].append(Image.fromarray(
                        self.project_detected_features(j,
                                                       selection,
                                                       forExtrinsics=True)))
            # scale image if zoom applies and update panel of tabs
            if self.zoomhandler != 0:
                width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
                new_size = int(self.imscale * width), int(self.imscale
                                                          * height)
                for j in range(self.n_cameras):
                    for i in range(len(self.list_panel[j])):
                        self.list_panel[j][i].scale('all', self.x, self.y,
                                                    self.scale, self.scale)
                        self.img[j][i] = ImageTk.PhotoImage(
                                    images[j][i].resize(new_size))
                        self.list_panel[j][i].itemconfig(
                                    self.list_image_on_panel[j][i],
                                    image=self.img[j][i])
            # Update panel of tabs
            else:
                self.imscale = 1
                width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
                new_size = int(self.imscale * width), int(self.imscale
                                                          * height)
                for j in range(self.n_cameras):
                    for i in range(len(self.list_panel[j])):
                        self.list_panel[j][i].scale('all', 0, 0, 1, 1)
                        self.list_panel[j][i].coords(
                                self.list_image_on_panel[j][i], 0, 0)
                        self.img[j][i] = ImageTk.PhotoImage(
                                images[j][i].resize(new_size))
                        self.list_panel[j][i].itemconfig(
                                self.list_image_on_panel[j][i],
                                image=self.img[j][i])
            self.scale = 1

        # for no valid selection, update with empty picture the panel of tabs
        else:
            for j in range(self.n_cameras):
                for i in range(len(self.list_panel[j])):
                    self.list_panel[j][i].delete('all')
                    self.list_image_on_panel[j][i] = \
                        self.list_panel[j][i].create_image(0, 0,
                                                           anchor=tk.N
                                                           + tk.W,
                                                           image=None)

    # self.panel1.itemconfig(self.image_on_panel1, image = None)

    def image_features(self, camera, index):
        """Function to create an picture with the original one and its detected features with markers."""
        features = self.detected_features[camera][index]
        im = self.img_original[camera][index]
        return create_feature_image(im, features, self.p_height, self.p_width)

    def update_added_deleted(self, *args):
        """Function to update heat map when a new image is added or an image is deleted."""
        self.polygons = []
        DEFAULT_WIDTH = 320
        DEFAULT_HEIGHT = 240
        self.zoomhandler = 0
        if self.n_total.get() > 0:
            for j in range(self.n_cameras):
                # recalculate heat_map
                self.heat_map[j] = self.density_cloud_heat_map(j)
        for j in range(self.n_cameras):
            width = self.size[j][1]
            height = self.size[j][0]
            for i in range(len(self.paths[0])):
                geometry = []
                points = [0,self.p_height-1,self.p_width*self.p_height-1,self.p_width*self.p_height-self.p_height]
                for p in points:
                    c = self.detected_features[j][i][p]
                    x_p = c[0][0]*DEFAULT_WIDTH/width
                    y_p = c[0][1]*DEFAULT_HEIGHT/height
                    geometry.append([x_p, y_p])
                poly = plt.Polygon(geometry)
                self.polygons.append(poly)
        # update data browser
        self.loadImagesBrowser()

    def density_cloud_heat_map(self, camera):
        """Function to calculate a density cloud map of all the images using its detected features."""
        return create_heat_map(self.size[camera],
                               self.detected_features[camera])


    def show_moving_features(self, camera, index):
        """Function to represent new desired feature position after click."""
        im = self.img_original[camera][index]
        return create_moving_features_image(
            im, self.size[camera], self.detected_features[camera],
            index, self.index_corner.get(), self.new_coord_feature[camera])


    def project_detected_features(self, camera, index, forExtrinsics=False):
        """Function to get the images comparing the original in green and its projection in red.

        The current selected feature index is represented by a circle over the point.
        """
        im = self.img_original[camera][index]
        if forExtrinsics:
            projections = self.projected_stereo[camera]
        else:
            projections = self.projected[camera]

        return create_projection_image(
            im, self.size[camera], self.detected_features[camera],
            projections, index, self.index_corner.get(),
            self.p_height, self.p_width)


    def updateBarError(self, k):
        """Function to update the color of the bars in the bar charts depending of the selection.

        The selected bar is red, the others are blue.
        """
        if k == 0:
            index = self.index.get()
        else:
            index = self.index_corner.get()
        for j in range(self.n_cameras):
            # TODO maybe save old index?
            if self.r_error[j]:
                for i in range(len(self.dr[k][j])):
                    if i == index:
                        self.dr[k][j][i].set_color('#9a1046')
                    else:
                        self.dr[k][j][i].set_color('#5095c8')
                self.bar[k][j].draw()

    def loadBarError(self, r_up):
        """Function to update error bar chart."""
        xlabel_names = [self._('Images'), self._('Features')]
        title_names = [self._('RMS Reprojection Error'),
                       self._('Pixel Distance Error')]
        factor_width = [10, 7]
        for k in r_up:
            self.dr[k] = []
            for j in range(self.n_cameras):
                self.ax[k][j].clear()
                data = None
                m_error = None
                index = None
                # getting error data depending of the chart type
                # (RMS reprojection error or pixel distance error)
                if k == 0:
                    if self.r_error[j]:
                        data = self.r_error[j]
                        m_error = np.mean(data)
                        index = self.index.get()
                else:
                    if self.r_error_p[j]:
                        # converted to size-1 arrays
                        data = self.r_error_p[j][self.index.get()].T[0]
                        index = self.index_corner.get()

                if data is not None:
                    # defining bars of the chart #
                    ind = np.arange(len(data))
                    # height of bars correspond to the list of data errors
                    rects = self.ax[k][j].bar(ind, data, align='center')
                    self.dr[k].append([])
                    # set bars color according to index of selected image
                    for rect, i in zip(rects, ind):
                        rect.set_label(i + 1)
                        if i == index:
                            rect.set_color('#9a1046')
                        else:
                            rect.set_color('#5095c8')
                        self.dr[k][j].append(rect)
                    # set tick of labels for the x and y axes
                    self.ax[k][j].set_xticks(ind)
                    if self.ax[k][j].patches:
                        self.ax[k][j].set_xticklabels(tuple(ind + 1),
                                                      rotation=65,
                                                      size=self.ax[k][j]
                                                               .patches[0]
                                                               .get_width()
                                                      * factor_width[k])
                        # draw to update, necessary to keep changes
                        self.bar[k][j].draw()
                        y_ticks = self.ax[k][j].get_yticks()
                        self.ax[k][j].set_yticks(y_ticks)
                        self.ax[k][j].set_yticklabels(
                                [item.get_text() for item in
                                 self.ax[k][j].get_yticklabels()], size=10)
                    # create dashed line for RMS reprojection mean
                    if k == 0:
                        self.ax[k][j].axhline(y=m_error, color='k',
                                              linestyle='--', label='z')
                        handles, _ = self.ax[k][j].get_legend_handles_labels()
                        self.ax[k][j].\
                            legend(handles[0:1],
                                   [self
                                    ._('Mean RMS Reprojection Error is: %.5f')
                                    % m_error],
                                   loc='lower center',
                                   prop={'size': self.ax[k][j].
                                         patches[0].get_width() * 15})
                    # inform about the not updated of the chart when applies
                    if self.update:
                        self.ax[k][j].set_title(title_names[k], fontsize=10)
                    else:
                        self.ax[k][j].set_title(title_names[k]
                                                + self._(' (Not Updated)'),
                                                color='#9a1046',
                                                fontsize=10)
                # for empty error data, only set the chart titles
                else:
                    self.ax[k][j].set_title(title_names[k], fontsize=10)
                # set names of labels for the x and y axes
                self.ax[k][j].set_xlabel(xlabel_names[k], fontsize=7)
                self.ax[k][j].set_ylabel('Pixels', fontsize=7)
                # set size chart and re draw the bars
                self.ax[k][j].autoscale(tight=True)
                self.f[k][j].tight_layout()  # Adjust size
                self.bar[k][j].draw()

    def on_press(self, event, i, j):
        """Function to handle the event of pressing over one of the bar in the chart to update selected pose.

        j is camera, i is graphic. TODO: Maybe change logic? (easier to understand...).
        """
        # checks if a calibration has already succeed
        if self.camera_matrix[0][0][0] != 0:  # Fx is zero only when reset
            b_continue = False
            for rect in self.dr[i][j]:
                if event.inaxes == rect.axes:
                    b_continue = True
                    break
            if b_continue:
                # compares if the click is inside the bar,
                # for each bar in the chart
                for rect in self.dr[i][j]:
                    contains, _ = rect.contains(event)
                    # update for the selected bar
                    if contains:
                        self.updateSelectionperclick(int(rect.get_label()), i)
                        break
