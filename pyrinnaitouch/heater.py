import socket
import time
import argparse
import json
from .commands import *
from .util import *
import logging

_LOGGER = logging.getLogger(__name__)

def HandleHeatingMode(client,j,brivisStatus):
    oop = GetAttribute(j[1].get("HGOM"),"OOP",None)
    if not oop:
        # Probably an error
        _LOGGER.error("No OOP - Not happy, Jan")

    else:
        switch = GetAttribute(oop,"ST",None)
        if switch == "N":
            _LOGGER.debug("Heater is ON")
            brivisStatus.systemOn = True
            brivisStatus.heaterStatus.heaterOn = True

            # Heater is on - get attributes
            fanSpeed = GetAttribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
            brivisStatus.heaterStatus.fanSpeed = int(fanSpeed) # Should catch errors!

            # Heater is on - get attributes
            circFan = GetAttribute(oop,"CF",None)
            _LOGGER.debug("Circulation Fan is: {}".format(circFan))
            brivisStatus.heaterStatus.CirculationFanOn(circFan)

            # GSO should be there
            gso = GetAttribute(j[1].get("HGOM"),"GSO",None)
            if not gso:
                # Probably an error
                _LOGGER.error("No GSO when heater on. Not happy, Jan")
            else:
                # Heater is on - get attributes
                opMode = GetAttribute(gso,"OP",None)
                _LOGGER.debug("Heat OpMode is: {}".format(opMode)) # A = Auto, M = Manual
                brivisStatus.heaterStatus.SetMode(opMode)

                # Set temp?
                setTemp = GetAttribute(gso,"SP",None)
                _LOGGER.debug("Heat set temp is: {}".format(setTemp))
                brivisStatus.heaterStatus.setTemp = int(setTemp)

        elif switch == "F":
            # Heater is off
            _LOGGER.debug("Heater is OFF")
            brivisStatus.systemOn = False
            brivisStatus.heaterStatus.heaterOn = False

        za = zb = zc = zd = None
        z = GetAttribute(j[1].get("HGOM"),"ZAO",None)
        if z:
            za = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("HGOM"),"ZBO",None)
        if z:
            zb = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("HGOM"),"ZCO",None)
        if z:
            zc = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("HGOM"),"ZDO",None)
        if z:
            zd = GetAttribute(z,"UE",None)
        brivisStatus.heaterStatus.SetZones(za,zb,zc,zd)

class HeaterStatus():
    """Heater function status"""
    heaterOn = False
    fanSpeed = 0
    circulationFanOn = False
    manualMode = False
    autoMode = False
    setTemp = 0
    zoneA = False
    zoneB = False
    zoneC = False
    zoneD = False

    def SetMode(self,mode):
        # A = Auto Mode and M = Manual Mode
        if mode == "A":
            self.autoMode = True
            self.manualMode = False
        elif mode == "M":
            self.autoMode = False
            self.manualMode = True

    def SetZones(self,za,zb,zc,zd):
        # Y = On, N = off
        self.zoneA = YNtoBool(za)
        self.zoneB = YNtoBool(zb)
        self.zoneC = YNtoBool(zc)
        self.zoneD = YNtoBool(zd)

    def CirculationFanOn(self,statusStr):
        # Y = On, N = Off
        if statusStr == "Y":
            self.circulationFanOn = True
        else:
            self.circulationFanOn = False


