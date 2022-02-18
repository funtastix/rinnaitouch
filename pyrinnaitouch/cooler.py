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

    gss = GetAttribute(j[1].get("CGOM"),"GSS",None)
    if not gss:
        _LOGGER.error("No GSO here")

    else:
        switch = GetAttribute(gss,"CC",None)
        if switch == "Y":
            _LOGGER.debug("Cooling is ON")
            brivisStatus.systemOn = True
            brivisStatus.coolingStatus.coolingOn = True

            # Cooling is on - get attributes
            circFan = GetAttribute(gss,"FS",None)
            _LOGGER.debug("Circulation Fan is: {}".format(circFan))
            brivisStatus.coolingStatus.CirculationFanOn(circFan)

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

        elif switch == "N":
            # Heater is off
            _LOGGER.debug("Cooling is OFF")
            brivisStatus.systemOn = False
            brivisStatus.coolingStatus.coolingOn = False

        za = zb = zc = zd = None
        z = GetAttribute(j[1].get("CGOM"),"ZAO",None)
        if z:
            za = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("CGOM"),"ZBO",None)
        if z:
            zb = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("CGOM"),"ZCO",None)
        if z:
            zc = GetAttribute(z,"UE",None)
        z = GetAttribute(j[1].get("CGOM"),"ZDO",None)
        if z:
            zd = GetAttribute(z,"UE",None)
        brivisStatus.coolingStatus.SetZones(za,zb,zc,zd)


class CoolingStatus():
    """Cooling function status"""
    coolingOn = False
    circulationFanOn = False
    manualMode = False
    autoMode = False
    setTemp = 0
    zoneA = False
    zoneB = False
    zoneC = False
    zoneD = False

    zones = []

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

