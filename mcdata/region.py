"""
Region files (*.mca).

http://minecraft.gamepedia.com/Region_file_format

Todo:

* positions are 0-1023 for now. (Should be (X, Z) tuple.)

* save chunk.

* "pos" is a bad name.
"""
from __future__ import division
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


# def write_int(self)
#    pass

class RegionFile(object):
    # Todo: file object instead of filename and mode?
    def __init__(self, filename, mode='rb'):
        self.file = open(filename, mode)

        # The first two sectors are chunk headers, so they
        # are marked as used.
        self._sector_usage = SectorUsage([1, 1])
        self._headers = []

        self._load_headers()

    def _load_headers(self):
        # Rewind in case we're called more than once.
        self.file.seek(0)

        for i in range(NUM_CHUNKS):
            header = {'offset': read_int(self.file, 3),
                      'sector_count': read_int(self.file, 1)}
            self._headers.append(header)

            if header['offset']:
                self._sector_usage.mark(header['offset'], header['sector_count'])

        # Load timestamps.
        for i in range(NUM_CHUNKS):
            self._headers[i]['timestamp'] = read_int(self.file, 4)

    def __getitem__(self, index):
        # Todo: this test is already done in __iter__().
        # Also, what should happen if the chunk doesn't exist?
        # (Exception probably.)
        header = self._headers[index]
        if header['offset'] == 0:
            return None

        self.file.seek(header['offset'] * SECTOR_SIZE)

        length = read_int(self.file, 4)
        # Todo: what if compression is not zlib?
        compression = read_int(self.file, 1)
        data = _zlib.decompress(self.file.read(length - 1))

        return _nbt.decode(data)

    # def save_chunk(self, chunk):
    #     pass

    def delete_chunk(self, index):
        # Todo:
        header = self._headers[index]
        if header['offset']:
            self._sector_usage.free(header['offset'], header['sector_count'])
            header['offset'] = header['sector_count'] = 0
            # Todo: clear data?

    def __iter__(self):
        for index, header in enumerate(self._headers):
            if header['offset']:
                yield self[index]

    def __len__(self):
        return MAX_CHUNKS

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()
        return False
