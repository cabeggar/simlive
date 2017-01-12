#!/usr/bin/python
import json
from multicast import Multicast
from system import System
from topology import Topology
from trace import Trace


def remove_channel(channel_to_remove, topology, trace, system):
    # Remove channel traffic from delivery tree
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

    # Remove access traffic of that channel
    for node_id in xrange(len(topology.topo.number_of_nodes())):
        viewer_number = system.viewers[node_id][channel]
        recalculate_access_traffic(channel, node_id, system, topology, viewer_number)

    # Delete that channel from system
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
            # topology.topo.edge[u][v]['capacity'] += int(100 * viewer_number * probability)
            topology.topo.edge[u][v]['cost'] -= int(100 * viewer_number * probability)


def remove_user(topology, trace, system):
    for channel, request in trace.requests.iteritems():
        for i in xrange(topology.topo.number_of_nodes()):
            if request[i] < system.viewers[i][channel]:
                if request[i] == 0:
                    # TODO: Do we need to tera down the corresponding server?
                    del system[i][channel]
                    continue
                # TODO: deal with non int diff on each server
                diff = system[i][channel] - request[i]
                recalculate_access_traffic(channel, i, system, topology, diff)

def update_network_status(topology, trace, system):

    failed_access = 0

    # Update number of viewers in the system
    for channel, request in trace.requests.iteritems():
        for i in xrange(topology.topo.number_of_nodes()):
            system.viewers[i][channel] = request[i]

    # Restore initial value of network status
    for node in topology.topo.nodes():
        if node in topology.servers:
            topology.topo.node[node]['qoe'] = topology.topo.node[node]['init_qoe'][:]
            topology.topo.node[node]['server'] = topology.topo.node[node]['init_server']
    for u, v in topology.topo.edges_iter():
        topology.topo.edge[u][v]['capacity'] = topology.topo.edge[u][v]['bandwidth']
        topology.topo.edge[u][v]['cost'] = topology.topo.edge[u][v]['init_cost']

    # Update server capacities
    for pos, channel_ap in enumerate(system.access_point):
        for channel, ap in channel_ap.iteritems():
            viewer_number = trace.requests[channel][pos]
            for server, probability in ap.iteritems():
                # TODO: set qoe value, fix over-minus bug
                topology.topo.node[server]['qoe'][pos] += int(1 * viewer_number * probability)
                topology.topo.node[server]['server'] -= int(1 * viewer_number * probability)

    # Calculate failed access
    for server in topology.servers:
        if topology.topo.node[server]['server'] < 0:
            failed_access += 0 - topology.topo.node[server]['server']

    failed_channels = set()

    # Calculate failed channels
    for target, source_channel in system.delivery_tree.iteritems():
        for source, channels in source_channel.iteritems():
            # TODO: set capacity value, fix over-minus bug
            if 'qoe' in topology.topo.node[source]:
                topology.topo.node[source]['qoe'][target] += 1
            links = []
            path = topology.routing[source][target]
            for k in xrange(1, len(path)):
                links.append((path[k-1], path[k]))
            for u, v in links:
                # TODO: set capacity value, fix over-minus bug
                topology.topo.edge[u][v]['capacity'] -= 100 * len(channels)
                if topology.topo.edge[u][v]['capacity'] < 0:
                    for channel in channels:
                        failed_channels.add(channel)
                topology.topo.edge[u][v]['cost'] += 100

    # for u, v in topology.topo.edges_iter():
    #     print topology.topo.edge[u][v]['capacity']

    return failed_access, len(failed_channels)


if __name__ == "__main__":
    with open('topo/nsfnet.json') as sample_topo:
        # Load topology
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

            # Remove leaving channel and users
            for channel in system.channels:
                if channel not in trace.channels:
                    remove_channel(channel, topology, trace, system)

            # Remove users based on access probabilities
            remove_user(topology, trace, system)

            # Add new channels
            for channel, src in trace.channels.items():
                if channel not in system.channels:
                    # Assign the server closest to streamer as source server
                    system.channels[channel]['src'] = topology.get_nearest_server(src)
                    system.channels[channel]['sites'] = []

            algo = Multicast(topology, trace, system)
            # Compute deliver tree and access points for current trace. The results should be stored in system
            algo = algo.compute()
            # Update network status based on updated system
            failed_access, failed_deliver = update_network_status(topology, trace, system)
            print failed_access, failed_deliver, len(trace.requests)
            i += 1