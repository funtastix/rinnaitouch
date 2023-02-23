# Rinnai/Brivis Touch Wifi HASS integration

![Pylint](https://github.com/funtastix/rinnaitouch/workflows/Pylint/badge.svg)

This custom component was originally inspired by the below projects and attempts to create an integration.

[MyTouch](https://github.com/christhehoff/MyTouch)
[@C-Westin](https://github.com/C-Westin/rinnai_touch_climate)
[@jerryzou](https://github.com/jerryzou/rinnai_touch_climate)

Also heavily used the documentation: [NBW2API](https://hvac-api-docs.s3.us-east-2.amazonaws.com/NBW2API_Iss1.3.pdf)

## :blue_heart: Thanks

Thanks to all the above for the groundwork on this!

## :flight_departure: Dependencies

This component has a dependency on [pyrinnaitouch](https://github.com/funtastix/pyrinnaitouch) which will be installed automatically by Home Assistant.

## Capabilities

Read more details in the [wiki](https://github.com/funtastix/rinnaitouch/wiki) and feel free to send me contributions.

To support the controller and make it work with the HA climate entity, these are the mappings:

#### HVAC modes:
- HVAC_MODE_HEAT → Heating mode (gas heater)
- HVAC_MODE_COOL → Cooling Mode (evap or refrigerated)
- HVAC_MODE_OFF → Unit Off (any operating mode)
- HVAC_MODE_FAN_ONLY - Only circulation fan is on while in heating or cooling mode \
    <b>Note</b>: HVAC_MODE_FAN_ONLY is not available while in  Mode Evaporative where the water pump switch to off achieves a similar result

#### PRESET modes:
- PRESET_MANUAL → Manual mode \
  in Evaporative Mode this allow fan level control, in Heat/Cooler Mode this sets a single target temperature
- PRESET_AUTO → Auto mode \
  in Evaporative Mode this means Comfort Setting, in Heat/Cooler Mode, this means Schedule

There is now internally a cooling selector (preselected, only available if multiple cooling methods installed)
- COOLING_EVAP → Evap mode
- COOLING_COOL → Refrigerated mode

You can manipulate the Fan as required.

There is support for an external temperature sensor, to avoid having 0 degrees in the UI all the time. NC-6 Controllers do not report their temperature. (NC-7s do, and it should work. Please raise an issue if it doesn't)

<b>Cooling mode</b> has been tested by other users and seems to work well, as I do not have cooling.

Support for <b>zones</b> has come a long way, but there is still more testing to be done. I don't have zones myself.

## Further Plans

I've recently refactored the code to make it more manageable, but I don't have any further plans, not will I put in the work to integrate into core. HACS is a pretty good place to be, and I'm planning to keep the integraion updated while I have personal use (probably years to come).

## Installation

Use [HACS](https://hacs.xyz/docs/basic/getting_started) to install by adding the repository and downloading any version from 0.9.0.

## Installation for testing

1. Logon to your HA or HASS with SSH
2. Go to the HA 'custom_components' directory within the HA installation path (The directory is in the folder where the 'configuration.yaml' file is located. If this is not available - create this directory).
3. Run `cd custom_components`
4. Run `git clone https://github.com/funtastix/rinnaitouch` within the `custom_components` directory. This will create a new rinnaitouch/custom_components/rinnaitouch subdirectory.
5. Copy everything from rinnaitouch/custom_components/rinnaitouch to rinnaitouch (base of the clone): `cp -r rinnaitouch/custom_components/rinnaitouch/* rinnaitouch/`
6. Restart your HA/HASS service
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
