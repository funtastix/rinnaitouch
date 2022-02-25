# Top level mode
# Operating mode
modeCoolCmd = '{"SYST": {"OSS": {"MD": "C" } } }'
modeEvapCmd = '{"SYST": {"OSS": {"MD": "E" } } }'
modeHeatCmd = '{"SYST": {"OSS": {"MD": "H" } } }'

# Heating Commands
heatOnCmd = '{"HGOM": {"OOP": {"ST": "N" } } }'
heatOffCmd = '{"HGOM": {"OOP": {"ST": "F" } } }'
heatCircFanOn = '{"HGOM": {"OOP": {"ST": "Z" } } }'
heatCircFanSpeed = '{{"HGOM": {{"OOP": {{"FL": "{speed}" }} }} }}' # 1 - 16

heatSetTemp = '{{"HGOM": {{"GSO": {{"SP": "{temp}" }} }} }}'
heatSetManual = '{{"HGOM": {{"GSO": {{"OP": "M" }} }} }}'
heatSetAuto = '{{"HGOM": {{"GSO": {{"OP": "A" }} }} }}'
heatAdvance = '{{"HGOM": {{"GSO": {{"AO": "A" }} }} }}'

heatZoneOn = '{{"HGOM": {{"Z{zone}O": {{"UE": "Y" }} }} }}'
heatZoneOff = '{{"HGOM": {{"Z{zone}O": {{"UE": "N" }} }} }}'
heatZoneSetTemp = '{{"HGOM": {{"Z{zone}O": {{"SP": "{temp}" }} }} }}'
heatZoneSetManual = '{{"HGOM": {{"Z{zone}O": {{"OP": "M" }} }} }}'
heatZoneSetAuto = '{{"HGOM": {{"Z{zone}O": {{"OP": "A" }} }} }}'
heatZoneAdvance = '{{"HGOM": {{"Z{zone}O": {{"AO": "A" }} }} }}'

HEAT_COMMANDS = [heatOnCmd, heatOffCmd, heatSetTemp, heatCircFanOn, heatZoneOn, heatZoneOff, heatSetManual, heatSetAuto, heatAdvance, heatZoneSetTemp, heatZoneSetManual, heatZoneSetAuto, heatZoneAdvance, heatCircFanSpeed]

# Cooling Commands
coolOnCmd = '{"CGOM": {"OOP": {"ST": "N" } } }'
coolOffCmd = '{"CGOM": {"OOP": {"ST": "F" } } }'
coolCircFanOn = '{"CGOM": {"OOP": {"ST": "Z" } } }'
coolCircFanSpeed = '{{"CGOM": {{"OOP": {{"FL": "{speed}" }} }} }}' # 1 - 16

coolSetTemp = '{{"CGOM": {{"GSO": {{"SP": "{temp}" }} }} }}'
coolSetManual = '{{"CGOM": {{"GSO": {{"OP": "M" }} }} }}'
coolSetAuto = '{{"CGOM": {{"GSO": {{"OP": "A" }} }} }}'
coolAdvance = '{{"CGOM": {{"GSO": {{"AO": "A" }} }} }}'

coolZoneOn = '{{"CGOM": {{"Z{zone}O": {{"UE": "Y" }} }} }}'
coolZoneOff = '{{"CGOM": {{"Z{zone}O": {{"UE": "N" }} }} }}'
coolZoneSetTemp = '{{"CGOM": {{"Z{zone}O": {{"SP": "{temp}" }} }} }}'
coolZoneSetManual = '{{"CGOM": {{"Z{zone}O": {{"OP": "M" }} }} }}'
coolZoneSetAuto = '{{"CGOM": {{"Z{zone}O": {{"OP": "A" }} }} }}'
coolZoneAdvance = '{{"CGOM": {{"Z{zone}O": {{"AO": "A" }} }} }}'

COOL_COMMANDS = [coolOnCmd, coolOffCmd, coolSetTemp, coolCircFanOn, coolZoneOn, coolZoneOff, coolSetManual, coolSetAuto, coolAdvance, coolZoneSetTemp, coolZoneSetManual, coolZoneSetAuto, coolZoneAdvance, coolCircFanSpeed]

# Evap Cooling commands
evapOnCmd =  '{"ECOM": {"GSO": {"SW": "N" } } }'
evapOffCmd =  '{"ECOM": {"GSO": {"SW": "F" } } }'

evapPumpOn = '{"ECOM": {"GSO": {"PS": "N" } } }'
evapPumpOff = '{"ECOM": {"GSO": {"PS": "F" } } }'

evapFanOn = '{"ECOM": {"GSO": {"FS": "N" } } }'
evapFanOff = '{"ECOM": {"GSO": {"FS": "F" } } }'
evapFanSpeed = '{{"ECOM": {{"GSO": {{"FL": "{speed}" }} }} }}' # 1 - 16

evapSetManual = '{{"ECOM": {{"GSO": {{"OP": "M" }} }} }}'
evapSetAuto = '{{"ECOM": {{"GSO": {{"OP": "A" }} }} }}'
evapSetComfort = '{{"ECOM": {{"GSO": {{"SP": "{comfort}" }} }} }}'

evapZoneOn = '{{"ECOM": {{"GSO": {{"Z{zone}UE": "Y" }} }} }}'
evapZoneOff = '{{"ECOM": {{"GSO": {{"Z{zone}UE": "N" }} }} }}'
evapZoneSetManual = '{{"ECOM": {{"GSS": {{"Z{zone}AE": "N" }} }} }}'
evapZoneSetAuto = '{{"ECOM": {{"GSS": {{"Z{zone}AE": "Y" }} }} }}'

EVAP_COMMANDS = [evapOnCmd, evapOffCmd, evapPumpOn, evapPumpOff, evapFanOn, evapFanOff, evapFanSpeed, evapSetManual, evapSetAuto, evapSetComfort, evapZoneOn, evapZoneOff, evapZoneSetManual, evapZoneSetAuto]

MODE_COMMANDS = [modeCoolCmd, modeEvapCmd, modeHeatCmd, heatOnCmd, coolOnCmd, evapOnCmd, heatSetAuto, heatSetManual, coolSetAuto, coolSetManual, evapSetAuto, evapSetManual]