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

import time
import math
import logging
import threading

from motor_controller import MotorController
from vision_controller import VisionController, MarkerFilter, Marker, Token
from sr import MARKER_ROBOT
from servo_controller import ServoController
from ruggeduino_controller import RuggeduinoController
from threads import *
from state_utils import StateInterrupt

UP, DOWN, MIDDLE = ('UP', 'DOWN', 'MIDDLE')
OPEN, CLOSE = ('OPEN', 'CLOSE')
CENTER, WHEEL = ('center', 'wheel')
WHEEL_SPAN = 0.378

class IOInterface(object):

    def __init__(self, Robot):
        self.log = logging.getLogger('Robot.IO')
        self.log.info("Initializing")
        # Aliases for English readability
        self.drive = self.turn = self._move

        try:
            self._setup_controllers(Robot)
        except:
            self.log.critical("Could not set-up hardware controller")
            raise
        try:
            self.running = True
            tr = ThreadRegister(self)
            #self.bump_thread = BumpThread()
            self._bump_callback = lambda s: None
            self._marker_callback = lambda m: None
            #tr.add_thread(self.bump_thread)
            #self.bump_thread.start()
        except Exception as e:
            self.log.critical("Unable to start threads")
            self.log.exception(e)
            raise
        
        self.log.info("Done")

    def _setup_controllers(self, robot):
        self.log.debug("Setup controllers")
        self.left_wheel = MotorController(robot, type='wheel', id='LEFT')
        self.right_wheel = MotorController(robot, type='wheel', id='RIGHT')
        self.camera = VisionController(robot)
        self.grabber = ServoController(robot, type='grabber')
        self.arm = ServoController(robot, type='arm')
        self._setup_switch_sources(robot)
        #self.bump_FrL = RuggeduinoController(robot, type='bump', id='FRONT_L')
        #self.bump_FrR = RuggeduinoController(robot, type='bump', id='FRONT_R')
        #self.bump_BkL = RuggeduinoController(robot, type='bump', id='BACK_L')
        #self.bump_BkR = RuggeduinoController(robot, type='bump', id='BACK_R')
        self.token_sensL = RuggeduinoController(robot, type='sensor', id='TOKEN_L')
        self.token_sensR = RuggeduinoController(robot, type='sensor', id='TOKEN_R')

    def _setup_switch_sources(self, robot):
        #for id in ['FRONT_L', 'FRONT_R', 'BACK_L', 'BACK_R']:
        #    RuggeduinoController(robot, type='bump_src', id=id).write(False)
        RuggeduinoController(robot, type='sensor_src', id='TOKEN_L').write(False)
        RuggeduinoController(robot, type='sensor_src', id='TOKEN_R').write(False)

    def _move(self, instruction):
        if not isinstance(instruction, MoveInstruction):
            raise TypeError("Invalid movement instruction")
        self.log.debug("Do movement %s", instruction)
        instruction.action(self)

    def goto_marker(self, marker, speed, comparator=None, offset=0):
        self.log.debug("goto marker %s %.1f", marker, speed)
        if comparator is None or not hasattr(comparator, '__call__'):
            comparator = lambda a, b: a.info.code == b.info.code
        reached = False
        blind_spot = 0.66
        while True: # Alternatively, on each new find, call goto_marker within
            horiz_dist = Marker(marker).horizontal_dist - offset
            travel_dist = horiz_dist / 2 # set dist to travel half the measured
            if marker.rot_y < 0:
                Dir = Left # negative rot_y indicates a left turn
            else:
                Dir = Right # positive rot_y means right turn
            if not reached: # if reached flag is true then should not rotate
                degree = marker.rot_y
                if degree < 1: degree += 0.7 # rotation < 1 is too subtle
                if degree < 2: degree *= 2 # amplify rotation
                self.turn(Dir(degree, Speed(speed / 3))) # face marker
            self.drive(Distance(travel_dist, speed)) # drive half way
            if reached: # set below
                self.log.info("Reached marker")
                break
            potential_markers = [] # new markers of the same type stored here
            for new_marker in self.get_markers():
                if comparator(new_marker, marker):
                    potential_markers.append(new_marker) # append based on comparator
            closest = self.get_closest_marker(potential_markers) # closest new
            if closest is None: # there are no markers found
                if travel_dist < blind_spot: # we have traveled beyond blind_spot
                    self.log.info("Distance to go in blind_spot (%.4f)",
                                  travel_dist)
                    reached = True # break on next loop
                else:
                    self.log.warning("Lost the marker")
                    break # lost the marker
            else:
                self.log.debug("Re-found marker")
                c = Marker(closest)
                expected = horiz_dist - min(0.1, travel_dist / 3.0)
                if c.horizontal_dist >= expected:
                    self.log.warning("Did not travel far enough (%f >= %f) (%f, %f)" % (
                        c.horizontal_dist, expected, closest.dist, marker.dist))
                    return 0
                marker = closest # the new marker to target
            if not reached:
                if marker.info.marker_type in MarkerFilter.include("TOKENS"):
                    reached = self.is_holding_token()
                    self.log.debug("Not reached, holding:%s", reached)
                    if reached: break
        return reached

    def face_marker(self, marker, speed):
        self.log.debug("Going to face marker %s", marker)
        m_orient = abs(marker.orientation.rot_y)
        if m_orient < 0:
            Dir1, Dir2 = Left, Right
            self.log.debug("Going left then right")
        else:
            Dir1, Dir2 = Right, Left
            self.log.debug("Going right then left")
        self.turn(Dir1(abs(marker.rot_y), Speed(speed)))
        self.drive(Distance((0.5 * marker.dist) /
                             abs(math.cos(math.radians(m_orient))), speed))
        self.turn(Dir2(3 * m_orient, Speed(speed)))

    def face_marker_2(self, marker, speed):
        theta = abs(marker.orientation.rot_y)
        length = marker.dist
        if theta < 0:
            Dir1, Dir2 = Left, Right
            self.log.debug("Going left then right")
        else:
            Dir1, Dir2 = Right, Left
            self.log.debug("Going right then left")
        self.turn(Dir1(2 * theta, Speed(speed)))
        x = (length / 2) * math.cos(math.radians(theta))
        self.drive(Distance(x, speed))
        angle = 2 * theta
        self.turn(Dir2(angle, Speed(speed)))
        self.drive(Distance(x, speed))

    def face_marker_3(self, marker, speed):
        self.log.debug("Going to face marker %s", marker)
        m_orient = abs(marker.orientation.rot_y)
        if m_orient < 0:
            Dir1, Dir2 = Left, Right
            self.log.debug("Going left then right")
        else:
            Dir1, Dir2 = Right, Left
            self.log.debug("Going right then left")
        self.turn(Dir1(abs(marker.rot_y), Speed(speed)))
        self.drive(Distance((0.7 * marker.dist) /
                             abs(math.cos(math.radians(m_orient))), speed))
        self.turn(Dir2(2 * m_orient, Speed(speed)))

    def navigate_to_marker(self, marker, speed, comparator=None):
        self.log.debug("navigating to marker")
        self.face_marker_3(marker, speed) # face the marker
        markers = self.get_markers() # rescan for the marker
        old_marker = marker
        for new_marker in markers:
            if new_marker.info.code == marker.info.code:
                marker = new_marker
                self.log.debug("Found marker, continuing")
                break
        if marker is old_marker: # the marker got lost
            self.log.warning("Could not find marker")
            return False
        if self.goto_marker(marker, speed, comparator):
            return True
        markers = self.get_markers() # rescan for the marker
        for new_marker in markers:
            if new_marker.info.code == marker.info.code:
                marker = new_marker
                self.log.debug("Found marker again, continuing")
                break
        if marker is old_marker: # the marker got lost
            self.log.warning("Could not find marker")
            return False
        self.navigate_to_marker(marker, speed, comparator)
        

    def is_holding_token(self):
        return self.token_sensL.read() or self.token_sensR.read()

    def move_arm(self, direction, delay=False):
        if direction not in [UP, DOWN, MIDDLE]:
            raise TypeError("Invalid arm movement")
        if direction == UP:
            angle = self.arm.MIN
        elif direction == DOWN:
            angle = self.arm.MAX
        elif direction == MIDDLE:
            angle = self.arm.MAX / 2
        self.log.debug("Move arm %s (angle = %d)", direction, angle)
        self.arm.set_angle(angle)
        if delay:
            self.wait(0.5)

    def open_grabber(self, delay=False):
        self.log.debug("OPEN grabber (angle = %d)", self.grabber.MIN)
        self.grabber.set_angle(self.grabber.MIN)
        if delay:
            self.wait(0.7)

    def close_grabber(self, delay=False):
        self.log.debug("CLOSE grabber (angle = %d)", self.grabber.MAX)
        self.grabber.set_angle(self.grabber.MAX)
        if delay:
            self.wait(0.7)

    def get_markers(self, _filter=None):
        markers = self.camera.find_markers()
        self._marker_callback(markers)
        self.log.debug("get_markers %s", str(self.camera.fmt_markers(markers)))
        if _filter is not None:
            markers = filter(lambda m: m.info.marker_type in _filter, markers)
        return markers

    def get_closest_marker(self, markers):
            self.log.debug("Get closest marker to robot")
            return self.camera.get_closest(markers)

    def get_closest_marker_rotation(self, markers, degree=0):
        self.log.debug("Get closest marker from degree (%f)", degree)
        return self.camera.get_rotation_nearest(markers, degree)

    def _stop_operation(self, filter=None):
        self.log.info("Stopping current action")
        try:
            self.right_wheel.stop()
            self.left_wheel.stop()
        except Exception as e:
            self.log.exception(e)
        raise StateInterrupt('stop', 'operation.stop')

    def wait(self, seconds):
        self.log.debug("Wait %.4f seconds", seconds)
        time.sleep(seconds)

    def set_bump_handler(self, callback):
        self._bump_callback = callback

    def set_marker_handler(self, callback):
        self._marker_callback = callback

    def bumped(self, sensor):
        if sensor is self.bump_FrL:
            self._bump_callback('Front.Left')
        elif sensor is self.bump_FrR:
            self._bump_callback('Front.Right')
        elif sensor is self.bump_BkL:
            self._bump_callback('Back.Left')
        elif sensor is self.bump_BkR:
            self._bump_callback('Back.Right')

    def create_token_obj(self, markers):
        return Token(markers)

    def stop(self):
        self.log.info("Stopping all communications")
        self.running = False

