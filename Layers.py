from scapy.packet import *
from scapy.fields import *
from scapy.layers.inet import IP, UDP, Ether


__all__=[
    "IP", "UDP", "Ether",

    "messages", "MessageWrapper",
    "RequestMessage", "ResponseMessage", "EventMessage", "UnknownMessage",

    "commands", "CommandWrapper", "known_unknown_commands",
    "ReliableCommand", "UnreliableCommand", "FragmentCommand",
    "PhotonHeader",
]


'''
Scapy definition of the PUN(Photon Unity Networking) protocol built over UDP

References:
    https://doc.photonengine.com/realtime/current/connection-and-authentication/tcp-and-udp-port-numbers
        !the same ports aren't used!
        Default Ports by Protocol and Purpose
        Port Number 	Protocol 	Purpose
        5058 or 27000 	UDP 	Client to Nameserver (UDP)
        5055 or 27001 	UDP 	Client to Master Server (UDP)
        5056 or 27002 	UDP 	Client to Game Server (UDP)
        4533 	        TCP 	Client to Nameserver (TCP)
        4530 	        TCP 	Client to Master Server (TCP)
        4531 	        TCP 	Client to Game Server (TCP)
        80 or 9090 	    TCP 	Client to Master Server (WebSockets)
        80 or 9091 	    TCP 	Client to Game Server (WebSockets)
        80 or 9093 	    TCP 	Client to Nameserver (WebSockets)
        443 or 19090 	TCP 	Client to Master Server (Secure WebSockets)
        443 or 19091 	TCP 	Client to Game Server (Secure WebSockets)
        443 or 19093 	TCP 	Client to Nameserver (Secure WebSockets)
    https://doc.photonengine.com/realtime/current/reference/binary-protocol
        not all commands are defined
    https://github.com/mazurwiktor/albion-online-addons/blob/03b67fcb33a1df38d862863028644cbdc10fde3a/src/photon_decode/layout.rs
        main source
'''


messages={}
'''
2: RequestMessage
3: ResponseMessage
4: EventMessage
'''

def add_message(message_class):
    assert message_class.id not in messages
    messages[message_class.id] = message_class
    return message_class



@add_message
class RequestMessage(Packet):
    name = "RequestMessage"
    id = 2
    fields_desc = [
        ByteField("code", 0),
    ]

@add_message
class ResponseMessage(Packet):
    name = "ResponseMessage"
    id = 3
    fields_desc = [
        ByteField("code",           0),
        ShortField("return_code",   0)
    ]

@add_message
class EventMessage(Packet):
    name = "EventMessage"
    id = 4
    fields_desc = [
        ByteField("code", 0),
    ]


class UnknownMessage(Packet):
    name = "UnknownMessage"
    fields_desc = [
        PacketField("discarded", None, Raw),
    ]


class MessageWrapper(Packet):
    name = "MessageWrapper"
    fields_desc = [
        ByteField("skipped",        0),
        ByteField("message_type",   0),

        # auto select apropriate sessage type
        MultipleTypeField(
            [ (PacketField("message", None, message_class), lambda  p,message_id=message_id:(p.message_type==message_id))
                for message_id, message_class in messages.items()],
            PacketField("message", None, UnknownMessage)
        )
    ]



commands={}
'''
6:  ReliableCommand: needs confirmation and maybe flow control
7:  UnreliableCommand: clasic UDP
8:  FragmentCommand: for breaking up big commands
'''

def add_command(command_class):
    assert command_class.id not in commands
    commands[command_class.id] = command_class
    return command_class


@add_command
class ReliableCommand(Packet):
    name = "ReliableCommand"
    id=6
    fields_desc = [
        IntField("sequence_number", 0),

        PacketField("message", None, MessageWrapper)
    ]
    def extract_padding(self, s):
        return b'', s

@add_command
class UnreliableCommand(Packet):
    name = "UnreliableCommand"
    id=7
    fields_desc = [
        IntField("sequence_number", 0),
        IntField("unreliable_info", 0),

        PacketField("message", None, MessageWrapper)
    ]
    def extract_padding(self, s):
        return b'', s

@add_command
class FragmentCommand(Packet):
    name = "FragmentCommand"
    id=8
    fields_desc=[
        IntField("sequence_number",         0),


        IntField("start_sequence_number",   0),
        IntField("fragment_count",          0),
        IntField("fragment_number",         0),
        IntField("total_length",            0),
        IntField("fragment_offset",         0),

        PacketField("command_fragment", None, Raw)
    ]
    def extract_padding(self, s):
        return b'', s


known_unknown_commands=[
    1, # 8 bytes, first 4 x0
    5, # 4 bytes
]

class UnknownCommand(Packet):
    name="UnknownCommand"
    fields_desc = [
        PacketField("discarded", None, Raw),
    ]

class CommandWrapper(Packet):
    name = "CommandWrapper"
    fields_desc = [
        ByteField(  "command_type",  0),

        ByteField(  "channel_id",    0),
        ByteField(  "flags",         0),
        ByteField(  "reserved_byte", 0),

        IntField(   "msg_len",       0),

        # auto select apropriate command type
        MultipleTypeField(
            [ (PacketLenField("actual_command", None, command_clas, length_from=lambda p:(p.msg_len-8)), lambda  p,command_id=command_id:(p.command_type==command_id))
                for command_id, command_clas in commands.items()],
            PacketLenField("actual_command", None, UnknownCommand, length_from=lambda p:(p.msg_len-8))
        )
    ]
    def extract_padding(self, s):
        return b'', s


class PhotonHeader(Packet):
    name = "PhotonHeader"
    fields_desc = [
        ShortField( "peer_id",          0),
        ByteField(  "crc_enabled",      0),
        ByteField(  "command_count",    0),
        IntField(   "timestamp",        0),
        IntField(   "challenge",        0),
        PacketListField("commands", None, CommandWrapper, count_from=lambda p:(p.command_count))
    ]

# oprts used by the master, game(per map) and chat(maybe known as Nameserver in PUN) servers
albion_ports = [
    4535,
    5055,
    5056
]

for bport in albion_ports:
    bind_layers(UDP, PhotonHeader, sport=bport)
    bind_layers(UDP, PhotonHeader, dport=bport)
