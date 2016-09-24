#!/usr/bin/env python
import os, getopt, sys, subprocess

IMAGE_NAME = "test_mariadb"
OFFICIAL_IMAGE_NAME = "mariadb:latest"
PASSWORD = "pass"

def build_image():
    subprocess.call(["docker", "build", "-t", IMAGE_NAME, "."])

def delete_image():
    subprocess.call(["docker", "rmi", IMAGE_NAME])

def start_cluster():
    # Run each node on the same network so instances can connect to one another
    # Start cluster node
    subprocess.call(["docker", "run", "--network=bridge", "-d", "-p", "10666:3306", IMAGE_NAME, "mysqld","--wsrep-new-cluster"]) 

def add_node():
    # Add node to default cluster
    subprocess.call(["docker", "run", "--network=bridge", "-d", "-p", "10667:3306", IMAGE_NAME, "mysqld","--wsrep_cluster_address=gcomm://172.17.0.2:3306"]) 

def build_test_cluster():
    subprocess.call(["docker", "run", "--name=maria_cluster_host" ,"--network=bridge", "-d", "-p", "10666:3306", IMAGE_NAME, "mysqld","--wsrep-new-cluster"]) 
    subprocess.call(["docker", "run", "--network=bridge", "-d", "-p", "10667:3306", IMAGE_NAME, "mysqld","--wsrep_cluster_address=gcomm://maria_cluster_host:3306"]) 

def usage():
    print "usage"

if __name__ == '__main__':
    # Get opts
    try:
        long_args = ["help", "image", "start_cluster", "add_node", "build_default"]
        opts, args = getopt.getopt(sys.argv[1:], "be:he:s:c:r:", long_args)
        print "Opts : ", opts
        print "Args : ", args
    except getopt.GetoptError as err:
        print "opt err: ", str(err)
        usage()
        sys.exit(2)

    # Check options
    for o, a in opts:
        if o in ("--image"):
            for a in args:
                if a in ("build"):
                    build_image()
                if a in ("delete"):
                    delete_image()
        if o in ("--start_cluster"):
            start_cluster()
        if o in ("--build_default"):
            build_test_cluster()
