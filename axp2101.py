# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Dario Cammi
#
# SPDX-License-Identifier: MIT
"""
`axp2101`
================================================================================

Circuitpython driver for AXP2101 power management IC


* Author(s): Dario Cammi

Implementation Notes
--------------------

**Hardware:**

* `AXP2101 X-Powers <http://www.x-powers.com/en.php/Info/product_detail/article_id/95>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/CDarius/CircuitPython_AXP2101.git"

from adafruit_bus_device.i2c_device import I2CDevice

try:
    import busio
    from typing import Tuple
except ImportError:
    pass


# pylint: disable=too-few-public-methods
class BatteryStatus:
    """Enum-like class from AXP2101 battery charging status

    .. py:attribute:: DISCHARGING
        :type: BatteryStatus

        The battery is discharging, battery is powering the devices

    .. py:attribute:: STANDBY
        :type: BatteryStatus

        The battery is neither charging neither discharging

    .. py:attribute:: CHARGING
        :type: BatteryStatus

        The battery is charging

    """

    def __init__(self, value):
        self.value = value


#: BatteryStatus: The battery is charging
BatteryStatus.DISCHARGING = BatteryStatus(1)
BatteryStatus.STANDBY = BatteryStatus(2)
BatteryStatus.CHARGING = BatteryStatus(3)


class AXP2101:
    """Circuitpython driver for AXP2101 power management IC

    This driver class is designed not to be directly instanciated but to be extended.
    The subclass should not directly expose LDOs but specific properties and methos
    to interact with connected hardware. For example on M5Stack Core3 the DLDO1 is the
    output power the LCD backlight. The subclass instead of expose the DLDO1 voltage control
    should expose a property to control the DLDO1 brightness

    :param ~busio.I2C i2c: The I2C bus AXP2101 is connected to
    :param int device_address: The I2C bus addres. Default to 0x34

    **Quickstart: Importing and using the device**

    Here is an example of using the :py:class:`AXP2101` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        import board
        from axp201 import AXP201

    Once this is done you can define your `board.I2C` object and define your sensor object

    .. code-block:: python

        i2c = board.I2C()  # uses board.SCL and board.SDA
        pmic = AXP2101(i2c)

    Now you can get the AXP2101 battery status

    .. code-block:: python

        is_battery_connected = pmic.is_battery_connected
        battery_voltage = pmic.battery_voltage
    """

    def __init__(self, i2c: busio.I2C, device_address: int = 0x34):
        self._device = I2CDevice(i2c, device_address)
        self._buffer = bytearray(2)
        # Enable power key press interrupt
        self._set_bit_in_register(0x41, 0x0C, True)
        # Enable battery voltage ADC
        self._set_bit_in_register(0x30, 0x01, True)
        # Enable all ALDOxx
        self._set_bit_in_register(0x90, 0x0F, True)

    def power_off(self) -> None:
        """Switch off the AXP2101 and the connected devices"""
        self._set_bit_in_register(0x10, 0x01, True)

    @property
    def power_key_was_pressed(self) -> Tuple[bool, bool]:
        """Power key pressed status

        :returns: Two booleans: Power key is short press and power key is long press
        """
        reg_val = self._read_register8(0x49)
        short_press = (reg_val & 0x08) != 0
        long_press = (reg_val & 0x04) != 0
        # clear the readed interrupt events
        if short_press or long_press:
            self._write_register8(0x49, 0x0C)

        return (short_press, long_press)

    @property
    def is_battery_connected(self) -> bool:
        """True when a battery is connected to AXP2101"""
        reg_val = self._read_register8(0x00)
        return (reg_val & 0b00001000) != 0

    @property
    def battery_level(self) -> int:
        """Battery level in percentage (0% - 100%)

        Returns 0 if no battery is connected to AXP2101
        """
        return self._read_register8(0xA4)

    @property
    def battery_voltage(self) -> int:
        """Battery voltage in mV"""
        return self._read_register14(0x34)

    @property
    def battery_charging_enabled(self) -> bool:
        """Enable/disable the battery charging"""
        reg_val = self._read_register8(0x18)
        return (reg_val & 0x02) != 0

    @battery_charging_enabled.setter
    def battery_charging_enabled(self, enabled: bool) -> None:
        if isinstance(enabled, bool):
            self._set_bit_in_register(0x18, 0x02, enabled)
        else:
            raise ValueError("Enabled must be a boolean")

    @property
    def battery_status(self) -> BatteryStatus:
        """Battery charging status

        Returns if the battery is charging, discharging or in standby
        Returns ``None`` if no battery is connected

        +-------------------------------------------+
        | Statuse                                   |
        +===========================================+
        | :py:attr:`BatteryStatus.DISCHARGING`      |
        +-------------------------------------------+
        | :py:attr:`BatteryStatus.STANDBY`          |
        +-------------------------------------------+
        | :py:attr:`BatteryStatus.CHARGING`         |
        +-------------------------------------------+

        """
        if not self.is_battery_connected:
            return None

        reg_val = (self._read_register8(0x01) & 0b01100000) >> 5
        if reg_val == 0b00:
            return BatteryStatus.STANDBY
        if reg_val == 0b01:
            return BatteryStatus.CHARGING
        if reg_val == 0b10:
            return BatteryStatus.DISCHARGING

        return None

    @property
    def _aldo1_voltage_setpoint(self) -> int:
        """Get/set ALDO1 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(0)

    @_aldo1_voltage_setpoint.setter
    def _aldo1_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(0, voltage)

    @property
    def _aldo2_voltage_setpoint(self) -> int:
        """Get/set ALDO2 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(1)

    @_aldo2_voltage_setpoint.setter
    def _aldo2_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(1, voltage)

    @property
    def _aldo3_voltage_setpoint(self) -> int:
        """Get/set ALDO3 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(2)

    @_aldo3_voltage_setpoint.setter
    def _aldo3_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(2, voltage)

    @property
    def _aldo4_voltage_setpoint(self) -> int:
        """Get/set ALDO4 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(3)

    @_aldo4_voltage_setpoint.setter
    def _aldo4_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(3, voltage)

    @property
    def _bldo1_voltage_setpoint(self) -> int:
        """Get/set BLDO1 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(4)

    @_bldo1_voltage_setpoint.setter
    def _bldo1_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(4, voltage)

    @property
    def _bldo2_voltage_setpoint(self) -> int:
        """Get/set BLDO2 ouput voltage in mV

        The output achievable voltage range is 500-3500 mV
        Setting property to 0 disable the output
        """
        return self.__get_ldo(5)

    @_bldo2_voltage_setpoint.setter
    def _bldo2_voltage_setpoint(self, voltage: int) -> None:
        self.__set_ldo(5, voltage)

    @property
    def _dldo1_voltage_setpoint(self) -> int:
        """Get/set DLDO1 ouput voltage in mV

        The output achievable voltage range is 500-3400 mV
        Setting property to 0 disable the output
        """
        return self.__get_dldo(1)

    @_dldo1_voltage_setpoint.setter
    def _dldo1_voltage_setpoint(self, voltage: int) -> None:
        self.__set_dldo(1, voltage)

    @property
    def _dldo2_voltage_setpoint(self) -> int:
        """Get/set DLDO2 ouput voltage in mV

        The output achievable voltage range is 500-1400 mV
        Setting property to 0 disable the output
        """
        return self.__get_dldo(2)

    @_dldo2_voltage_setpoint.setter
    def _dldo2_voltage_setpoint(self, voltage: int) -> None:
        self.__set_dldo(2, voltage)

    def __set_ldo(self, num: int, voltage: int) -> None:
        """Set an LDO (ALDOx, BLDOx) output voltage

        :param int num: LDO number -> 0=ALDO1 ~ 3=ALDO4, 4=BLDO1, 5=BLDO2
        :param int voltage: Desired output voltage in mV.
            The output achievable voltage range is 500-3500 mV
            Setting ``voltage`` to 0 disable the output
        """
        if 0 <= num <= 5:
            reg_volt = num + 0x92
            reg90bit = 1 << num
            if 0 <= voltage <= 3500:
                if voltage >= 500:
                    reg_value = (voltage - 500) // 100
                    self._write_register8(reg_volt, reg_value)
                    self._set_bit_in_register(0x90, reg90bit, True)
                else:
                    self._set_bit_in_register(0x90, reg90bit, False)
            else:
                raise ValueError("LDO voltage out of range. Allowed range 0-3500 mV")
        else:
            raise ValueError("Invalid LDO number")

    def __get_ldo(self, num: int) -> int:
        """Get an LDO (ALDOx, BLDOx) output voltage

        :param int num: LDO number -> 0=ALDO1 ~ 3=ALDO4, 4=BLDO1, 5=BLDO2
        """
        if 0 <= num <= 5:
            reg_volt = num + 0x92
            reg90bit = 1 << num
            reg90 = self._read_register8(0x90)
            if (reg90 & reg90bit) != 0:
                reg_value = self._read_register8(reg_volt)
                return reg_value * 100 + 500

            return 0

        raise ValueError("Invalid LDO number")

    def __set_dldo(self, num: int, voltage: int) -> None:
        """Set a DLDOx output voltage

        :param int num: DLDO number -> 1=DLDO1, 2=DLDO2
        :param int voltage: Desired output voltage in mV.
            The output achievable voltage range is 500-3400 mV for DLDO1
            and 500-1400 mV for DLDO2
            Setting ``voltage`` to 0 disable the output
        """
        if 1 <= num <= 2:
            if num == 1:
                reg_volt = 0x99
                max_volt = 3400
                reg_enable = 0x90
                reg_enable_bit = 0x80
            else:
                reg_volt = 0x9A
                max_volt = 1400
                reg_enable = 0x91
                reg_enable_bit = 0x01

            if 0 <= voltage <= max_volt:
                if voltage >= 500:
                    step_volt = 100 if num == 1 else 50
                    reg_value = (voltage - 500) // step_volt
                    self._write_register8(reg_volt, reg_value)
                    self._set_bit_in_register(reg_enable, reg_enable_bit, True)
                else:
                    self._set_bit_in_register(reg_enable, reg_enable_bit, False)
            else:
                raise ValueError(
                    f"LDO voltage out of range. Allowed range 0-{max_volt} mV"
                )
        else:
            raise ValueError("Invald DLDO number")

    def __get_dldo(self, num: int) -> None:
        """Set a DLDOx output voltage

        :param int num: DLDO number -> 1=DLDO1, 2=DLDO2
        """
        if 1 <= num <= 2:
            if num == 1:
                reg_volt = 0x99
                reg_enable = 0x90
                reg_enable_bit = 0x80
            else:
                reg_volt = 0x9A
                reg_enable = 0x91
                reg_enable_bit = 0x01

            reg_enable_val = self._read_register8(reg_enable)
            if (reg_enable_val & reg_enable_bit) != 0:
                step_volt = 100 if num == 1 else 50
                reg_value = self._read_register8(reg_volt)
                return reg_value * step_volt + 500

            return 0

        raise ValueError("Invald DLDO number")

    def _set_bit_in_register(self, register: int, bitmask: int, value: bool) -> None:
        """Set a single or multiple bits in a 8 bit register

        :param int register: Register number. Allowed range: 0-255
        :param int bitmask: Bitmask 8 bit wide with the bits to set/clear
        :param bool value: Desired bits value
        """

        self._buffer[0] = register
        with self._device:
            self._device.write_then_readinto(
                self._buffer, self._buffer, out_end=1, in_start=1
            )
            if value:
                self._buffer[1] |= bitmask
            else:
                self._buffer[1] &= ~bitmask

            self._device.write(self._buffer)

    def _write_register8(self, register: int, value: int) -> None:
        """Write an AXP2101 8bit register

        :param int register: Register number. Allowed range: 0-255
        :param int value: Value to write: Allowed range: 0x0 - 0xFF
        """

        self._buffer[0] = register
        self._buffer[1] = value
        with self._device:
            self._device.write(self._buffer)

    def _read_register8(self, register: int) -> int:
        """Read an AXP2101 8bit register

        :param int register: Register number. Allowed range: 0-255
        :returns: The register value
        """

        self._buffer[0] = register
        with self._device:
            self._device.write_then_readinto(
                self._buffer, self._buffer, out_end=1, in_end=1
            )

        return self._buffer[0]

    def _read_register14(self, register: int) -> int:
        """Read an AXP2101 14bit register

        :param int register: Register number. Allowed range: 0-255
        :returns: The register value
        """

        self._buffer[0] = register
        with self._device:
            self._device.write_then_readinto(self._buffer, self._buffer, out_end=1)

        return (self._buffer[0] & 0x3F) << 8 | self._buffer[1]
