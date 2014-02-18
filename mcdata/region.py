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
        self[pos:pos + size] = bytearray(1) * size

    def alloc(self, size):
        pos = self.find(bytearray(size))
        if pos == -1:
            self.rstrip(bytearray(0))  # This doesn't work.
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
        self._chunk_headers = []
        self._chunk_lookup = {}  # Chunk headers indexed by (x, z).

        self._load_headers()

    def _load_headers(self):
        # Rewind in case we're called more than once.
        self.file.seek(0)

        for i in range(NUM_CHUNKS):
            chunk = {'offset': read_int(self.file, 3),
                      'sector_count': read_int(self.file, 1)}
            self._chunk_headers.append(chunk)

            # Compute coordinates for this chunk.
            # Todo: this is probably not correct.
            chunk['xz'] = (i & 0x1f, i >> 5)

            self._chunk_lookup[chunk['xz']] = chunk

            if chunk['offset']:
                self._sector_usage.mark(chunk['offset'], chunk['sector_count'])

        # Load timestamps.
        for i in range(NUM_CHUNKS):
            self._chunk_headers[i]['timestamp'] = read_int(self.file, 4)

    def read_chunk(self, x, z):
        # Todo: this test is already done in __iter__().
        # Also, what should happen if the chunk doesn't exist?
        # (Exception probably.)
        chunk = self._chunk_lookup[(x, z)]
        if chunk['offset'] == 0:
            # Todo: which exception?
            raise LookupError('chunk {!r} is now spawned'.format((x, z)))

        self.file.seek(chunk['offset'] * SECTOR_SIZE)

        length = read_int(self.file, 4)
        # Todo: what if compression is not zlib?
        compression = read_int(self.file, 1)
        data = _zlib.decompress(self.file.read(length - 1))

        return _nbt.decode(data)

    # def write_chunk(self, chunk):
    #     pass

    # def delete_chunk(self, x, z):
    #     pass  # Todo: do nothing if the chunk is already deleted.

    def __iter__(self):
        for chunk in self._chunk_headers:
            if chunk['offset']:
                yield self.read_chunk(*chunk['xz'])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()
        return False
