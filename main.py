#!/usr/bin/python
from topology import Topology
import json
from trace import Trace
from system import System
from collections import defaultdict

def remove_channel(channel_to_remove, topology, trace, system):
    for target, source_channel in system.delivery_tree.iteritems():
        for source, channel in source_channel.iteritems():
            if channel == channel_to_remove:
                # TODO: set new qoe value
                topology.topo.node[source]['qoe'] += 1
                links = []
                path = topology.routing[source][target]
                for k in xrange(1, len(path)):
                    links.append((path[k-1], path[k]))
                for u, v in links:
                    # TODO: set capacity value
                    topology.topo.edge[u][v]['capacity'] += 100

    for node_id in xrange(len(topology.topo.number_of_nodes())):
        viewer_number = system.viewers[node_id][channel]
        recalculate_access_traffic(channel, node_id, system, topology, viewer_number)


def recalculate_access_traffic(channel, node_id, system, topology, viewer_number):
    for server, probability in system.access_point[node_id][channel].iteritems():
        # TODO: set new qoe value
        topology.topo.node[server]['qoe'] += int(1 * viewer_number * probability)
        links = []
        path = topology.routing[node_id][server]
        for k in xrange(1, len(path)):
            links.append((path[k - 1], path[k]))
        for u, v in links:
            # TODO: set capacity value
            topology.topo.edge[u][v]['capacity'] += int(100 * viewer_number * probability)


def get_request_delta(topology, trace, system):
    request_delta = defaultdict(defaultdict(int))
    for channel, request in trace.requests.iteritems():
        for i in xrange(topology.topo.number_of_nodes):
            if request[i] > system[i][channel]:
                request_delta[channel][i] = request[i] - system[i][channel]
            elif request[i] < system[i][channel]:
                # TODO: deal with non int diff on each server
                diff = system[i][channel] - request[i]
                recalculate_access_traffic(channel, i, system, topology, diff)
    return request_delta


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