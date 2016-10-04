#!/usr/bin/env python
#
# @filename : build.py
# @author   : Manuel A. Rodriguez (manuel.rdrs@gmail.com)
# @breif    : Simple build script to quickly bring up and tear down
#             a mariadb galera cluster, and possibly other configurations.
#
import os, getopt, sys, subprocess, json, time, ConfigParser

# Docker image name via dockerfile
IMAGE_NAME = "test_mariadb"
PROXY_IMAGE_NAME = "test_maxscale"
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
PROXY = "max_scale"

# MaxScale
MAXSCALE_CFG = "maxscale/maxscale.cnf"

# External MYSQL settings
DEFAULT_DB          = "test_db"
DEFAULT_USER        = "test_user"
DEFAULT_USER_PASS   = "testpass"

# Build docker image.
def build_maria_image():
    # Build mariadb image
    print "Building mariadb image ..."
    os.chdir("mariadb")
    subprocess.call(["docker", "build", "-t", IMAGE_NAME, "."])
    os.chdir("..")
    print "done."

def build_maxscale_image():
    print "Building maxscale image ..."
    os.chdir("maxscale")
    subprocess.call(["docker", "build", "-t", PROXY_IMAGE_NAME, "."])
    os.chdir("..")
    print "done."

# Delete docker image.
def delete_image():
    subprocess.call(["docker", "rmi", IMAGE_NAME])

