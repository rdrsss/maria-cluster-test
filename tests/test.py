#!/usr/bin/env python
#
# @filename : test.py
# @author   : Manuel A. Rodriguez (manuel.rdrs@gmail.com)
# @breif    : Test script to access a given cluster and test it.
import os, getopt, sys

import MySQLdb, _mysql_exceptions

MYSQL_USER = 'test_user'
MYSQL_PASS = 'beefcake'

MAXSCALE_HOST = '0.0.0.0'
MAXSCALE_PORT = 10101

TEST_DB = 'test_db'


def create_database():
    try:
        # Create connection
        conn = MySQLdb.connect(
                host=MAXSCALE_HOST, 
                port=MAXSCALE_PORT,
                user=MYSQL_USER,
                passwd=MYSQL_PASS)
        print 'Creating test database'
        c = conn.cursor()
        c.execute('CREATE DATABASE %s;' % TEST_DB)
        c.close()
        conn.close()
    except _mysql_exceptions.OperationalError as err:
        print 'Create Database exception : ' + str(err)

def drop_database():
    try:
        # Create connection
        conn = MySQLdb.connect(
                host=MAXSCALE_HOST, 
                port=MAXSCALE_PORT,
                user=MYSQL_USER,
                passwd=MYSQL_PASS)
        print 'Deleting test database'
        c = conn.cursor()
        c.execute('DROP DATABASE %s;' % TEST_DB)
        c.close()
        conn.close()
    except _mysql_exceptions.OperationalError as err:
        print 'Drop Database exception : ' + str(err)

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
            drop_database()

