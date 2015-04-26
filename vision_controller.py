"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

import math

from sr.vision import (MARKER_ARENA,
                       MARKER_ROBOT,
                       MARKER_SLOT,
                       MARKER_TOKEN_TOP,
                       MARKER_TOKEN_BOTTOM,
                       MARKER_TOKEN_SIDE)

DEFAULT_RESOLUTION = (960, 720)

MARKER_FILTERS = {
    'TOKENS': [MARKER_TOKEN_TOP, MARKER_TOKEN_BOTTOM, MARKER_TOKEN_SIDE],
    'ROBOTS': [MARKER_ROBOT],
    'SLOTS': [MARKER_SLOT],
    'WALLS': [MARKER_ARENA]
}

CAMERA_HEIGHT = 0.376 # Height in meters for the elevation above the ground

class VisionController(object):
    def __init__(self, robot):
        self.res = DEFAULT_RESOLUTION
        self._see = robot.see
        self._stats = {
            'cam_init': [],
            'capture': [],
            'img_scan': []
        }

    def find_markers(self):
        markers, timings = self._see(self.res, True)
        self._record_timings(timings)
        return markers

    def _record_timings(self, times):
        self._stats['cam_init'].append(times['cam'])
        self._stats['capture'].append(times['yuyv'])
        self._stats['img_scan'].append(times['find_markers'])

    def print_stat(self):
        timesvars = [[]] * 3
        timesvars[0] = self._stats['cam_init']
        timesvars[1] = self._stats['capture']
        timesvars[2] = self._stats['img_scan']
        averages = []
        for times in timesvars:
            avg = 0
            for time in times:
                avg += time
            avg /= float(len(times))
            averages.append(avg)
        print "It took %f seconds for camera to initialize" % averages[0]
        print "It took %f seconds to capture the image" % averages[1]
        print "It took %f seconds to scan for libkoki markers" % averages[2]

    def change_resolution(self, new_res):
        if type(new_res) == tuple and len(new_res) == 2:
            if type(new_res[0]) == int and type(new_res[1]) == int:
                self.res = new_res
                return True
        return False

    @classmethod
    def get_closest(self, markers):
        if len(markers) == 0: return None
        closest = markers[0]
        for m in markers:
            if m.dist < closest.dist:
                closest = m
        return closest

    @classmethod
    def get_rotation_nearest(self, markers, degree=0):
        """Returns the marker closest to degree from a list of markers."""
        if len(markers) == 0: return None
        getrad = lambda d: math.radians(abs(d - 180))
        if degree > 180: degree = degree - 360
        target = getrad(degree)
        closest = [math.pi, markers[0]]
        for m in markers:
            diff = abs(target - getrad(m.rot_y))
            if diff < closest[0]:
                closest = [diff, m]
        return closest[1]

    @classmethod
    def fmt_markers(self, markers):
        return str(map(self.fmt_marker, markers))

    @classmethod
    def fmt_marker(self, m):
        return "Marker(code=%d, type=%d, dist=%f rot_y=%f orientation(rot_y=%f))" % (
            m.info.code, m.info.marker_type, m.dist, m.rot_y, m.orientation.rot_y)

class MarkerFilter:
    @staticmethod
    def include(*types):
        accept = []
        for filter in types:
            if filter.upper() in MARKER_FILTERS:
                accept += MARKER_FILTERS[filter.upper()]
        return accept

    @staticmethod
    def exclude(*types):
        accept = []
        for v in MARKER_FILTERS.values(): accept += v
        for filter in types:
            if filter.upper() in MARKER_FILTERS:
                for m in MARKER_FILTERS[filter.upper()]:
                    accept.remove(m)
        return accept

class Marker:
    # A marker helper class
    def __init__(self, marker):
        self.marker = marker

    def get_center_height(self):
        height = self.marker.info.size / 2
        # rulebook.pdf specifies some height adjustments
        if self.marker.info.marker_type == MARKER_ARENA:
            # Figure 4: The markers are placed 50mm above the floor.
            height += 0.05
        elif self.marker.info.marker_type == MARKER_SLOT:
            # Section 3.5.2: 20  5mm above the floor.
            height += 0.02
        elif self.marker.info.marker_type == MARKER_ROBOT:
            # A robot has a max height of 0.5m, best guess is to assume the
            # badge is half that height
            height += 0.25
        # Tokens are on the ground so mo height adjustments required
        return height

    @property
    def horizontal_dist(self):
        square = (self.marker.dist ** 2) - (self.vertical_height ** 2)
        if square < 0: return 0
        return math.sqrt(square)

    @property
    def vertical_height(self):
        # Returns the height of the marker from the camera
        return CAMERA_HEIGHT - self.get_center_height()

    def __str__(self):
        return "Marker(rotation=%.2f, distance=%.2f, orientation=%s)" %(
            self.marker.rot_y, self.horizontal_dist, self.marker.orientaton)
    def __repr__(self):
        return repr(self.marker)

class Token:
    def __init__(self, markers):
        filt = MarkerFilter.include('TOKENS')
        markers = filter(lambda m: m.info.marker_type in filt, markers)
        self.top = self.bottom = None
        self.sides = []
        for marker in markers:
            if marker.info.marker_type == MARKER_TOKEN_TOP:
                self.top = marker
            elif marker.info.marker_type == MARKER_TOKEN_BOTTOM:
                self.bottom = marker
            elif marker.info.marker_type == MARKER_TOKEN_SIDE:
                self.sides.append(marker)

    def getTopMarker(self):
        if self.top: return Marker(self.top)

    def getBottomMarker(self):
        if self.bottom: return Marker(self.bottom)

    def getSides(self):
        return map(Marker, self.sides)

    def getClosestSide(self):
        return VisionController.get_rotation_nearest(self.sides)

    def __str__(self):
        return "Token(top=%s, bottom=%s, sides=%s)" % (self.getTopMarker(),
                                                       self.getBottomMarker(),
                                                       self.getSides())
    def getSide(self, side):
        if not self.top and not self.bottom:
            return None
        if side == 'front':
            pass
        elif side == 'back':
            pass
        elif side == 'left':
            pass
        elif side == 'right':
            pass
