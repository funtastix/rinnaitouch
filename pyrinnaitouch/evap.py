import socket
import time
import argparse
import json
from .commands import *
from .util import *
import logging

_LOGGER = logging.getLogger(__name__)

def HandleEvapMode(client,j,brivisStatus):
    gso = GetAttribute(j[1].get("ECOM"),"GSO",None)
    if not gso:
        _LOGGER.error("No GSO here")
    else:
        #_LOGGER.debug("Looking at: {}".format(gso))
        switch = GetAttribute(gso,"SW", None)
        if switch == "N":
            opmode = GetAttribute(gso, "OP", None)
            #_LOGGER.debug("setting opmode: {}".format(opmode))
            brivisStatus.evapStatus.SetMode(opmode)

            _LOGGER.debug("EVAP is ON")
            brivisStatus.systemOn = True
            brivisStatus.evapStatus.evapOn = True

            if opmode == "M":
                # Evap is on and manual - what is the fan speed
                evapFan = GetAttribute(gso,"FS",None)
                _LOGGER.debug("Fan is: {}".format(evapFan))
                brivisStatus.evapStatus.FanOn(evapFan)
            
                fanSpeed = GetAttribute(gso,"FL",None)
                _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
                brivisStatus.evapStatus.FanSpeed(int(fanSpeed))

                waterPump = GetAttribute(gso,"PS",None)
                _LOGGER.debug("Water Pump is: {}".format(waterPump))
                brivisStatus.evapStatus.WaterPumpOn(waterPump)
            else:
                # Evap is on and auto - look for comfort level
                comfort = GetAttribute(gso, "SP", 0)
                _LOGGER.debug("Comfort Level is: {}".format(comfort))
                brivisStatus.evapStatus.Comfort(comfort)

        elif switch == "F":
            # Evap is off
            _LOGGER.debug("EVAP is OFF")
            brivisStatus.systemOn = False
            brivisStatus.evapStatus.evapOn = False

class EvapStatus():
    """Evap function status"""
    evapOn = False
    manualMode = False
    autoMode = False
    fanOn = False
    fanSpeed = 0
    waterPumpOn = False
    comfort = 0

    def FanOn(self,statusStr):
        # N = On, F = Off
        if statusStr == "N":
            self.fanOn = True
        else:
            self.fanOn = False

    def FanSpeed(self,speedInt):
        self.fanSpeed = speedInt

    def WaterPumpOn(self,statusStr):
        # N = On, F = Off
        if statusStr == "N":
            self.waterPumpOn = True
        else:
            self.waterPumpOn = False

    def SetMode(self,mode):
        # A = Auto Mode and M = Manual Mode
        if mode == "A":
            self.autoMode = True
            self.manualMode = False
        elif mode == "M":
            self.autoMode = False
            self.manualMode = True

    def Comfort(self, comfort):
        self.comfort = comfort

