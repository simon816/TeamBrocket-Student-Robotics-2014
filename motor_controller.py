"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

import math

MOTOR_RPM = {  # model: RPM
    '919D1481': 87, # Quoted value = 106
    '918D151': 2416 # Quoted value = 2416
}
MOTOR_MAP = {  # type: (motor_model, motor_board_serial, identifier: channel)
    'WHEELS': ('919D1481', 'SR0YG1F', {
        'LEFT': {'channel': 0, 'rpmoffset': 8},
        'RIGHT': {'channel': 1, 'rpmoffset': 0}
    })
}

DIAMETER = {
    'wheel': 0.1013
}

class MotorController(object):
    def __init__(self, robot, type, id):
        if type == 'wheel':
            map = MOTOR_MAP['WHEELS']
        else:
            raise TypeError("Unknown motor type %s" % type)

        self.diameter = DIAMETER[type]
        if id not in map[2].keys():
            raise TypeError("Invalid or no id for motor definition")
        board = robot.motors[map[1]]
        channel = map[2][id]['channel']
        self.RPM = MOTOR_RPM[map[0]] + map[2][id]['rpmoffset']
        self._motor = self._get_channel(board, channel)
        self.opp_dir = 0

    def _get_channel(self, board, channel):
        if not hasattr(board, 'm%d' % channel):
            raise TypeError("Unknown channel %d" % channel)
        return getattr(board, 'm%d' % channel)

    def forward(self, speed):
        if speed == 0: return self.stop()
        self.opp_dir = -1
        self._motor.power = abs(speed)

    def backward(self, speed):
        if speed == 0: return self.stop()
        self.opp_dir = 1
        self._motor.power = -abs(speed)

    def stop(self):
        self._motor.power = self.opp_dir
        self.opp_dir = 0

    def get_circumference(self):
        """Get circumference of motor wheel/rod using pre-defined
        diameter table."""
        return self.diameter * math.pi

    def get_rotations(self, seconds):
        """Return how many rotations would occur in the given seconds
        using pre-defined RPM table."""
        return (self.RPM / 60.0) * seconds

    def calc_distance(self, time, speed):
        """Calculate the expected distance moved in
        t seconds at d% speed."""
        circumference = self.get_circumference()
        revolutions = self.get_rotations(time)
        return circumference * revolutions * (speed / 100.0)

    def calc_wait_time(self, dist, speed):
        """Calculate the delay it takes to travel dist at d% speed."""
        dist, speed = abs(dist), abs(speed)
        return (6000 * dist) / (self.RPM * self.get_circumference() * speed)

    def calc_rpm(self, duration, actual_dist, speed):
        """
        Calculate the true RPM of the motor given the duration of the journey,
        the actual distance traveled and the speed as a percentage.
        The diameter of the circle that drives the movement (i.e wheel) must be
        known.

        Use this in testing to correct the RPM stated above.
        """

        return (6000*actual_dist) / (duration*self.get_circumference()*speed)
