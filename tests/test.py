#!/usr/bin/env python
#
# @filename : test.py
# @author   : Manuel A. Rodriguez (manuel.rdrs@gmail.com)
# @breif    : Test script to access a given cluster and test it.
import os, getopt, sys, time

import MySQLdb, _mysql_exceptions

MYSQL_USER = 'test_user'
MYSQL_PASS = 'beefcake'

MAXSCALE_HOST = '0.0.0.0'
MAXSCALE_PORT = 10101

TEST_DB = 'test_db'
TABLE_ACCOUNTS = 'test_accounts'

def execute_statement(statement):
        # Create connection
        conn = MySQLdb.connect(
                host=MAXSCALE_HOST, 
                port=MAXSCALE_PORT,
                user=MYSQL_USER,
                passwd=MYSQL_PASS)
        c = conn.cursor()
        c.execute(statement)
        c.close()
        conn.close()

def create_database():
    try:
        print 'Creating test database'
        execute_statement('CREATE DATABASE %s;' % TEST_DB)
    except _mysql_exceptions.OperationalError as err:
        print 'Create database exception : ' + str(err)
    except _mysql_exceptions.ProgrammingError as err:
        print 'Create database exception : ' + str(err)

def create_table():
    try:
        print 'Creating table'
        statement = '''
            USE %s;
            CREATE TABLE %s (
                AccountID int,
                Name varchar(255));
            ''' % (TEST_DB, TABLE_ACCOUNTS)
        execute_statement(statement)
    except _mysql_exceptions.OperationalError as err:
        print 'Create table exception : ' + str(err)

def create_entries():
    try:
        print 'Creating entries'
        for x in range (0, 100):
            statement = '''
                USE %s;
                INSERT INTO %s 
                VALUES ('%d', '%s');
                ''' % (TEST_DB, TABLE_ACCOUNTS, x, 'testname')
            execute_statement(statement)
    except _mysql_exceptions.OperationalError as err:
        print 'Create entries exception : ' + str(err)

def drop_database():
    try:
        print 'Delete test database'
        execute_statement('DROP DATABASE %s;' % TEST_DB)
    except _mysql_exceptions.OperationalError as err:
        print 'Drop database exception : ' + str(err)

def usage():
    print "usage"

# Main
if __name__=='__main__':
    # Get opts
    try:
        long_args = [
                "help",
                "run"
                ]
        opts, args = getopt.getopt(sys.argv[1:], "be:he:s:c:r:", long_args)
        print "Opts : ", opts
        print "Args : ", args
    except getopt.GetoptError as err:
        print "opt err: ", str(err)
        usage()
        sys.exit(2)
    # Check options
    for o, a in opts:
        if o in ("--help"):
            usage()
        if o in ("--run"):
            create_database()
            # run tests here
            create_table()
            create_entries()
#            time.sleep(5)
            drop_database()

