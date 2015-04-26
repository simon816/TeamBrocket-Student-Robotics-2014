"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
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
