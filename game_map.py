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

def get_our_tokens(corner):
    codes = range(40 + corner, 49 + corner, 4)
    return codes

def get_arena_codes_for_corner(corner):
    if corner == 0:
        return range(3) + range(25, 28)
    if corner == 1:
        return range(18, 24)
    if corner == 2:
        return range(11, 17)
    if corner == 3:
        return range(4, 10)

def closest_slot(corner):
    if corner == 0: return 32
    if corner == 1: return 39
    if corner == 2: return 36
    if corner == 3: return 35
