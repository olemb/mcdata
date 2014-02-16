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
        # This assumes that the outer tag is a compound.
        # Return its value.
        data = self._read_tag()[1]
        # print(self.datalen - self.file.tell(), 'bytes left')
        return data

    def _read_tag(self):
        # print('=== NEW TAG')
        typeid = ord(self.file.read(1))
        if typeid == 0:
            raise StopIteration

        typename = _TYPE_NAMES[typeid] 
        name = self._read_string()

        if typename == 'list':
            datatype = _TYPE_NAMES[self._read_byte()]
            tag = self._read_list(datatype)
        elif typename == 'compound':
            tag = self._read_compound()
        else:
            tag = Tag(typename, getattr(self, '_read_' + typename)())

        return (name, tag)

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
                name, value = self._read_tag()
                compound[name] = value
        except StopIteration:
            # Why do we have to do this?
            # Shouldn't that happen automatically?
            pass
        return compound

    def _read_list(self, datatype):
        length = self._read_int()
        if length == 0:
            # Note: if length is 0 the datatype is 0,
            # which means you can't determine the data type
            # of an empty list.
            return []

        read = getattr(self, '_read_' + datatype)
        return [read() for _ in range(length)]

    def _read_intarray(self):
        length = self._read_int()
        return [self._read_int() for _ in range(length)]

class Encoder(object):
    def __init__(self):
        self.data = bytearray()

    def encode(self, tag):
        # Todo: TAGFORMAT
        self._write_tag('<compound>', tag)
        return self.data

    def _write_tag(self, name, value):
        # Todo: TAGFORMAT
        name = name[:-1]
        name, typename = name.rsplit('<', 1)

        if typename.endswith('list'):
            datatype, typename = typename[:-4], typename[-4:]

        self.data.append(_TYPE_IDS[typename])
        self._write_string(name)

        if typename == 'list':
            self._write_list(value, datatype)
        else:
            getattr(self, '_write_{}'.format(typename))(value)

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

    def _write_bytearray(self, value):
        self._write_int(len(value))
        self.data.extend(value)

    def _write_string(self, value):
        data = value.encode('UTF-8')
        self._write_short(len(data))
        self.data.extend(data)

    def _write_compound(self, tag):
        for name, value in sorted(tag.items()):
            self._write_tag(name, value)
        self._write_end()

    def _write_list(self, value, datatype):
        if len(value) == 0:
            # Empty list. Type and length are both 0.
            self._write_byte(0)
            self._write_int(0)
        else:
            typeid = _TYPE_IDS[datatype]
            self._write_byte(typeid)
            self._write_int(len(value))
            write = getattr(self, '_write_{}'.format(datatype))
            for item in value:
                write(item)

    def _write_intarray(self, value):
        self._write_int(len(value))
        for n in value:
            self._write_int(n)

    def _write_end(self):
        self.data.append(0)

def decode(data):
    return Decoder(data).decode()

def encode(data):
    return Encoder().encode(data)

def load(filename):
    return decode(_gzip.GzipFile(filename, 'rb').read())

def save(filename, data):
    _gzip.GzipFile(filename, 'wb').write(str(encode(data)))

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
