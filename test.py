#!/usr/bin/env python
import sys
import json
from pprint import pprint
from mcdata import nbt

data = nbt.read(sys.argv[1])
pprint(data)
# print(json.dumps(data, indent=2))
