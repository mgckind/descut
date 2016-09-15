#!/usr/bin/env python3
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os,sys,io
import pandas as pd
import numpy as np
import time
import multiprocessing as mp
#import easyaccess as ea
import subprocess
import astrometry
import fitsio
from fitsio import FITS, FITSHDR
import mongo_util as mu
import f2n
import prettytable as pt
from astropy import wcs
import astropy.wcs.utils as wu
from multiprocessing import Pool

#con = ea.connect('desoper')
FITS_OUTNAME  = "{outdir}/thumbs_DESJ_{ra}{dec}/{prefix}J{ra}{dec}_{band}_{nite}.{ext}"
PNG_OUTNAME  = "{outdir}/thumbs_DESJ_{ra}{dec}/{prefix}J{ra}{dec}_{band}_{nite}.png"
des_root = '/archive_data/desarchive/'
personal = False

# SOUT = sys.stdout

def cmdline():
	import argparse
	parser = argparse.ArgumentParser(description="Make exposure cutout/thumbs with given postions")

	#positional argument
	# parser.add_argument('RA', type=float, help='RA')
	# parser.add_argument('DEC', type=float, help='DEC')
	parser.add_argument('inputFile', type=str, help='Path to a CSV file containing a list of postions (RA, DEC)')
	# parser.add_argument('username', type=str, help='DES Credential: username')
	# parser.add_argument('password', type=str, help='DES Credential: password')

	#optional arguments
	parser.add_argument("--xsize", type=float, action="store", help="Length of x-side in arcmins of image [default = 1.0]")
	parser.add_argument("--ysize", type=float, action="store", help="Length of y-side of in arcmins image [default = 1.0]")
	parser.add_argument("--tag", type=str, action="store", default = 'Y2A1_FINALCUT',
		help="Tag used for retrieving files [default=Y2A1_FINALCUT]")
	parser.add_argument("--bands", type=str, action='store', nargs = '+', default=['g','i','z','r','Y'], help="Bands used for images. Can either be 'all' (uses all bands, and is the default), or a list of individual bands")
	parser.add_argument("--outdir", type=str, action='store', default=os.getcwd(),
		help="Output directory location [default='./']")
	parser.add_argument('--username', type=str, default = 'demo_user', help='DES Credential: username')
	parser.add_argument('--password', type=str, default = '07spihc', help='DES Credential: password')
	parser.add_argument('--noBlacklist', type=str, help='Check to exclue exposures from the des_admin.blacklist')
	parser.add_argument('--listOnly', type=str, help='Only make the cuts, no png for web')
	parser.add_argument("--log", type=str, action='store', default=None, help="Output logfile")
	args=parser.parse_args()

	args.noBlacklist = args.noBlacklist == 'True'
	args.listOnly = args.listOnly == 'True'
	args.override = not (args.xsize is None and args.ysize is None)

	if not os.path.exists(args.outdir):
		os.makedirs(args.outdir)

	# logs in case of failure
	logPath = '{}/log.log'.format(args.outdir)
	args.log = open(logPath, 'w')

	#some global vars
	global SOUT
	SOUT = args.log

	global listOnly
	listOnly = args.listOnly

	#change collection to match blacklist option
	mu.select_collection(args.noBlacklist)
	
	SOUT.write('inputFile: {} \n'.format(args.inputFile))
	SOUT.write('xsize: {} \n'.format(args.xsize))
	SOUT.write('ysize: {} \n '.format(args.ysize))
	SOUT.write('bands: {} \n'.format(args.bands))
	SOUT.write('noBlacklist: {} \n'.format(args.noBlacklist))
	SOUT.write('listOnly: {} \n'.format(args.listOnly))
	# print ('log', args.log)

	return args
