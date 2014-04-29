"""
    This file is part of Team Brocket Robotics (herein BrocketSource).

    BrocketSource is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BrocketSource is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with BrocketSource. If not, see <http://www.gnu.org/licenses/>.
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