class MoveInstruction(object):
    def __init__(self, *args):
        name = self.__class__.__name__
        if not hasattr(self, 'setup'):
            raise TypeError("%s must be properly sub classed" % name)
        self.reverse = False
        self.speed = None
        self.setup(*args)
        self._repr = "<IO.%s%s>" % (name, str(args))

    def __repr__(self):
        return self._repr

    def drive_motors(self, io):
        if self.reverse:
            io.left_wheel.backward(self.speed)
            io.right_wheel.backward(self.speed - 3)
        else:
            io.left_wheel.forward(self.speed - 3)
            io.right_wheel.forward(self.speed)

    def stop_motors(self, io):
        io.left_wheel.stop()
        io.right_wheel.stop()

class Distance(MoveInstruction):
    def setup(self, meters, speed, stop=True):
        if meters < 0:
            self.reverse = True
            meters = -meters
        else:
            self.reverse = False
        self.meters = meters
        self.speed = speed
        self.stop = stop

    def action(self, io):
        self.drive_motors(io)
        time1 = io.left_wheel.calc_wait_time(self.meters, self.speed)
        time2 = io.right_wheel.calc_wait_time(self.meters, self.speed)
        io.wait(max(time1, time2))
        #if time1 > time2: # if left wheel takes longer than right wheel
        #    io.right_wheel.stop()
        #elif time2 > time1: # if right wheel takes longer than left wheel
        #    io.left_wheel.stop()
        #io.wait(abs(time1 - time2))
        if self.stop:
            self.stop_motors(io)

