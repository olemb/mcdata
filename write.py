from pprint import pprint
from mcdata.nbt import encode, decode
import mcdata

fmt = '/home/olemb/.minecraft/saves/{}/level.dat'

def load(name):
    return mcdata.nbt.load(fmt.format(name))

def save(name, data):
    return mcdata.nbt.save(fmt.format(name), data)

data = load('a')
# print(data['Data:compound']['LevelName:string'])
# print()
# data['Data:compound']['LevelName:string'] = 'Fisk!'

old = data

save('b', data)
new = load('a')
# print(old == new)
