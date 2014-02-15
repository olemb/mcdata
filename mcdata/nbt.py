"""
Functions for reading NBT (Named Binary Tags) files.

Todo:

    * fix arguments for Encode()/.encode() and Decode()/.decode().
"""
from __future__ import print_function
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
        print('    {:08x}: {:02x} {!r}'.format(pos,
                                               ord(char),
                                               char))
        pos += 1
        return char

    def read(self, length):
        data = b''

        print('  {READ')
        for i in range(length):
            data += self._read_byte()
        print('  }')

        return data

class Decoder(object):
    def __init__(self, data, hexdata=False):
        self.file = TagFile(data)
        # self.file = TagFileDebugger(self.file)

    def decode(self):
        # This assumed that the outer tag is a compound.
        return self._read_tag()[1]

    def _read_tag(self):
        typeid = ord(self.file.read(1))
        typename = _TYPE_NAMES[typeid]
        if typename == 'end':
            raise StopIteration

        name = self._read_string()

        if typename == 'list':
            datatype = _TYPE_NAMES[self._read_byte()]
            name = '{}:{}list'.format(name, datatype)
            value = self._read_list(datatype)
        else:
            name = '{}:{}'.format(name, typename)
            value = getattr(self, '_read_' + typename)()            

        return (name, value)

    def _read_byte(self):
        return ord(self.file.read(1))

    def _read_short(self):
        # 4 byte signed.
        return struct.unpack('>h', self.file.read(2))[0]

    def _read_int(self):
        # 4 byte signed.
        return struct.unpack('>i', self.file.read(4))[0]

    def _read_long(self):
        # 8 byte signed.
        return struct.unpack('>q', self.file.read(8))[0]

    def _read_float(self):
        # 8 byte signed.
        return struct.unpack('>f', self.file.read(4))[0]

    def _read_double(self):
        # 8 byte signed.
        return struct.unpack('>d', self.file.read(8))[0]

    def _read_bytearray(self):
        # Todo: implement hexdata.
        length = self._read_int()
        return bytearray(self.file.read(length))

    def _read_string(self):
        length = struct.unpack('>h', self.file.read(2))[0]
        if length:
            return self.file.read(length).decode('UTF-8')
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
        read = getattr(self, '_read_' + datatype)
        return [read() for _ in range(length)]
        print(lst)
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
            typename, datatype = typename[:-4], typename[-4:]

        self.data.append(_TYPE_IDS[typename])
        self._write_string(name)

        if typename == 'list':
            self.data.append(_TYPE_IDS[datatype])
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
        self.data.extend(value)

    def _write_string(self, value):
        self.data.extend(struct.pack('>h', len(value)))
        self.data.extend(value.encode('UTF-8'))

    def _write_compound(self, tag):
        for key, value in tag.items():
            self._write_tag(key, value)
            self._write_end()

    def _write_list(self, value, datatype):
        self.data.append(_TYPE_IDS[datatype])
        write = getattr(self, '_write_{}'.format(datatype))
        for item in value:
            write(item)

    def _write_intarray(self, value):
        self._write_list(value, 'int')

    def _write_end(self):
        self.data.append(0)

def decode(data):
    return Decoder(data).decode()

def encode(value):
    return Encoder().encode(value)

def read(filename):
    return decode(gzip.GzipFile(filename, 'rb').read())
