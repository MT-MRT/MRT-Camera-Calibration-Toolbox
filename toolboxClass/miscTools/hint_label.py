# Loading a hint label with mouseoverevent as seen in:
# https://www.python-forum.de/viewtopic.php?t=18687 user wuf
# modified by Sebastian Schramm

import tkinter as tk
import threading


class MyHintLabel(tk.Toplevel):

    def __init__(self, message,
                 auto_clear=False, wait_popup=True):
        """Init hint."""
        self.message = message
        self.auto_clear = auto_clear
        self.wait_popup = wait_popup

        self.AUTO_CLEAR_TIME = 6000  # ms
        self.POPUP_TIME = 3.0  # s

        self.TIP_X_OFFSET = 10
        self.TIP_Y_OFFSET = 10

        if self.wait_popup:
            self.load_hint()
            self.timer = threading.Timer(self.POPUP_TIME, self.show_hint)
            self.timer.start()
        else:
            self.load_hint()
            self.show_hint()

        if self.auto_clear:
            self.after(self.POPUP_TIME, self.clear_hint)

    def load_hint(self):
        """Load hint."""
        tk.Toplevel.__init__(self)
        self.overrideredirect(True)
        self.message_label = tk.Label(self, compound='left', text=self.message,
                                      bg='#EFEFFF', fg='#9A1046')

        self.message_label.pack()
        self.attributes("-alpha", 0.0)

    def show_hint(self):
        """Show hint."""
        try:
            self.xpos = self.winfo_pointerx()  # get actual cursor position
            self.ypos = self.winfo_pointery()
            self.geometry('+%d+%d' % (self.xpos+self.TIP_X_OFFSET,
                                      self.ypos+self.TIP_Y_OFFSET))
            self.attributes("-alpha", 0.85)
        except (tk.TclError, RuntimeError):
            pass

    def clear_hint(self):
        """Destroy hint."""
        self.destroy()
