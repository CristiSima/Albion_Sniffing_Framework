from copy import deepcopy
from pprint import pprint
from functools import partial
from typing import List, Tuple, Union, Dict, Any, Callable
from dataclasses import dataclass, field, KW_ONLY

pprint = partial(pprint, width=150)

'''
https://en.wikipedia.org/wiki/Hooking
The naming is not ideal since the framework _hooks_ the different message types(Request, Response, Event)
in order to separate them to specific messages(RequestMove, PlayerInfoResponse, FameEvent)
which can be in turn hooked by other components(see in custom)

Each message stream has it's own StreamSeparator which saparates messages based on the value of a specified field,
by chaining multiple StreamSeparators you can hopefuly(since we don't know the separation schema) isolate specific messages/


'''

# only for reference
Content = Dict
# from protocol16_parser and/or layers:
Response = Tuple[int, int, str, Content]
Event = Tuple[int, Content]
Request = Tuple[int, Content]


'''
StreamSeparator -> (Stream)Separator
MessageStream -> (Message)Stream
'''

def group_by(theList, N): return [theList[n:n+N] for n in range(0, len(theList), N)]
def group_by_2(theList): return group_by(theList, 2)

__all__=[
    "MessageStream",
    "StreamSeparator",
    "RequestBundle",
    "ReponseBundle",
    "EventBundle",
    "state",
]

class state:
    location_id = None

class TRANSLATOR_DEFAULT: pass 
class TRANSLATOR_IGNORE: pass 
class SEPARATOR_MESSAGECODE: pass 
MESSAGE_CONTENT = -1

@dataclass
class TranslateDefinition:
    '''
    new_key: use TRANSLATOR_IGNORE to skip the entry

    !!! keep in mind that the default value is used directly,
    !!! if a mutable type is used(list, dict, object) and is mutated, changes will propagate to other messages
    '''
    old_key: int
    new_key: str

    _: KW_ONLY
    default_value: Any = TRANSLATOR_DEFAULT
    default_factory: Callable[[], Any] = TRANSLATOR_DEFAULT
    transformer: Callable[[Any], Any] = None
    presence_guaranteed: bool = True

    def apply(self, target):
        if self.old_key not in target[MESSAGE_CONTENT]:
            # old_key not present

            if self.default_value is not TRANSLATOR_DEFAULT:
                # provide default
                return self.new_key, self.default_value
            
            if self.default_factory is not TRANSLATOR_DEFAULT:
                # provide default
                return self.new_key, self.default_factory()

            # TODO: some way of providing more context would be helpful for the user
            transformer = self.transformer if self.transformer else ""
            if self.presence_guaranteed:
                print(f"Old Key: {self.old_key} not presend for replaceing with {transformer}({self.new_key})")

            return False

        if self.new_key is TRANSLATOR_IGNORE:
            return TRANSLATOR_IGNORE, TRANSLATOR_IGNORE

        value = target[MESSAGE_CONTENT][self.old_key]

        if self.transformer :
            value = self.transformer(value)

        return self.new_key, value

    __call__ = apply


class MessageTranslator:
    """docstring for MessageTranslator."""

    def __init__(self, translations: List[TranslateDefinition]):
        self.translations = translations

    def translate(self, org_target):
        target = deepcopy(org_target)

        for translator in self.translations:
            result = translator(target)

            if not result:
                continue

            new_key, value = result

            if new_key is not TRANSLATOR_IGNORE:
                target[MESSAGE_CONTENT][new_key] = value

            if translator.old_key in target[MESSAGE_CONTENT]:
                del target[MESSAGE_CONTENT][translator.old_key]

        return target

    __call__ = translate


class MessageStream:
    """docstring for MessageStream."""

    def __init__(self, translator=None):
        self.hooks = []
        self.translator = translator

    def add_hook(self, func):
        self.hooks.append(func)
        return func

    def use_hooks(self, target):
        # don't waste time
        if len(self.hooks) == 0:
            return

        if self.translator:
            target = self.translator(target)

        for hook in self.hooks:
            hook(target)

    __call__ = use_hooks


class StreamSeparator:
    """docstring for StreamSeparator."""

    def __init__(self, identifier_index, unknown_identifier_stream=None):
        '''
        '''
        self.identifier_index = identifier_index
        self.streams = {}
        self.unknown_identifier_stream = unknown_identifier_stream

    def separate(self, target):
        if self.identifier_index is SEPARATOR_MESSAGECODE:
            identifier = target[0]
        elif self.identifier_index in target[MESSAGE_CONTENT]:
            identifier = target[MESSAGE_CONTENT][self.identifier_index]
        else:
            identifier=None

        if identifier in self.streams:
            self.streams[identifier](target)
        elif self.unknown_identifier_stream:
            self.unknown_identifier_stream(target)

    def add_stream(self, identifier, stream):
        self.streams[identifier] = stream
        return stream

    def add_stream_d(self, identifier):
        return partial(self.add_stream, identifier)

    def clear_unknown_stream(self):
        self.set_unknown_stream(None)
    def set_unknown_stream(self, stream):
        self.unknown_identifier_stream = stream

    def __getitem__(self, identifier):
        return self.streams[identifier]

    __setitem__ = add_stream

    __call__ = separate


