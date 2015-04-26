"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

import threading

class ThreadRegister:
    def __init__(self, io):
        self.threads = {}
        self.io = io
    def add_thread(self, thread):
        self.threads[thread.name] = thread
        thread.reg = self
        thread.io = self.io
        thread.daemon = True
        thread.setup()
    def check_running_state(self, thread):
        return True

class Runnable(threading.Thread):
    def setup(self):
        pass

class BumpThread(Runnable):
    def setup(self):
        self.name = "bump_thread"
        self.sensors = [self.io.bump_FrL, self.io.bump_FrR,
                        self.io.bump_BkL, self.io.bump_BkR]
    def run(self):
        while self.reg.check_running_state(self):
            for sensor in self.sensors:
                if sensor.read():
                    self.io.bumped(sensor)
            self.io.wait(0.2)
