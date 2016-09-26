#!/usr/bin/env python
#
# @filename : build.py
# @author   : Manuel A. Rodriguez (manuel.rdrs@gmail.com)
# @breif    : Simple build script to quickly bring up and tear down
#             a mariadb galera cluster, and possibly other configurations.
#
import os, getopt, sys, subprocess, json

# Docker image name via dockerfile
IMAGE_NAME = "test_mariadb"
# Official docker image name as per dockerhub
OFFICIAL_IMAGE_NAME = "mariadb:latest"
# Default port to map container to
DEFAULT_PORT = 10666
# Default password to save
PASSWORD = "pass"

# Cluster naming
CLUSTER_PREFIX = "mariadb_cluster_"

# Build docker image.
def BuildImage():
    subprocess.call(["docker", "build", "-t", IMAGE_NAME, "."])

# Delete docker image.
def DeleteImage():
    subprocess.call(["docker", "rmi", IMAGE_NAME])

# Get node ip from container.
def GetNodeIp(node_name):
    ps = subprocess.Popen(("docker", "inspect", node_name), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    ins = json.loads(out)
    ip_address = ins[0]['NetworkSettings']['IPAddress']
    return ip_address

# Start the galera cluster host.
def StartClusterHost(node_name, bind_port):
    subprocess.call([
        "docker", 
        "run", 
        "--name="+node_name, 
        "--network=bridge", 
        "-e", 
        "MYSQL_ROOT_PASSWORD="+PASSWORD, 
        "-d", 
        "-p", 
        bind_port + ":3306", 
        IMAGE_NAME, 
        "mysqld", 
        "--wsrep-new-cluster"]) 

# Start a cluster node, connecting to cluster host.
def StartClusterNode(node_name, bind_port, ip_address):
    subprocess.call([
        "docker", 
        "run", 
        "--name="+node_name, 
        "--network=bridge", 
        "-e", 
        "MYSQL_ROOT_PASSWORD="+PASSWORD, 
        "-d", 
        "-p", 
        bind_port + ":3306", 
        IMAGE_NAME, 
        "mysqld",
        "--wsrep_cluster_address=gcomm://"+ip_address]) 

# Find all containers with cluster prefix
def GetClusterContainerNames():
    ps = subprocess.Popen(("docker", "ps"), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    if len(out) == 0:
        print("Zero len docker ps")
    # Parse output
    container_names = []
    #split lines
    sp = out.splitlines();
    for line in sp:
        # split string
        fields = line.split()
        for f in fields:
            if CLUSTER_PREFIX in f:
                container_names.append(f)
    return container_names

# Start test cluster, bring up host and nodes to connect.
def StartTestCluster(num_nodes):
    # Start cluster
    print "Starting cluster host ..."
    StartClusterHost(CLUSTER_PREFIX + "host", str(DEFAULT_PORT))
    # Get cluster host ip
    ip_address = GetNodeIp(CLUSTER_PREFIX + "host")
    # Get ip of first node
    port_num = DEFAULT_PORT + 1
    print "Starting cluster nodes ..."
    for n in range(0, int(num_nodes)):
        StartClusterNode(CLUSTER_PREFIX + "node_" + str(n), str(port_num), ip_address)
        port_num += 1

# Stop already running test cluster.
def StopTestCluster():
    container_names = GetClusterContainerNames()
    if len(container_names) > 0:
        print "Stopping containers ..."
        subprocess.call(["docker", "stop"] + container_names)
        print "\nCleaning up container names ..."
        subprocess.call(["docker", "rm"] + container_names)
    else:
        print "No containers to stop."

def Usage():
    usage = """\
        --help          : print out this usage text.
        --image         : image options
                          build (build docker image (rmi))
                          delete (delete docker image (rmi))
        --start-cluster : Start test cluster, brings up host, and nodes attached.
        --stop-cluster  : Stop running test cluster.
    """
    print usage

if __name__ == '__main__':
    # Get opts
    try:
        long_args = ["help", "image", "start-cluster", "stop-cluster"]
        opts, args = getopt.getopt(sys.argv[1:], "be:he:s:c:r:", long_args)
        print "Opts : ", opts
        print "Args : ", args
    except getopt.GetoptError as err:
        print "opt err: ", str(err)
        Usage()
        sys.exit(2)

    # Check options
    for o, a in opts:
        if o in ("--help"):
            Usage()
        if o in ("--image"):
            for a in args:
                if a in ("build"):
                    BuildImage()
                if a in ("delete"):
                    DeleteImage()
        if o in ("--start-cluster"):
            # Look for number of nodes
            if len(args) > 0:
                StartTestCluster(args[0])
            else:
                print "Define number of nodes"

        if o in ("--stop-cluster"):
            StopTestCluster()