def run_mongo(args):
	
	"""
	Run the program with mongodb 
	"""
	#starting time for the process
	t0 = time.time()
	#specify log output
	SOUT.write('# Starting Job! \n')
	SOUT.write('# Read object positions \n')

	df_list = pd.read_csv(args.inputFile, na_values=[''])
	df_list.columns = [x.upper() for x in df_list.columns]

	# if use size from input then change the value from file
	if args.override:
		df_list['XSIZE'] = args.xsize
		df_list['YSIZE'] = args.ysize

	if not validate_ra_dec(df_list):
		SOUT.write("!!!Warning!!! \n Cutout service terminated! \n")
		SOUT.write("ERROR!!! Missing ra and dec values! \n")
		return 

	df_list = format_data(df_list)

	bands = args.bands
	# tag = args.tag

	#used to check whether program running on personal machine 
	global personal
	if not os.path.exists('/archive_data/desarchive/ACT/check_connection.txt'):
		personal = True


	demo_list=[]
	folder_names = []
	pos_no_img = []
	exp_fail = []
	total_fail = 0
	total_exposures = 0

	#error log path
	global error_stream
	err_file = args.outdir+'/error.log'
	error_stream = open(err_file, 'w')

	# task pool dataframe 
	global df_pool
	pool_col = ['ra', 'dec', 'xs', 'ys', 'exp_filename', 'exp_path', 'raw_image_dir', 'outname', 'pngName', 'temp_log']

	# multiprocessing pool
	global p
	p = Pool(processes=4)
	
	for i in range(len(df_list)):
		# init df_pool dataframe for storing mp task data
		df_pool=pd.DataFrame(columns=pool_col)
		
		#found images or not 	
		match_found = True

		SOUT.write('************************************************************** \n')
		SOUT.write("# Querying for object ({},{}) \n".format(df_list.RA[i],df_list.DEC[i]))

		df_w_path = mu.query_to_pandas(df_list.RA[i],df_list.DEC[i],bands)
		total_exposures += len(df_w_path)
	
		if len(df_w_path)==0:
			match_found = False
			# print ('No Images Found for ({},{})!'.format(df_list.RA[i],df_list.DEC[i]))
			SOUT.write('# No Images Found for ({},{})! \n'.format(df_list.RA[i],df_list.DEC[i]))
			demo_list.append(None)
			folder_names.append(None)
			pos_no_img.append((df_list.RA[i],df_list.DEC[i]))
			
			#if no images found for this position, jump out of the loop
			continue

		if match_found:
			
			#check to see if program running on personal machine instead of DES machine
			if personal:
				SOUT.write('# Program not running on des machine, will download the fits files \n')
				#save all raw images to a temp folder under outdir
				save_images(args,df_w_path,df_list['RA'][i], df_list['DEC'][i])

			SOUT.write('# Start cutting the fits images and generate pngs \n')

			demo_png, fail_num = fitscutter(df_w_path, df_list['RA'][i],df_list['DEC'][i], xsize=df_list['XSIZE'][i], \
				ysize= df_list['YSIZE'][i], outdir=args.outdir)
			demo_list.append(demo_png)
			folder_names.append(demo_png.split('/')[0])
			exp_fail.append((df_list.RA[i],df_list.DEC[i]))
			exp_fail.append(fail_num)
			total_fail += fail_num


	# write the summary at the end 
	SOUT.write('------------------------------------------------------------------------------------ \n')
	SOUT.write('# A little summary!!! \n')

	if (len(pos_no_img) > 0 ):
		SOUT.write('# {} out of {} positions has no exposures found! These postions are listed below: \n'.format(len(pos_no_img), len(df_list)))
		for x in pos_no_img:
			SOUT.write('# {} \n'.format(x))

	SOUT.write('# Totally {} exposures has been found and {} of them failed to generate the thumbnail cuts! \n'.format(total_exposures, total_fail))
	
	if total_fail>0:
		SOUT.write('# Details are listed below: \n')
		SOUT.write('(RA, DEC),  # of Fails \n')
		for z in range(int(len(exp_fail)/2)):
			m = z*2
			SOUT.write('{}  {} \n'.format(exp_fail[m], exp_fail[m+1]))

	SOUT.write('# Job finished, total time used {}s'.format(time.time()-t0))
	
	# generate list of objects file
	if not listOnly:
		df_list = df_list.assign(demo_png = demo_list, image_title = folder_names)
		df_list = df_list.dropna(axis=0)
		df_list.to_json(args.outdir+'/list.json', orient='records')	
	
	# close output streams 
	SOUT.close()
	error_stream.close()	

