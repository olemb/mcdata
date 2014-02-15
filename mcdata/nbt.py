"""
Functions for reading NBT (Named Binary Tags) files.

Todo:

    * fix arguments for Encode()/.encode() and Decode()/.decode().
"""
from __future__ import print_function
import sys  # Used for debugging.
import gzip
import struct

_TYPE_NAMES = {}
_TYPE_IDS = {}

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
del i, name


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
        sys.stdout.write('    {:08x}: {:02x} {!r}\n'.format(pos,
                                                            ord(char),
                                                            char))
        pos += 1
        return char

    def read(self, length):
        data = b''

        sys.stdout.write('  {READ\n')
        for i in range(length):
            data += self._read_byte()
        sys.stdout.write('  }\n')
        sys.stdout.flush()

        return data

class Decoder(object):
    def __init__(self, data, hexdata=False):
        self.hexdata = hexdata
        self.file = TagFile(data)
        # self.file = TagFileDebugger(self.file)

    def decode(self):
        # This assumes that the outer tag is a compound.
        # Return its value.
        return self._read_tag()[1]

    def _read_tag(self):
        typeid = ord(self.file.read(1))
        typename = _TYPE_NAMES[typeid] 
        if typename == 'end':
            raise StopIteration

        name = self._read_string()

        if typename == 'list':
            datatypeid = self._read_byte()
            datatype = _TYPE_NAMES[datatypeid]
            name = '{}:{}list'.format(name, datatype)
            value = self._read_list(datatype)
        else:
            name = '{}:{}'.format(name, typename)
            value = getattr(self, '_read_' + typename)()

        return (name, value)

    def _read_byte(self):
        return ord(self.file.read(1))

    def _read_short(self):
        return struct.unpack('>h', self.file.read(2))[0]

    def _read_int(self):
        return struct.unpack('>i', self.file.read(4))[0]

    def _read_long(self):
        return struct.unpack('>q', self.file.read(8))[0]

    def _read_float(self):
        return struct.unpack('>f', self.file.read(4))[0]

    def _read_double(self):
        return struct.unpack('>d', self.file.read(8))[0]

    def _read_bytearray(self):
        # Todo: implement hexdata.
        length = self._read_int()
        data = bytearray(self.file.read(length))
        return data

        if self.hexdata:
            return ':'.join('{:02x}'.format(byte) for byte in data)
        else:
            return data

    def _read_string(self):
        length = self._read_short()
        if length:
            string = self.file.read(length).decode('UTF-8')
            # if 'wooden' in string:
            #     print(repr(string))
        else:
            return ''

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

        if datatype == 'end' and length == 0:
            # This makes no sense!
            # level.dat sometimes contains an empty list
            # of type 'end' (typeid == 0). Just skip.
            return []

        read = getattr(self, '_read_' + datatype)
        return [read() for _ in range(length)]
        return lst

    def _read_intarray(self):
        length = self._read_int()
        value = []
        for i in range(length):
            value.append(self._read_int())
        return value

class Encoder(object):
    def __init__(self):
        self.data = bytearray()

    def encode(self, tag):
        self._write_tag(':compound', tag)
        return self.data

    def _write_tag(self, name, value):
        name, typename = name.rsplit(':', 1)
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
        self.data.extend(struct.pack('>h', value))

    def _write_int(self, value):
        self.data.extend(struct.pack('>i', value))

    def _write_long(self, value):
        self.data.extend(struct.pack('>q', value))

    def _write_float(self, value):
        self.data.extend(struct.pack('>f', value))

    def _write_double(self, value):
        self.data.extend(struct.pack('>d', value))

    def _write_bytearray(self, value):
        # Todo: handle hex string.
        self._write_int(len(value))
        self.data.extend(value)

    def _write_string(self, value):
        data = value.encode('UTF-8')
        self._write_short(len(data))
        self.data.extend(data)

    def _write_compound(self, tag):
        for key, value in tag.items():
            self._write_tag(key, value)
        self._write_end()

    def _write_list(self, value, datatype):
        write = getattr(self, '_write_{}'.format(datatype))
        for item in value:
            write(item)
        self._write_end()

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
    return decode(gzip.GzipFile(filename, 'rb').read())

def save(filename, data):
    gzip.GzipFile(filename, 'wb').write(str(encode(data)))

