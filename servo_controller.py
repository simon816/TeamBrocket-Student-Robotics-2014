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

SERVO_MAP = { # type: (Min rotation, Max rotation, servo board, servo slot)
    'GRABBER': (1, 50, 0, 6),
    'ARM': (1, 81, 0, 0)
}

class ServoController(object):
    def __init__(self, robot, type):
        if type.upper() in SERVO_MAP:
            data = SERVO_MAP[type.upper()]
        else:
            raise TypeError("Unknown servo type %s" % type)

        board, slot = data[2:4]
        if len(robot.servos) - 1 < board:
            raise IndexError("Unknown servo board %d" % board)
        if slot < 0 or slot > 7:
            raise IndexError("There are only 8 servo outputs on a servo board")
        self._servo = (robot.servos[board], slot)
        self.MIN, self.MAX = data[:2]

    def set_angle(self, angle):
        if angle < self.MIN or angle > self.MAX:
            raise ValueError("Cannot set angle greater or less than max or min")
        self._servo[0][self._servo[1]] = angle

    def get_angle(self):
        angle = self._servo[0][self._servo[1]]
        if angle < self.MIN:
            self.set_angle(self.MIN)
            angle = self.MIN
        elif angle > self.MAX:
            self.set_angle(self.MAX)
            angle = self.MAX
        return angle
