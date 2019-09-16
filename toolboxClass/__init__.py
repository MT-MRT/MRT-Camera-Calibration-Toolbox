from toolboxClass import _GUI, _Load, _Popups, _Update, _Calibration, _Plot,\
                         _Export, _Delete


class MRTCalibrationToolbox(_GUI.Mixin, _Load.Mixin, _Popups.Mixin,
                            _Update.Mixin, _Calibration.Mixin, _Plot.Mixin,
                            _Export.Mixin, _Delete.Mixin,):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        # For two screens, divide by corresponding factor 2
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        master.title("MRT Camera Calibration Toolbox")
        self.initialize_GUI_variables()
        self.initializeVariables()
        self.reset_camera_parameters()
        self.reset_error()
        self.initUI()
        self.traces_GUI()
        self.updateCameraParametersGUI()
        self.add_session_popup()
