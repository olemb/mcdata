import json
import zlib
from pprint import pprint
from collections import Counter
import mcdata.nbt

class Anvil(object):
    def __init__(self, filename):
        self.file = open(filename, 'rb')

    def _read_int(self, numbytes):
        value = 0
        while numbytes:
            value <<= 8
            value |= ord(self.file.read(1))
            numbytes -= 1
        return value

    def _iter_offsets(self):
        for i in range(1024):
            offset = self._read_int(3)
            sector_count = self._read_int(1)
            if offset:
                yield offset

    def _get_chunk(self):
        offset = min(self._iter_offsets())
        self.file.seek(offset * (1024*8))
        length = self._read_int(4)
        compression = self._read_int(1)
        data = zlib.decompress(self.file.read(length-1))

        return mcdata.nbt.decode(data)
        

filename = '/home/olemb/.minecraft/saves/a/region/r.0.0.mca'
chunk = Anvil(filename)._get_chunk()

def fix(obj):
    """Replace all bytearrays with hex string."""

    if isinstance(obj, dict):
        return {name: fix(value) for name, value in obj.items()}
    elif isinstance(obj, list):
        return [fix(value) for value in obj]
    elif isinstance(obj, bytearray):
        return ':'.join('{:02x}'.format(byte) for byte in obj)
    else:
        return obj

def json_encode(value):
    value = fix(value)
    return json.dumps(value, indent=2, sort_keys=True)

# sections = chunk['Level<compound>']['Sections<compoundlist>']
# blocks = sections[0]['Blocks<bytearray>']
# print(Counter(blocks))

# pprint(chunk)
print(json_encode(chunk))
