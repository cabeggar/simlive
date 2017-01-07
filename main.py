#!/usr/bin/python
from topology import Topology
import json
from trace import Trace
from system import System

def remove_channel(channel_to_remove, topology, trace, system):
    for target, source_channel in system.delivery_tree:
        for source, channel in source_channel:
            if channel == channel_to_remove:
                links = []
                path = topology.routing[source][target]
                for k in xrange(1, len(path)):
                    links.append((path[k-1], path[k]))
                for u, v in links:
                    # TODO: set capacity value
                    topology.topo.edge[u][v]['capacity'] += 100

    for node_id in xrange(len(topology.topo.number_of_nodes())):
        viewer_number = system.viewers[node_id][channel]
        for server, probability in system.access_point[node_id][channel]:
            links = []
            path = topology.routing[node_id][server]
            for k in xrange(1, len(path)):
                links.append((path[k-1], path[k]))
            for u, v in links:
                # TODO: set capacity value
                topology.topo.edge[u][v]['capacity'] += int(100 * viewer_number * probability)


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

            """
            TODO: System
            * add new channel ?
            o remove leaving channel
            * assign access point
            * append deliver tree
            * compute link and QoE cost, link and access utilization
            * access control (ap control and delivery tree control, record deny rate)
            """

            # Remove leaving channel and users
            for channel in system.channels:
                if channel not in trace.channels:
                    remove_channel(channel, topology, trace, system)

            # Algorithm

            # Measurement