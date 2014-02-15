from pprint import pprint
from mcdata.nbt import encode, decode
import mcdata

data = {'Data:compound': {'DayTime:long': 19734000,
                   'GameRules:compound': {'commandBlockOutput:string': u'true',
                                          'doDaylightCycle:string': u'false',
                                          'doFireTick:string': u'true',
                                          'doMobLoot:string': u'true',
                                          'doMobSpawning:string': u'true',
                                          'doTileDrops:string': u'true',
                                          'keepInventory:string': u'true',
                                          'mobGriefing:string': u'false',
                                          'naturalRegeneration:string': u'true'},
                   'GameType:int': 0,
                   'LastPlayed:long': 1392485228000,
                                      # 1392459870402
                                      # Why 3 extra digits? (402)
                   'LevelName:string': u'NBT Test!',
                   'MapFeatures:byte': 1,
                   'RandomSeed:long': -6835287926081588652,
                   'SizeOnDisk:long': 0,
                   'SpawnX:int': 15,
                   'SpawnY:int': 62,
                   'SpawnZ:int': 173,
                   'Time:long': 38837956,
                   'allowCommands:byte': 1,
                   'generatorName:string': u'default',
                   'generatorOptions:string': '',
                   'generatorVersion:int': 1,
                   'hardcore:byte': 0,
                   'initialized:byte': 1,
                   'rainTime:int': 71770,
                   'raining:byte': 0,
                   'thunderTime:int': 43990,
                   'thundering:byte': 0,
                   'version:int': 19133}}

mcdata.nbt.write('/home/olemb/.minecraft/saves/test/level.dat', data)
