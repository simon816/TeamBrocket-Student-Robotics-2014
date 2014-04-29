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