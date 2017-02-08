#!/usr/bin/python
from topology import Topology
import json
import sys
from system import System
from trace import Trace

if __name__ == "__main__":
    # Initialize network
    topology = None

    with open('topo/nsfnet.json') as sample_topo:
        data = json.load(sample_topo)
        topology = Topology(data)

    if topology is None:
        print "Error Initializing Network..."
        sys.exit(1)
    else:
        topology.print_topo_info()

    # Loading Trace
    trace = Trace('trace/')

    # initialize simulation system
    system = System(topology, trace)

    while True:
        if not system.run():
            break
