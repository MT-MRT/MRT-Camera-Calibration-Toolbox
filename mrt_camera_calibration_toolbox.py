import _GUI
import _Load
import _Popups
import _Update
import _Calibration
import _Plot
import _Export
import _Delete

class MRTCalibrationToolbox(_GUI.Mixin, _Load.Mixin, _Popups.Mixin, _Update.Mixin, _Calibration.Mixin, _Plot.Mixin, _Export.Mixin, _Delete.Mixin,):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self.screen_width = master.winfo_screenwidth()  # For two screens, divide by corresponding factor 2
        self.screen_height = master.winfo_screenheight()
        master.title("MRT Camera Calibration Toolbox")
        self.initialize_GUI_variables()
        self.initializeVariables()
        self.reset_camera_parameters()
        self.reset_error()
        self.initUI()
        self.traces_GUI()
        self.updateCameraParametersGUI()
