#!/usr/bin/env python
import os, getopt, sys, subprocess, json

IMAGE_NAME = "test_mariadb"
OFFICIAL_IMAGE_NAME = "mariadb:latest"
PASSWORD = "pass"

NODE_0 = "mariadb_node_0"
NODE_1 = "mariadb_node_1"
NODE_2 = "mariadb_node_2"

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

def start_test_cluster():
    # Start cluster
    subprocess.call(["docker", "run", "--name="+NODE_0 ,"--network=bridge", "-d", "-p", "10666:3306", IMAGE_NAME, "mysqld","--wsrep-new-cluster"]) 
    #docker inspect mariadb_node_0 | grep IPAddress | cut -d '"' -f 4
    # Get ip of first node
    ps = subprocess.Popen(("docker", "inspect", NODE_0), stdout=subprocess.PIPE)
    out, err = ps.communicate()

    ins = json.loads(out)
    ip_address = ins[0]['NetworkSettings']['IPAddress']
    subprocess.call(["docker", "run", "--name="+NODE_1 ,"--network=bridge", "-d", "-p", "10667:3306", IMAGE_NAME, "mysqld","--wsrep_cluster_address=gcomm://"+ip_address]) 
    subprocess.call(["docker", "run", "--name="+NODE_2 ,"--network=bridge", "-d", "-p", "10668:3306", IMAGE_NAME, "mysqld","--wsrep_cluster_address=gcomm://"+ip_address]) 

def stop_test_cluster():
    subprocess.call(["docker", "stop", NODE_0, NODE_1, NODE_2])
    subprocess.call(["docker", "rm", NODE_0, NODE_1, NODE_2])

def usage():
    print "usage"

if __name__ == '__main__':
    # Get opts
    try:
        long_args = ["help", "image", "start-cluster", "stop-cluster", "add-node", "build-default"]
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
        if o in ("--start-cluster"):
            start_test_cluster()
        if o in ("--stop-cluster"):
            stop_test_cluster()
