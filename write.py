import sys
import json
from pprint import pprint
from mcdata.nbt import load, save, Tag, TagWrapper
import mcdata

def mkname(name):
    return '/home/olemb/.minecraft/saves/{}/level.dat'.format(name)

if 1:
    data = load(mkname('a'))
    level = TagWrapper(data)

    # data.value['Data']

    print(level['Data/GameRules/keepInventory'])

    # pprint(data)
    # save(mkname('b'), data)
    #data = load(mkname('b'))
    #pprint(data)