class Time(MoveInstruction):
    def setup(self, seconds, speed=None, stop=True):
        self.seconds = seconds
        self.speed = speed
        if speed is not None:
            if speed < 0:
                self.reverse = True
                speed = -speed
            else:
                self.reverse = False
        self.stop = stop

    def action(self, io):
        self.drive_motors(io)
        io.wait(self.seconds)
        if self.stop:
            self.stop_motors(io)

class Speed:
    def __init__(self, speed):
        self.speed = speed
    def __repr__(self):
        return "<IO.Speed(%d)>" % self.speed

class Rotation(MoveInstruction):
    def __init__(self, degree, measure, pivot=CENTER, stop=True):
        self.degree = degree = abs(degree)
        self.left_wheel_action = None
        self.right_wheel_action = None
        self.stop = stop
        super(Rotation, self).__init__(measure, pivot)
        self._repr = "<IO.%s%s>" % (self.__class__.__name__, (degree, measure,
                                                              pivot))
        self.dist = self.calc_dist(pivot)
        if isinstance(measure, Time):
            self.speed = (self.dist / measure.seconds) * 100.0
            self.time_func = lambda io: (measure.seconds, measure.seconds)
        elif isinstance(measure, Speed):
            self.speed = measure.speed
            self.time_func = lambda io: (io.left_wheel.calc_wait_time(self.dist,
            self.speed), io.right_wheel.calc_wait_time(self.dist, self.speed))
            if self.speed < 0:
                self.left_wheel_action = 'backward'
                self.right_wheel_action = 'backward'
        else:
            raise TypeError("Invalid measurement %s" % measure)

    def action(self, io):
        if self.left_wheel_action is not None:
            getattr(io.left_wheel, self.left_wheel_action)(self.speed)
        if self.right_wheel_action is not None:
            getattr(io.right_wheel, self.right_wheel_action)(self.speed)
        time1, time2 = self.time_func(io)
        io.wait(min(time1, time2))
        if time1 > time2: # if left wheel takes longer than right wheel
            io.right_wheel.stop()
        elif time2 > time1: # if right wheel takes longer than left wheel
            io.left_wheel.stop()
        io.wait(abs(time1 - time2))
        self.stop_motors(io)

    def calc_dist(self, point):
        """Returns the distance the driving wheel needs to turn given the point
        of rotation (WHEEL or CENTER)."""
        var1 = math.pi * WHEEL_SPAN * abs(self.degree)
        if point == WHEEL:
            var1 *= 2
        return var1 / 360

class Right(Rotation):
    def setup(self, instruction, pivot):
        self.left_wheel_action = 'forward'
        self.right_wheel_action = 'backward'
        if pivot == WHEEL:
            self.right_wheel_action = None

class Left(Rotation):
    def setup(self, instruction, pivot):
        self.left_wheel_action = 'backward'
        self.right_wheel_action = 'forward'
        if pivot == WHEEL:
            self.left_wheel_action = None
