#!/usr/bin/python
import json
from multicast import Multicast
from system import System
from topology import Topology
from trace import Trace
from random import shuffle
import os.path

def remove_channel(channel_to_remove, topology, trace, system):
    # Remove channel traffic from delivery tree
    for target, source_channel in system.delivery_tree.iteritems():
        for source, channel in source_channel.iteritems():
            if channel == channel_to_remove:
                topology.topo.node[source]['qoe'][target] -= 1
                links = topology.get_links_on_path(source, target)
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
        links = topology.get_links_on_path(node_id, server)
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

    failed_access = 0
    failed_channels = set()
    channels = system.channels.keys()[:]
    shuffle(channels) # Shuffle the order of channels for random choice

    for channel in channels:
        # Try to add channel delivery traffic into network
        for target, source_channel in system.delivery_tree.iteritems():
            for source, channel_arr in source_channel.iteritems():
                if channel not in channel_arr or channel in failed_channels:
                    continue
                links = topology.get_links_on_path(source, target)
                for u, v in links:
                    # TODO: set capacity value
                    if topology.topo.edge[u][v]['capacity'] - 100 < 0:
                        # If capacity doesn't allow, mark the channel as delivery failure
                        failed_channels.add(channel)
                        break

        # Update channel delivery traffic if capacity allows otherwise update access failure users
        if channel in failed_channels:
            failed_access += sum(trace.requests[channel])
        else:
            for target, source_channel in system.delivery_tree.iteritems():
                for source, channel_arr in source_channel.iteritems():
                    if channel in channel_arr:
                        # TODO: set qoe value
                        if 'qoe' in topology.topo.node[source]:
                            topology.topo.node[source]['qoe'][target] += 1
                        links = topology.get_links_on_path(source, target)
                        for u, v in links:
                            # TODO: set capacity and cost value
                            topology.topo.edge[u][v]['capacity'] -= 100
                            topology.topo.edge[u][v]['cost'] += 100

    # Update server capacities
    for pos, channel_ap in enumerate(system.access_point):
        for channel, ap in channel_ap.iteritems():
            if channel in failed_channels:
                continue
            viewer_number = trace.requests[channel][pos]
            for server, probability in ap.iteritems():
                # TODO: set qoe and server value
                # Try to fill server capacity with user requests
                if topology.topo.node[server]['server'] - int(viewer_number * probability) < 0:
                    failed_access += int(viewer_number * probability) - topology.topo.node[server]['server']
                    topology.topo.node[server]['qoe'][pos] += topology.topo.node[server]['server']
                    topology.topo.node[server]['server'] = 0
                else:
                    topology.topo.node[server]['qoe'][pos] += int(viewer_number * probability)
                    topology.topo.node[server]['server'] -= int(viewer_number * probability)

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
            # Exit point
            if not os.path.isfile('trace/' + str(i)):
                print "END"
                break

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