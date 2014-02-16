from __future__ import print_function
import sys as _sys  # Used for debugging.
import gzip as _gzip
import json as _json
import struct as _struct

_TYPE_NAMES = {}
_TYPE_IDS = {}

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

class Tag(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value
        if isinstance(value, Tag):
            raise ValueError()

    def walk(self):
        todo = [(self, [])]

        while todo:
            (tag, path) = todo.pop()
            if tag.type == 'compound':
                # Add all values.
                for name in sorted(tag.value.keys(), reverse=True):
                    todo.append((tag.value[name], path + [name]))
            elif tag.type == 'list':
                for i, subtag in enumerate(reversed(tag.value)):
                    todo.append((subtag, path + [str(i)]))

            # Todo: are there ever spaces in tag names?
            yield (tag, '/' + '/'.join(path))

    # Todo: keys()

    def __getitem__(self, path):
        if not self.type in ['compound', 'list']:
            # Todo: more informative message?
            raise ValueError("{} tag doesn't support lookup".format(self.type))

        # Todo: handle ValueError and TypeError.

        if path[:1] != '/':
            raise KeyError(path)

        parts = [part for part in path.split('/') if part]

        tag = self
        for part in parts:
            if tag.type == 'compound':
                try:
                    tag = tag.value[part]
                except KeyError:
                    raise KeyError(path)
            elif tag.type == 'list':
                try:
                    tag.value[int(part)]
                except (ValueError, IndexError):
                    raise KeyError(path)
            else:
                raise KeyError(path)
        
        return tag

    def __setitem__(self, name, value):
        if not self.type in ['compound', 'list']:
            # Todo: more informative message?
            raise ValueError("{} tag doesn't support lookup".format(self.type))
        elif not isinstance(value, Tag):
            raise ValueError('value must be Tag')
    
        # Todo: set item.

    def __repr__(self):
        if self.type == 'compound':
            value = '{{{} items}}'.format(len(self.value))
        elif self.type == 'list':
            value = '[{} items]'.format(len(self.value))
        else:
            value = repr(self.value)
        return '<{} {}>'.format(self.type, value)


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
        data = self._read_tag('compound')
        # print(self.datalen - self.file.tell(), 'bytes left')
        return data

    def _read_tag(self, typename):
        """Read data for tag."""
        read = getattr(self, '_read_' + typename)
        return Tag(typename, read())

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
                compound[name] = self._read_tag(typename)
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

class DebugByteArray(bytearray):
    def append(self, byte):
        print(repr(byte))
    def extend(self, bytes):
        for byte in bytes:
            self.append(byte)

class Encoder(object):
    def __init__(self):
        self.data = None

    def encode(self, tag):
        self.data = bytearray()
        # self.data = DebugByteArray()

        # The outer compound has no name.
        self._write_byte(_TYPE_IDS['compound'])
        self._write_string('')
        self._write_tag(tag)

        # Todo: support Python 3.
        return str(self.data)

    def _write_tag(self, tag):
        getattr(self, '_write_{}'.format(tag.type))(tag.value)

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
            self.data.append(_TYPE_IDS[tag.type])  # Type byte.
            self._write_string(name)
            self._write_tag(tag)
            
        self.data.append(0)  # End tag.

    def _write_list(self, lst):
        if len(lst) == 0:
            # Empty list. Type and length are both 0.
            self._write_byte(0)
            self._write_int(0)
        else:
            # Get datatype from first element.
            # Todo: check if all elements are of the same type.
            datatype, _ = lst[0].type
            typeid = _TYPE_IDS[datatype]

            self._write_byte(typeid)
            self._write_int(len(lst))

            for tag in lst:
                self._write_tag(tag)

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

def _tmp_encode_python1(tag):
    encode = _tmp_encode_python1
    if tag.type == 'compound':
        value = {key: encode(value) for key, value in tag.value.items()}
    elif tag.type == 'list':
        value = [encode(item) for item in tag.value]
    else:
        value = tag.value
    return [tag.type, value]

def _tmp_encode_typeless_python(tag, keys_only=False):
    """Encode tags as Python with types removed.
    
    This can't be encoded back to NBT.q
    """
    encode = lambda t: _tmp_encode_typeless_python(t, keys_only=keys_only)

    if tag.type == 'compound':
        value = {key: encode(value) for key, value in tag.value.items()}
    elif tag.type == 'list':
        value = [encode(item) for item in tag.value]
    else:
        if keys_only:
            value = ''
        else:
            value = tag.value
    return value

class TagWrapper(object):
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
            tag = tag.value[part]
        return tag.value

    def __setitem__(self, path, value):
        tag = self.tag
        for part in path.split('/'):
            tag = tag.value[part]
        tag.value = value

def print_structure(tag, indent=0):
    if tag.type == 'compound':
        for name in sorted(tag.value.keys()):
            child = tag.value[name]
            if child.type in ['compound', 'list', 'bytearray', 'intarray']:
                if len(child.value) == 1:
                    plural = ''
                else:
                    plural = 's'
                length = '[{}]'.format(len(child.value))
            else:
                length = ''

            print('{}{} <{}{}>'.format('.' * indent, name, child.type, length))
            print_structure(tag.value[name], indent + 1)

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

_init_types()
