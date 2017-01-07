#!/usr/bin/python
from topology import Topology
import json
from trace import Trace
from system import System
from multicast import Multicast

if __name__ == "__main__":
    with open('topo/nsfnet.json') as sample_topo:
        data = json.load(sample_topo)
        topology = Topology(data)
        for node in topology.topo.nodes():
            print topology.topo.node[node]
        for u, v in topology.topo.edges_iter():
            print topology.topo.edge[u][v]
        print topology.routing

        i = 1
        while True:
            # Read crawled data
            trace = Trace('trace/' + str(i), topology.topo.number_of_nodes())
            system = System(topology)
            algo = Multicast(topology, trace, system)


            """
            TODO: System
            * add new channel
            * remove leaving channel
            * assign access point
            * append deliver tree
            * compute link and QoE cost, link and access utilization
            * access control (ap control and delivery tree control, record deny rate)
            """

            # Measurement