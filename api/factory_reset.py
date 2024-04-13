import sqlite3
# -- pins definition

# CREATE TABLE pins (
# 	pi_version INTEGER NOT NULL,
# 	pin INTEGER NOT NULL,
# 	bcm INTEGER NOT NULL,
# 	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
# );
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
con = sqlite3.connect("sprinkers.db")
cur = con.cursor()
cur.executemany("INSERT INTO pins(pi_version,pin,bcm) VALUES(?, ?, ?)", pin_data)

con.commit()
con.close()