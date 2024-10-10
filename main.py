# import scapy
# from scapy.all import *
import traceback
from streams import *
from event import start as event_start, send_event
from scapy.sendrecv import *
from scapy.utils import *
from scapy.all import get_if_hwaddr
from layers import *
from scapy.pipetool import CLIFeeder, PipeEngine
from scapy.scapypipes import (WiresharkSink)
import protocol16_parser as protocol16
import json
from pprint import pprint
from time import sleep

def group_by(theList, N): return [theList[n:n+N] for n in range(0, len(theList), N)]
def group_by_2(theList): return group_by(theList, 2)


show_unknown_command_types=False


interface = "Ethernet"
mac_address = get_if_hwaddr(interface)

import extensions


def decode_message(message):
    if message.message_type == EventMessage.id:
        return protocol16.Parse_EventData(message.message.original)

    elif message.message_type == RequestMessage.id:
        return protocol16.Parse_OperationRequest(message.message.original)

    elif message.message_type == ResponseMessage.id:
        return protocol16.Parse_OperationResponse(message.message.original)

    else:
        print("unknown message type:  ", message.message_type)

fragmented_commands = {}


def handle_FragmentCommand(command):
    if command.start_sequence_number not in fragmented_commands:
        # new command
        fragmented_commands[command.start_sequence_number] = {}

    # save contents of fragment
    fragmented_commands[command.start_sequence_number][command.fragment_number] = command.command_fragment.original

    if len(fragmented_commands[command.start_sequence_number]) != command.fragment_count:
        # waiting for fragments
        return

    # reasemble command
    fragmented_command = b"".join([
        fragmented_commands[command.start_sequence_number][i]
            for i in range(command.fragment_count)
    ])

    # delete fragments
    del fragmented_commands[command.start_sequence_number]

    fragmented_command = decode_message(MessageWrapper(fragmented_command))

    if not fragmented_command:
        # failed to decode
        return

    fragmented_command = fragmented_command[0]

    # responses can have excesive sizes, so just asume this is a ResponseMessage
    ReponseBundle(fragmented_command)


def handle_unknown_command(command):
    if command.command_type in known_unknown_commands:
        return

    if show_unknown_command_types:
        print("unknown_command: ", command.command_type, "|", len(command.original))


def procces_packet(pOrg):
    if not pOrg.haslayer(PhotonHeader):
        return
    pHeader = pOrg[PhotonHeader]

    ether: Ether = pOrg[Ether]
    # this might not hold for ppl 2 network interface, eg: laptops or PC with WIFI
    # TODO: make more robust
    assert ether.dst == mac_address or ether.src == mac_address
    incomming_request = ether.dst == mac_address

    for i, command in enumerate(pHeader.commands):
        try:
            command.command_type
        except Exception as e:
            # command.show()
            print(f"Error parsing command {i}/{len(pHeader.commands)}:")
            # print("\t"+traceback.format_exc().replace("\n", "\n\t"))
            # pOrg.show()
            break

        if command.command_type not in commands:
            handle_unknown_command(command)
            continue

        command = command.actual_command

        if command.id == FragmentCommand.id:
            handle_FragmentCommand(command)
            continue

        try:
            command.message.message_type
        except Exception as e:
            # command.show()
            print(traceback.format_exc())
            pOrg.show()
            exit()

        if command.message.message_type == EventMessage.id:
            pass
            event = protocol16.Parse_EventData(command.message.message.original)[0]
            # print("Event: ", event)
            EventBundle(event)

        elif command.message.message_type == RequestMessage.id:
            pass
            request = protocol16.Parse_OperationRequest(command.message.message.original)[0]
            # print("Request: ", request)
            RequestBundle(request)

        elif command.message.message_type == ResponseMessage.id:
            pass
            response = protocol16.Parse_OperationResponse(command.message.message.original)[0]
            # print("Response: ", response)
            ReponseBundle(response)

        else:
            pass
            # print("unknown message type:  ", command.message.message_type)
            # command.message.show()

conf.layers.filter([Ether, IP, UDP, PhotonHeader])
sniffer_settings = {
    "filter":"udp",
    "store": False,
}
event_start()


# sniff(iface=interface, prn=procces_packet, **sniffer_settings), exit()

capture_file = "captures/change_zone.pcapng"
capture_file = "captures/0_to_city.pcapng"

input("Using a capture? is the event engine ready?")
sniff(prn=procces_packet, offline=capture_file, store=False)
input("exit?"), exit()
