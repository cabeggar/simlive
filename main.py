#!/usr/bin/python
import json
from multicast import Multicast
from system import System
from topology import Topology
from trace import Trace


def remove_channel(channel_to_remove, topology, trace, system):
    for target, source_channel in system.delivery_tree.iteritems():
        for source, channel in source_channel.iteritems():
            if channel == channel_to_remove:
                topology.topo.node[source]['qoe'][target] -= 1
                links = []
                path = topology.routing[source][target]
                for k in xrange(1, len(path)):
                    links.append((path[k-1], path[k]))
                for u, v in links:
                    # TODO: set capacity value
                    topology.topo.edge[u][v]['capacity'] += 100
                    topology.topo.edge[u][v]['cost'] -= 100

    for node_id in xrange(len(topology.topo.number_of_nodes())):
        viewer_number = system.viewers[node_id][channel]
        recalculate_access_traffic(channel, node_id, system, topology, viewer_number)

    del system.channels[channel]
    for node_stat in system.access_point:
        del node_stat[channel]
    for node_stat in system.viewers:
        del node_stat[channel]
    for t in system.delivery_tree:
        for s in system.delivery_tree[t]:
            system.delivery_tree[t][s].remove(channel)

def recalculate_access_traffic(channel, node_id, system, topology, viewer_number):
    for server, probability in system.access_point[node_id][channel].iteritems():
        # TODO: set new qoe value
        topology.topo.node[server]['qoe'][node_id] += int(1 * viewer_number * probability)
        links = []
        path = topology.routing[node_id][server]
        for k in xrange(1, len(path)):
            links.append((path[k - 1], path[k]))
        for u, v in links:
            # TODO: set capacity value
            topology.topo.edge[u][v]['capacity'] += int(100 * viewer_number * probability)
            topology.topo.edge[u][v]['cost'] -= int(100 * viewer_number * probability)


def remove_user(topology, trace, system):
    for channel, request in trace.requests.iteritems():
        for i in xrange(topology.topo.number_of_nodes):
            if request[i] < system[i][channel]:
                if request[i] == 0:
                    # TODO: Do we need to tera down the corresponding server?
                    del system[i][channel]
                    continue
                # TODO: deal with non int diff on each server
                diff = system[i][channel] - request[i]
                recalculate_access_traffic(channel, i, system, topology, diff)

def update_network_status(topology, trace, system):

    failed_access = 0
    failed_deliver = 0

    for node in topology.topo.nodes():
        if node in topology.servers:
            topology.topo.node[node]['qoe'] = topology.topo.node[node]['init_qoe'][:]
    for u, v in topology.topo.edges_iter():
        topology.topo.edge[u][v]['capacity'] = topology.topo.edge[u][v]['bandwidth']
        topology.topo.edge[u][v]['oost'] = topology.topo.edge[u][v]['init_cost']

    for pos in system.access_point:
        for channel, ap in system.access_point[pos].iteritems():
            viewer_number = trace.requests[channel][pos]
            for server, probability in ap.iteritems():
                success = True
                # TODO: set qoe value, fix over-minus bug
                topology.topo.node[server]['qoe'][pos] += int(1 * viewer_number * probability)
                links = []
                path = topology.routing[pos][server]
                for k in xrange(1, len(path)):
                    links.append((path[k-1], path[k]))
                for u, v in links:
                    # TODO: set capacity value, fix over-minus bug
                    topology.topo.edge[u][v]['capacity'] -= int(100 * viewer_number * probability)
                    if topology.topo.edge[u][v]['capacity'] < 0 and success == True:
                        failed_access += viewer_number * probability
                        success = False
                    topology.topo.edge[u][v]['cost'] += int(100 * viewer_number * probability)

    for target, source_channel in system.delivery_tree.iteritems():
        for source, channel in source_channel.iteritems():
            success = True
            # TODO: set capacity value, fix over-minus bug
            topology.topo.node[source]['qoe'][target] += 1
            links = []
            path = topology.routing[source][target]
            for k in xrange(1, len(path)):
                links.append((path[k-1], path[k]))
            for u, v in links:
                # TODO: set capacity value, fix over-minus bug
                topology.topo.edge[u][v]['capacity'] -= 100
                if topology.topo.edge[u][v]['capacity'] < 0 and success == True:
                    failed_deliver += 1
                    success = False
                topology.topo.edge[u][v]['cost'] += 100

    return failed_access, failed_deliver


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

            # Remove users based on access probabilities
            remove_user(topology, trace, system)

            # Add new channels
            for channel, src in trace.channels.items():
                if channel not in system.channels:
                    system.channels[channel]['src'] = src

            algo = Multicast(topology, trace, system)
            # Compute deliver tree and access points for current trace. The results should be stored in system
            algo = algo.compute()
            # Update network status based on updated system
            failed_access, failed_deliver = update_network_status(topology, trace, system)