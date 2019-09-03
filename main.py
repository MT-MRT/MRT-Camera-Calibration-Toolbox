import tkinter as tk
from mrt_camera_calibration_toolbox import MRTCalibrationToolbox

root = tk.Tk()

root.wait_visibility()
root.grab_set()
my_gui = MRTCalibrationToolbox(root)

root.mainloop()
