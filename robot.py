"""
    This file is part of Team Brocket Robotics, licensed under the MIT License.
    A copy of the MIT License can be found in LICENSE.txt
"""

import sys
import logging
import os
import time
from subprocess import Popen

from sr.robot import Robot

from IOInterface import IOInterface

RUN_TESTS = False
COMP_MODE = True

def setup_logger(root):
    logger = logging.getLogger('Robot')
    logger.setLevel(logging.DEBUG)

    live_log = logging.StreamHandler(sys.stdout)
    live_log.setLevel(logging.INFO)
    live_log.setFormatter(logging.Formatter('%(asctime)s.%(msecs)d [%(levelname)s] [%(name)s] %(message)s', "%M:%S"))
    logger.addHandler(live_log)

    path = os.path.join(root, "comp" if COMP_MODE else "", time.strftime("%Y-%m-%d",  time.localtime()))
    if not os.path.exists(path):
        os.makedirs(path)
    filename = os.path.join(path, time.strftime("%H.%M.%S", time.localtime()) + ".log")
    i = 0
    while os.path.exists(filename):
        filename = os.path.join(path, time.strftime("%H.%M.%S", time.localtime()) + "_%d.log" % i)
        i += 1
    file_log = logging.FileHandler(filename)
    file_log.setLevel(logging.DEBUG)
    file_log.setFormatter(logging.Formatter('%(asctime)s@%(threadName)s [%(levelname)s] [%(name)s,%(funcName)s:%(lineno)d] %(message)s'))
    logger.addHandler(file_log)

    return logger

def set_time(ziproot):
    try:
        mtime = os.path.getmtime(os.path.join(ziproot, 'robot.zip'))
        if time.time() > mtime:
            return
        date = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(mtime))
        Popen(["date", "-s", date]).wait()
    except:
        pass

global R

def setup():
    global R
    R = Robot.setup()
    R.init()
    set_time(R.usbkey)
    logger = setup_logger(R.usbkey)
    logger.info('Battery Voltage: %.2f' % R.power.battery.voltage)
    R.wait_start()
    try:
        io = IOInterface(R)
    except:
        logger.exception("IOInterface could not initialize")
        raise
    return logger, io, R.zone

if __name__ == '__main__' or __name__ == '__builtin__':
    logger, io, corner = setup()
    if RUN_TESTS:
        import tests
        global R
        tests.run(logger, io, R)
    else:
        import gamelogic
        gamelogic.PlayGame(logger, io, corner)
