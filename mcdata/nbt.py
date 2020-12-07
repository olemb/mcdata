from __future__ import print_function
import io as _io
import sys as _sys  # Used for debugging.
import gzip as _gzip
import json as _json
from struct import Struct as _Struct

_TYPE_NAMES = {}
_TYPE_IDS = {}
_READERS = {}
_WRITERS = {}
# Todo: better name.
_STRUCTS = {fmt: _Struct(fmt) for fmt in ['>b', '>h', '>i', '>q', '>f', '>d']}
END = 0


class Collection(object):
    """Common base class for Compound and List.

    Used for isinstance().
    """
    pass


class Compound(dict, Collection):
    def __init__(self, *args, **kw):
        self.types = {}
        dict.__init__(self, *args, **kw)

    def get_type(self, name): 
        return self.types[name]

    def __setitem__(self, name, value):
        if isinstance(name, tuple):
            name, typename = name
            self.types[name] = typename
        dict.__setitem__(self, name, value)

    def __delitem__(self, name):
        del self.types[name]
        dict.__delitem__(self, name)

    __getattr__ = dict.__getitem__

    # check()  # performs sanity checking on data. (Valid type, range etc.)

    # deepcopy()
    # update()  # Update types?

    def __repr__(self):
        return '<compound keys={}>'.format(list(sorted(self.keys())))


class List(list, Collection):
    def __init__(self, type='compound', items=None):
        self.type = type
        if items is not None:
            self.extend(items)

    def __repr__(self):
        return '<list type={} len={}>'.format(self.type, len(self))


class DebugFile(object):
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

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()
        return False


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
        compound[(name, _TYPE_NAMES[typeid])] = _READERS[typeid](infile)

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


def read_longarray(infile):
    length = read_int(infile)
    return [read_long(infile) for _ in range(length)]


def decode(bytestring):
    with _io.BytesIO(bytestring) as infile:
        # Skip outer compound type and name.
        read_byte(infile)
        read_string(infile)
        return read_compound(infile)


def load(filename):
    try:
        return decode(_gzip.GzipFile(filename, 'rb').read())
    except (IOError, OSError):
        # Python 2 raises IOError.
        # Python 3 raises OSError.
        pass

    return decode(open(filename, 'rb').read())


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


def write_bytearray(outfile, array):
    write_int(outfile, len(array))
    outfile.write(array)


def write_string(outfile, value):
    encoded = value.encode('utf-8')
    write_short(outfile, len(encoded))
    outfile.write(encoded)


def write_compound(outfile, compound):
    for name, value in sorted(compound.items()):
        typeid = _TYPE_IDS[compound.types[name]]
        write_byte(outfile, typeid)
        write_string(outfile, name)
        _WRITERS[typeid](outfile, value)

    write_byte(outfile, END)


def write_list(outfile, lst):
    if len(lst) == 0:
        write_byte(outfile, lst.type or 0)
        write_int(outfile, 0)
        return

    if lst.type is None:
        # Try to determine list type from content.
        if isinstance(lst[0], Compound):
            typeid = _TYPE_IDS['compound']
        else:
            raise ValueError("non-empty list must have type != None")
    else:
        typeid = _TYPE_IDS[lst.type]

    write_byte(outfile, typeid)
    write_int(outfile, len(lst))

    write = _WRITERS[typeid]
    for value in lst:
        write(outfile, value)


def write_intarray(outfile, array):
    write_int(outfile, len(array))
    for n in array:
        write_int(outfile, n)


def write_longarray(outfile, array):
    write_int(outfile, len(array))
    for n in array:
        write_long(outfile, n)


def encode(compound):
    with _io.BytesIO() as outfile:
        # The outer compound has no name.
        write_byte(outfile, _TYPE_IDS['compound'])
        write_string(outfile, '')
        write_compound(outfile, compound)

        return outfile.getvalue()

def save(filename, compound):
    _gzip.GzipFile(filename, 'wb').write(encode(compound))


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
    return ':'.join('{:02x}'.format(byte) for byte in array)

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
                                   'intarray',
                                   'longarray'],
                                  start=1):
        _TYPE_NAMES[typeid] = name
        _TYPE_IDS[name] = typeid
        _READERS[typeid] = namespace['read_{}'.format(name)]
        _WRITERS[typeid] = namespace['write_{}'.format(name)]

_init_types(globals())
