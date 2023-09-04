from astropy.io import fits
from ROOT import TH1D
import os, sys
from datetime import *
from desi_sqlite import *


def read_header_peramp(peramp):
	expid = peramp.header["EXPID"]

	night = peramp.header["NIGHT"]

	program = programs.get(peramp.header["PROGRAM"], -1)
	if program == -1:
		print("WARNING: unknown program", peramp.header["PROGRAM"])

	obstype = obstypes.get(peramp.header["OBSTYPE"], -1)
	if obstype == -1:
		print("WARNING: unknown obstype", peramp.header["OBSTYPE"])

	time = datetime.strptime(peramp.header["DATE-OBS"].split('.')[0], '%Y-%m-%dT%H:%M:%S').timestamp()

	header = {
		'expid':expid,
		'night':night,
		'obstype':obstype,
		'program':program,
		'time':int(time)
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


#db_name = "desi_v1.db"
#data_dir = "/home/otto/DESI/20230816/"

if len(sys.argv) != 3:
	print("use:", "create_db dbfile.db directory_with_fit_files")
	sys.exit()

db_name = sys.argv[1]
data_dir = sys.argv[2]


fits_files = [f for f in os.listdir(data_dir) if f.endswith(".fits")]


new_db = os.path.isfile(db_name) == False

db_con = get_db_connection(db_name)
if new_db  == True:
	print("create new DB", db_name)
	create_tables(db_con)


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
		data['peramp'] = read_data_peramp(peramp)



	try:
		percam_index = fitsdata.index_of('PER_CAMERA')
	except:
		percam_index = None

	if percam_index != None:
		percam = fitsdata[percam_index]	
		data['percamera'] = read_data_percamera(percam)
		if percam.header['TFIELDS'] == 16:
			data['percamera_sig'] = read_data_percamera_sig(percam)


	try:
		percamfiber_index = fitsdata.index_of('PER_CAMFIBER')
	except:
		percamfiber_index = None

	if percamfiber_index != None:
		percamfiber = fitsdata[percamfiber_index]	
		data['percamfiber'] = read_data_percamfiber(percamfiber)
		if percamfiber.header['TFIELDS'] == 11:
			data['percamfiber_science'] = read_data_percamfiber_science(percamfiber)


	try:
		perspectro_index = fitsdata.index_of('PER_SPECTRO')
	except:
		perspectro_index = None

	if perspectro_index != None:
		perspectro = fitsdata[perspectro_index]	
		if 11 <= header['program']<= 15 :
			data['perspectro_led'] = read_data_perspectro(perspectro)
		elif header['program'] == 9:
			data['perspectro_short_arcs'] = read_data_perspectro(perspectro)
		elif header['program'] == 10:
			data['perspectro_long_arcs'] = read_data_perspectro(perspectro)

	insert_data(db_con, header, data)
	#print(data)