def validate_ra_dec(df):
	'''validate ra and dec column in input file

	'''
	if not ("RA" in df.columns and "DEC" in df.columns):
		return False
	elif df[['RA', 'DEC']].isnull().any().any():
		return False
	else:
		return True

def format_data(df):
	'''fillin missing size with 1 and convert all data to float type

	'''
	df_mod = df.copy()

	if "XSIZE" in df_mod.columns and 'YSIZE' in df_mod.columns:
		df_mod[['XSIZE', 'YSIZE']]=df_mod[['XSIZE', 'YSIZE']].fillna(1)
	else:
		df_mod['XSIZE']=1
		df_mod['YSIZE']=1

	for x in df_mod.columns:
		df_mod[x]=df_mod[x].astype(float)

	return df_mod
def save_images(args, df_w_path, ra, dec):
	user = args.username
	password = args.password
	root ='https://desar2.cosmology.illinois.edu/DESFiles/desarchive/'
	cmd = 'wget --user={} --password={} --no-check-certificate -O {}/{} {}{}'
	outdir = args.outdir+'/'+"RA_{}_DEC_{}".format(ra, dec)
	#make the output directory if not exists
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	#wget all images from the archive
	for i in range(len(df_w_path)):
		#print (df_w_path['FULL_PATH'][i])
		subprocess.call(cmd.format(user, password, outdir, df_w_path['FILENAME'][i]+'.fz', root, df_w_path['FULL_PATH'][i]+'.fz'), shell=True)


def get_thumbFitsName(ra,dec,band,nite,prefix='DES',ext='fits',outdir=os.getcwd()):
	""" Common function to set the Fits thumbnail name """
	# ra  = astrometry.dec2deg(ra/15.,sep="",plussign=False)
	# dec = astrometry.dec2deg(dec,   sep="",plussign=True)
	kw = locals()
	outname = FITS_OUTNAME.format(**kw)
	return outname

def get_thumbPngName(ra,dec,band,nite,prefix='DES',outdir=os.getcwd()):
	""" Common function to set the Fits thumbnail name """
	# ra  = astrometry.dec2deg(ra/15.,sep="",plussign=False)
	# dec = astrometry.dec2deg(dec,   sep="",plussign=True)
	kw = locals()
	outname = PNG_OUTNAME.format(**kw)
	return outname
