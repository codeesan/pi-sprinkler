import sqlite3

def factory_reset(verify:str):
	if (verify != "I want to reset"):
		return(403)
		exit()
	else:
		pin_data = [(4,3,2),
			(4,5,3),
			(4,7,4),
			(4,11,17),
			(4,13,27),
			(4,15,22),
			(4,19,10),
			(4,21,9),
			(4,23,11),
			(4,29,5),
			(4,31,6),
			(4,33,13),
			(4,35,19),
			(4,37,26),
			(4,8,14),
			(4,10,15),
			(4,12,18),
			(4,16,23),
			(4,18,24),
			(4,22,25),
			(4,24,8),
			(4,26,7),
			(4,32,12),
			(4,36,16),
			(4,38,20),
			(4,40,21),
		]
		con = sqlite3.connect("sprinklers.db")
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS pins")
		con.commit()
		cur.execute("CREATE TABLE pins (pi_version INTEGER NOT NULL, pin INTEGER NOT NULL, bcm INTEGER NOT NULL, id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT);")
		con.commit()
		cur.executemany("INSERT INTO pins(pi_version,pin,bcm) VALUES(?, ?, ?)", pin_data)
		con.commit()
		con.close()

		valve_data = [
			('front north','small front yard',3),
			('front south 1','bottom of big yard',5),
			('front south 2','middle of big yard',7),
			('front south 3','top of big yard',11),
			('front planter','Planter',13),
			('back yard 1','close to patio',15),

		]
		con = sqlite3.connect("sprinklers.db")
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS valves")
		con.commit()
		cur.execute("CREATE TABLE valves (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, pin INTEGER NOT NULL);")
		con.commit()
		cur.executemany("INSERT INTO valves(name,description,pin) VALUES(?, ?, ?)", valve_data)

		con.commit()
		con.close()


		zone_name_data = [
			('front yard', 'Lawns in the front yard'),
			('front garden', 'flowers and shrubs in the front yard'),
			
		]
		con = sqlite3.connect("sprinklers.db")
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS zone_names")
		con.commit()
		cur.execute("CREATE TABLE zone_names (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT);")
		con.commit()
		cur.executemany("INSERT INTO zone_names(name,description) VALUES(?, ?)", zone_name_data)

		con.commit()
		con.close()

		zone_data = [
			(1,1),
			(1,2),
			(1,3),
			(1,4),
			(2,5),
		]

		con = sqlite3.connect("sprinklers.db")
		cur = con.cursor()
		cur.execute("DROP TABLE IF EXISTS zones")
		con.commit()
		cur.execute("CREATE TABLE zones (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, zone_id INTEGER NOT NULL, valve INTEGER NOT NULL);")
		con.commit()
		cur.executemany("INSERT INTO zones(zone_id,valve) VALUES(?, ?)", zone_data)

		con.commit()
		con.close()

		return(200)