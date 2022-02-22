import socket
import time
import argparse
import json
from .commands import *
from .util import *
import logging

_LOGGER = logging.getLogger(__name__)

def HandleEvapMode(client,j,brivisStatus):
    cfg = GetAttribute(j[1].get("ECOM"),"CFG",None)
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

                brivisStatus.evapStatus.zoneA = YNtoBool(GetAttribute(gso,"ZAUE",False))
                brivisStatus.evapStatus.zoneB = YNtoBool(GetAttribute(gso,"ZBUE",False))
                brivisStatus.evapStatus.zoneC = YNtoBool(GetAttribute(gso,"ZCUE",False))
                brivisStatus.evapStatus.zoneD = YNtoBool(GetAttribute(gso,"ZDUE",False))

            else:
                # Evap is on and auto - look for comfort level
                comfort = GetAttribute(gso, "SP", 0)
                _LOGGER.debug("Comfort Level is: {}".format(comfort))
                brivisStatus.evapStatus.Comfort(comfort)

                brivisStatus.evapStatus.zoneA = False
                brivisStatus.evapStatus.zoneB = False
                brivisStatus.evapStatus.zoneC = False
                brivisStatus.evapStatus.zoneD = False

            gss = GetAttribute(j[1].get("ECOM"),"GSS",None)
            if not gss:
                _LOGGER.error("No GSS here")
            else:
                brivisStatus.evapStatus.commonAuto = YNtoBool(GetAttribute(gss,"ZUAE",False))
                brivisStatus.evapStatus.zoneAAuto = YNtoBool(GetAttribute(gss,"ZAAE",False))
                brivisStatus.evapStatus.zoneBAuto = YNtoBool(GetAttribute(gss,"ZBAE",False))
                brivisStatus.evapStatus.zoneCAuto = YNtoBool(GetAttribute(gss,"ZCAE",False))
                brivisStatus.evapStatus.zoneDAuto = YNtoBool(GetAttribute(gss,"ZDAE",False))
                
                brivisStatus.evapStatus.prewetting = YNtoBool(GetAttribute(gss,"PW",False))
                brivisStatus.evapStatus.coolerBusy = YNtoBool(GetAttribute(gss,"BY",False))


        elif switch == "F":
            # Evap is off
            _LOGGER.debug("EVAP is OFF")
            brivisStatus.systemOn = False
            brivisStatus.evapStatus.evapOn = False

            brivisStatus.evapStatus.zoneA = False
            brivisStatus.evapStatus.zoneB = False
            brivisStatus.evapStatus.zoneC = False
            brivisStatus.evapStatus.zoneD = False

            brivisStatus.evapStatus.commonAuto = False
            brivisStatus.evapStatus.zoneAAuto = False
            brivisStatus.evapStatus.zoneBAuto = False
            brivisStatus.evapStatus.zoneCAuto = False
            brivisStatus.evapStatus.zoneDAuto = False

class EvapStatus():
    """Evap function status"""
    evapOn = False
    manualMode = False
    autoMode = False
    fanOn = False
    fanSpeed = 0
    waterPumpOn = False
    comfort = 0
    commonAuto = False
    temperature = 999
    prewetting = False
    coolerBusy = False

    #zones
    zones = []
    zoneA = False
    zoneAAuto = False
    zoneB = False
    zoneBAuto = False
    zoneC = False
    zoneCAuto = False
    zoneD = False
    zoneDAuto = False

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

