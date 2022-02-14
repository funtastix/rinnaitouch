# Top level mode
# Operating mode
modeCoolCmd = '{"SYST": {"OSS": {"MD": "C" } } }'
modeEvapCmd = '{"SYST": {"OSS": {"MD": "E" } } }'
modeHeatCmd = '{"SYST": {"OSS": {"MD": "H" } } }'

# Heating Commands
#heatCmd = '{"HGOM": {"OOP": {"ST": "{}" } } }' # N = On, F = Off
heatOnCmd = '{"HGOM": {"OOP": {"ST": "N" } } }'
heatOffCmd = '{"HGOM": {"OOP": {"ST": "F" } } }'
heatCircFanOn = '{"HGOM": {"OOP": {"ST": "Z" } } }'

heatSetTemp = '{{"HGOM": {{"GSO": {{"SP": "{temp}" }} }} }}'
heatSetManual = '{{"HGOM": {{"GSO": {{"OP": "M" }} }} }}'
heatSetAuto = '{{"HGOM": {{"GSO": {{"OP": "A" }} }} }}'

#heatZone = '{"HGOM": {"Z{zone}O": {"UE": "{}" } } }'  # Y = On, N = Off
heatZoneOn = '{{"HGOM": {{"Z{zone}O": {{"UE": "Y" }} }} }}'
heatZoneOff = '{{"HGOM": {{"Z{zone}O": {{"UE": "N" }} }} }}'
#heatZoneA = '{"HGOM": {"ZAO": {"UE": "{}" } } }'  # Y = On, N = Off
#heatZoneB = '{"HGOM": {"ZBO": {"UE": "{}" } } }'
#heatZoneC = '{"HGOM": {"ZCO": {"UE": "{}" } } }'
#heatZoneD = '{"HGOM": {"ZDO": {"UE": "{}" } } }'

HEAT_COMMANDS = [heatOnCmd, heatOffCmd, heatSetTemp, heatCircFanOn, heatZoneOn, heatZoneOff, heatSetManual, heatSetAuto]

# Cooling Commands
#coolCmd = '{"CGOM": {"OOP": {"ST": "{}" } } }' # N = On, F = Off
coolOnCmd = '{"CGOM": {"OOP": {"ST": "N" } } }'
coolOffCmd = '{"CGOM": {"OOP": {"ST": "F" } } }'
coolCircFanOn = '{"CGOM": {"OOP": {"ST": "Z" } } }'

coolSetTemp = '{{"CGOM": {{"GSO": {{"SP": "{temp}" }} }} }}'
coolSetManual = '{{"CGOM": {{"GSO": {{"OP": "M" }} }} }}'
coolSetAuto = '{{"CGOM": {{"GSO": {{"OP": "A" }} }} }}'

#coolZone = '{"HGOM": {"Z{zone}O": {"UE": "{}" } } }'  # Y = On, N = Off
coolZoneOn = '{{"CGOM": {{"Z{zone}O": {{"UE": "Y" }} }} }}'
coolZoneOff = '{{"CGOM": {{"Z{zone}O": {{"UE": "N" }} }} }}'
#coolZoneA = '{"CGOM": {"ZAO": {"UE": "{}" } } }'  # Y = On, N = Off
#coolZoneB = '{"CGOM": {"ZBO": {"UE": "{}" } } }'
#coolZoneC = '{"CGOM": {"ZCO": {"UE": "{}" } } }'
#coolZoneD = '{"CGOM": {"ZDO": {"UE": "{}" } } }'

COOL_COMMANDS = [coolOnCmd, coolOffCmd, coolSetTemp, coolCircFanOn, coolZoneOn, coolZoneOff, coolSetManual, coolSetAuto]

# Evap Cooling commands
#evapCmd =  '{"ECOM": {"GSO": {"SW": "{}" } } }' # N = On, F = Off
evapOnCmd =  '{"ECOM": {"GSO": {"SW": "N" } } }'
evapOffCmd =  '{"ECOM": {"GSO": {"SW": "F" } } }'

#evapPumpCmd = '{"ECOM": {"GSO": {"PS": "{}" } } }' # N = On, F = Off
evapPumpOn = '{"ECOM": {"GSO": {"PS": "N" } } }'
evapPumpOff = '{"ECOM": {"GSO": {"PS": "F" } } }'

#evapFanCmd = 'N000014{"ECOM": {"GSO": {"FS": "{}" } } }' # N = On, F = Off
evapFanOn = '{"ECOM": {"GSO": {"FS": "N" } } }'
evapFanOff = '{"ECOM": {"GSO": {"FS": "F" } } }'
evapFanSpeed = '{{"ECOM": {{"GSO": {{"FL": "{speed}" }} }} }}' # 1 - 16

evapSetManual = '{{"ECOM": {{"GSO": {{"OP": "M" }} }} }}'
evapSetAuto = '{{"ECOM": {{"GSO": {{"OP": "A" }} }} }}'
evapSetComfort = '{{"ECOM": {{"GSO": {{"SP": "{comfort}" }} }} }}'

EVAP_COMMANDS = [evapOnCmd, evapOffCmd, evapPumpOn, evapPumpOff, evapFanOn, evapFanOff, evapFanSpeed, evapSetManual, evapSetAuto, evapSetComfort]

MODE_COMMANDS = [modeCoolCmd, modeEvapCmd, modeHeatCmd, heatOnCmd, coolOnCmd, evapOnCmd, heatSetAuto, heatSetManual, coolSetAuto, coolSetManual, evapSetAuto, evapSetManual]