from . import nbt

def make_seed(s):
    # Todo: handle number.
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


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
