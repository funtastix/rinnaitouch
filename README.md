# Rinnai/Brivis Touch Wifi HASS integration

![Pylint](https://github.com/funtastix/rinnaitouch/workflows/Pylint/badge.svg)

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

Read more details in the [wiki](https://github.com/funtastix/rinnaitouch/wiki)

To support the controller and make it work with the HA climate entity, these are the mappings and they have changed with version 0.10.0:

HVAC modes:
- HVAC_MODE_HEAT → Heating mode (gas heater)
- HVAC_MODE_COOL → Cooling Mode (evap or refrigerated)
- HVAC_MODE_OFF → Unit Off (any operating mode)
- HVAC_MODE_FAN_ONLY - Only circulation fan is on while in heating or cooling mode

PRESET modes:
- PRESET_MANUAL → Manual mode
- PRESET_AUTO → Auto mode

There is now internally a cooling selector (preselected, only available if multiple cooling methods installed)
- COOLING_EVAP → Evap mode
- COOLING_COOL → Refrigerated mode

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
6. <del>Break out the library `pyrinnaitouch` and upload to PyPi</del>
7. <del>Make component HACS compatible</del>

## Installation

Use [HACS](https://hacs.xyz/docs/basic/getting_started) to install by adding the repository and downloading any version from 0.9.0.

## Installation for testing

1. Logon to your HA or HASS with SSH
2. Go to the HA 'custom_components' directory within the HA installation path (The directory is in the folder where the 'configuration.yaml' file is located. If this is not available - create this directory).
3. Run `cd custom_components`
4. Run `git clone https://github.com/funtastix/rinnaitouch` within the `custom_components` directory. This will create a new rinnaitouch/custom_components/rinnaitouch subdirectory.
5. Move everything from rinnaitouch/custom_components/rinnaitouch to rinnaitouch (base of the clone): `mv rinnaitouch/custom_components/rinnaitouch/* rinnaitouch/`
6. Restart your HA/HASS service in the UI with `<your-URL>/config/server_control`
7. Add your Rinnai Touch either by: HA UI by navigating to "Integrations" -> "Add Integration" -> "Rinnai Touch" (If it is not available, clear your web browser cache to renew the integrations list.)

## Enable Debug

```YAML
logger:
  default: warn
  logs:
    custom_components.rinnaitouch: debug
    custom_components.rinnaitouch.pyrinnaitouch: debug
    pyrinnaitouch: debug
```
