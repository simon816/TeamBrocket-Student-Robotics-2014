"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

class _Watcher(object):
    def last_seen(self):
        pass
    def get_id(self):
        pass

class RobotWatcher(_Watcher):

    ROBOTS = {}

    class Robot:
        def __init__(self, marker):
            self.distance_away = marker.dist


    def seen_robot(self, marker):
        if marker.info.code not in self.ROBOTS:
            self.ROBOTS[marker.info.code] = Robot(marker)

class TokenWatcher(_Watcher):
    def __init__(self, marker):
        pass

class ArenaWatcher(_Watcher):
    pass