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

from sr.ruggeduino import (INPUT,
                           OUTPUT,
                           INPUT_PULLUP)

PIN_TYPES = {  # mode, signal_type {digital or analogue}
    'BUMP': (INPUT_PULLUP, 'digital'),
    'BUMP_SRC': (OUTPUT, 'digital'),
    'SENSOR': (INPUT_PULLUP, 'digital'),
    'SENSOR_SRC': (OUTPUT, 'digital')
}

PIN_MAP = {  # type: (board_serial, identifier: pin_no)
#    'BUMP': ('75230313833351314151', {
#            'BACK_L': 9,
#            'BACK_R': 7,
#            'FRONT_L': 5,
#            'FRONT_R': 11
#    }),
#    'BUMP_SRC': ('75230313833351314151', {
#            'BACK_L': 8,
#            'BACK_R': 6,
#            'FRONT_L': 4,
#            'FRONT_R': 10
#    }),
    'SENSOR': ('75230313833351314151', {
        'TOKEN_R': 3,
        'TOKEN_L': 5
    }),
    'SENSOR_SRC': ('75230313833351314151', {
        'TOKEN_R': 2,
        'TOKEN_L': 4
    })
}

class RuggeduinoController:
    def __init__(self, robot, type, id):
        type = type.upper()
        if type in PIN_MAP:
            map = PIN_MAP[type]
        else:
            raise TypeError("Unknown ruggeduino type %s" % type)

        if id not in map[1].keys():
            raise TypeError("Invalid or no id for ruggeduino definition")
        pin = map[1][id]

        ruggeduino = robot.ruggeduinos[map[0]]
        if not ruggeduino._is_srduino():
            raise TypeError("Must be an SR ruggeduino")

        info = PIN_TYPES[type]
        if pin in (0, 1) and info[1] == 'digital':
            raise IndexError("Cannot use pin %d as it is reserved internally" %
                             pin)
        if info[1] not in ('analogue', 'digital'):
            raise TypeError("Unknown signal type %r" % info[1])

        ruggeduino.pin_mode(pin, info[0])
        name = 'write' if info[0] == OUTPUT else 'read'
        self.is_output = name == 'write'
        self.is_input = not self.is_output
        function = '%s_%s' % (info[1], name)
        if function == 'analogue_write':
            raise NotImplementedError("Writing to analogue output not possible")
        method = getattr(ruggeduino, function)
        invert = info[0] == INPUT_PULLUP and info[1] == 'digital'
        self._ruggeduino = (method, pin, invert)
        def toString():
            return  "Ruggeduino(%s.%s)" % (type, id)
        self.__str__ = toString
        self.__repr__ = self.__str__

    def _run(self, *args):
        value = self._ruggeduino[0](*(self._ruggeduino[1],) + args)
        if self._ruggeduino[2]: value = not value
        return value

    def read(self):
        """Returns the value of the pin, float for analogue - the voltage,
        and boolean for digital - True for high and False for low."""
        if not self.is_input:
            raise TypeError("Trying to read a non-input pin")
        return self._run()

    def write(self, value):
        """Write a value to the pin,
        boolean only - True for high and False for low."""
        if not self.is_output:
            raise TypeError("Trying to write to a non-output pin")
        return self._run(value)
