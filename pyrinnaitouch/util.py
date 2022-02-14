import socket
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

def GetAttribute(data, attribute, defaultValue):
    return data.get(attribute) or defaultValue

def YNtoBool(str):
    """Convert Rinnai YN to Bool"""
    if str == "Y":
        return True
    else:
        return False