def StreamPrint_Generator(stream_name, use_pprint=False):
    if use_pprint:
        def temp(*args):
            print(f"{stream_name:<20}:", end=" ")
            pprint(args)
    else:
        def temp(*args):
            print(f"{stream_name:<20}:", *args)
    return temp


def addPrintStreamTo(stream_name, use_pprint=False):
    '''debug/dev/reverse use only
    '''
    target_stream = eval(stream_name)
    add_function = target_stream.add_hook or target_stream.add_stream
    add_function(StreamPrint_Generator(stream_name, use_pprint=use_pprint))


RequestBundle = StreamSeparator(SEPARATOR_MESSAGECODE)
RequestBundle[1] = StreamSeparator(253)

SelfSay = RequestBundle[1].add_stream(188, MessageStream(MessageTranslator([
    TranslateDefinition(253, TRANSLATOR_IGNORE),
    TranslateDefinition(0,   "msg",         transformer=bytes.decode),
])))

# made when moving
RequestMove = RequestBundle[1].add_stream(21, MessageStream(MessageTranslator([
    TranslateDefinition(253, TRANSLATOR_IGNORE),
    TranslateDefinition(1,   "src"),
    TranslateDefinition(3,   "dst"),
    TranslateDefinition(2,   "angle"), #degrees
    TranslateDefinition(4,   "speed"), #degrees
])))


ReponseBundle = StreamSeparator(SEPARATOR_MESSAGECODE)
ReponseBundle[1] = StreamSeparator(253)

# Confirmed @ Game.26.040.287170 - 18.09.2024 10:02
PlayerInfoResponse = ReponseBundle[1].add_stream(2, MessageStream(MessageTranslator([
    TranslateDefinition(253, TRANSLATOR_IGNORE),
    TranslateDefinition(1,   "CharacterID", transformer=bytes.hex),
    TranslateDefinition(8,   "LocationID",  transformer=bytes.decode),
    TranslateDefinition(2,   "player_name", transformer=bytes.decode),
    TranslateDefinition(52,  "guild_name",  transformer=bytes.decode, presence_guaranteed=False),
    TranslateDefinition(9,   "pos"),
])))

@PlayerInfoResponse.add_hook
def PlayerInfoResponse_save_location(target):
    state.location_id = target[MESSAGE_CONTENT]["LocationID"]
    print(f"Entered {type(state.location_id)}({state.location_id})")


EventBundle = StreamSeparator(SEPARATOR_MESSAGECODE)
EventBundle[1] = StreamSeparator(252)
# EventBundle[1].set_unknown_stream(print)

IncommingChatMessage = EventBundle[1].add_stream(68, MessageStream(MessageTranslator([
    TranslateDefinition(252, TRANSLATOR_IGNORE),
    TranslateDefinition(0,   "chanel_id"),
    TranslateDefinition(1,   "player_name"),
    TranslateDefinition(2,   "message")
])))

# Confirmed @ Game.26.040.287170 - 18.09.2024 10:02
FameEvent = EventBundle[1].add_stream(82, MessageStream(MessageTranslator([
    TranslateDefinition(252, TRANSLATOR_IGNORE),
    TranslateDefinition(1,   "total_fame"),
    TranslateDefinition(2,   "fame_gained", transformer=lambda x:x/10_000),
    # 3: is not fame_type
])))

DestinyBoardUpdate = EventBundle[1].add_stream(143, MessageStream(MessageTranslator([
    TranslateDefinition(252, TRANSLATOR_IGNORE),
    TranslateDefinition(1,   "node_id"),
    TranslateDefinition(2,   "node_level"),
    TranslateDefinition(3,   "progress"),
    TranslateDefinition(4,   "current_fame"), # [[fame]]
])))

IncommingWisper = EventBundle[1].add_stream(70, MessageStream(MessageTranslator([
    TranslateDefinition(252, TRANSLATOR_IGNORE),
    TranslateDefinition(0,   "player_name"),
    TranslateDefinition(1,   "message_content"),
    TranslateDefinition(2,   "idk")
])))

ChatMessage = EventBundle[1].add_stream(68, MessageStream(MessageTranslator([
    TranslateDefinition(252, TRANSLATOR_IGNORE),
    TranslateDefinition(0,   "channel_id"),
    TranslateDefinition(1,   "player_name"),
    TranslateDefinition(2,   "message_content")
])))

SayMessage = EventBundle[1].add_stream(69, MessageStream(MessageTranslator([
    TranslateDefinition(252, None),
    # not done
])))
