import pandas as pd
from pymongo import MongoClient
import pymongo as pmg
import os, json
from bson.json_util import dumps


client = MongoClient(port=27017, host="mongodb")
db = client.descut
coll = db.Y3A1_FINALCUT

def select_collection(noBlacklist):
	global coll
	if noBlacklist:
		print ('# Blacklist excluded!!')
		coll = db.Y3A1_FINALCUT_CLEAN
	
def query_to_pandas(ra, dec, bands):
	#0.2 is the raidus in degree
	#check to see if the query will possible cross 360/0 line
	in_range = False
	# print (coll)
	#variable to choose which racmin, racmax to use 
	rac_max = 'RACMAX'
	rac_min = 'RACMIN'
	if ra>359.4 or ra<0.6:

		if ra <1:
			ra = ra + 360

		in_range = True
		query_cur = coll.find({"loc_360":{"$geoWithin":{"$center":[[ra,dec], 0.2]}}},{'_id':0})
	else:
		query_cur = coll.find({"loc":{"$geoWithin":{"$center":[[ra,dec], 0.2]}}},{'_id':0})
	
	json_str = dumps(query_cur)

	#from json string to pandas dataframe 
	query_df = pd.read_json(json_str,orient = 'records')
	#if no exposure match, then return
	if (len(query_df)<1):
		return query_df
	#if in the range then test for crossing and make the new ra_max for filtering later 
	if in_range:
		rac_max = 'new_rac_max'
		rac_min = 'new_rac_min'
		query_df['new_rac_max'] = (query_df['RACMAX']<10).map({True:1, False:0})*360+query_df['RACMAX']
		query_df['new_rac_min'] = (query_df['RACMIN']<10).map({True:1, False:0})*360+query_df['RACMIN']
		

	#mask out images that doesn't contain the point
	mask = (query_df[rac_max]>ra) & (query_df[rac_min] < ra) & (query_df['DECCMAX']>dec) & (query_df['DECCMIN'] < dec)	
	query_df = query_df[mask]

	#if no exposures left after mask, then return
	if (len(query_df)<1):
		return query_df
	#mask out images with bands not needed 
	band_mask = query_df['BAND'].isin(bands)
	query_df = query_df[band_mask]

	#if no exposures left after band-mask, then return
	if (len(query_df)<1):
		return query_df

	query_df.sort_values('NITE', inplace=True)

	query_df.reset_index(drop=True, inplace=True)

	return query_df



def setup():

	cursor = coll.find()
	#create loc field for geospatial index
	for doc in cursor:
		coll.update({'_id': doc['_id']}, {'$set': {'loc':[doc['RA_CENT'],doc['DEC_CENT']]}})

	#create the full_path field
	cursor = coll.find()
	for doc in cursor:
		coll.update({'_id': doc['_id']}, {'$set': {'FULL_PATH':doc['PATH']+'/'+doc['FILENAME']+'.fz'}})

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

'''
	The estimated query radius is derived from following
		
		import math

		#228 is the number of pixel for one arcmin 
		width=2048/228/60
		height = width*2

		diag = math.sqrt(width**2+height**2)
		diag = diag*1.2 #add another 20 percent for flexibility 
		half_diag_rad = diag*math.pi/180/2  #convert from degree to radian

'''