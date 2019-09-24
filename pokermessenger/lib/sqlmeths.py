from contextlib import contextmanager
import sqlite3

@contextmanager
def connect(file):
    try:
        con = sqlite3.connect(file)
        yield con
        con.commit()
        con.close()
    except sqlite3.Error as err:
        yield print(err)

def safesqlexe(fun):
    def wrapper(con, *args, **kwargs):
        try:
            ret = fun(con, *args, **kwargs)
            return ret if ret is not None else True
        except sqlite3.Error as e:
            print(e)
    return wrapper

@safesqlexe
def executesql(con, *sqls):
    for sql in sqls: con.cursor().execute(sql)

@safesqlexe
def insert(con, table, **vals):
    strkeys = map(str, vals.keys())
    sql = f'''INSERT INTO {table}({', '.join(strkeys)})
          VALUES({', '.join(['?'] * len(vals))})'''
    con.cursor().execute(sql, tuple(vals.values()))
    con.commit()

@safesqlexe
def update(con, table, valsdic, wheredic):
    vals = ', '.join([f'{key}=?' for key in valsdic])
    where = ' AND '.join([f'{key}=?' for key in wheredic])
    sql = f'''UPDATE {table} SET {vals} WHERE {where}'''
    con.cursor().execute(sql, tuple(valsdic.values()) +
                              tuple(wheredic.values()))
    con.commit()

@safesqlexe
def deletefromtable(con, table, wheredic):
    where = ' AND '.join([f'{key}=?' for key in wheredic])
    sql = f'DELETE FROM {table} WHERE {where}'
    con.cursor().execute(sql, tuple(wheredic.values()))
    con.commit()
@safesqlexe
def emptytable(con, table):
    con.cursor().execute(f'DELETE FROM {table}')
    con.commit()

@safesqlexe
def getcol(con, table, colname):
    cur = con.cursor()
    cur.execute(f'SELECT {colname} FROM {table}')
    return cur.fetchall()

@safesqlexe
def getasdict(con, table, idname, idval):
    cur = con.cursor()
    cur.execute(f'PRAGMA table_info({table})')
    keys = map(lambda l: l[1], cur.fetchall())
    cur.execute(f'SELECT * FROM {table} WHERE {idname}=?', (idval,))
    vals = cur.fetchall()
    if len(vals) == 1: return dict(tuple(zip(keys, vals[0])))
    else: return {}

@safesqlexe
def getasdicts(con, table, key, value, wheredic):
    formatted = ' AND '.join([f'{wkey}=?' for wkey in wheredic])
    sql = f'SELECT {key}, {value} FROM {table} WHERE {formatted}'
    cur = con.cursor()
    cur.execute(sql, tuple(wheredic.values()))
    return dict(cur.fetchall())
