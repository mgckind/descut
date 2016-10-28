'''
This is the code to create new table using easyaccess
the tag and new table name need to edited manually
the database name for mongo is descut
the collection name for full dataset and clean dataset need to be specified
'''
import easyaccess as ea
import pandas as pd
import numpy as np
from pymongo import MongoClient
import subprocess
import pymongo

connection = ea.connect()
cursor = connection.cursor()
ops_proctag = 'Y3A1_FINALCUT'
full_table = 'descut_full'
clean_table = 'descut_clean'
sr_blacklist = 'prod.blacklist'
dest_blacklist = 'blacklist'

# create table include blacklist
query = '''
create table {0} as
SELECT
file_archive_info.FILENAME,
file_archive_info.COMPRESSION,
file_archive_info.PATH,
image.PFW_ATTEMPT_ID,
image.BAND,
image.CCDNUM,
image.EXPNUM,
image.CROSSRA0,
image.NITE,
image.RACMIN,image.RACMAX,
image.DECCMIN,image.DECCMAX,
image.RA_CENT,image.DEC_CENT,
image.RAC1, image.RAC2, image.RAC3, image.RAC4,
image.DECC1, image.DECC2, image.DECC3, image.DECC4,
file_archive_info.PATH || '/' || file_archive_info.FILENAME as FULL_PATH,
(case when image.CROSSRA0='Y' THEN abs(image.RACMAX - (image.RACMIN-360)) ELSE abs(image.RACMAX - image.RACMIN) END) as RA_SIZE,
abs(image.DECCMAX - image.DECCMIN) as DEC_SIZE
FROM
ops_proctag, image, file_archive_info
WHERE
file_archive_info.FILENAME = image.FILENAME AND
image.PFW_ATTEMPT_ID = ops_proctag.PFW_ATTEMPT_ID AND
image.FILETYPE = 'red_immask' AND
ops_proctag.TAG = '{1}'
'''.format(full_table, ops_proctag)

qq = cursor.execute(query)

# create blacklist table which has only filename colunum
query_b = '''
create table {0} as
SELECT
filename
FROM
{1}, {2}
WHERE
{1}.EXPNUM = {2}.EXPNUM AND
{1}.CCDNUM = {2}.CCDNUM
'''.format(dest_blacklist, full_table, sr_blacklist)

qq_b = cursor.execute(query_b)


# create a clean table exclude blacklist files
query_c = '''
create table {0} as
SELECT * FROM {1} WHERE {1}.filename <> {2}.filename
'''.format(clean_table,full_table,dest_blacklist)

qq_c = cursor.execute(query_c)


# get table to dataframe and output them to list of dicts 
query_get = 'select path || '/' || filename as full_path, {0}.* from {0}'
df_full = connection.query_to_pandas(query_get.format(full_table))
df_clean = connection.query_to_pandas(query_get.format(clean_table))
full_list = df_full.to_dict(orient='records')
clean_list = df_clean.to_dict(orient='records')

# init connection to mongo and specify collection name 
db = MongoClient().descut
coll_full = 'tag'
coll_clean = 'tag_clean'

# bulk insert dicts into mongo collection
record = db[coll_full].insert_many(full_list)
record_c = db[coll_clean].insert_many(clean_list)

# format documents: clean data errors, create index
































