# Albion Sniffing Framework

A framework for parsing, analyzing, and processing game data transmitted over the network for Albion. It can also be used for any game that utilizes **PUN**(**P**hoton **U**nity **N**etworking) by removing Albion specific parts.

## Protocol Architecture
PUN uses UDP, and each packet can contain multiple Commands, the most relevant being:
- ReliableCommand: needs confirmation and maybe flow control
- UnreliableCommand: classic UDP
- FragmentCommand: for breaking up big commands

These commands contain a Message with game data, the most relevant types being:
- RequestMessage
- ResponseMessage 
- EventMessage

Each message contains serialized data using "protocol16".

## Project Structure

### [layers.py](./layers.py)
Basic protocol definition and binding over UDP using Scapy.

### [protocol16_parser.py](./protocol16_parser.py)
Reimplementation of object deserialization used by PUN2.

### [streams.py](./streams.py)
Event, [Message using PUN terminology](./layers.py), identification, and field renaming.

### [event.py](./event.py)
Flask and SocketIO server for exporting data to external user 3rd party component. 

### [extensions](./extensions)
A place for user created extensions, these can be a single python file or a directory that can function as a python package(have a `__init__.py`).  
There are examples for each of them in the form of:

#### [fame_meter.py](./extensions/fame_meter.py)
A basic PoC fame meter that outputs to the console.

#### [hello_world](./extensions/hello_world)
An extension for tracking the current player's name and exposing it using a socketIO room and web page.

## Credit
A lot of information used in making this project was taken or confirmed from other projects, hopefully, I haven't missed any:
- [github.com/0blu/PhotonPackageParser](https://github.com/0blu/PhotonPackageParser)
- [github.com/mazurwiktor/albion-online-addons](https://github.com/mazurwiktor/albion-online-addons)

## License

This software has been released under the GNU General Public License (GPL) Version 2.0.