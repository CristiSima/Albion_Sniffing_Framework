from struct import unpack

'''
A library for decoding Photon's Protocol16 used for their PUN(Photon Unity Network) library

It is used to serialize game objects or events by reducing them to standard (C#) types.

The generic serialized object is encoded as:
###############################################
#  TypeIdentifier  #  serialized object data  #
#------------------#--------------------------#
#      1 byte      #   object type dependent  #
###############################################

With the type identifiers beeing:
0x00      => None,
0x2A: "*" => None,
0x44: "D" => Dictionary,
0x61: "a" => StringArray,
0x62: "b" => Byte,
0x64: "d" => Double,
0x65: "e" => EventData,
0x66: "f" => Float,
0x69: "i" => Integer,
0x6B: "k" => Short,
0x6C: "l" => Long,
0x6E: "n" => BooleanArray,
0x6F: "o" => Boolean,
0x70: "p" => OperationResponse,
0x71: "q" => OperationRequest,
0x73: "s" => String,
0x78: "x" => ByteArray,
0x79: "y" => Array,
0x7A: "z" => ObjectArray,


Some of these types directly encode standard type, others contain more generic objects
and others have a TypeIdentifier field of their own.

References:
    https://github.com/0blu/PhotonPackageParser/tree/37ac7beed721aaee2a98b3741142ccae98246904/Protocol16
        C# implementation
    https://github.com/mazurwiktor/albion-online-addons/tree/03b67fcb33a1df38d862863028644cbdc10fde3a/src/photon_decode
        Rust implementation
'''


get	    = lambda data,L:(data[:L], data[L:])
get_u8  = lambda data  :(data[0] , data[1:])

datatype_parsers = {}


def add_datatype_parser(key):
    '''
    Decorator generator for registering a new parser
    '''

    # decode ascii
    if type(key) is str:
        key = ord(key)

    def add_decorator(func):
        datatype_parsers[key] = func
        return func

    return add_decorator


@add_datatype_parser(0)    # None
@add_datatype_parser("*")  # Null
def Parse_None(data):
    return None, data
    
NO_OBJECT_CODES = [0, ord("*")]


def Parse_Object(data, type_code=None):
    if type_code is None or type_code in NO_OBJECT_CODES:
        type_code, data = Parse_Byte(data)
    return datatype_parsers[type_code](data)


@add_datatype_parser("b")
def Parse_Byte(data):
	return data[0], data[1:]

@add_datatype_parser("o")
def Parse_Boolean(data):
	return data[0] > 0, data[1:]

@add_datatype_parser("k")
def Parse_Short(data):
	parsed = unpack(">H", data[:2])[0]
	data = data[2:]
	return parsed, data

@add_datatype_parser("i")
def Parse_Integer(data):
	parsed = unpack(">I", data[:4])[0]
	data = data[4:]
	return parsed, data


@add_datatype_parser("l")
def Parse_Long(data):
	parsed = unpack(">Q", data[:8])[0]
	data = data[8:]
	return parsed, data

@add_datatype_parser("s")
def Parse_String(data):
    size, data = Parse_Short(data)
    parsed, data = get(data, size)
    return parsed, data

@add_datatype_parser("f")
def Parse_Float(data):
	parsed = unpack(">f", data[:4])[0]
	data = data[4:]
	return parsed, data

@add_datatype_parser("d")
def Parse_Double(data):
	parsed = unpack(">d", data[:8])[0]
	data = data[8:]
	return parsed, data


def generic_Array_parser(data, size, parser_func):
    '''
    Helper function for decoding an array with a provided parser function
    '''
    parsed = []
    for i in range(size):
        temp, data = parser_func(data)
        parsed.append(temp)

    return parsed, data


@add_datatype_parser("a")
def Parse_StringArray(data):
    size, data = Parse_Short(data)
    return generic_Array_parser(data, size, Parse_String)

@add_datatype_parser("y")
def Parse_Array(data):
    size,data = Parse_Short(data)
    type_code, data = Parse_Byte(data)
    return generic_Array_parser(data, size, datatype_parsers[type_code])

@add_datatype_parser("x")
def Parse_ByteArray(data):
    size, data = Parse_Integer(data)
    parsed, data = generic_Array_parser(data, size, Parse_Byte)
    return bytes(parsed), data

@add_datatype_parser("n")
def Parse_BooleanArray(data):
    size, data = Parse_Short(data)
    return generic_Array_parser(data, size, Parse_Boolean)

@add_datatype_parser("z")
def Parse_ObjectArray(data):
    size, data = Parse_Short(data)
    return generic_Array_parser(data, size, Parse_Object)

@add_datatype_parser("D")
def Parse_Dictionary(data):
    default_key_type_code, data = Parse_Byte(data)
    default_val_type_code, data = Parse_Byte(data)
    size, data = Parse_Short(data)

    parsed = {}
    for _ in range(size):
        key, data = Parse_Object(data, default_key_type_code)
        val, data = Parse_Object(data, default_val_type_code)

        parsed[key] = val

    return parsed, data

def Parse_Parameters(data):
    size, data = Parse_Short(data)
    parsed = {}
    for _ in range(size):
        key, data = Parse_Byte(data)
        val, data = Parse_Object(data)
        parsed[key] = val

    return parsed, data

@add_datatype_parser("e")
def Parse_EventData(data):
    code, data = Parse_Byte(data)
    parameters, data = Parse_Parameters(data)
    return (code, parameters), data


@add_datatype_parser("p")
def Parse_OperationResponse(data):
    code, data = Parse_Byte(data)
    return_code, data = Parse_Short(data)
    debug_msg, data = Parse_Object(data)
    parameters, data = Parse_Parameters(data)
    return (code, return_code, debug_msg, parameters), data

@add_datatype_parser("q")
def Parse_OperationRequest(data):
    code, data = Parse_Byte(data)
    parameters, data = Parse_Parameters(data)
    return (code, parameters), data
