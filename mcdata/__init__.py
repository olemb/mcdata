def make_seed(text):
    # Todo: handle number.
    h = 0
    for char in text:
        h = (31 * h + ord(char)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def _get_region(x, z):
    return int(x // 512), int(z // 512)


def _get_chunk_index(x, z):
    # Get coordinates within region
    x %= 512
    z %= 512
    return ((z // 16) * 32) + (x // 16)


def get_chunk_location(x, z):
    region = *_get_region(x, z)
    index = _get_chunk_index(x, z)
    return 'r.{}.{}.mca'.format(region, index),


class Nibbler(object):
    """Access a bytearray as an array of nibbles."""
    def __init__(self, array):
        self.array = array

    def __getitem__(self, pos):
        byte = self.array[pos // 2]
        if pos & 1:
            # High nibble.
            return byte >> 4
        else:
            # Low nibble.
            return byte & 0x0f

    def __setitem__(self, pos, value):
        byte = self.array[pos // 2]
        if pos & 1:
            # Replace high nibble.
            byte = (byte & 0xf0) | (value << 4)
        else:
            # Replace low nibble
            byte = (byte & 0x0f | value)
        self.array[pos // 2] = byte

    def __len__(self):
        return len(self.array) * 2

    def __str__(self):
        return ':'.join('{:01x}'.format(nibble) for nibble in self)

    def __repr__(self):
        return '<nibbler len={} {}>'.format(len(self), str(self))
