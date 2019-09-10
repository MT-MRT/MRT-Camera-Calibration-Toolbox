import tkinter as tk

import MRTCalibrationToolbox

root = tk.Tk()

root.wait_visibility()
root.grab_set()
my_gui = MRTCalibrationToolbox(root)

root.mainloop()
