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

from IOInterface import *
from state_utils import StateMachine, StateInterrupt
import game_map

class PlayGame:
    def __init__(self, log, io, corner):
        self.log = log
        self.io = io
        self.our_tokens = game_map.get_our_tokens(corner)
        self.log.info("Token codes for this match: %s", str(self.our_tokens))
        self.corner = corner
        self.startup()

    def AdjDir(self, Dir):
        if self.corner in [0, 2]:
            return Dir
        self.log.info("Adjusted direction (from %s)", str(Dir))
        return Left if Dir is Right else Right

    def startup(self):
        self.state = StateMachine({"START": self.preset_start,
                                   "SEARCH_SLOT": self.search_slot,
                                   "DRIVE_TO_SLOT": self.drive_to_slot,
                                   "PLACE_TOKEN": self.place_token,
                                   "TURN_TO_TOKEN": self.next_token,
                                   "SEARCH_TOKEN": self.search_token,
                                   "DRIVE_TO_TOKEN": self.drive_to_token,
                                   "PICK_TOKEN": self.pickup_token,
                                   "TURN_TO_SLOT": self.next_slot})

        self.state.bind('change', self.state_changed)
        self.state.bind('error', self.state_error)
        self.state.bind('finish', self.state_finished)
        self.state.bind('interrupt', self.state_interrupted)
        self.on_interrupt = None
        self.reset()
        for state in self.state.next_state():
            self.state.change_state(state)

    def set_state(self, state, *args):
        self.state.set_state(state, args)
    def state_changed(self, fromstate, tostate):
        self.log.info("State Changed from %s to %s", fromstate, tostate)
    def state_error(self, state, errors):
        self.log.error(str(state) + " encountered errors")
        for e in errors:
            self.log.exception(e)
    def state_finished(self, state):
        self.log.info(str(state) + " finished")
    def state_interrupted(self, state, ex):
        self.log.info(str(state) + " interrupted" + str(ex))
        if self.on_interrupt:
            self.on_interrupt()
            self.on_interrupt = None

    def reset(self):
        self.io.set_bump_handler(self.onbump)
        self.io.set_marker_handler(self.handle_markers)
        self.io.open_grabber()
        self.io.move_arm(DOWN, True)
        self.has_token = False
        self.searches = {'SLOTS': 0, 'TOKENS': 0}
        self.from_start = False
        self.done_count = 0
        self.set_state("START")

    def onbump(self, bump):
        self.log.info(bump)

    def handle_markers(self, markers):
        currstate = self.state.get_active_state().name
        obsticles = MarkerFilter.include('ROBOTS', 'WALLS')
        for marker in markers:
            if marker.info.marker_type in obsticles:
                if marker.dist < 0.5:
                    def after_interrupt():
                        self.log.info("Move away")
                        self.io.drive(Distance(-0.9, 50))
                        self.io.turn(Right(10, Speed(50)))
                    self.on_interrupt = after_interrupt
                    self.log.info("Obsticle found, %s", str(marker))
                    self.io._stop_operation()
            if marker.info.marker_type in MarkerFilter.include('SLOTS'):
                if currstate == "SEARCH_TOKEN" and marker.rot_y < 5:
                    self.log.info("Found slot while searching for token")
                    def itrpt():
                        self.io.turn(Right(90, Speed(50)))
                        self.set_state("SEARCH_TOKEN")
                    self.on_interrupt = itrpt()
                    raise StateInterrupt('slotfound', [])
            if marker.info.marker_type in MarkerFilter.include("WALLS"):
                if currstate == "SEARCH_TOKEN":
                    self.log.info("Check walls here")
                    
                    # check looking at correct wall
                    continue
                    #game_map.get_arena_codes_for_corner(self.corner)

    def preset_start(self):
        self.from_start = True
        self.log.info("Grabbing token")
        self.io.close_grabber(True)
        self.io.move_arm(UP, True)
        self.has_token = True
        self.log.info("Drive 2.3 meters")
        self.io.drive(Distance(2.3, 80))
        self.io.move_arm(MIDDLE, True)
        self.io.turn(self.AdjDir(Left)(40, Speed(60)))
        self.set_state("SEARCH_SLOT")

    def search_slot(self):
        def filt(markers):
            if not self.from_start: return markers
            for marker in markers:
                if marker.info.code == game_map.closest_slot(self.corner):
                    return [marker]
            return markers
        self.search_func("SLOTS", self.AdjDir(Right), "DRIVE_TO_SLOT", max_rot=270,
                         rot_cb=lambda:self.io.drive(Distance(0.5, 50)), filt=filt)

    def search_func(self, type, Dir, next_state, max_rot=200, rot_cb=None,
                    filt=None):
        if not hasattr(rot_cb, '__call__'):
            rot_cb = lambda: self.io.drive(Distance(1, 50))
        if not hasattr(filt, '__call__'):
            filt = lambda m:m
        found = False
        self.searches[type] += 1
        rotation = 0
        self.log.info("Looking for %s", type)
        while not found:
            markers = self.io.get_markers(MarkerFilter.include(type))
            markers = filt(markers)
            if len(markers) > 0:
                marker = self.io.get_closest_marker(markers)
                self.log.info("Found marker, %s", str(marker))
                found = True
            elif rotation > max_rot:
                self.log.info("Turned too much")
                found = rot_cb()
                rotation = 0
            else:
                rotation += self.scan_move(Dir)
        self.set_state(next_state, marker)

    def drive_to_slot(self, slot):
        assert self.has_token
        if self.io.goto_marker(slot, 70, offset=0.3): #navigate_to_marker
            self.log.info("Got to slot")
            self.set_state("PLACE_TOKEN")
        elif self.from_start:
            self.log.info("From start, just place down")
            self.io.drive(Distance(0.1, 40))
            self.set_state("PLACE_TOKEN")
        elif self.searches["SLOTS"] >= 2:
            self.log.info("Searched for >= 2 times, drop here")
            self.set_state("PLACE_TOKEN")
        else:
            self.log.info("Search again")
            self.set_state("SEARCH_SLOT")

    def place_token(self):
        assert self.has_token
        self.from_start = False
        self.searches["SLOTS"] = 0
        self.io.move_arm(UP, True)
        self.io.open_grabber()
        self.io.move_arm(DOWN)
        self.has_token = False
        self.done_count += 1
        self.set_state("TURN_TO_TOKEN")

    def next_token(self):
        self.log.info("Head to next token")
        self.io.drive(Distance(-0.7, 60)) # reverse out of zone
        if self.done_count < 2:
            self.log.info("Turn face near token")
            self.io.turn(self.AdjDir(Left)(147, Speed(50)))
            self.io.drive(Distance(1, 65))
        elif self.done_count == 2:
            self.log.info("Face far token")
            self.io.turn(self.AdjDir(Right)(94, Speed(50)))
            self.io.drive(Distance(2, 65))
        self.set_state("SEARCH_TOKEN")

    def search_token(self):
        def check(tokens):
            return filter(lambda m:m.info.code in self.our_tokens, tokens)
        self.search_func("TOKENS", self.AdjDir(Left), "DRIVE_TO_TOKEN", filt=check)

    def drive_to_token(self, token):
        assert not self.has_token
        result = self.io.goto_marker(token, 70) #navigate_to_marker
        if result:
            self.set_state("PICK_TOKEN")
        else:
            self.log.info("lost marker (searching again)")
            if result is 0:
                self.log.info("Got stuck, reversing")
                self.io.drive(Distance(-0.7, 50))
                self.io.turn(self.AdjDir(Right)(90, Speed(50), WHEEL))
            self.set_state("SEARCH_TOKEN")

    def pickup_token(self):
        if not self.io.is_holding_token():
            self.log.info("Not holding token, move 0.3m")
            self.io.drive(Distance(0.3, 30))
        else:
            self.log.info("Holding token")
        self.io.close_grabber(True)
        self.log.info("Pull token out")
        self.io.move_arm(MIDDLE, True)
        self.io.drive(Distance(-0.2, 50))
        self.io.move_arm(UP, True)
        self.has_token = True
        self.set_state("TURN_TO_SLOT")

    def next_slot(self):
        self.io.drive(Distance(-0.5, 50)) # Carry token out further
        if not self.check_has_token():
            self.log.warning("Dont have token")
            self.io.move_arm(DOWN)
            self.io.open_grabber()
            self.has_token = False
            self.io.drive(Distance(-0.5, 80))
            self.set_state("SEARCH_TOKEN")
            return
        self.log.info("Has token")
        if self.done_count < 2:
            self.io.turn(self.AdjDir(Left)(133, Speed(50)))
            self.io.drive(Distance(2.1, 50))
            self.io.turn(self.AdjDir(Left)(46, Speed(50)))
        else:
            self.io.turn(Left(170, Speed(50)))
            self.io.drive(Distance(2, 70))
        self.set_state("SEARCH_SLOT")

    def check_has_token(self):
        tokens = self.io.get_markers([MarkerFilter.include("TOKENS")[1]])
        tokens = filter(lambda m:m.info.code in self.our_tokens, tokens)
        tokens = filter(lambda m:m.dist < 0.5, tokens)
        has_token = len(tokens)
        has_token = has_token or self.io.is_holding_token()
        return has_token

    def scan_move(self, Direction):
        degree = 17
        self.log.info("Scanning, turning %s by %d", Direction, degree)
        self.io.turn(Direction(degree, Speed(50)))
        self.io.wait(1)
        return degree

