from toolboxClass import _GUI, _Load, _Popups, _Update, _Calibration, _Plot,\
                         _Export, _Delete, _Language


class MRTCalibrationToolbox(_GUI.Mixin, _Load.Mixin, _Popups.Mixin,
                            _Update.Mixin, _Calibration.Mixin, _Plot.Mixin,
                            _Export.Mixin, _Delete.Mixin, _Language.Mixin):

    def __init__(self, master, *args, **kwargs):
        self.master = master
        if args and args[0] in ('en', 'de'):
            self.language = args[0]
        else:
            self.language = 'en'
        self.set_language()
        # For two screens, divide by corresponding factor 2
        w = master.winfo_screenwidth()
        h = master.winfo_screenheight()
        if (w / h == 32 / 9):
            w /= 2
        self.screen_width = w
        self.screen_height = h
        master.title(self._(u'MRT Camera Calibration Toolbox'))
        self.initialize_GUI_variables()
        self.initializeVariables()
        self.reset_camera_parameters()
        self.reset_error()
        self.initUI()
        self.traces_GUI()
        self.updateCameraParametersGUI()
        self.add_session_popup()