def fitscutter(df_w_path, ra, dec, xsize, ysize, prefix='DES',outdir=os.getcwd()):

	"""
	Makes cutouts around ra, dec for a given xsize and ysize
	ra,dec can be scalars or lists/arrays
	"""
	
	# from default arcmin to arcsec
	# scale = 60

	global df_pool

	#conver the position from decimals to degrees 
	RA  = astrometry.dec2deg(ra/15.,sep="",plussign=False)
	DEC = astrometry.dec2deg(dec,   sep="",plussign=True)

	# raw image folder and cut output folder
	raw_image_dir = outdir+'/'+"RA_{}_DEC_{}/".format(ra, dec)
	thumbs_folder = outdir+'/'+'thumbs_DESJ_{}{}'.format(RA, DEC)
	
	
	if not os.path.exists(thumbs_folder):
		os.makedirs(thumbs_folder)

	expnum = len(df_w_path)
	######################################
	# Loop over ra/dec and xsize,ysize
	for k in range(len(df_w_path)):

		se_log = '# cutting {} out of {} exposures \n'.format(k+1, expnum) + \
		'# SE filename: {} \n'.format(df_w_path['FILENAME'][k])

		# naming for cutout fits and pngs
		band = df_w_path['BAND'][k]
		nite = df_w_path['NITE'][k]
		outname = get_thumbFitsName(RA,DEC,band,nite,prefix=prefix,outdir=outdir)
		pngName = get_thumbPngName(RA,DEC,band,nite,prefix=prefix, outdir = outdir)
		# make the cut with all inputs 
		task_dic = {'ra':ra,'dec':dec,'xs':xsize,'ys':ysize,'exp_filename':df_w_path['FILENAME'][k], \
			'exp_path':df_w_path['FULL_PATH'][k],'raw_image_dir':raw_image_dir, 'outname':outname, 'pngName':pngName, 'temp_log':se_log}
		task_s = pd.Series(task_dic)

		df_pool=df_pool.append(task_s, ignore_index=True)
	
	df_pool.set_index('pngName', drop=False)
	p.map(task_try, list(df_pool.iterrows()))
	subprocess.check_call(['rm', '-rf', raw_image_dir]) 

	#write the log after cuts finished 
	for temp_log in df_pool['temp_log']:
		SOUT.write(temp_log)

	# write front_end json for displaying
	fail_index = df_pool.loc[df_pool['outname'].isnull()].exp_filename.tolist()
	df_w_path = df_w_path.loc[~df_w_path['FILENAME'].isin(fail_index)]
	df_pool_pure = df_pool.dropna(axis=0)
	png_list = df_pool_pure['pngName'].apply(lambda x: os.path.split(x)[1]).tolist()

	if (len(df_w_path) != len(df_pool_pure)):
		print ('dataframe size error')
		return 
	
	if not listOnly:
		df_w_path = df_w_path.assign(png_name=png_list)
		front_record = df_w_path[['BAND','NITE', 'png_name', 'CCDNUM', 'EXPNUM']]
		front_record.to_json(thumbs_folder+'/png_list.json', orient = 'records')

	# end log for each position
	SOUT.write('# Object ({},{}) is finished\n'.format(ra, dec))
	SOUT.write('$$ {} out of {} exposures successfully generated the thumb cuts! $$\n '.format(len(png_list), expnum))

	# output the exposure files information to a txt file
	to_table(df_w_path,ra,dec,thumbs_folder)

	return ('thumbs_DESJ_{}{}/{}'.format(RA, DEC, png_list[0]) , expnum-len(png_list))


def to_table(df_w_path, ra, dec, thumbs_folder):
	'''
	Write pandas df to a txt table
	'''
	pTable =  pt.PrettyTable()
	table_df = df_w_path.copy()
	table_df.insert(0, 'DEC', dec)
	table_df.insert(0, 'RA', ra)
	output = io.StringIO()
	table_df = table_df[['RA', 'DEC', 'BAND', 'NITE', 'CCDNUM', 'EXPNUM', 'PFW_ATTEMPT_ID']]
	
	pTable.field_names= ['RA', 'DEC', 'BAND', 'NITE', 'CCDNUM', 'EXPNUM', 'PFW_ATTEMPT_ID']
	
	for i in range(len(table_df)):
		pTable.add_row(table_df.ix[i].tolist())
	
	p_str = pTable.get_string()

	with open(thumbs_folder+'/table.txt', 'w') as oStream:
		oStream.write(p_str)

	output.close()
def task_try (series):
	data = series[1]
	ra = data.loc['ra']
	dec = data.loc['dec']
	xs = data.loc['xs']
	ys = data.loc['ys']
	exp_filename = data.loc['exp_filename']
	exp_path = data.loc['exp_path']
	raw_image_dir = data.loc['raw_image_dir']
	outname = data.loc['outname']
	pngName = data.loc['pngName']
	temp_log = data.loc['temp_log']
	# print (data.loc, len(series))
	
	global df_pool

	try:
		cut_save(ra, dec, xs, ys, exp_filename, exp_path,raw_image_dir, outname, pngName)
	except Exception as e:
		err_log = '!! This exposure failed !! \n' + repr(e)+'\n'
		df_pool.set_value(pngName,'temp_log',temp_log+err_log)
		df_pool.set_value(pngName, 'outname', None)
		error_stream.write('({},{}), {}\n'.format(ra, dec, df_w_path['FILENAME'][k]))
	else:
		return
		# png_list.append(os.path.split(pngName)[1])


