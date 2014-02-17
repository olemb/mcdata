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

_init_types()

def split_path(path):
    return [part for part in path.split('/') if part]

def canonize_path(path):
    return '/' + '/'.join(path)

class Collection(object):
    """Common base class for Compound and List.

    Used for isinstance().
    """
    pass

class Compound(dict, Collection):
    def __init__(self, items=None, **kw):
        self.types = {}
        if items is not None:
            for (name, type, value) in items:
                self.add(name, type, value)

        for name, (type, value) in kw.items():
            self.add(name, type, value)

    # def get_type(self, name):                                                 
    #     return self.types[name]                                               

    def add(self, name, type, value):
        self.types[name] = type
        dict.__setitem__(self, name, value)

    def __setitem__(self, name, value):
        if name in self:
            dict.__setattr__(self, name, value)
        else:
            raise KeyError(name)

    def __delitem__(self, name):
        if name in self:
            dict.__delattr__(self, name)
            del self.types[name]
        else:
            raise KeyError(name)

    def copy(self):
        # Todo: check if this works
        other = Compound()
        other.types = self.types.copy()
        list.update(other, self)
        return other

    # Todo: __repr__()

    # check()  # performs sanity checking on data. (Valid type, range etc.)

    # deepcopy()
    # update()

class List(list, Collection):
    def __init__(self, type, items=None):
        self.type = type
        if items is not None:
            self.extend(items)

    # Todo: __repr__()

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

        # Get all _read_*() methods in a neat lookup table.
        self._readers = {}
        for name in dir(self):
            if name.startswith('_read'):
                typename = name.rsplit('_', 1)[1]
                self._readers[typename] = getattr(self, name)

    def decode(self):
        # Skip outer compound type and name.
        # Todo: check if this is 0 and ''.
        self._read_byte()
        self._read_string()
        tag = self._readers['compound']()
        # print(self.datalen - self.file.tell(), 'bytes left')
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
        compound = Compound()
        while True:
            typename = _TYPE_NAMES[self._read_byte()]
            if typename == 'end':
                break
            name = self._read_string()
            compound.add(name, typename, self._readers[typename]())

        return compound

    def _read_list(self):
        datatype = _TYPE_NAMES[self._read_byte()]
        length = self._read_int()
        if length == 0:
            # Note: if length is 0 the datatype is 0,
            # which means you can't determine the data type
            # of an empty list.
            return List(None)

        return List(datatype,
                    [self._readers[datatype]() for _ in range(length)])

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

        # Get all _write_*() methods in a neat lookup table.
        # Todo: this is duplicated in the Decoder. Unduplicate.
        self._writers = {}
        for name in dir(self):
            if name.startswith('_write'):
                typename = name.rsplit('_', 1)[1]
                self._writers[typename] = getattr(self, name)

    def encode(self, tag):
        self.data = bytearray()
        # self.data = DebugByteArray()

        # The outer compound has no name.
        self._write_byte(_TYPE_IDS['compound'])
        self._write_string('')
        self._writers['compound'](tag)

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
        for name, value in sorted(compound.items()):
            typename = compound.types[name]
            self.data.append(_TYPE_IDS[typename])
            self._write_string(name)
            self._writers[compound.types[name]](value)
            
        self.data.append(0)  # End tag.

    def _write_list(self, lst):
        if len(lst) == 0:
            # Empty list. Type and length are both 0.
            self._write_byte(0)
            self._write_int(0)
        else:
            if lst.type is None:
                raise ValueError("non-empty list must have type != None")

            datatype = lst.type
            self._write_byte(_TYPE_IDS[datatype])
            self._write_int(len(lst))

            for value in lst:
                self._writers[datatype](value)

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

def _hex_encode_bytearray(array):
    return ':'.join('{:02x}'.format(byte) for byte in array)

# JSON:
#     return _json.dumps(data, indent=2, sort_keys=True)

def walk(comp):
    todo = [('', 'compound', comp)]

    while todo:
        (path, typename, value) = todo.pop()
        yield (path or '/', typename, value)

        tag = value

        if isinstance(tag, Compound):
            for name in sorted(tag, reverse=True):
                typename = tag.types[name]
                value = tag[name]
                todo.append(('{}/{}'.format(path, name),
                             typename,
                             value))
        elif isinstance(tag, List):
            typename = tag.type
            i = len(tag)
            for value in tag:
                i -= 1
                todo.append(('{}/{}'.format(path, i),
                            typename,
                            value))

def print_tree(tree):
    for path, typename, value in walk(tree):
        if typename in ['compound', 'list']:
            print('{}  ({})'.format(path, typename))
        else:
            if isinstance(value, bytearray):
                value = _hex_encode_bytearray(value)
            print('{}  ({})  {!r}'.format(path, typename, value))
