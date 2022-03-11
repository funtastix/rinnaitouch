import socket
import time
import argparse
import json
from .commands import *
from .util import *
import logging

_LOGGER = logging.getLogger(__name__)

def HandleCoolingMode(client,j,brivisStatus):
    cfg = GetAttribute(j[1].get("CGOM"),"CFG",None)
    if not cfg:
        # Probably an error
        _LOGGER.error("No CFG - Not happy, Jan")

    else:
        if YNtoBool(GetAttribute(cfg, "ZAIS", None)):
            brivisStatus.heaterStatus.zones.append("A")
        if YNtoBool(GetAttribute(cfg, "ZBIS", None)):
            brivisStatus.heaterStatus.zones.append("B")
        if YNtoBool(GetAttribute(cfg, "ZCIS", None)):
            brivisStatus.heaterStatus.zones.append("C")
        if YNtoBool(GetAttribute(cfg, "ZDIS", None)):
            brivisStatus.heaterStatus.zones.append("D")

    oop = GetAttribute(j[1].get("CGOM"),"OOP",None)
    if not oop:
        # Probably an error
        _LOGGER.error("No OOP - Not happy, Jan")

    else:
        switch = GetAttribute(oop,"ST",None)
        if switch == "N":
            _LOGGER.debug("Cooling is ON")
            brivisStatus.systemOn = True
            brivisStatus.coolingStatus.coolingOn = True
            brivisStatus.heaterStatus.CirculationFanOn(switch)

            # Cooling is on - get attributes
            fanSpeed = GetAttribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
            brivisStatus.heaterStatus.fanSpeed = int(fanSpeed) # Should catch errors!

            # GSO should be there
            gso = GetAttribute(j[1].get("CGOM"),"GSO",None)
            if not gso:
                # Probably an error
                _LOGGER.error("No GSO when cooling on. Not happy, Jan")
            else:
                # Heater is on - get attributes
                opMode = GetAttribute(gso,"OP",None)
                _LOGGER.debug("Cooling OpMode is: {}".format(opMode)) # A = Auto, M = Manual
                brivisStatus.coolingStatus.SetMode(opMode)

                # Set temp?
                setTemp = GetAttribute(gso,"SP",None)
                _LOGGER.debug("Cooling set temp is: {}".format(setTemp))
                brivisStatus.coolingStatus.setTemp = int(setTemp)

        elif switch == "Y":
            # Heater is off
            _LOGGER.debug("Cooling is OFF")
            brivisStatus.systemOn = False
            brivisStatus.coolingStatus.coolingOn = False
            brivisStatus.heaterStatus.CirculationFanOn(switch)

        elif switch == "Z":
            _LOGGER.debug("Circulation Fan is: {}".format(switch))
            brivisStatus.systemOn = True
            brivisStatus.heaterStatus.CirculationFanOn(switch)

            fanSpeed = GetAttribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
            brivisStatus.heaterStatus.fanSpeed = int(fanSpeed) # Should catch errors!

        za = zb = zc = zd = None
        z = GetAttribute(j[1].get("CGOM"),"ZAO",None)
        if z:
            za = GetAttribute(z,"UE",None)
            brivisStatus.coolingStatus.zoneAsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZBO",None)
        if z:
            zb = GetAttribute(z,"UE",None)
            brivisStatus.coolingStatus.zoneBsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZCO",None)
        if z:
            zc = GetAttribute(z,"UE",None)
            brivisStatus.coolingStatus.zoneCsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZDO",None)
        if z:
            zd = GetAttribute(z,"UE",None)
            brivisStatus.coolingStatus.zoneDsetTemp = GetAttribute(z,"SP", 999)
        brivisStatus.coolingStatus.SetZones(za,zb,zc,zd)

        z = GetAttribute(j[1].get("CGOM"),"ZAS",None)
        if z:
            brivisStatus.coolingStatus.zoneAAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.coolingStatus.zoneAtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZBS",None)
        if z:
            brivisStatus.coolingStatus.zoneBAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.coolingStatus.zoneBtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZCS",None)
        if z:
            brivisStatus.coolingStatus.zoneCAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.coolingStatus.zoneCtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZDS",None)
        if z:
            brivisStatus.coolingStatus.zoneDAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.coolingStatus.zoneDtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("CGOM"),"ZUS",None)
        if z:
            brivisStatus.coolingStatus.commonAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.coolingStatus.temperature = GetAttribute(z,"MT", 999)

class CoolingStatus():
    """Cooling function status"""
    coolingOn = False
    fanSpeed = 0
    circulationFanOn = False
    manualMode = False
    autoMode = False
    setTemp = 0
    commonAuto = False
    temperature = 999

    #zones
    zones = []
    zoneA = False
    zoneAAuto = False
    zoneAtemp = 999
    zoneAsetTemp = 999
    zoneB = False
    zoneBAuto = False
    zoneBtemp = 999
    zoneBsetTemp = 999
    zoneC = False
    zoneCAuto = False
    zoneCtemp = 999
    zoneCsetTemp = 999
    zoneD = False
    zoneDAuto = False
    zoneDtemp = 999
    zoneDsetTemp = 999

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
        # Z = On, N = Off
        if statusStr == "Z":
            self.circulationFanOn = True
        else:
            self.circulationFanOn = False

