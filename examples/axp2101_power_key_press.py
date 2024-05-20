# SPDX-FileCopyrightText: Copyright (c) 2024 Dario Cammi
#
# SPDX-License-Identifier: MIT
"""
This script demonstrate how to get the power key press status
"""
import time
import board
from axp2101 import AXP2101

i2c = board.I2C()
pmic = AXP2101(i2c)

while True:
    short_press, long_press = pmic.power_key_was_pressed
    if short_press:
        print("Power key was short pressed")
    elif long_press:
        print("Power key was long pressed")
    else:
        print("Power key isn't press")

    time.sleep(1)
