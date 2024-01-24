#!/bin/env python3
from astropy.io import fits
import os, sys
from datetime import *
import psycopg2
import common_postgres as copo


def read_header_peramp(peramp):
	expid = peramp.header["EXPID"]
	night = peramp.header["NIGHT"]
	program = peramp.header["PROGRAM"]
	obstype = peramp.header["OBSTYPE"]
	time = peramp.header["DATE-OBS"].split('.')[0].replace('T', ' ')

	header = {
		'expid':expid,
		'night':night,
		'obstype':obstype,
		'program':program,
		'time':time
	}
	return header


def read_data_peramp(peramp):
	data = []
	for f in peramp.data:
		data.append("({1}, {2}, '{3}', '{4}', {5}, {6}, {7} )".format(*f))
	return ','.join(data)

def read_data_percamera(percamera):
	data = []
	for f in percamera.data:
		data.append("({1}, {2}, '{3}', {4}, {5}, {6}, {7}, {8}, {9})".format(*f))
	return ','.join(data)

def read_data_percamera_sig(percamera):
	data = []
	for f in percamera.data:
		data.append("({1}, {2}, '{3}', {10}, {11}, {12}, {13}, {14}, {15})".format(*f))
	return ','.join(data)

def read_data_percamfiber(percamfiber):
	data = []
	for f in percamfiber.data:
		data.append("({1}, {2}, '{3}', {4}, {5}, {6}, {7})".format(*f))
	return ','.join(data)

def read_data_percamfiber_science(percamfiber):
	data = []
	for f in percamfiber.data:
		data.append("({1}, {2}, '{3}', {4}, {8}, {9}, {10})".format(*f))
	return ','.join(data)

def read_data_perspectro(perspectro):
	data = []
	for f in perspectro.data:
		dastring = ','.join([str(d) for d in f[4:]])
		data.append("({}, '{}', {})".format(f[1], f[3], dastring))
	return ','.join(data)

def insert_data(db_con, header, data_dic):
	db_cur = db_con.cursor()
	db_cur.execute("SELECT expid FROM nw_header  WHERE expid = {}".format(header["expid"]))
	result = db_cur.fetchall()
	if len(result) != 0:
		print("expid {} exists in DB. new data are not added".format(header["expid"]))
		return False

	
	insert_header_com = "INSERT INTO nw_header VALUES ({expid}, {night}, '{obstype}', '{program}', '{time}')".format(**header)
	db_cur.execute(insert_header_com)


	for table, data in data_dic.items():
		insert_data_com = "INSERT INTO {} VALUES {}".format(table, data)
		#print("data", table)
		db_cur.execute(insert_data_com)
		db_con.commit()

	return True


def find_fits_files(data_dir):
	data_files = []
	for f in os.listdir(data_dir):
		fullname = os.path.join(data_dir, f)
		if os.path.isdir(fullname):
			data_files += find_fits_files(fullname)
		elif f.endswith(".fits") and f.startswith('qa-'):
			data_files.append(fullname)

	return data_files

#db_name = "desi_v1.db"
#data_dir = "/home/otto/DESI/20230816/"

if len(sys.argv) != 2:
	print("use:", " directory_with_fit_files")
	sys.exit()

data_dir = sys.argv[1]

fits_files = find_fits_files(data_dir)

print(fits_files)

#exit(0)

db_con = copo.get_db_connection()

for fits_file in fits_files:
	fitsdata = fits.open(os.path.join(data_dir, fits_file))
	data = {}

	try:
		peramp_index = fitsdata.index_of('PER_AMP')
	except:
		peramp_index = None
	
	if peramp_index != None:
		peramp = fitsdata[peramp_index]	
		header = read_header_peramp(peramp)
		if header['program'] not in copo.programs:
			print("WARNING: will not fill data for program", header['program'])
			continue
		if header['obstype'] not in copo.obstypes:
			print("WARNING: will not fill data for obstype", header['obstype'])
			continue
		data['nw_peramp'] = read_data_peramp(peramp)



	try:
		percam_index = fitsdata.index_of('PER_CAMERA')
	except:
		percam_index = None

	if percam_index != None:
		percam = fitsdata[percam_index]	
		data['nw_percamera'] = read_data_percamera(percam)
		if percam.header['TFIELDS'] == 16:
			data['nw_percamera_sig'] = read_data_percamera_sig(percam)


#	try:
#		percamfiber_index = fitsdata.index_of('PER_CAMFIBER')
#	except:
#		percamfiber_index = None
#
#	if percamfiber_index != None:
#		percamfiber = fitsdata[percamfiber_index]	
#		data['nw_percamfiber'] = read_data_percamfiber(percamfiber)
#		if percamfiber.header['TFIELDS'] == 11:
#			data['nw_percamfiber_science'] = read_data_percamfiber_science(percamfiber)


	try:
		perspectro_index = fitsdata.index_of('PER_SPECTRO')
	except:
		perspectro_index = None

	if perspectro_index != None:
		perspectro = fitsdata[perspectro_index]	
		print("spectro", header['program'])
		if header['program'] in copo.led_programs :
			data['nw_perspectro_led'] = read_data_perspectro(perspectro)
		elif header['program'] in copo.short_arcs_programs:
			data['nw_perspectro_short_arcs'] = read_data_perspectro(perspectro)
		elif header['program'] in copo.long_arcs_programs:
			data['nw_perspectro_long_arcs'] = read_data_perspectro(perspectro)


	print('###############################################################')
	print(header)
	print(data.keys())
	insert_data(db_con, header, data)

