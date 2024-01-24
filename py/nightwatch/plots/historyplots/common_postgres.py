import psycopg2


def get_db_connection():
	db_con = psycopg2.connect( host="localhost", database="dbtest1", user="otto", password="pw-9119")
	return db_con

led_programs = {
'CALIB DESI-CALIB-00 LEDs only',
'CALIB DESI-CALIB-01 LEDs only',
'CALIB DESI-CALIB-02 LEDs only',
'CALIB DESI-CALIB-03 LEDs only',
'LED03 flat for CTE check',
}

long_arcs_programs = {
'CALIB long Arcs Cd+Xe',
#'CALIB long Arcs all',
}

short_arcs_programs = {
'CALIB short Arcs all',
}

other_programs = {
'CALIB ZEROs for nightly bias',
'CALIB Dark 5min',
'ZEROs for dark sequence C',
'DARK 1200.0s for dark sequence C',
'BRIGHT',
'DARK',
'ZEROs for morning darks',
'Morning darks',
'ZEROs to stabilize CCDs',
#'tile 80011, donut memory leak test',
}


obstypes = {
'DARK',
'ZERO',
'SCIENCE',
'FLAT',
'ARC',
#'OTHER'
}

programs =  other_programs | long_arcs_programs | short_arcs_programs | led_programs

