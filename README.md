# Python Interface to NimbleStroker

## Intended Users

This little piece of code might be useful for people who would like
to control their NimbleStroker from a PC without the
manufacturer-recommended connectivity module. It might also offer advanced
users an easier way to play with their toy, without installing and
configuring a whole massive Arduino IDE.

## Drawbacks

The Actuator (the pumping part of the toy) expects to receive a new
position sample with quite a high repetition rate (preferably 500 Hz).
If the computer or serial port lags, your toy might not run as smoothly
as under Pendant control.

## License

This is free and unencumbered software released into the public domain.
See LICENSE.md for details. Do not blame me if your d**k falls off
or the house catches fire as a result of using this module.

## Electrical Interface

According to the manufacturer, the Actuator communications port is wired
as follows:

| Pin | Function | Comment                       |
|-----|----------|-------------------------------|
| 1   | Unused   |                               |
| 2   | +12 V    | I have measured 8 V here      |
| 3   | TX (5 V) | Actuator to Pendant           |
| 4   | RX (5 V) | Pendant to Actuator           |
| 5   | GND      |                               |
| 6   | Unused   | Controls reset of the Pendant |

In order to connect to that, you need a USB-to-Serial converter with
5 V I/O. There are many inexpensive converters that match this specification.

To control the NimbleStroker Actuator, you have to connect only three wires.

| Actuator Pin | Converter Pin |
|--------------|---------------|
| GND          | GND           |
| TX           | RX or RxD     |
| RX           | TX or TxD     |

To build the interface, you can use and old (4 wire!) telephone cable
with RJ11 connector and a soldering iron.

## Protocol

The protocol is [nicely documented](https://github.com/ExploratoryDevices/NimbleConModule/blob/main/docs/hardware-specs.md) in the ExploratoryDevices repository.

Here is some additional information that you can get from sniffing the
communication between the Pendant and the Actuator:
 - The "FORCE_COMMAND" seems to always be set to the maximum of 1023
 - The "ACK" bit means that the Actuator is enabled
 - The control frame is sent every 2 ms

## What does the code do?

Out of the box, the code will drive the Actuator with a constant waveform
analogous to the one coming from the Pendant with moderate intensity,
texture, and nature. Feel free to adapt the waveform to your needs.

If you would like to spy on the protocol, there is also a commented-out
code for capturing and analysing the frames.
