#!/usr/bin/env python
import sys
from mcdata import nbt

data = nbt.load(sys.argv[1])
print(nbt.encode_json(data))
