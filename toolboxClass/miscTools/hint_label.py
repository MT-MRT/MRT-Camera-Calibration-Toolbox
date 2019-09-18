# Loading a hint label with mouseoverevent as seen in:
# https://www.python-forum.de/viewtopic.php?t=18687 user wuf
# modified by Sebastian Schramm

import tkinter as tk


class MyHintLabel(tk.Toplevel):

    def __init__(self, xpos, ypos, message, auto_clear=False):
        '''
        Show hint
        '''
        self.xpos = xpos
        self.ypos = ypos
        self.message = message
        self.auto_clear = auto_clear

        self.TIP_X_OFFSET = 8
        self.TIP_Y_OFFSET = 8
        self.AUTO_CLEAR_TIME = 1000  # ms
        self.TIP_SYMBOL = 'Bla Bla Bla!'

        tk.Toplevel.__init__(self)
        self.overrideredirect(True)

        self.message_label = tk.Label(self, compound='left', text=self.message,
                                      bg='white', fg='#9A1046')
        self.message_label.pack()
        self.geometry("+%d+%d" % (self.xpos+self.TIP_X_OFFSET,
                                  self.ypos+self.TIP_Y_OFFSET))

        if self.auto_clear:
            self.after(self.AUTO_CLEAR_TIME, self.clear_tip)

    def clear_hint(self):
        '''
        Destroy hint
        '''
        self.destroy()
