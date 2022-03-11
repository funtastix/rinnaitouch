import socket
import time
import argparse
import json
from .commands import *
from .util import *
import logging

_LOGGER = logging.getLogger(__name__)

def HandleHeatingMode(client,j,brivisStatus):
    cfg = GetAttribute(j[1].get("HGOM"),"CFG",None)
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
            brivisStatus.heaterStatus.CirculationFanOn(switch)

            # Heater is on - get attributes
            fanSpeed = GetAttribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
            brivisStatus.heaterStatus.fanSpeed = int(fanSpeed) # Should catch errors!

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

                gss = GetAttribute(j[1].get("HGOM"),"GSS",None)
                if not gss:
                    _LOGGER.error("No GSS here")
                else:
                    brivisStatus.heaterStatus.preheating = YNtoBool(GetAttribute(gss,"PH",False))

        elif switch == "F":
            # Heater is off
            _LOGGER.debug("Heater is OFF")
            brivisStatus.systemOn = False
            brivisStatus.heaterStatus.heaterOn = False
            brivisStatus.heaterStatus.CirculationFanOn(switch)

        elif switch == "Z":
            _LOGGER.debug("Circulation Fan is: {}".format(switch))
            brivisStatus.systemOn = True
            brivisStatus.heaterStatus.heaterOn = False
            brivisStatus.heaterStatus.CirculationFanOn(switch)

            fanSpeed = GetAttribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: {}".format(fanSpeed))
            brivisStatus.heaterStatus.fanSpeed = int(fanSpeed) # Should catch errors!

        za = zb = zc = zd = None
        z = GetAttribute(j[1].get("HGOM"),"ZAO",None)
        if z:
            za = GetAttribute(z,"UE",None)
            brivisStatus.heaterStatus.zoneAsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZBO",None)
        if z:
            zb = GetAttribute(z,"UE",None)
            brivisStatus.heaterStatus.zoneBsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZCO",None)
        if z:
            zc = GetAttribute(z,"UE",None)
            brivisStatus.heaterStatus.zoneCsetTemp = GetAttribute(z,"SP", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZDO",None)
        if z:
            zd = GetAttribute(z,"UE",None)
            brivisStatus.heaterStatus.zoneDsetTemp = GetAttribute(z,"SP", 999)
        brivisStatus.heaterStatus.SetZones(za,zb,zc,zd)

        z = GetAttribute(j[1].get("HGOM"),"ZAS",None)
        if z:
            brivisStatus.heaterStatus.zoneAAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.heaterStatus.zoneAtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZBS",None)
        if z:
            brivisStatus.heaterStatus.zoneBAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.heaterStatus.zoneBtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZCS",None)
        if z:
            brivisStatus.heaterStatus.zoneCAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.heaterStatus.zoneCtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZDS",None)
        if z:
            brivisStatus.heaterStatus.zoneDAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.heaterStatus.zoneDtemp = GetAttribute(z,"MT", 999)
        z = GetAttribute(j[1].get("HGOM"),"ZUS",None)
        if z:
            brivisStatus.heaterStatus.commonAuto = YNtoBool(GetAttribute(z,"AE",None))
            brivisStatus.heaterStatus.temperature = GetAttribute(z,"MT", 999)

class HeaterStatus():
    """Heater function status"""
    heaterOn = False
    fanSpeed = 0
    circulationFanOn = False
    manualMode = False
    autoMode = False
    setTemp = 0
    commonAuto = False
    temperature = 999
    preheating = False

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


