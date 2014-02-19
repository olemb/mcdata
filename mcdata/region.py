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
from . import nbt as _nbt

NUM_CHUNKS = 1024
SECTOR_SIZE = 4096
HEADER_SIZE = SECTOR_SIZE * 2

class SectorUsage(bytearray):
    def mark(self, pos, size):
        self[pos:pos + size] = b'\x01' * size

    def alloc(self, size):
        # Remove any free sectors from the end.
        while self.endswith('\x00'):
            self.pop()

        pos = self.find(bytearray(size))
        if pos == -1:
            pos = len(self)
        self.mark(pos, size)
        return pos

    def free(self, pos, size):
        self[pos:pos + size] = bytearray(size)


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
    outfile.write(bytes)


class RegionFile(object):
    # Todo: file object instead of filename and mode?
    def __init__(self, filename, mode='r'):
        # Todo: accept file like object.
        self.mode = mode
        self.closed = False

        # The first two sectors are chunk headers, so they
        # are marked as used.
        self._sector_usage = SectorUsage([1, 1])
        self._chunks = []

        file_existed = _os.path.exists(filename)
        self.file = open(filename, {'r': 'rb', 'w': 'wb'}[mode])

        if file_existed:
            self._load_headers()
        else:
            self._init_headers()

    def _init_headers(self):
        self._chunks.extend({'offset': 0,
                             'sector_count': 0,
                             'timestamp': 0} for _ in range(MAX_LENGTH))

    def _load_headers(self):
        # Rewind in case we're called more than once.
        self.file.seek(0)

        for i in range(NUM_CHUNKS):
            chunk = {'offset': read_int(self.file, 3),
                      'sector_count': read_int(self.file, 1)}
            self._chunks.append(chunk)

            if chunk['offset']:
                self._sector_usage.mark(chunk['offset'], chunk['sector_count'])

        # Load timestamps.
        for i in range(NUM_CHUNKS):
            self._chunks[i]['timestamp'] = read_int(self.file, 4)

    def _save_headers(self):
        raise NotImplemented

    def __getitem__(self, index):
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

    def __setitem__(self, chunk):
        # Todo: which exception?
        raise Exception('not implemented')

    def __delitem__(self, index):
        # Todo:
        chunk = self._chunks[index]
        if chunk['offset']:
            self._sector_usage.free(chunk['offset'], chunk['sector_count'])
            chunk['offset'] = chunk['sector_count'] = 0
            # Todo: clear data?

    def __iter__(self):
        for index, chunk in enumerate(self._chunks):
            if chunk['offset']:
                yield self[index]

    def __len__(self):
        return MAX_CHUNKS

    def close(self):
        # self._save_headers()
        if not self.closed:
            if 'w' in self.mode: 
                self._save_headers()
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        return False
