# SPDX-FileCopyrightText: Copyright (c) 2024 Dario Cammi
#
# SPDX-License-Identifier: Unlicense
"""
This script detect if a battery is connected to AXP2101 and
if it is connected it reads the voltage
"""
import time
import board
from axp2101 import AXP2101

i2c = board.I2C()
pmic = AXP2101(i2c)

while True:
    if pmic.is_battery_connected:
        battery_voltage = pmic.battery_voltage
        print(f"Battery voltage {battery_voltage}V")
    else:
        print("No battery connected")

    time.sleep(1)
