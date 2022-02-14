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

## Further Plans

1. <del>Work on stability. Sending commands is not fully reliable. The above documentation, page 16 indicates how to properly deal with that.</del>
2. Filter HVAC modes by system ability
3. Break out the library `pyrinnaitouch` and upload to PyPi
4. Make component HACS compatible

## Installation

1. Logon to your HA or HASS with SSH
2. Go to the HA 'custom_components' directory within the HA installation path (The directory is in the folder where the 'configuration.yaml' file is located. If this is not available - create this directory).
3. Run `cd custom_components`
4. Run `git clone https://github.com/funtastix/rinnaitouch` within the `custom_components` directory
5. Restart your HA/HASS service in the UI with `<your-URL>/config/server_control`
8. Add your fireplace either by: HA UI by navigating to "Integrations" -> "Add Integration" -> "Rinnai Touch" (If it is not available, clear your web browser cache to renew the integrations list.)