"""
Region files (*.mca).

http://minecraft.gamepedia.com/Region_file_format

Todo:

* positions are 0-1023 for now. (Should be (X, Z) tuple.)

* add Chunk object?

* save chunk.

* "pos" is a bad name.
"""
import zlib as _zlib
from . import nbt as _nbt

NUM_CHUNKS = 1024
SECTOR_SIZE = 4096
HEADER_SIZE = SECTOR_SIZE * 2

class ChunkHeader(object):
    def __init__(self, pos=0, offset=0, sector_count=0, timestamp=0):
        # Todo: compute (X, Z)
        self.pos = 0
        self.offset = offset
        self.sector_count = sector_count
        self.timestamp = timestamp

    def __repr__(self):
        fmt = '<ChunkHeader {} offset={} sector_count={} timestamp={}>'
        return fmt.format(self.pos,
                          self.offset,
                          self.sector_count,
                          self.timestamp)

class Chunk(object):
    # Todo: create empty chunk if data is None?
    # Todo: load data on demand?
    def __init__(self, data):
        self.data = data

    @property
    def x(self):
        return self.data['Level']['xPos']

    @x.setter
    def x(self, value):
        self.data['Level']['xPos'] = value

    @property
    def y(self):
        return self.data['Level']['yPos']

    @y.setter
    def y(self, value):
        self.data['Level']['yPos'] = value


class RegionFile(object):
    def __init__(self, filename, mode='rb'):
        self.file = open(filename, mode)
        self.headers = self._load_chunk_headers()

    def _load_chunk_headers(self):
        # Rewind in case we're called more than once.
        self.file.seek(0)
        headers = [ChunkHeader(i) for i in range(NUM_CHUNKS)]

        for header in headers:
            header.offset = self._read_int(3)
            header.sector_count = self._read_int(1)

        for header in headers:
            header.timestamp = self._read_int(4)

        return headers

    def _read_chunk(self, pos):
        header = self.headers[pos]
        if header.offset == 0:
            return {}

        self.file.seek(header.offset * SECTOR_SIZE)

        length = self._read_int(4)
        compression = self._read_int(1)
        data = _zlib.decompress(self.file.read(length-1))

        return Chunk(_nbt.decode(data))

    def _read_int(self, numbytes):
        value = 0
        while numbytes:
            value <<= 8
            value |= ord(self.file.read(1))
            numbytes -= 1
        return value

    def __iter__(self):
        for i in range(NUM_CHUNKS):
            yield self._read_chunk(i)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()
        return False
