import sqlite3
from sqlite3 import Error

databaseFile = './bars.db'

createStatement = """ CREATE TABLE IF NOT EXISTS bars (
                                        id integer PRIMARY KEY,
                                        chipName text NOT NULL,
                                        groupId integer NOT NULL,
                                        position integer NOT NULL
                                    ); """



def createConnection():
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(databaseFile)
        print(sqlite3.version)
        return conn
    except Error as e:
        print(e)

    return None


def initDatabase(dbConnector, SQLstatement):
    try:
        c = dbConnector.cursor()
        c.execute(SQLstatement)
    except Error as e:
        print(e)


def addBar(dbConnector, bar):
    sql = """INSERT INTO bars(chipName, groupId, position)
    VALUES(?,?,?)"""
    cur = dbConnector.cursor()
    cur.execute(sql, bar)
    dbConnector.commit()
    return cur.lastrowid

def updateBar(dbConnector, chipName, groupId, position):
    sql = """UPDATE bars
    SET groupId = ?,
        position = ?
    WHERE chipName = ?
    """
    cur = dbConnector.cursor()
    cur.execute(sql, (groupId, position, chipName))
    dbConnector.commit()

def deleteAllBars(dbConnector):
    sql = """DELETE FROM bars"""
    cur = dbConnector.cursor()
    cur.execute(sql)
    dbConnector.commit()


def retrieveBars(dbConnector):
    sql = """SELECT * FROM bars"""
    dbConnector.row_factory = sqlite3.Row
    cur = dbConnector.cursor()
    cur.execute(sql)
    bars = cur.fetchall()
    return bars

def retrieveBar(dbConnector, chipName):
    sql = """SELECT * FROM bars WHERE chipName = ?"""
    dbConnector.row_factory = sqlite3.Row
    cur = dbConnector.cursor()
    cur.execute(sql, (chipName,))
    bar = cur.fetchall()
    return bar

def retrieveGroup(dbConnector, groupId):
    sql = """SELECT * FROM bars WHERE groupId = ?"""
    dbConnector.row_factory = sqlite3.Row
    cur = dbConnector.cursor()
    cur.execute(sql, (groupId,))
    group = cur.fetchall()
    return group

def getMaxGroupId(dbConnector) -> int:
    sql = """SELECT MAX(groupId) FROM bars"""
    cur = dbConnector.cursor()
    cur.execute(sql)
    maxGroupId = cur.fetchall()
    maxGroupId = maxGroupId[0][0]
    if maxGroupId is None:
        maxGroupId = 0
    return maxGroupId

def getMaxPositionId(dbConnector, groupId) -> int:
    sql = """SELECT MAX(position) FROM bars WHERE groupId = ?"""
    cur = dbConnector.cursor()
    cur.execute(sql, (groupId,))
    maxPos = cur.fetchall()
    maxPos = maxPos[0][0]
    if maxPos is None:
        maxPos = 0
    return maxPos


def deleteChipRecord(dbConnector, chipName: str):
    with dbConnector:
        sql = """DELETE FROM bars WHERE chipName = ?"""
        cur = dbConnector.cursor()
        cur.execute(sql, (chipName,))
        dbConnector.commit()



def init():
    conn = createConnection()
    initDatabase(conn, createStatement)
    conn.close()


def testAddBars():
    conn = createConnection()
    with conn:
        bar0 = ('esp1', 0, 0)
        bar1 = ('esp2', 0, 1)
        bar2 = ('esp3', 0, 2)
        bar3 = ('esp4', 1, 0)
        bar4 = ('esp5', 1, 1)
        bar5 = ('esp6', 1, 2)
        addBar(conn, bar0)
        addBar(conn, bar1)
        addBar(conn, bar2)
        addBar(conn, bar3)
        addBar(conn, bar4)
        addBar(conn, bar5)

def testRetrieveBars():
    conn = createConnection()
    with conn:
        result = retrieveBars(conn)
        return result
