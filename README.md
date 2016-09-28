# maria-dockerfile
Test script to bring up and tear down a galera cluster easily. Provides docker file for latest mariadb version.

## usage
```
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
```
