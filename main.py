import tkinter as tk
from toolboxClass import MRTCalibrationToolbox

# 'en' or 'de'
language = 'en'

root = tk.Tk()
root.wait_visibility()
root.grab_set()
my_gui = MRTCalibrationToolbox(root, language)
root.mainloop()