# cut function for individual exposure
def cut_save(ra, dec, xs, ys, exp_filename, exp_path, raw_image_dir, outname, pngName):
	
	# Intitialize the FITS object
	if personal:
		ifits = fitsio.FITS(raw_image_dir+exp_filename+'.fz','r')
	else:
		ifits = fitsio.FITS(des_root+exp_path+'.fz','r')

	# Get the SCI, WGT and MSK headers
	h_sci = ifits['sci'].read_header()
	h_msk = ifits['msk'].read_header()
	h_wgt = ifits['wgt'].read_header()

	# Read in the WCS with astropy wcs
	w = wcs.WCS(h_sci)

	# Get the pixel-scale of the input image
	scale = wu.proj_plane_pixel_scales(w)
	x_scale = scale[0].tolist()*3600
	y_scale = scale[1].tolist()*3600

	# Define the geometry of the thumbnail
	x0, y0 = w.wcs_world2pix(ra,dec,0)
	x0=round(x0.tolist())
	y0=round(y0.tolist())

	# #one fix for the header problem, way off x, y for given ra,dec 
	# if abs(x0)>6000 or abs(y0) > 6000:
	# 	x0,y0 = wcs.sky2image(ra+360,dec)

	dx = int(0.5*xs*60/x_scale)
	dy = int(0.5*ys*60/y_scale)
	naxis1 = 2*dx+1
	naxis2 = 2*dy+1
	y1 = y0-dy
	y2 = y0+dy+1
	x1 = x0-dx
	x2 = x0+dx+1

	if y1<0: 
		y1=0
		# if at edge, set x0+1 as crpix1
		dy = y0
	if x1<0: 
		x1=0
		# if at edge, set y0+1 as crpix2
		dx = x0


	# Create a canvas
	im_section_sci = np.zeros((naxis1,naxis2))
	im_section_msk = np.zeros((naxis1,naxis2))
	im_section_wgt = np.zeros((naxis1,naxis2))

	# Read in the image section we want for SCI/WGT/MSK
	im_section_sci = ifits['sci'][y1:y2,x1:x2]
	im_section_msk = ifits['msk'][y1:y2,x1:x2]
	im_section_wgt = ifits['wgt'][y1:y2,x1:x2]

	# make deepcopy of orginal header
	h_section_sci = wcs.WCS.deepcopy(h_sci)
	h_section_msk = wcs.WCS.deepcopy(h_msk)
	h_section_wgt = wcs.WCS.deepcopy(h_wgt)
	# update the copy as a new headers
	h_section_sci['CRPIX1']=h_sci['CRPIX1']-x0+dx+1
	h_section_sci['CRPIX2']=h_sci['CRPIX2']-y0+dy+1	
	h_section_msk['CRPIX2']=h_msk['CRPIX2']-y0+dy+1
	h_section_msk['CRPIX2']=h_msk['CRPIX2']-y0+dy+1
	h_section_wgt = h_wgt
	# add new cutout center to new header
	h_section_sci['RA_CUTOUT']=ra
	h_section_sci['DEC_CUTOUT']=dec
	h_section_msk['RA_CUTOUT']=ra
	h_section_msk['DEC_CUTOUT']=dec
	h_section_wgt['RA_CUTOUT']=ra
	h_section_wgt['DEC_CUTOUT']=dec
	

	# Write out the file
	# SOUT.write('# write the new fits file \n')
	ofits = fitsio.FITS(outname,'rw',clobber=True)
	ofits.write(im_section_sci,header=h_section_sci, extname='SCI')
	ofits.write(im_section_msk,header=h_section_msk, extname='MSK')
	ofits.write(im_section_wgt,header=h_section_wgt, extname='WGT')
	ofits.close()

	#create pngs
	# SOUT.write('# making the pngs \n')
	if not listOnly: fits_to_pngs(outname, pngName)


def fits_to_pngs(source_name, outname, zscale='lin'):
	png = f2n.fromfits(source_name)
	png.setzscale(z1='auto', z2='flat')
	png.makepilimage(zscale)
	png.tonet(outname)


if __name__ == "__main__":

	args = cmdline()

	run_mongo(args)









# cmdline()