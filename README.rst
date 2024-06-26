Introduction
============


.. image:: https://readthedocs.org/projects/circuitpython-axp2101/badge/?version=latest
    :target: https://circuitpython-axp2101.readthedocs.io/
    :alt: Documentation Status



.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/CDarius/CircuitPython_AXP2101/workflows/Build%20CI/badge.svg
    :target: https://github.com/CDarius/CircuitPython_AXP2101/actions
    :alt: Build Status


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

Circuitpython driver for AXP2101 power management IC


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.

Installing from PyPI
=====================
.. note:: This library is not available on PyPI yet. Install documentation is included
   as a standard element. Stay tuned for PyPI availability!

Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install axp2101

Or the following command to update an existing version:

.. code-block:: shell

    circup update

Usage Example
=============

.. code-block:: python

    # Read battery voltage
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

Documentation
=============
API documentation for this library can be found on `Read the Docs <https://circuitpython-axp2101.readthedocs.io/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/CDarius/CircuitPython_AXP2101/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
