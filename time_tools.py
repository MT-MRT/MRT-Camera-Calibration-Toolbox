import time


class chronometer():
    def __init__(self):
        self.t = time.time()

    def gettime(self):
        return time.time() - self.t
