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

def sqlite_put(table,id,statement):
    result = []
    con = sqlite3.connect("sprinklers.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(statement)
    con.commit()
    cur = con.cursor()
    select_statement = "select * from {0} where id={1}".format(table,id)
    for row in cur.execute(select_statement):
        print(dict(row))
        result.append(dict(row))
    con.commit()
    con.close()
    return result