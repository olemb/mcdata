from __future__ import print_function
import sys as _sys  # Used for debugging.
import gzip as _gzip
import json as _json
import struct as _struct

_TYPE_NAMES = {}
_TYPE_IDS = {}

class Tag(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return '<{!r} {}>'.format(self.value, self.type)

def _init_types():
    """Initialize type lookup tables."""
    for i, name in enumerate(['end',
                              'byte',
                              'short',
                              'int',
                              'long',
                              'float',
                              'double',
                              'bytearray',
                              'string',
                              'list',
                              'compound',
                              'intarray']):

        _TYPE_NAMES[i] = name
        _TYPE_IDS[name] = i

class TagFile(object):
    def __init__(self, data):
        self.pos = 0
        self.data = data
    
    def tell(self):
        return self.pos

    def read(self, length):
        data = self.data[self.pos:self.pos+length]
        self.pos += length
        return data

class TagFileDebugger(object):
    """Wraps around TagFile."""
    def __init__(self, file):
        self.file = file

    def _read_byte(self):
        char = self.file.read(1)
        pos = self.file.tell()
        _sys.stdout.write('    {:08x}: {:02x} {!r}\n'.format(pos,
                                                             ord(char),
                                                             char))
        pos += 1
        return char

    def tell(self):
        return self.file.tell()

    def read(self, length):
        data = b''

        _sys.stdout.write('  {READ\n')
        for i in range(length):
            data += self._read_byte()
        _sys.stdout.write('  }\n')
        _sys.stdout.flush()

        return data

class Decoder(object):
    def __init__(self, data):
        self.datalen = len(data)
        self.file = TagFile(data)
        # self.file = TagFileDebugger(self.file)

    def decode(self):
        # Skip outer compound type and name.
        # Todo: check if this is 0 and ''.
        self._read_byte()
        self._read_string()

        data = self._read_compound()
        # print(self.datalen - self.file.tell(), 'bytes left')
        return data

    def _read_tag(self, typename):
        read = getattr(self, '_read_' + typename)
        tag = Tag(typename, read())

        if tag.type in ['list', 'compound']:
            return tag.value
        else:
            return tag

    def _read_byte(self):
        return ord(self.file.read(1))

    def _read_short(self):
        return _struct.unpack('>h', self.file.read(2))[0]

    def _read_int(self):
        return _struct.unpack('>i', self.file.read(4))[0]

    def _read_long(self):
        return _struct.unpack('>q', self.file.read(8))[0]

    def _read_float(self):
        return _struct.unpack('>f', self.file.read(4))[0]

    def _read_double(self):
        return _struct.unpack('>d', self.file.read(8))[0]

    def _read_bytearray(self):
        length = self._read_int()
        return bytearray(self.file.read(length))

    def _read_string(self):
        length = self._read_short()
        if length:
            data = self.file.read(length)
            string = data.decode('UTF-8')
            return string
        else:
            return u''

    def _read_compound(self):
        compound = {}
        try:
            while True:
                typename = _TYPE_NAMES[self._read_byte()]
                if typename == 'end':
                    break
                name = self._read_string()
                value = self._read_tag(typename)
                compound[name] = value
        except StopIteration:
            # Why do we have to do this?
            # Shouldn't that happen automatically?
            pass
        return compound

    def _read_list(self):
        datatype = _TYPE_NAMES[self._read_byte()]
        length = self._read_int()
        if length == 0:
            # Note: if length is 0 the datatype is 0,
            # which means you can't determine the data type
            # of an empty list.
            return []

        return [self._read_tag(datatype) for _ in range(length)]

    def _read_intarray(self):
        length = self._read_int()
        return [self._read_int() for _ in range(length)]

def _get_type_and_value(tag):
    if isinstance(tag, dict):
        return 'compound', tag
    elif isinstance(tag, list):
        return 'list', tag
    else:
        return tag.type, tag.value

class Encoder(object):
    def __init__(self):
        self.data = None

    def encode(self, tag):
        self.data = bytearray()
        # The outer compound has no name.
        self._write_byte(_TYPE_IDS['compound'])
        self._write_int(0)
        self._write_compound(tag)

        # Todo: support Python 3.
        return str(self.data)

    def _write_byte(self, value):
        self.data.append(value)

    def _write_short(self, value):
        self.data.extend(_struct.pack('>h', value))

    def _write_int(self, value):
        self.data.extend(_struct.pack('>i', value))

    def _write_long(self, value):
        self.data.extend(_struct.pack('>q', value))

    def _write_float(self, value):
        self.data.extend(_struct.pack('>f', value))

    def _write_double(self, value):
        self.data.extend(_struct.pack('>d', value))

    def _write_bytearray(self, array):
        self._write_int(len(array))
        self.data.extend(array)

    def _write_string(self, value):
        data = value.encode('UTF-8')
        self._write_short(len(data))
        self.data.extend(data)

    def _write_compound(self, compound):
        for name, tag in sorted(compound.items()):
            typename, value = _get_type_and_value(tag)

            self.data.append(_TYPE_IDS[typename])  # Type byte.
            self._write_string(name)
            getattr(self, '_write_{}'.format(typename))(value)
            
        self.data.append(0)  # End tag.

    def _write_list(self, lst):
        if len(lst) == 0:
            # Empty list. Type and length are both 0.
            self._write_byte(0)
            self._write_int(0)
        else:
            # Get datatype from first element.
            # Todo: check if all elements are of the same type.
            datatype, _ = _get_type_and_value(lst[0])
            typeid = _TYPE_IDS[datatype]

            self._write_byte(typeid)
            self._write_int(len(lst))

            write = getattr(self, '_write_{}'.format(datatype))
            for item in lst:
                _, value = _get_type_and_value(item)
                write(value)

    def _write_intarray(self, array):
        self._write_int(len(array))
        for n in array:
            self._write_int(n)

def decode(data):
    return Decoder(data).decode()

def encode(data):
    return Encoder().encode(data)

def load(filename):
    return decode(_gzip.GzipFile(filename, 'rb').read())

def save(filename, data):
    _gzip.GzipFile(filename, 'wb').write(encode(data))



#
# Everything below here doesn't work yet.
#


def _hex_encode_bytearrays(obj):
    """Replace all bytearrays in an NBT tree with hex strings."""
    fix = _hex_encode_bytearrays

    if isinstance(obj, dict):
        return {name: fix(value) for name, value in obj.items()}
    elif isinstance(obj, list):
        return [fix(value) for value in obj]
    elif isinstance(obj, bytearray):
        return ':'.join('{:02x}'.format(byte) for byte in obj)
    else:
        return obj

def _hex_decode_bytearrays(obj):
    """Decode all hex encoded bytearrays."""
    raise NotImplemented

def encode_json(data, indent=True):
    """Encode NBT data as JSON.

    The data will be indented with 2 spaces.
    Byte arrays are hex encoded."""
    data = _hex_encode_bytearrays(data)
    return _json.dumps(data, indent=2, sort_keys=True)

def decode_json(string):
    raise NotImplemented

def keys_only(obj):
    if isinstance(obj, dict):
        return {name: keys_only(value) for name, value in obj.items()}
    else:
        return ''

class ValueWrapper(object):
    """
    Access tag values directly. Keys must exist.

    Example:

    >>> from mcdata.nbt import load, ValueWrapper
    >>> ValueWrapper(load('level.dat'))
    >>> level['Data/GameRules/keepInventory']
    true
    >>> level['Data/GameRules/keepInventory'] = 'false'
    >>> # ... and save
    """

    def __init__(self, tag):
        # Todo: name? 'tag'?
        self.tag = tag   

    def __getitem__(self, path):
        tag = self.tag
        for part in path.split('/'):
            tag = tag[part]
        return tag.value

    def __setitem__(self, path, value):
        tag = self.tag
        for part in path.split('/'):
            tag = tag[part]
        tag.value = value

_init_types()
