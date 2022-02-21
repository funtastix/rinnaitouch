# Rinnai/Brivis Touch Wifi HASS integration

![Lint](https://github.com/funtastix/rinnaitouch/workflows/Lint/badge.svg) ![Pylint](https://github.com/funtastix/rinnaitouch/workflows/Pylint/badge.svg)

## :information_source: Based on python project [MyTouch](https://github.com/christhehoff/MyTouch)

This custom component is inspired by the above project and various other attempts to create an integration.

[@C-Westin](https://github.com/C-Westin/rinnai_touch_climate)
[@jerryzou](https://github.com/jerryzou/rinnai_touch_climate)

Also heavily used the documentation: [NBW2API](https://hvac-api-docs.s3.us-east-2.amazonaws.com/NBW2API_Iss1.3.pdf)

## :blue_heart: Thanks

Thanks to all the above for the groundwork on this!

## :flight_departure: Dependencies

This component has a dependency on `pyrinnaitouch` which currently resides in a subdirectory but in the future will be installed automatically by Home Assistant.

## Capabilities

To support the controller and make it work with the HA climate entity,these are the mappings:

HVAC modes:
- HVAC_MODE_HEAT_COOL → Manual Mode (all operating modes)
- HVAC_MODE_AUTO → Auto Mode (all operating modes)
- HVAC_MODE_OFF → Unit Off (any operating mode)

PRESET modes:
- PRESET_COOL → Cooling mode
- PRESET_HEAT → Heater mode
- PRESET_EVAP → Evap mode

You can manipulate the Fan as required. Fan Only mode in Evap will turn off the pump.

I have added support for an external temperature sensor, as it bothered me to have 0 degrees in the UI all the time. NC-6 Controllers do not report their temperature. (NC-7s do, but I have not implemented that yet)

Basically, it supports the full functionality of the network controller. I have mapped these via HVAC states and PRESETS:

I have not tested the Cooling mode, as I do not have cooling

## Further Plans

1. <del>Work on stability. Sending commands is not fully reliable. The above documentation, page 16 indicates how to properly deal with that.</del>
2. <del>Filter HVAC modes by system ability</del>
3. <del>Implement reading NC-7 temperature for when no external sensor is set up</del>
4. <del>Implement zone switches</del>
5. All items in the [project list](https://github.com/funtastix/rinnaitouch/projects/1)
6. Break out the library `pyrinnaitouch` and upload to PyPi
7. Make component HACS compatible

## Installation

1. Logon to your HA or HASS with SSH
2. Go to the HA 'custom_components' directory within the HA installation path (The directory is in the folder where the 'configuration.yaml' file is located. If this is not available - create this directory).
3. Run `cd custom_components`
4. Run `git clone https://github.com/funtastix/rinnaitouch` within the `custom_components` directory
5. Restart your HA/HASS service in the UI with `<your-URL>/config/server_control`
8. Add your fireplace either by: HA UI by navigating to "Integrations" -> "Add Integration" -> "Rinnai Touch" (If it is not available, clear your web browser cache to renew the integrations list.)