def get_node_exposed_port(node_name):
    ps = subprocess.Popen(("docker", "inspect", node_name), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    ins = json.loads(out)
    port = ins[0]['NetworkSettings']['Ports']['3306/tcp'][0]['HostPort']
    return port

# Get node ip from container.
def get_node_ip(node_name):
    ps = subprocess.Popen(("docker", "inspect", node_name), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    ins = json.loads(out)
    ip_address = ins[0]['NetworkSettings']['IPAddress']
    return ip_address

# Start proxy node.
def start_proxy():
    print "Starting proxy service"
    names = GetClusterContainerNames()
    # Make sure cluster is running
    if not any(CLUSTER_PREFIX+CLUSTER_HOST in n for n in names):
        print "No cluster running, no cluster host found"
        return
    # Check if proxy instance exists
    if any(CLUSTER_PREFIX+PROXY in n for n in names):
        print "Proxy already running"
        return
    # Generate Config
    generate_maxscale_config()
    # Build Image
    build_maxscale_image()
    # Start Proxy
    subprocess.call([
        "docker", 
        "run", 
        "--name="+CLUSTER_PREFIX+PROXY, 
        "--network=bridge", 
        "-d", 
        "-p", 
        "10101" + ":4006", 
        "-p", 
        "9099" + ":4008", 
        PROXY_IMAGE_NAME])

# Stop proxy node.
def stop_proxy():
    print "Stopping proxy service"
    subprocess.call(["docker", "stop", CLUSTER_PREFIX + PROXY])
    subprocess.call(["docker", "rm", CLUSTER_PREFIX + PROXY])

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
        time.sleep(1)
        # Setup cluster
        subprocess.call([
            "docker",
            "exec",
            node_name,
            "bash",
            "setup.sh"])
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

# Get all container ip's
def GetClusterContainerIps():
    # Get container names
    names = GetClusterContainerNames()
    container_ips = []
    for n in names:
        if n != CLUSTER_PREFIX + PROXY:
             container_ips.append(get_node_ip(n))
    return container_ips
    
# Cleanup possible orphaned contianers
def cleanup_orphaned():
    ps = subprocess.Popen(("docker", "ps", "-a"), stdout=subprocess.PIPE)
    out, err = ps.communicate()
    names = ParseContainerNames(out)
    if len(names) > 0:
        print "Cleaning up container names ..."
        for c in names:
            subprocess.call(["docker", "rm", c])
    else:
        print "No containers found"

# Start test cluster, bring up host and nodes to connect.
def start_test_cluster(num_nodes):
    # Build Image
    build_maria_image()
    # Start cluster
    print "Starting cluster host ..."
    s = StartClusterHost(CLUSTER_PREFIX + CLUSTER_HOST, str(DEFAULT_PORT))
    if s:
        # Get cluster host ip
        ip_address = get_node_ip(CLUSTER_PREFIX + CLUSTER_HOST)
        # Get ip of first node
        port_num = DEFAULT_PORT + 1
        print "Starting cluster nodes ..."
        for n in range(0, int(num_nodes)):
            StartClusterNode(CLUSTER_PREFIX + CLUSTER_NODE + str(n), str(port_num), ip_address)
            port_num += 1

# Stop already running test cluster.
def stop_test_cluster():
    container_names = GetClusterContainerNames()
    if len(container_names) > 0:
        print "Stopping containers ..."
        subprocess.call(["docker", "stop"] + container_names)
        print "\nCleaning up container names ..."
        subprocess.call(["docker", "rm"] + container_names)
    else:
        print "No containers to stop."

# Add node to existing cluster
def add_node():
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine number to increment on
        highest_num = -1
        for n in containers:
            if CLUSTER_PREFIX + CLUSTER_NODE in n:
                #get number
                a = n.strip(CLUSTER_PREFIX + CLUSTER_NODE)
                if a > highest_num:
                    highest_num = a
        # Get port from highest container
        port = get_node_exposed_port(CLUSTER_PREFIX + CLUSTER_NODE + str(highest_num))
        print "exposed port : " + port
        # Get cluster host ip
        ip_address = get_node_ip(CLUSTER_PREFIX + CLUSTER_HOST)
        # Add new node
        new_node_number = str(int(highest_num)+1)
        new_node_port = str(int(port)+1)
        print "adding node : " + new_node_number + " on port : " + new_node_port
        StartClusterNode(CLUSTER_PREFIX + CLUSTER_NODE + new_node_number, new_node_port, ip_address)
    else:
        print "No cluster running"

# Remove node from existing cluster
def remove_node():
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine nubmer to decrement on
        highest_num = -1 
        for n in containers:
            if CLUSTER_PREFIX + CLUSTER_NODE in n:
                #get number
                a = n.strip(CLUSTER_PREFIX + CLUSTER_NODE)
                if a > highest_num:
                    highest_num = a
        if highest_num > -1:
            name = str(CLUSTER_PREFIX + CLUSTER_NODE + str(highest_num))
            print "Stopping node : " + name
            # remove node
            subprocess.call(["docker", "stop", name])
            subprocess.call(["docker", "rm", name])
        else:
            print "No available nodes"
    else:
        print "No cluster running"

# Remove node from existing cluster
def remove_named_node(name):
    # Get running containers
    containers = GetClusterContainerNames()
    if len(containers) > 0:
        # Determine nubmer to decrement on
        print containers
        # remove node
        subprocess.call(["docker", "stop", name])
        subprocess.call(["docker", "rm", name])
    else:
        print "No cluster running"

def generate_maxscale_config():
    # Get ip's for all nodes in cluster
    ips = GetClusterContainerIps()
    if len(ips) <= 0 :
        print "Could not resolve cluster node ips"
        return
    # Generate server names
    server_names = []
    count = 0
    for i in ips:
        server_names.append("cluster_node_" + str(count))
        count += 1

    # Create comma delimited string for use in cfg
    servers  = ",".join(server_names)
    print servers

    # setup variable number of nodes in cnf
    config = ConfigParser.ConfigParser()
    # Setup MaxScale
    config.add_section('maxscale')
    config.set('maxscale', 'threads', '2')
    # MaxAdmin
    config.add_section('MaxAdmin')
    config.set('MaxAdmin', 'type', 'service')
    config.set('MaxAdmin', 'router', 'cli')
    # MaxAdmin Listener
    config.add_section('MaxAdmin Unix Listener')
    config.set('MaxAdmin Unix Listener', 'type', 'listener')
    config.set('MaxAdmin Unix Listener', 'service', 'MaxAdmin')
    config.set('MaxAdmin Unix Listener', 'protocol', 'maxscaled')
    config.set('MaxAdmin Unix Listener', 'socket', 'default')
    # Galera Monitor
    config.add_section('Galera Monitor')
    config.set('Galera Monitor', 'type', 'monitor')
    config.set('Galera Monitor', 'module', 'galeramon')
    #config.set('Galera Monitor', 'disable_master_failback', '1')
    config.set('Galera Monitor', 'servers', servers)
    config.set('Galera Monitor', 'user', 'maxscale')
    config.set('Galera Monitor', 'passwd', 'password')
    # Replication Montior
    #config.add_section('Replication Monitor')
    #config.set('Replication Monitor', 'type', 'monitor')
    #config.set('Replication Monitor', 'module', 'mysqlmon')
    #config.set('Replication Monitor', 'servers', servers) 
    #config.set('Replication Monitor', 'user', 'maxscale')
    #config.set('Replication Monitor', 'passwd', 'password')
    # Splitter Service
    config.add_section('Splitter Service')
    config.set('Splitter Service', 'type', 'service')
    config.set('Splitter Service', 'router', 'readwritesplit')
    config.set('Splitter Service', 'servers', servers)
    config.set('Splitter Service', 'user', 'maxscale')
    config.set('Splitter Service', 'passwd', 'password')
    # Splitter Listener
    config.add_section('Splitter Listener')
    config.set('Splitter Listener', 'type', 'listener')
    config.set('Splitter Listener', 'service', 'Splitter Service')
    config.set('Splitter Listener', 'protocol', 'MySQLClient')
    config.set('Splitter Listener', 'port', '4006')
    # Multi Master Monitor
    #config.add_section('Multi-Master Monitor')
    #config.set('Multi-Master Monitor', 'type', 'monitor')
    #config.set('Multi-Master Monitor', 'module', 'mmmon')
    #config.set('Multi-Master Monitor', 'servers', servers)
    #config.set('Multi-Master Monitor', 'user', 'maxscale')
    #config.set('Multi-Master Monitor', 'passwd', 'password')
    #config.set('Multi-Master Monitor', 'detect_stale_master', 'true')
    # Debug Interface
    config.add_section('Debug Interface')
    config.set('Debug Interface', 'type', 'service')
    config.set('Debug Interface', 'router', 'debugcli')
    # Debug Listener
    config.add_section('Debug Listener')
    config.set('Debug Listener', 'type', 'listener')
    config.set('Debug Listener', 'service', 'Debug Interface')
    config.set('Debug Listener', 'protocol', 'telnetd')
    config.set('Debug Listener', 'port', '4442')
    # Setup servers
    count = 0
    for s in server_names:
        print s
        config.add_section(s)
        config.set(s, 'type', 'server')
        config.set(s, 'address', ips[count])
        config.set(s, 'port', '3306')
        config.set(s, 'protocol', 'MySQLBackend')
        count += 1

    with open(MAXSCALE_CFG, 'wb') as configfile:
        config.write(configfile)

    return

# Display script usage
def usage():
    usage = """\
        --help                  : Print out this usage text.
        --image                 : Image options.
                                  [build] (build docker image (rmi)).
                                  [delete] (delete docker image (rmi)).
        --start-cluster         : Start test cluster, brings up host, and nodes attached.
        --stop-cluster          : Stop running test cluster.
        --cleanup-containers    : Cleanup orphaned containers (rm).
        --add-node              : Add node to existing cluster.
                                  Provide number of nodes to add.
        --remove-node           : Remove node from existing cluster.
                                  Provide number of nodes to remove.
        --remove-named-node     : Remove a node via it's container name.
                                  Provide container names to remove.
        --start-proxy           : Start MaxScale instance.
        --stop-proxy            : Stop MaxScale instnace.
        --generate-proxy-cfg    : Generate MaxScale config. Run after bringing up a cluster.
    """
    print usage

# Main
if __name__ == '__main__':
    # Get opts
    try:
        long_args = [
                "help", 
                "image", 
                "start-cluster", 
                "stop-cluster", 
                "cleanup-containers", 
                "add-node", 
                "remove-node", 
                "remove-named-node",
                "start-proxy",
                "stop-proxy",
                "generate-proxy-cfg"]
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
        if o in ("--image"):
            for a in args:
                if a in ("build"):
                    build_maria_image()
                    build_maxscale_image()
                elif a in ("delete"):
                    delete_image()
                else:
                    print "Provide arg, [build] or [delete]"
        if o in ("--start-cluster"):
            # Look for number of nodes
            if len(args) > 0:
                start_test_cluster(args[0])
            else:
                print "Define number of nodes"
        if o in ("--stop-cluster"):
            stop_test_cluster()
        if o in ("--cleanup-containers"):
            cleanup_orphaned()
        if o in ("--add-node"):
            if len(args) > 0:
                for num in range(0, int(args[0])):
                    add_node()
            else:
                print "Provide number of nodes"
        if o in ("--remove-node"):
            if len(args) > 0:
                for num in range(0, int(args[0])):
                    remove_node()
            else:
                print "Provide number of nodes"
        if o in ("--remove-named-node"):
            if len(args) > 0:
                for name in args:
                    remove_named_node(name)
            else:
                print "Provide node names"
        if o in ("--start-proxy"):
            start_proxy()
        if o in ("--stop-proxy"):
            stop_proxy()
        if o in ("--generate-proxy-cfg"):
            generate_maxscale_config()


