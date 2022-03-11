import socket
import time
import json
import re
import asyncio
from .heater import HandleHeatingMode, HeaterStatus
from .cooler import HandleCoolingMode, CoolingStatus
from .evap import HandleEvapMode, EvapStatus
from .commands import *
import logging
from .util import *

_LOGGER = logging.getLogger(__name__)

class Event(object):

    def __init__(self):
        self.__eventhandlers = []

    def __iadd__(self, handler):
        self.__eventhandlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__eventhandlers.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        for eventhandler in self.__eventhandlers:
            if eventhandler is not None:
                eventhandler(*args, **keywargs)

class BrivisStatus():
    """Overall Class for describing status"""
    #modes
    evapMode = False
    coolingMode = False
    heaterMode = False
    systemOn = False
    tempUnit = None
    hasHeater = True
    hasCooling = True
    hasEvap = True

    #system info
    firmwareVersion = None
    wifiModuleVersion = None

    #zones
    zoneAdesc = None
    zoneBdesc = None
    zoneCdesc = None
    zoneDdesc = None
    isMultiSetPoint = False

    #faults
    hasFault = False

    heaterStatus = HeaterStatus()
    coolingStatus = CoolingStatus()
    evapStatus = EvapStatus()

    def setMode(self,mode):
        if mode == Mode.HEATING:
            self.heaterMode = True
            self.coolingMode = False
            self.evapMode = False
        elif mode == Mode.COOLING:
            self.heaterMode = False
            self.coolingMode = True
            self.evapMode = False
        elif mode == Mode.EVAP:
            self.heaterMode = False
            self.coolingMode = False
            self.evapMode = True

# Ideally we could create an enum, but looks like that needs enum library - which nmight not be
# available???
class Mode:
    HEATING = 1
    EVAP = 2
    COOLING = 3
    RC = 4
    NONE = 5

def ReadableMode(mode):
    if mode == 1:
        return "HEATING"
    elif mode == 2:
        return "EVAP"
    elif mode == 3:
        return "COOLING"
    elif mode == 4:
        return "RC"
    else:
        return "NONE"

