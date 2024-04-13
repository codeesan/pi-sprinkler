import sqlite3

def sqlite_to_dict(statement):
    result = []
    con = sqlite3.connect("sprinklers.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    for row in cur.execute(statement):
        print(dict(row))
        result.append(dict(row))
    con.commit()
    con.close()
    return result
    