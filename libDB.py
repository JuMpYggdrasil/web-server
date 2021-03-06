import sqlite3
from sqlite3 import Error
import time
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
import json

maindatabase = "/home/pi/Sensors_Database/sensorData.db"

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("SQLite is connected")
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
        
def select_sensors(conn,qrol):
    # sql = 'SELECT '+qrol+' FROM sensors ORDER BY timeStamp DESC LIMIT 1500'
    sql = 'SELECT '+qrol+' FROM sensors WHERE timeStamp BETWEEN datetime("now","-24 hours") and datetime("now","+24 hours")';
    # sql = 'SELECT '+qrol+' FROM sensors WHERE timeStamp BETWEEN date("now") and date("now","+1 day")';
    # sql = 'SELECT '+qrol+' FROM sensors'
    cur = conn.cursor()
    cur.execute(sql)
    selectedData = cur.fetchall()
    conn.commit()
    return selectedData

def delete_sensors(conn, timeStamp):
    """
    Delete a sensors by sensors timeStamp
    :param conn:  Connection to the SQLite database
    :param timeStamp: timeStamp of the sensors
    :return:
    """
    sql = 'DELETE FROM sensors WHERE timeStamp<=?'
    cur = conn.cursor()
    cur.execute(sql, (timeStamp,))
    conn.commit()

def delete_all_sensors(conn):
    """
    Delete all rows in the sensors table
    :param conn: Connection to the SQLite database
    :return:
    """
    sql = 'DELETE FROM sensors'# DELETE FROM sensors WHERE id='1';
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def logDB(name,temp,humid,value,staus) :
    sql_create_sensors_table = """ CREATE TABLE IF NOT EXISTS sensors (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT NOT NULL,
                                    temp TEXT,
                                    humid TEXT,
                                    value TEXT,
                                    staus TEXT,
                                    timeStamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                ); """
    sqlite_insert_with_param = """INSERT INTO sensors (
                                    name,temp,humid,value,staus)
                                    VALUES (?, ?, ?, ?, ?)
                                ;"""
    try:
        sqliteConnection = create_connection(maindatabase)
        create_table(sqliteConnection, sql_create_sensors_table)
        dateTimeValue = datetime.now()
        cursor = sqliteConnection.cursor()
        data_tuple = (name,temp,humid,value,staus)
        #data_tuple = (name,temp,humid,value,staus,dateTimeValue)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        
        sqliteConnection.commit()
        print("Python Variables inserted successfully into sensors table")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("SQLite connection is closed")

def clearOldDB() :
    
    try:
        sqliteConnection = create_connection(maindatabase)
        last_2_month = datetime.now() - relativedelta(months=2)
        #last_month = datetime.now() - relativedelta(months=1)
        #last_minutes = datetime.now() - relativedelta(minutes=10)
        cursor = sqliteConnection.cursor()
        data_tuple=(last_2_month)
        #data_tuple=(last_minutes)
        delete_sensors(sqliteConnection,data_tuple)
        
        sqliteConnection.commit()
        print("SQLite delete old data")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to delete old data", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("SQLite connection is closed")
            
def queryDB(qroll) :
    rows = []
    try:
        sqliteConnection = create_connection(maindatabase)
        cursor = sqliteConnection.cursor()
        rowsDummy = select_sensors(sqliteConnection,qroll)
        rows = [item for t in rowsDummy for item in t]
        rows.reverse()
        #print(rows)    
        #print(type(rows))
        sqliteConnection.commit()
        print("SQLite query data")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to select_sensors from sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("SQLite connection is closed")
            return rows
    return rows

def main():
    ## test add data into DB , create table if not exist
    logDB("fl0","35.2","12.4","DHT","true")
    # logDB("fl0","37.2","18.4","DHT","true")

    ## test clear old data in DB
    # clearOldDB()

    ## display humid list
    x = queryDB("humid")
    print(x)

if __name__ == '__main__':
    main()