class RinnaiSystem:

    clients = {}
    instances = {}

    TEMP_CELSIUS = "°C"
    TEMP_FAHRENHEIT = "°F"

    def __init__(self, ip_address):
        self._touchIP = ip_address
        self._touchPort = 27847
        self._sendSequence = 1
        self._lastupdated = 0
        self._status = BrivisStatus()
        self._lastclosed = 0
        self._client = None
        self._zones = []
        self._jsonerrors = 0
        self._nosendupdates = 0
        if ip_address not in RinnaiSystem.clients:
            RinnaiSystem.clients[ip_address] = self._client
        else:
            self._client = RinnaiSystem.clients[ip_address]
        RinnaiSystem.instances[ip_address] = self
        self.OnUpdated = Event()

    def setZones(self, zones):
        self._zones = zones

    @staticmethod
    def getInstance(ip_address):
        if ip_address in RinnaiSystem.instances:
            return RinnaiSystem.instances[ip_address]
        else:
            return RinnaiSystem(ip_address)

    def SubscribeUpdates(self,objMethod):
        self.OnUpdated += objMethod

    def UnsubscribeUpdates(self,objMethod):
        self.OnUpdated -= objMethod

    async def ReceiveData(self, client, timeout=5):
        total_data = []
        data = ''
        nodata = False

        begin = time.time()
        while 1:
            try:
                data = client.recv(4096)
                if data and (len(data) > 0):
                    total_data.append(data)
                else:
                    nodata = True
            except:
                pass

            if time.time()-begin > timeout or nodata:
                break

        return b"".join(total_data)

    async def HandleStatus(self, client, brivisStatus):
        # Make sure enough time passed to get a status message
        await asyncio.sleep(1.5)
        #status = client.recv(4096)
        #_LOGGER.debug(status)

        try:
            status = await self.ReceiveData(client, 2)
            #jStr = status[14:]
            exp = re.search('^.*([0-9]{6}).*(\[[^\[]*\])[^]]*$', str(status))
            seq = int(exp.group(1))
            if seq >= 255:
                seq = 0
            else:
                seq = seq + 1
            self._sendSequence = seq
            jStr = exp.group(2)
            #jStr = '[{"SYST": {"CFG": {"MTSP": "N", "NC": "00", "DF": "N", "TU": "C", "CF": "1", "VR": "0183", "CV": "0010", "CC": "043", "ZA": " ", "ZB": " ", "ZC": " ", "ZD": " " }, "AVM": {"HG": "Y", "EC": "N", "CG": "Y", "RA": "N", "RH": "N", "RC": "N" }, "OSS": {"DY": "TUE", "TM": "16:45", "BP": "Y", "RG": "Y", "ST": "N", "MD": "C", "DE": "N", "DU": "N", "AT": "999", "LO": "N" }, "FLT": {"AV": "N", "C3": "000" } } },{"CGOM": {"CFG": {"ZUIS": "N", "ZAIS": "Y", "ZBIS": "Y", "ZCIS": "N", "ZDIS": "N", "CF": "N", "PS": "Y", "DG": "W" }, "OOP": {"ST": "F", "CF": "N", "FL": "00", "SN": "Y" }, "GSS": {"CC": "N", "FS": "N", "CP": "N" }, "APS": {"AV": "N" }, "ZUS": {"AE": "N", "MT": "999" }, "ZAS": {"AE": "N", "MT": "999" }, "ZBS": {"AE": "N", "MT": "999" }, "ZCS": {"AE": "N", "MT": "999" }, "ZDS": {"AE": "N", "MT": "999" } } }]'
            _LOGGER.debug("Sequence: %s Json: %s", seq, jStr)

            j = json.loads(jStr)
            #_LOGGER.debug(json.dumps(j[0], indent = 4))

            cfg = GetAttribute(j[0].get("SYST"),"CFG",None)
            if not cfg:
                # Probably an error
                _LOGGER.error("No CFG - Not happy, Jan")

            else:
                if GetAttribute(cfg, "TU", None) == "F":
                    brivisStatus.tempUnit = RinnaiSystem.TEMP_FAHRENHEIT
                else:
                    brivisStatus.tempUnit = RinnaiSystem.TEMP_CELSIUS

                brivisStatus.isMultiSetPoint = YNtoBool(GetAttribute(cfg, "MTSP", None))
                brivisStatus.zoneAdesc = GetAttribute(cfg, "ZA", None).strip()
                brivisStatus.zoneBdesc = GetAttribute(cfg, "ZB", None).strip()
                brivisStatus.zoneCdesc = GetAttribute(cfg, "ZC", None).strip()
                brivisStatus.zoneDdesc = GetAttribute(cfg, "ZD", None).strip()
                brivisStatus.firmwareVersion = GetAttribute(cfg, "VR", None).strip()
                brivisStatus.wifiModuleVersion = GetAttribute(cfg, "CV", None).strip()

            avm = GetAttribute(j[0].get("SYST"),"AVM",None)
            if not avm:
                # Probably an error
                _LOGGER.error("No AVM - Not happy, Jan")

            else:
                if GetAttribute(avm, "HG", None) == "Y": # or GetAttribute(avm, "RA", None) == "Y" or GetAttribute(avm, "RH", None) == "Y":
                    brivisStatus.hasHeater = True
                else:
                    brivisStatus.hasHeater = False
                if GetAttribute(avm, "CG", None) == "Y": # or GetAttribute(avm, "RA", None) == "Y" or GetAttribute(avm, "RC", None) == "Y":
                    brivisStatus.hasCooling = True
                else:
                    brivisStatus.hasCooling = False
                if GetAttribute(avm, "EC", None) == "Y":
                    brivisStatus.hasEvap = True
                else:
                    brivisStatus.hasEvap = False

            flt = GetAttribute(j[0].get("SYST"), "FLT", None)
            if not avm:
                # Probably an error
                _LOGGER.error("No FLT - Not happy, Jan")

            else:
                brivisStatus.hasFault = YNtoBool(GetAttribute(flt, "AV", None))

            if 'HGOM' in j[1]:
                HandleHeatingMode(client,j,brivisStatus)
                brivisStatus.setMode(Mode.HEATING)
                _LOGGER.debug("We are in HEAT mode")

            elif 'CGOM' in j[1]:
                HandleCoolingMode(client,j,brivisStatus)
                brivisStatus.setMode(Mode.COOLING)
                _LOGGER.debug("We are in COOL mode")

            elif 'ECOM' in j[1]:
                HandleEvapMode(client,j,brivisStatus)
                brivisStatus.setMode(Mode.EVAP)
                _LOGGER.debug("We are in EVAP mode")

            else:
                _LOGGER.debug("Unknown mode")
            return True
        except ConnectionError as conerr:
            _LOGGER.error("Couldn't decode JSON (connection), skipping (%s)", repr(connerr))
            _LOGGER.debug("Client shutting down")
            self._client.shutdown(socket.SHUT_RDWR)
            self._client.close()
            self._lastclosed = time.time()
            return False
        except Exception as err:
            _LOGGER.error("Couldn't decode JSON (exception), skipping (%s)", repr(err))
            self._jsonerrors = self._jsonerrors + 1
            #_LOGGER.debug("Client shutting down")
            #self._client.shutdown(socket.SHUT_RDWR)
            #self._client.close()
            #self._lastclosed = time.time()
            return False

    async def set_cooling_mode(self):
        return await self.validate_and_send(modeCoolCmd)

    async def set_evap_mode(self):
        return await self.validate_and_send(modeEvapCmd)

    async def set_heater_mode(self):
        return await self.validate_and_send(modeHeatCmd)

    async def turn_heater_on(self):
        return await self.validate_and_send(heatOnCmd)

    async def turn_heater_off(self):
        return await self.validate_and_send(heatOffCmd)

    async def turn_heater_fan_only(self):
        return await self.validate_and_send(heatCircFanOn)

    async def set_heater_temp(self, temp):
        cmd=heatSetTemp
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(temp=temp))
            return True
        else:
            return False

    async def set_heater_auto(self):
        return await self.validate_and_send(heatSetAuto)

    async def set_heater_manual(self):
        return await self.validate_and_send(heatSetManual)

    async def heater_advance(self):
        return await self.validate_and_send(heatAdvance)

    async def turn_heater_zone_on(self, zone):
        cmd=heatZoneOn
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def turn_heater_zone_off(self, zone):
        cmd=heatZoneOff
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_heater_zone_temp(self, zone, temp):
        cmd=heatZoneSetTemp
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone, temp=temp))
            return True
        else:
            return False

    async def set_heater_zone_auto(self, zone):
        cmd=heatZoneSetAuto
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_heater_zone_manual(self, zone):
        cmd=heatZoneSetManual
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_heater_zone_advance(self, zone):
        cmd=heatZoneAdvance
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def turn_cooling_on(self):
        return await self.validate_and_send(coolOnCmd)

    async def turn_cooling_off(self):
        return await self.validate_and_send(coolOffCmd)

    async def turn_cooling_fan_only(self):
        return await self.validate_and_send(coolCircFanOn)

    async def set_cooling_temp(self, temp):
        cmd=coolSetTemp
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(temp=temp))
            return True
        else:
            return False

    async def set_cooling_auto(self):
        return await self.validate_and_send(coolSetAuto)

    async def set_cooling_manual(self):
        return await self.validate_and_send(coolSetManual)

    async def cooling_advance(self):
        return await self.validate_and_send(coolAdvance)

    async def turn_cooling_zone_on(self, zone):
        cmd=coolZoneOn
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def turn_cooling_zone_off(self, zone):
        cmd=coolZoneOff
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_cooling_zone_temp(self, zone, temp):
        cmd=coolZoneSetTemp
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone, temp=temp))
            return True
        else:
            return False

    async def set_cooling_zone_auto(self, zone):
        cmd=coolZoneSetAuto
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_cooling_zone_manual(self, zone):
        cmd=coolZoneSetManual
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_cooling_zone_advance(self, zone):
        cmd=coolZoneAdvance
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def turn_evap_on(self):
        return await self.validate_and_send(evapOnCmd)

    async def turn_evap_off(self):
        return await self.validate_and_send(evapOffCmd)

    async def turn_evap_pump_on(self):
        return await self.validate_and_send(evapPumpOn)

    async def turn_evap_pump_off(self):
        return await self.validate_and_send(evapPumpOff)

    async def turn_evap_fan_on(self):
        return await self.validate_and_send(evapFanOn)

    async def turn_evap_fan_off(self):
        return await self.validate_and_send(evapFanOff)

    async def set_evap_auto(self):
        return await self.validate_and_send(evapSetAuto)

    async def set_evap_manual(self):
        return await self.validate_and_send(evapSetManual)

    async def set_evap_fanspeed(self, speed):
        cmd=evapFanSpeed
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(speed=f'{speed:02d}'))
            return True
        else:
            return False

    async def set_heater_fanspeed(self, speed):
        cmd=heatCircFanSpeed
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(speed=f'{speed:02d}'))
            return True
        else:
            return False

    async def set_cooling_fanspeed(self, speed):
        cmd=coolCircFanSpeed
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(speed=f'{speed:02d}'))
            return True
        else:
            return False

    async def set_evap_comfort(self, comfort):
        cmd=evapSetComfort
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(comfort=comfort))
            return True
        else:
            return False

    async def turn_evap_zone_on(self, zone):
        cmd=evapZoneOn
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def turn_evap_zone_off(self, zone):
        cmd=evapZoneOff
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_evap_zone_auto(self, zone):
        cmd=evapZoneSetAuto
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    async def set_evap_zone_manual(self, zone):
        cmd=evapZoneSetManual
        if self.validateCmd(cmd):
            await self.sendCmd(cmd.format(zone=zone))
            return True
        else:
            return False

    def GetOfflineStatus(self):
        return self._status

    def validateCmd(self, cmd):
        if cmd in MODE_COMMANDS:
            return True
        if cmd in HEAT_COMMANDS and self._status.heaterMode:
            return True
        if cmd in COOL_COMMANDS and self._status.coolingMode:
            return True
        if cmd in EVAP_COMMANDS and self._status.evapMode:
            return True
        return False

    async def renewConnection(self):
        connection_error = False
        try:
            if self._client is not None:
                if self._client.getpeername and self._client.getpeername() is not None and self._jsonerrors < 4:
                    return True
        except (OSError, ConnectionError) as ocerr:
            _LOGGER.debug("Error 1st phase during renewConnection %s", ocerr)
            connection_error = True
            pass
        # TODO: need to also check for remote address in case the server has shut the connection down
        if self._client is None or self._client._closed or connection_error or (self._jsonerrors > 2):
            try:
                if connection_error or (self._jsonerrors > 2):
                    self._client.close()
                self._jsonerrors = 0
                self._client = await self.ConnectToTouch(self._touchIP,self._touchPort)
                RinnaiSystem.clients[self._touchIP] = self._client
                return True
            except ConnectionRefusedError as crerr:
                _LOGGER.debug("Error during renewConnection %s", crerr)
            except ConnectionError as cerr:
                _LOGGER.debug("Error during renewConnection %s", cerr)
            except Exception as eerr:
                _LOGGER.debug("Error during renewConnection %s", eerr)
        return False

    async def sendCmd(self, cmd):
        if await self.renewConnection():
            _LOGGER.debug("Client Variable: %s / %s", self._client, self._client._closed)

            seq = str(self._sendSequence).zfill(6)
            #self._sendSequence = self._sendSequence + 1
            _LOGGER.debug("Sending command: %s", "N" + seq + cmd)
            await self.SendToTouch(self._client, "N" + seq + cmd)
            status = BrivisStatus()
            res = await self.HandleStatus(self._client, status)
            if res:
                self._status = status
                self.OnUpdated()
        else:
            _LOGGER.debug("renewing connection failed, not sending command")

        #self._client.shutdown(socket.SHUT_RDWR)
        #self._client.close()

    async def validate_and_send(self, cmd):
        if self.validateCmd(cmd):
            await self.sendCmd(cmd)
            return True
        else:
            _LOGGER.error("Validation of command failed. Not sending")
            return False

    async def GetStatus(self):
        #every 5 updates, blindly send an empty command to maintain the connection
        self._nosendupdates = self._nosendupdates + 1
        if self._nosendupdates > 5:
            self._nosendupdates = 0
            try:
                _LOGGER.debug("sending empty command")
                await self.SendToTouch(self._client, "NA")
                _LOGGER.debug("sent empty command")
            except Exception as err:
                _LOGGER.debug("Empty command exception: %s", err)
                pass

        if await self.renewConnection():
            status = BrivisStatus()
            _LOGGER.debug("Client Variable: %s / %s", self._client, self._client._closed)
            res = await self.HandleStatus(self._client, status)
            if res:
                self._status = status
                self.OnUpdated()

            # don't shut down unless last shutdown is 1 hour ago
            if self._lastclosed == 0:
                self._lastclosed = time.time()
            if self._lastclosed + 3600 < time.time():
                _LOGGER.debug("Client shutting down")
                self._client.shutdown(socket.SHUT_RDWR)
                self._client.close()
                self._lastclosed = time.time()

            self._lastupdated = time.time()

        else:
            _LOGGER.debug("renewing connection failed, not sending command")

        return self._status

    async def async_will_remove_from_hass():
        try:
            self._client.shutdown(socket.SHUT_RDWR)
            self._client.close()
        except:
            _LOGGER.debug("Nothing to close")

    async def ConnectToTouch(self, touchIP, port):
        # connect the client
        # create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
        _LOGGER.debug("Creating new client...")
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10)
            client.connect((touchIP, port))
            return client
        except ConnectionRefusedError as crerr:
            raise crerr
            #should really take a few hours break to recover!


    async def SendToTouch(self, client, cmd):
        """Send the command and return the response."""
        #_LOGGER.debug("DEBUG: {}".format(cmd))
        response = "NA"
        client.sendall(cmd.encode())
        # Let that sink in
        #await asyncio.sleep(0.5)
        #response = client.recv(4096)
        #return response
