# MRT Camera Calibration Toolbox

## Introduction

The MRT Camera Calibration Toolbox is an application, developed in Python using OpenCV, which determines the parameters of a camera's perspective projection by performing an intrinsic and extrinsic geometric calibration. The application provides intrinsics, extrinsics and lens distortion parameters for each camera (two for stereo mode). For stereo mode, the transformations between the individual camera coordinate systems are given as well. The information for each camera pose can be loaded using images or text files with the 2D points of the pattern. The calibration can be also made using random subgroups from the total set of images. The computed parameters are the averaged over all iterations (subgroups), and both the final results and results per calibration can be exported to text files. 

## Why use this Toolbox?

- Calibration of multispectral stereo camera systems
- Calibration of camera systems with different resolutions
- Visualization of the reprojection error
- Image Cover Visibility
- Statistical validation by means of calibration with subsets
- Import and export of data
- It's free!

## Citation:  

So far no publication has been written on the current toolbox, we recommend the following paper for citation of the geometric calibration of cameras in several spectral ranges:
```
@INPROCEEDINGS{Rangel2014,
  author = {Rangel González, Johannes Havid and Soldan, Samuel and Kroll, Andreas},
  title = {3D Thermal Imaging: Fusion of Thermography and Depth Cameras},
  booktitle = {12th International Conference for Quantitative InfraRed Thermography (QIRT 2014)},
  year = {2014},
  address = {Bordeaux, France}
}
```

## Contact:  

If you have any questions, please email Daniela Aguirre Salazar at daguirres@unal.edu.co or Sebastian Schramm at sebastian.schramm@mrt.uni-kassel.de.
 
[Visit us](https://www.uni-kassel.de/maschinenbau/institute/mess-und-regelungstechnik/mrt.html)

