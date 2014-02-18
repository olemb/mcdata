from __future__ import print_function
import io as _io
import sys as _sys  # Used for debugging.
import gzip as _gzip
import json as _json
from struct import Struct as _Struct

_TYPE_NAMES = {}
_TYPE_IDS = {}
_READERS = {}
# Todo: better name.
_STRUCTS = {fmt: _Struct(fmt) for fmt in ['>b', '>h', '>i', '>q', '>f', '>d']}
END = 0


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
        print(name, value)
        if name in self:
            dict.__setitem__(self, name, value)
        else:
            raise KeyError(name)

    def __delitem__(self, name):
        if name in self:
            dict.__delitem__(self, name)
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


def _read_numeric(infile, format):
    struct = _STRUCTS[format]
    return struct.unpack(infile.read(struct.size))[0]


def _write_numeric(outfile, format, value):
    outfile.write(_STRUCTS[format].pack(value))


def read_byte(infile):
    return _read_numeric(infile, '>b')


def read_short(infile):
    return _read_numeric(infile, '>h')


def read_int(infile):
    return _read_numeric(infile, '>i')


def read_long(infile):
    return _read_numeric(infile, '>q')


def read_float(infile):
    return _read_numeric(infile, '>f')


def read_double(infile):
    return _read_numeric(infile, '>d')


def read_bytearray(infile):
    length = read_int(infile)
    return bytearray(infile.read(length))


def read_string(infile):
    length = read_short(infile)
    return infile.read(length).decode('utf-8')


def read_compound(infile):
    compound = Compound()
    while True:
        typeid = read_byte(infile)
        if typeid == 0:
            break
        name = read_string(infile)
        compound.add(name, _TYPE_NAMES[typeid], _READERS[typeid](infile))

    return compound


def read_list(infile):
    typeid = read_byte(infile)
    length = read_int(infile)

    if length == 0:
        return List(typeid or None)
    elif typeid == 0:
        raise IOError('non-empty list with no type byte')
    else:
        read = _READERS[typeid]
        typename = _TYPE_NAMES[typeid]
        return List(typename, (read(infile) for _ in range(length)))


def read_intarray(infile):
    length = read_int(infile)
    return [read_int(infile) for _ in range(length)]


def decode(bytestring):
    with _io.BytesIO(bytestring) as infile:
        # Skip outer compound type and name.
        read_byte(infile)
        read_string(infile)
        return read_compound(infile)


def load(filename):
    return decode(_gzip.GzipFile(filename, 'rb').read())



def write_byte(outfile, value):
    _write_numeric(outfile, '>b', value)


def write_short(outfile, value):
    _write_numeric(outfile, '>h', value)


def write_int(outfile, value):
    _write_numeric(outfile, '>i', value)


def write_long(outfile, value):
    _write_numeric(outfile, '>q', value)


def write_float(outfile, value):
    _write_numeric(outfile, '>f', value)


def write_double(outfile, value):
    _write_numeric(outfile, '>d', value)


def write_string(outfile, value):
    encoded = value.encode('utf-8')
    write_short(outfile, len(encoded))
    outfile.write(encoded)


def _write_intarray(outfile, array):
    write_int(outfile, len(array))
    for n in array:
        write_int(outfile, n)


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
        return bytes(self.data)

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

def encode(data):
    return Encoder().encode(data)

def save(filename, data):
    _gzip.GzipFile(filename, 'wb').write(encode(data))

# JSON:
#     return _json.dumps(data, indent=2, sort_keys=True)

def split_path(path):
    return [part for part in path.split('/') if part]

def canonize_path(path):
    return '/' + '/'.join(path)

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
            for value in reversed(tag):
                i -= 1
                todo.append(('{}/{}'.format(path, i),
                            typename,
                            value))

def _format_bytearray(array):
    return ','.join(str(byte) for byte in array)

def print_tree(tree):
    for path, typename, value in walk(tree):
        words = [path]

        if typename == 'list':
            typename = 'list:{}'.format(value.type or '')

        try:
            words.append('<{}[{}]>'.format(typename, len(value)))
        except TypeError:
            words.append('<{}>'.format(typename))

        if not isinstance(value, Collection):
            if isinstance(value, bytearray):
                words.append(_format_bytearray(value))
            else:
                words.append(repr(value))

        print('  '.join(words))


def _init_types(namespace):
    """Initialize type lookup tables."""
    for typeid, name in enumerate(['byte',
                                   'short',
                                   'int',
                                   'long',
                                   'float',
                                   'double',
                                   'bytearray',
                                   'string',
                                   'list',
                                   'compound',
                                   'intarray'],
                                  start=1):
        _TYPE_NAMES[typeid] = name
        _TYPE_IDS[name] = typeid
        _READERS[typeid] = namespace['read_{}'.format(name)]

_init_types(globals())
