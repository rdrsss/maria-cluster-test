#!/usr/bin/env python
#
# @filename : test.py
# @author   : Manuel A. Rodriguez (manuel.rdrs@gmail.com)
# @breif    : Test script to access a given cluster and test it.
import os, getopt, sys

import MySQLdb



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


