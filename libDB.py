import sqlite3
from sqlite3 import Error
import time
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
import json

database = "/home/pi/Sensors_Database/sensorData.db"
			
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
	sql = 'SELECT '+qrol+' FROM sensors WHERE timeStamp BETWEEN date(\'now\',\'-1 day\') and date(\'now\')';
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
    sql = 'DELETE FROM sensors'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def logDB(name,temp,humid,value,staus) :
	sql_create_sensors_table = """ CREATE TABLE IF NOT EXISTS sensors (
									id INTEGER PRIMARY KEY,
									name TEXT NOT NULL,
									temp TEXT,
									humid TEXT,
									value TEXT,
									staus TEXT,
									timeStamp DATETIME
								); """
	sqlite_insert_with_param = """INSERT INTO sensors (
									name,temp,humid,value,staus,timeStamp)
									VALUES (?, ?, ?, ?, ?, ?)
								;"""
	try:
		sqliteConnection = create_connection(database)
		create_table(sqliteConnection, sql_create_sensors_table)
		dateTimeValue = datetime.now()
		cursor = sqliteConnection.cursor()
		data_tuple = (name,temp,humid,value,staus,dateTimeValue)
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
		sqliteConnection = create_connection(database)
		last_month = datetime.now() - relativedelta(months=1)
		#last_minutes = datetime.now() - relativedelta(minutes=10)
		cursor = sqliteConnection.cursor()
		data_tuple=(last_month)
		#data_tuple=(last_minutes)
		delete_sensors(sqliteConnection,data_tuple)
		
		sqliteConnection.commit()
		print("SQLite delete old data")
		cursor.close()

	except sqlite3.Error as error:
		print("Failed to insert Python variable into sqlite table", error)
	finally:
		if (sqliteConnection):
			sqliteConnection.close()
			print("SQLite connection is closed")
			
def queryDB(qroll) :
	rows = []
	try:
		sqliteConnection = create_connection(database)
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
	# logDB("fl0","35.2","12.4","DHT","true")
	# logDB("fl0","37.2","18.4","DHT","true")
	clearOldDB()
	#x = queryDB("humid")

if __name__ == '__main__':
	main()