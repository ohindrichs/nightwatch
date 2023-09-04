import sqlite3


programs = {
'CALIB ZEROs for nightly bias':1,
'CALIB Dark 5min':2,
'ZEROs for dark sequence C':3,
'DARK 1200.0s for dark sequence C':4,
'BRIGHT':5,
'DARK':6,
'ZEROs for morning darks':7,
'Morning darks':8,
'CALIB short Arcs all':9,
'CALIB long Arcs Cd+Xe':10,
'CALIB DESI-CALIB-00 LEDs only':11,
'CALIB DESI-CALIB-01 LEDs only':12,
'CALIB DESI-CALIB-02 LEDs only':13,
'CALIB DESI-CALIB-03 LEDs only':14,
'LED03 flat for CTE check':15,
}

obstypes = {
'DARK':1,
'ZERO':2,
'SCIENCE':3,
'FLAT':4,
'ARC':5,
}



table_commands = {
'obstypes':"""
obstypes(
obstype TINYINT NOT NULL,
obstype_name TINYTEXT NOT NULL,
PRIMARY KEY (obstype)
)
""",

'programs':"""
programs(
program TINYINT NOT NULL,
program_name TINYTEXT NOT NULL,
PRIMARY KEY (program)
)
""",

'header':"""
header(
expid INT NOT NULL,
night INT NOT NULL,
obstype TINYINT NOT NULL,
program TINYINT NOT NULL,
time INT NOT NULL,
PRIMARY KEY (expid)
)
""",

'peramp':"""
peramp(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
cam CHAR NOT NULL,
amp CHAR NOT NULL,
readnoise FLOAT,
bias FLOAT,
cosmic_rate FLOAT)
""",

'percamera':"""
percamera(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
cam CHAR NOT NULL,
meandx FLOAT,
mindx FLOAT,
maxdx FLOAT,
meandy FLOAT,
mindy FLOAT,
maxdy FLOAT,
PRIMARY KEY (expid, spectro, cam)
)
""",

'percamera_sig':"""
percamera_sig(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
cam CHAR NOT NULL,
meanxsig FLOAT,
minxsig FLOAT,
maxxsig FLOAT,
meanysig FLOAT,
minysig FLOAT,
maxysig FLOAT,
PRIMARY KEY (expid, spectro, cam)
)
""",

'percamfiber':"""
percamfiber(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
cam CHAR NOT NULL,
fiber SMALLINT NOT NULL,
integ_raw_flux FLOAT,
median_raw_flux FLOAT,
median_raw_snr FLOAT,
PRIMARY KEY (expid, spectro, cam, fiber)
)
""",

'percamfiber_science':"""
percamfiber_science(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
cam CHAR NOT NULL,
fiber SMALLINT NOT NULL,
integ_calib_flux FLOAT,
median_calib_flux FLOAT,
median_calib_snr FLOAT,
PRIMARY KEY (expid, spectro, cam, fiber)
)
""",

'perspectro_led':"""
perspectro_led(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
b_integ_flux FLOAT,
r_integ_flux FLOAT,
z_integ_flux FLOAT,
PRIMARY KEY (expid, spectro)
)
""",

'perspectro_short_arcs':"""
perspectro_short_arcs(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
B4048 FLOAT,
B4679 FLOAT,
B4801 FLOAT,
B5087 FLOAT,
B5462 FLOAT,
R6145 FLOAT,
R6385 FLOAT,
R6404 FLOAT,
R6508 FLOAT,
R6680 FLOAT,
R6931 FLOAT,
R7034 FLOAT,
R7247 FLOAT,
Z7604 FLOAT,
Z8115 FLOAT,
Z8192 FLOAT,
Z8266 FLOAT,
Z8301 FLOAT,
Z8779 FLOAT,
Z8822 FLOAT,
Z8931 FLOAT,
PRIMARY KEY (expid, spectro)
)
""",

'perspectro_long_arcs':"""
perspectro_long_arcs(
expid INT NOT NULL,
spectro TINYINT NOT NULL,
B3612 FLOAT,                          
B4679 FLOAT,                          
B4801 FLOAT,                          
B5087 FLOAT,                          
R6440 FLOAT,                          
Z8234 FLOAT,                          
Z8283 FLOAT,                          
Z8822 FLOAT,                          
Z8955 FLOAT,                          
Z9048 FLOAT,                          
Z9165 FLOAT,                          
Z9802 FLOAT,
PRIMARY KEY (expid, spectro)
)
""",

}






def create_tables(db_con):
	db_cur = db_con.cursor()
	for table_command in table_commands.values():
		#print(table_command)
		db_cur.execute("CREATE TABLE " + table_command)
	db_con.commit()

	for name, number in programs.items():
		db_cur.execute("INSERT INTO programs VALUES ({}, '{}')".format(number, name))

	for name, number in obstypes.items():
		db_cur.execute("INSERT INTO obstypes VALUES ({}, '{}')".format(number, name))

	db_con.commit()

def get_db_connection(db_filename):
	db_con = sqlite3.connect(db_filename)
	return db_con


def insert_data(db_con, header, data_dic):
	db_cur = db_con.cursor()
	print(header)
	result = db_cur.execute("SELECT expid FROM header  WHERE expid = {}".format(header["expid"])).fetchall()
	if len(result) != 0:
		print("expid {} exists in DB. new data are not added".format(header["expid"]))
		return False

	
	insert_header_com = "INSERT INTO header VALUES ({expid}, {night}, {obstype}, {program}, {time})".format(**header)
	db_cur.execute(insert_header_com)


	for table, data in data_dic.items():
		insert_data_com = "INSERT INTO {} VALUES {}".format(table, data)
		print("data", table)
		db_cur.execute(insert_data_com)
		db_con.commit()

	return True




