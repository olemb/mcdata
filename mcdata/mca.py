"""
Region files (*.mca).

http://minecraft.gamepedia.com/Region_file_format
"""
import zlib
from . import nbt

NUM_LOCATIONS = 1024
SECTOR_SIZE = 4096
HEADER_SIZE = SECTOR_SIZE * 2

class ChunkLocation(object):
    def __init__(self, offset=0, sector_count=0, timestamp=0):
        self.offset = offset
        self.sector_count = sector_count
        self.timestamp = timestamp

    def read_location(self, regfile):
        data = bytearray(regfile.read(4))
        self.offset = data[0] << 16 | data[1] << 8 | data[2]
        self.sector_count = data[3]

    def read_timestamp(self, regfile):
        data = bytearray(regfile.read(4))
        self.timestamp = (data[0] << 24 |
                          data[1] << 16 |
                          data[2] << 8 |
                          data[0])

    def __repr__(self):
        fmt = '<ChunkLocation offset={} sector_count={} timestamp={}>'
        return fmt.format(self.offset,
                          self.sector_count,
                          self.timestamp)

def read_chunk_locations(regfile):
    locations = [ChunkLocation() for _ in range(NUM_LOCATIONS)]
    for loc in locations:
        loc.read_location(regfile)
    for loc in locations:
        loc.read_timestamp(regfile)
    return locations

def read_chunk(regfile):
    """Read a chunk from the region file.

    This returns the decompress chunk data as
    a byte string.
    """
    header = bytearray(regfile.read(5))
    length = (header[0] << 24 |
              header[1] << 16 |
              header[2] << 8 |
              header[3])
    compression_type = header[4]

    data = regfile.read(length - 1)

    if compression_type == 1:
        raise NotImplemented('GZip chunk compression is not supported')
    elif compression_type == 2:
        return zlib.decompress(data)

def read_mca_file(filename):
    """Read .mca file and return a list of Chunk objects."""

    chunks = []

    with open(filename, 'rb') as regfile:
        locations = read_chunk_locations(regfile)
        # Read chunk locations.

        for loc in locations:
            if loc.offset != 0:
                regfile.seek(loc.offset * SECTOR_SIZE)                
                chunk = read_chunk(regfile)
                chunks.append(nbt.parse(chunk))
            
    return chunks
