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

## Requirements

To use the toolbox, the modules listed below has to be installed on your computer. 

- Python3 (Tested for Python 3.4 and Python 3.6)
- OpenCV 4.1
- tkinter 8.6
- PIL 5.4.1
- numpy 1.16.4
- matplotlib 1.3.1

## Installation

You can download the source code and excecute the toolbox [mrt_camera_calibration_toolbox.py](https://github.com/MT-MRT/MRT-Camera-Calibration-Toolbox/blob/master/main.py) directly on your computer through the Linux or Windows terminal:

```
cd path/to/your/toolbox
python3 main.py
```

## Getting Started

Check this animation of a running example of the MRT Camera Calibration Toolbox. 

![example](https://github.com/MT-MRT/MRT-Camera-Calibration-Toolbox/blob/master/docs/example_single_chessboard.gif)

## Documentation

Documentation is currently under development...

## Contributing 

Contributions are very welcome. Open a fresh issue to start a discussion around a feature idea or a bug.

## Acknowledgments

For [quaternions.py](https://github.com/MT-MRT/MRT-Camera-Calibration-Toolbox/blob/master/quaternions.py) code based on: Christoph Hagen. "averaging quaternions". Available here: https://github.com/christophhagen/averaging-quaternions

Toolbar icons obtain from: https://www.iconfinder.com

## Citation

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

## Contact

If you have any questions, please email Daniela Aguirre Salazar at daguirres@unal.edu.co or Sebastian Schramm at sebastian.schramm@mrt.uni-kassel.de.
 
[Visit us](https://www.uni-kassel.de/maschinenbau/institute/mess-und-regelungstechnik/mrt.html)

