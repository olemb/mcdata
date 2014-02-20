"""
Region files (*.mca).

http://minecraft.gamepedia.com/Region_file_format

Todo:

* positions are 0-1023 for now. (Should be (X, Z) tuple.)

* save chunk.

* "pos" is a bad name.
"""
from __future__ import division
import os as _os
import math as _math
import zlib as _zlib
import time as _time
from . import nbt as _nbt

MAX_CHUNKS = 1024
SECTOR_SIZE = 4096
HEADER_SIZE = SECTOR_SIZE * 2
COMPRESSION_ZLIB = 1
# COMPRESSION_GZIP = ?

class SectorUsage(bytearray):
    def mark(self, pos, size):
        self[pos:pos + size] = b'\x01' * size

    def alloc(self, size):
        # Remove any free sectors from the end.
        while self.endswith(b'\x00'):
            self.pop()

        pos = self.find(bytearray(size))
        if pos == -1:
            pos = len(self)
        self.mark(pos, size)
        return pos

    def free(self, pos, size):
        self[pos:pos + size] = bytearray(size)

    def __repr__(self):
        usage = ''.join(map(str, self))
        return '<sector usage {}>'.format(usage)


def read_int(infile, size):
    value = 0
    while size:
        value <<= 8
        value |= ord(infile.read(1))
        size -= 1
    return value


def write_int(outfile, value, size):
    bytes = bytearray()
    while size:
        bytes.append(value & 0xff)
        value >>= 8
        size -= 1
    bytes.reverse()
    outfile.write(bytes)


class RegionFile(object):
    # Todo: file object instead of filename and mode?
    def __init__(self, filename, mode='r'):
        # Todo: accept file like object.
        self.mode = mode
        self.closed = False

        self._sector_usage = None
        self._chunks = []

        file_exists = _os.path.exists(filename)
        file_mode = {'r': 'rb', 'w': 'r+b'}[mode]

        if not file_exists:
            if mode == 'r':
                raise IOError('file not found: {!r}'.format(filename))
            else:
                # Create file.
                with open(filename, 'wb') as self.file:
                    # Write blank header.
                    self.file.write(b'\x00' * SECTOR_SIZE * 2)

        self.file = open(filename, file_mode)
        self._read_headers()

    def _read_headers(self):
        # The first two sectors are chunk headers, so they
        # are marked as used.
        self._sector_usage = SectorUsage([1, 1])

        self.file.seek(0)

        for i in range(MAX_CHUNKS):
            chunk = {'offset': read_int(self.file, 3),
                      'sector_count': read_int(self.file, 1)}
            self._chunks.append(chunk)

            if chunk['offset']:
                self._sector_usage.mark(chunk['offset'], chunk['sector_count'])

        for index in range(MAX_CHUNKS):
            self._chunks[index]['timestamp'] = read_int(self.file, 4)

    def _write_headers(self):
        self.file.seek(0)

        for chunk in self._chunks:
            write_int(self.file, chunk['offset'], 3)
            write_int(self.file, chunk['sector_count'], 1)

        for chunk in self._chunks:
            write_int(self.file, chunk['timestamp'], 4)

    def spawned(self, index):
        return bool(self._chunks[index]['offset'])

    @property
    def spawned_chunks(self):
        """Return list of indices of spawned chunks."""
        return [i for i in range(MAX_CHUNKS) if self.spawned(i)]

    def load_chunk(self, index):
        # Todo: this test is already done in __iter__().
        # Also, what should happen if the chunk doesn't exist?
        # (Exception probably.)
        chunk = self._chunks[index]
        if chunk['offset'] == 0:
            return None

        self.file.seek(chunk['offset'] * SECTOR_SIZE)

        length = read_int(self.file, 4)
        # Todo: what if compression is not zlib?
        compression = read_int(self.file, 1)
        data = _zlib.decompress(self.file.read(length - 1))

        return _nbt.decode(data)

    def save_chunk(self, index, chunk):
        if self.mode != 'w':
            raise IOError('region is opened as read only')

        data = _zlib.compress(_nbt.encode(chunk))

        # Todo: which exception?
        chunk = self._chunks[index]

        if chunk['offset']:
            self._sector_usage.free(chunk['offset'], chunk['sector_count'])

        total = len(data) + 5  # 5 bytes for length and compression type
        chunk['sector_count'] = int(_math.ceil(total / SECTOR_SIZE))
        chunk['offset'] = self._sector_usage.alloc(chunk['sector_count'])

        # Todo: is this correct?
        chunk['timestamp'] = int(_time.time() * 1000)
        
        self.file.seek(chunk['offset'] * SECTOR_SIZE)
        write_int(self.file, len(data) + 1, 4)  # + 1 for compression.
        write_int(self.file, COMPRESSION_ZLIB, 1)
        self.file.write(data)

        if total % SECTOR_SIZE:
            pad = SECTOR_SIZE - (total % SECTOR_SIZE)
            self.file.write(b'\x00' * pad)
            
    def remove_chunk(self, index):
        chunk = self._chunks[index]
        if chunk['offset']:
            self._sector_usage.free(chunk['offset'], chunk['sector_count'])
            chunk['offset'] = chunk['sector_count'] = 0
            # Todo: clear data?

    def close(self):
        if not self.closed:
            if 'w' in self.mode: 
                self._write_headers()
            self.file.close()

    def __iter__(self):
        for index in self.spawned_chunks:
            yield self.load_chunk(index)

    def __len__(self):
        return len(self.spawned_chunks)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False
