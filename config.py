#pip install mysql-connector-python

import os
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict

class Database(object):

    def __init__(self, config=None, username=None, password=None, host=None, port=None, db_name=None):
        if db_name is None:
            db_name = os.getenv('MYSQL_DATABASE') or 'pregnancy_harmony'
        if username is None:
            username = os.getenv('MYSQL_USERNAME') or 'root'
        if password is None:
            password = os.getenv('MYSQL_PASSWORD') or ''

        if host is None:
            host = os.getenv('MYSQL_HOST') or 'localhost'
        if port is None:
            port = os.getenv('MYSQL_PORT') or '3306'

        self.params_dict = {
            "host": host,
            "database": db_name,
            "user": username,
            "password": password,
            "port": port
        }

    def connect(self):
        """ Connect to the MySQL database server """
        conn = None
        try:
            # connect to the MySQL server
            conn = mysql.connector.connect(**self.params_dict)

        except (Exception, mysql.connector.Error) as error:
            raise error
        return conn

    def single_insert(self, insert_req):
        """ Execute a single INSERT request """
        conn = None
        cursor = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(insert_req)
            conn.commit()
        except (Exception, mysql.connector.Error) as error:
            if conn is not None:
                conn.rollback()
            raise error
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def execute(self, req_query):
        """ Execute a single request """
        """ for Update/Delete request """
        conn = None
        cursor = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(req_query)
            conn.commit()
        except (Exception, mysql.connector.Error) as error:
            if conn is not None:
                conn.rollback()
            raise error
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    def executeAndReturnId(self, req_query):
        """ Execute a single request and return id"""
        """ for insert request """
        conn = None
        cursor = None
        try:
            conn = self.connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(req_query)
            dt = cursor.lastrowid
            conn.commit()
            return dt
        except (Exception, mysql.connector.Error) as error:
            if conn is not None:
                conn.rollback()
            raise error
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
                
    def fetchone(self, get_req):
        conn=None
        cur=None
        try:
            conn = self.connect()
            cur = conn.cursor(dictionary=True)
            cur.execute(get_req)
            data = cur.fetchone()
            return data
        except (Exception, mysql.connector.Error) as error:
            raise error
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()

    def fetchall(self, get_req):
        conn = None
        cur = None
        try:
            conn = self.connect()
            cur = conn.cursor(dictionary=True)
            cur.execute(get_req)
            data = cur.fetchall()
            return data
        except (Exception, mysql.connector.Error) as error:
            raise error
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()
