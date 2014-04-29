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

from sr import *

from IOInterface import *

def chassis_test():
    io.open_grabber()
    io.move_arm(DOWN)
    
    io.drive(Distance(1, 50))
    io.turn(Right(90, Speed(70)))
    io.drive(Distance(0.5, 75))
    io.turn(Left(270, Speed(80)))
    io.drive(Distance(1, 80))
    io.turn(Right(90, Speed(30)))
    io.drive(Distance(0.5, 60))
    io.turn(Right(90, Speed(30)))
    io.stop()

def servo_test():
    io.move_arm(DOWN, True)
    while True:
        io.open_grabber(True)
        io.wait(1)
        io.close_grabber(True)
        io.wait(1)
        continue


        log.info("Move arm down")
        io.move_arm(DOWN, True)
        log.info("Open grabber")
        io.open_grabber(True)
        log.info("Close grabber")
        io.close_grabber(True)
        log.info("Move arm up")
        io.move_arm(UP)
        log.info("Wait 1 second")
        io.wait(1)

def goto_tokens():
    io.open_grabber()
    io.move_arm(DOWN)
    down = True
    while True:
        m = io.get_markers(MarkerFilter.include('TOKENS'))
        if len(m) > 0:
            io.navigate_to_marker(io.get_closest_marker_rotation(m), 70,
                                  comparator=lambda a, b: a.info.code == b.info.code)
            io.close_grabber()
            io.wait(0.2)
            io.move_arm(UP)
            io.wait(1)
            down = False
        elif not down:
            io.move_arm(DOWN)
            io.wait(0.2)
            io.open_grabber()
            down = True

def calcualte_rpm():
    speed = 50
    time = 2
    rpm = []
    for i in range(5):
        m = []
        while len(m) == 0:
            m = io.get_markers()
        m = io.get_closest_marker_rotation(m)
        start_dist = m.dist
        io.drive(Time(time, speed))
        m = []
        while len(m) == 0:
            m = io.get_markers()
        m = io.get_closest_marker_rotation(m)
        traveled = start_dist - m.dist
        rpm.append(io.left_wheel.calc_rpm(time, traveled, speed))
        log.info("RPM = %f", rpm[i])
        io.wait(5)
    t=0
    for r in rpm:
        t+=r
    log.info("AVG = %f", (t/5.0))

def calcualte_rpm2():
    io.drive(Distance(1, 100))

def bump_test():
    def bumped(place):
        log.info('Bumped on %s', place)
    io.bump_callback(bumped)
    while True:
        pass

def vision_test(R):
    while True:
        markers = R.see()
        print len(markers), "found."
        if len(markers) > 0:
            for marker in markers:
                if marker.info.marker_type != MARKER_TOKEN_SIDE: continue
                print "Marker is ", marker.dist, "m away."
                print "C.rot_y", marker.centre.polar.rot_y
                print "O.rot_y", marker.orientation.rot_y

def interrupt_test():
    import threading
    def interrupt():
        io.wait(1)
        io._stop_operation()
    threading.Thread(target=interrupt).start()
    io.drive(Distance(10, 100))

def token_test():
    def check():
        while True:
            log.info("Token is: %s", "IN" if io.is_holding_token() else "OUT")
    import threading
    t = threading.Thread(target=check)
    t.daemon = True
    t.start()
    while True:
        io.drive(Distance(0.5, 50))
        io.close_grabber(True)
        io.move_arm(UP, True)
        io.wait(0.5)
        io.move_arm(DOWN)
        io.open_grabber()    
        io.drive(Distance(-0.5, 50))

def run(log_, io_, R_):
    global log, io, R
    log, io, R  = log_, io_, R_
    #chassis_test()
    #servo_test()
    #bump_test()
    #interrupt_test()
    goto_tokens()
    #vision_test(R)
    #calcualte_rpm()
    #token_test()
    log.info("Finish execution")
