import psycopg2

programs = [
'CALIB ZEROs for nightly bias',
'CALIB Dark 5min',
'ZEROs for dark sequence C',
'DARK 1200.0s for dark sequence C',
'BRIGHT',
'DARK',
'ZEROs for morning darks',
'Morning darks',
'CALIB short Arcs all',
'CALIB long Arcs Cd+Xe',
'CALIB DESI-CALIB-00 LEDs only',
'CALIB DESI-CALIB-01 LEDs only',
'CALIB DESI-CALIB-02 LEDs only',
'CALIB DESI-CALIB-03 LEDs only',
'LED03 flat for CTE check',
'ZEROs to stabilize CCDs',
'CALIB long Arcs all',
#'tile 80011, donut memory leak test',
]

obstypes = [
'DARK',
'ZERO',
'SCIENCE',
'FLAT',
'ARC',
#'OTHER'
]

table_commands = {


'header':"""
CREATE TABLE nw_header(
expid INT NOT NULL,
night INT NOT NULL,
obstype en_program NOT NULL,
program en_obstype NOT NULL,
time INT NOT NULL,
PRIMARY KEY (expid)
);
CREATE INDEX expid_index ON nw_header (expid);
""",

'peramp':"""
CREATE TABLE nw_peramp(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
cam CHAR NOT NULL,
amp CHAR NOT NULL,
readnoise FLOAT,
bias FLOAT,
cosmic_rate FLOAT)
""",

'percamera':"""
CREATE TABLE nw_percamera(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
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
CREATE TABLE nw_percamera_sig(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
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

#'percamfiber':"""
#CREATE TABLE nw_percamfiber(
#expid INT NOT NULL,
#spectro SMALLINT NOT NULL,
#cam CHAR NOT NULL,
#fiber SMALLINT NOT NULL,
#integ_raw_flux FLOAT,
#median_raw_flux FLOAT,
#median_raw_snr FLOAT,
#PRIMARY KEY (expid, spectro, cam, fiber)
#)
#""",

#'percamfiber_science':"""
#CREATE TABLE nw_percamfiber_science(
#expid INT NOT NULL,
#spectro SMALLINT NOT NULL,
#cam CHAR NOT NULL,
#fiber SMALLINT NOT NULL,
#integ_calib_flux FLOAT,
#median_calib_flux FLOAT,
#median_calib_snr FLOAT,
#PRIMARY KEY (expid, spectro, cam, fiber)
#)
#""",

'perspectro_led':"""
CREATE TABLE nw_perspectro_led(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
b_integ_flux FLOAT,
r_integ_flux FLOAT,
z_integ_flux FLOAT,
PRIMARY KEY (expid, spectro)
)
""",

'perspectro_short_arcs':"""
CREATE TABLE nw_perspectro_short_arcs(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
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
CREATE TABLE nw_perspectro_long_arcs(
expid INT NOT NULL,
spectro SMALLINT NOT NULL,
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

enum_command = """
CREATE TYPE en_obstype AS ENUM ({0});
CREATE TYPE en_program AS ENUM ({1});
""".format(', '.join(['\''+n+'\'' for n in obstypes]), ', '.join(['\''+n+'\'' for n in programs]))

def get_db_connection():
	db_con = psycopg2.connect( host="localhost", database="dbtest1", user="otto", password="pw-9119")
	return db_con


def create_tables(db_con):
	db_cur = db_con.cursor()
	print(enum_command)
	db_cur.execute(enum_command)
	for table_command in table_commands.values():
		print(table_command)
		db_cur.execute(table_command)
	db_cur.close()
	db_con.commit()

db_con = get_db_connection()

create_tables(db_con)

db_con.close()



