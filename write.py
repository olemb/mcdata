import sys
import json
from pprint import pprint
from mcdata import nbt
from mcdata.nbt import load, save, Tag, TagWrapper

def mkname(name):
    return '/home/olemb/.minecraft/saves/{}/level.dat'.format(name)

if 1:
    data = load(mkname('a'))

    # level = TagWrapper(data)
    # data.value['Data']

    # print(level['Data/GameRules/keepInventory'])

    #pprint(nbt._tmp_encode_typeless_python(data,
    #                                       keys_only=True))

    nbt.print_structure(data)

    # save(mkname('b'), data)
    #data = load(mkname('b'))
    #pprint(data)
