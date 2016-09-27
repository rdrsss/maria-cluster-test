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
CLUSTER_NODE = "node_"
CLUSTER_HOST = "host"

# External MYSQL settings
DEFAULT_DB          = "test_db"
DEFAULT_USER        = "test_user"
DEFAULT_USER_PASS   = "testpass"

# Build docker image.
def BuildImage():
    subprocess.call(["docker", "build", "-t", IMAGE_NAME, "."])

# Delete docker image.
def DeleteImage():
    subprocess.call(["docker", "rmi", IMAGE_NAME])

def GetNodeExposedPort(node_name):
    ps = subprocess.Popen(("docker", "inspect", node_name), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    ins = json.loads(out)
    port = ins[0]['NetworkSettings']['Ports']['3306/tcp'][0]['HostPort']
    return port

# Get node ip from container.
def GetNodeIp(node_name):
    ps = subprocess.Popen(("docker", "inspect", node_name), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    ins = json.loads(out)
    ip_address = ins[0]['NetworkSettings']['IPAddress']
    return ip_address

# Start the galera cluster host.
def StartClusterHost(node_name, bind_port):
    ps = subprocess.Popen([
        "docker", 
        "run", 
        "--name="+node_name, 
        "--network=bridge", 
        "-e", 
        "MYSQL_ROOT_PASSWORD=" + PASSWORD, 
        "-e",
        "MYSQL_DATABASE=" + DEFAULT_DB,
        "-e"
        "MYSQL_USER=" + DEFAULT_USER,
        "-e",
        "MYSQL_PASSWORD=" + DEFAULT_USER_PASS,
        "-d", 
        "-p", 
        bind_port + ":3306", 
        IMAGE_NAME, 
        "mysqld", 
        "--wsrep-new-cluster"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE) 

    out, err = ps.communicate()
    if(len(str(err)) > 0):
        print "Error starting cluster host : " + err
        return False
    if(len(str(out))>0): 
        print "\t Container id : " + out
    return True

# Start a cluster node, connecting to cluster host.
def StartClusterNode(node_name, bind_port, ip_address):
    subprocess.call([
        "docker", 
        "run", 
        "--name="+node_name, 
        "--network=bridge", 
        "-d", 
        "-p", 
        bind_port + ":3306", 
        IMAGE_NAME, 
        "mysqld",
        "--wsrep_cluster_address=gcomm://"+ip_address]) 
    return True

# Parse containers from string buffer.
def ParseContainerNames(strbuf):
    if len(strbuf) == 0:
        print("Zero len docker ps")
    else:
        # Parse output
        container_names = []
        #split lines
        sp = strbuf.splitlines();
        for line in sp:
            # split string
            fields = line.split()
            for f in fields:
                if CLUSTER_PREFIX in f:
                    container_names.append(f)
        return container_names
    return []

# Find all containers with cluster prefix
def GetClusterContainerNames():
    ps = subprocess.Popen(("docker", "ps"), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    return ParseContainerNames(out)
    
# Cleanup possible orphaned contianers
def CleanupOrphaned():
    ps = subprocess.Popen(("docker", "ps", "-a"), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    names = ParseContainerNames(out)
    if len(names) > 0:
        print "Cleaning up container names ..."
        for c in names:
            subprocess.call(["docker", "rm"] + c)
    else:
        print "No containers found"

# Start test cluster, bring up host and nodes to connect.
def StartTestCluster(num_nodes):
    # Start cluster
    print "Starting cluster host ..."
    s = StartClusterHost(CLUSTER_PREFIX + CLUSTER_HOST, str(DEFAULT_PORT))
    if s:
        # Get cluster host ip
        ip_address = GetNodeIp(CLUSTER_PREFIX + CLUSTER_HOST)
        # Get ip of first node
        port_num = DEFAULT_PORT + 1
        print "Starting cluster nodes ..."
        for n in range(0, int(num_nodes)):
            StartClusterNode(CLUSTER_PREFIX + CLUSTER_NODE + str(n), str(port_num), ip_address)
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

# Add node to existing cluster
def AddNode():
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine number to increment on
        print containers
        highest_num = 0
        for n in containers:
            if CLUSTER_PREFIX + CLUSTER_NODE in n:
                #get number
                a = n.strip(CLUSTER_PREFIX + CLUSTER_NODE)
                if a > highest_num:
                    highest_num = a
        # Get port from highest container
        port = GetNodeExposedPort(CLUSTER_PREFIX + CLUSTER_NODE + str(highest_num))
        print "exposed port : " + port
        # Get cluster host ip
        ip_address = GetNodeIp(CLUSTER_PREFIX + CLUSTER_HOST)
        # Add new node
        new_node_number = str(int(highest_num)+1)
        new_node_port = str(int(port)+1)
        print "adding node : " + new_node_number + " on port : " + new_node_port
        StartClusterNode(CLUSTER_PREFIX + CLUSTER_NODE + new_node_number, new_node_port, ip_address)
    else:
        print "No cluster running"

# Remove node from existing cluster
def RemoveNode():
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine nubmer to decrement on
        print containers
    else:
        print "No cluster running"

# Remove node from existing cluster
def RemoveNamedNode():
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine nubmer to decrement on
        print containers
    else:
        print "No cluster running"

# Display script usage
def Usage():
    usage = """\
        --help                  : Print out this usage text.
        --image                 : Image options.
                                  [build] (build docker image (rmi)).
                                  [delete] (delete docker image (rmi)).
        --start-cluster         : Start test cluster, brings up host, and nodes attached.
        --stop-cluster          : Stop running test cluster.
        --cleanup-containers    : Cleanup orphaned containers (rm).
        --add-node              : Add node to existing cluster.
        --remove-node           : Remove node from existing cluster.
        --remove-named-node     : Remove a node via it's container name.
    """
    print usage

# Main
if __name__ == '__main__':
    # Get opts
    try:
        long_args = ["help", "image", "start-cluster", "stop-cluster", "cleanup-containers", "add-node", "remove-node", "remove-named-node"]
        opts, args = getopt.getopt(sys.argv[1:], "be:he:s:c:r:", long_args)
       # print "Opts : ", opts
       # print "Args : ", args
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
                elif a in ("delete"):
                    DeleteImage()
                else:
                    print "Provide arg, [build] or [delete]"
        if o in ("--start-cluster"):
            # Look for number of nodes
            if len(args) > 0:
                StartTestCluster(args[0])
            else:
                print "Define number of nodes"
        if o in ("--stop-cluster"):
            StopTestCluster()
        if o in ("--cleanup-containers"):
            CleanupOrphaned()
        if o in ("--add-node"):
            AddNode()
        if o in ("--remove-node"):
            RemoveNode()
        if o in ("--remove-named-node"):
            RemoveNamedNode()


