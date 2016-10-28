''' 
Use this script to create new geo location field and indexes for collections (full and clean can run in parallel)
'''
import pandas as pd
from pymongo import MongoClient
import pymongo as pmg
import os, json
from bson.json_util import dumps
import sys

client = MongoClient(port = 27017)
dbName = sys.argv[1]
collName = sys.argv[2]
db = client[dbName]
coll = db[collName]

# correct error in data types
bulk = coll.initialize_unordered_bulk_op()
bulk.find({'RACMAX':{'$type':2}}).update({'$set':{'RACMAX':float(doc['RACMAX'])}})
bulk.find({'RACMIN':{'$type':2}}).update({'$set':{'RACMIN':float(doc['RACMIN'])}})
bulk.find({'DECCMAX':{'$type':2}}).update({'$set':{'DECCMAX':float(doc['DECCMAX'])}})
bulk.find({'DECCMIN':{'$type':2}}).update({'$set':{'DECCMIN':float(doc['DECCMIN'])}})
bulk.find({'DEC_CENT':{'$type':2}}).update({'$set':{'DEC_CENT':float(doc['DEC_CENT'])}})
bulk.find({'RA_CENT':{'$type':2}}).update({'$set':{'RA_CENT':float(doc['RA_CENT'])}})
result_full = bulk.execute()

print(result_full)
print (coll.find({'RACMAX':{'$type':2}}).count())
print (coll.find({'RACMIN':{'$type':2}}).count())
print (coll.find({'DECCMAX':{'$type':2}}).count())
print (coll.find({'DECCMIN':{'$type':2}}).count())
print (coll.find({'DEC_CENT':{'$type':2}}).count())
print (coll.find({'RA_CENT':{'$type':2}}).count())


cursor = coll.find()
#create loc field for geospatial index
for doc in cursor:
	coll.update({'_id': doc['_id']}, {'$set': {'loc':[doc['RA_CENT'],doc['DEC_CENT']]}})

#query the objects that reside within 2 degrees interval from the 360/0 line
small_cur = coll.find({'RA_CENT':{'$lt':2}})
big_cur = coll.find({'RA_CENT':{'$gt':358}})

#create the loc_360 field
for doc in small_cur:
	coll.update({'_id': doc['_id']}, {'$set': {'loc_360':[doc['RA_CENT']+360,doc['DEC_CENT']]}})
for doc in big_cur:
	coll.update({'_id': doc['_id']}, {'$set': {'loc_360':[doc['RA_CENT'],doc['DEC_CENT']]}})

#create the index and set the min and max bounds 
coll.create_index([('loc', pmg.GEO2D)], name = 'image_cent', min = -90, max = 360)
coll.create_index([('loc_360', pmg.GEO2D)], name = 'image_cent_360', min = -90, max = 400)
