#!/usr/bin/python
import json
from multicast import Multicast
from system import System
from topology import Topology
from random import shuffle
from collections import defaultdict
from trace import Trace


def remove_channel(channel_to_remove, topology, system):
    # Remove channel traffic from delivery tree
    for target, source_channel in system.delivery_tree.iteritems():
        for source, channel in source_channel.iteritems():
            if channel_to_remove in channel:
                topology.topo.node[source]['qoe'][target] -= 1
                links = topology.get_links_on_path(source, target)
                for u, v in links:
                    # TODO: set capacity value
                    topology.topo.edge[u][v]['capacity'] += 100
                    topology.topo.edge[u][v]['cost'] -= 100

    # Remove access traffic of that channel
    for node_id in xrange(topology.topo.number_of_nodes()):
        viewer_number = system.viewers[node_id][channel_to_remove]
        recalculate_access_traffic(channel_to_remove, node_id, system, topology, viewer_number)

    # Delete that channel from system
    del system.channels[channel_to_remove]
    for node_stat in system.access_point:
        del node_stat[channel_to_remove]
    for node_stat in system.viewers:
        del node_stat[channel_to_remove]
    for t in system.delivery_tree:
        for s in system.delivery_tree[t]:
            if channel_to_remove in system.delivery_tree[t][s]:
                system.delivery_tree[t][s].remove(channel_to_remove)


def recalculate_access_traffic(channel, node_id, system, topology, viewer_number):
    for server, probability in system.access_point[node_id][channel].iteritems():
        # TODO: set new qoe value
        topology.topo.node[server]['qoe'][node_id] += int(1 * viewer_number * probability)
        links = topology.get_links_on_path(node_id, server)
        for u, v in links:
            # TODO: set capacity value
            # topology.topo.edge[u][v]['capacity'] += int(100 * viewer_number * probability)
            topology.topo.edge[u][v]['cost'] -= int(100 * viewer_number * probability)

def remove_users(leaving_users, topology, system):
    for position, access_numbers in enumerate(leaving_users):
        for access_point, viewer_number in access_numbers.iteritems():
            # TODO: set new qoe value
            topology.topo.node[access_point]['qoe'][position] += viewer_number
            links = topology.get_links_on_path(position, access_point)
            for u, v in links:
                # TODO: set capacity value
                topology.topo.edge[u][v]['cost'] -= viewer_number


def update_network_status(topology, trace, system, round_no, channels_with_new_delivery_tree, new_delivery_tree):
    # Update number of viewers in the system
    for new_viewer_id in trace.schedule[round_no][2]:
        position, channel, access_point = trace.viewers[new_viewer_id]
        system.viewers[position][channel] += 1

    # Restore traffic of expired delivery tree
    updated_channel = set()
    for channel in channels_with_new_delivery_tree:
        for u in system.delivery_tree.iterkeys():
            for v in system.delivery_tree[u].iterkeys():
                if channel in system.delivery_tree[u][v]:
                    links = topology.get_links_on_path(u, v)
                    for x, y in links:
                        topology.topo.edge[x][y]['capacity'] += 100
                        topology.topo.edge[x][y]['cost'] -= 1
                    system.delivery_tree[u][v].remove(channel)
                    updated_channel.add(channel)


    failed_access = 0
    failed_channels = set()
    channels = list(channels_with_new_delivery_tree)
    shuffle(channels)  # Shuffle the order of channels for random choice

    for channel in channels:
        # Try to add channel delivery traffic into network
        for target, source_channel in new_delivery_tree.iteritems():
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
        if channel not in failed_channels:
            for target, source_channel in new_delivery_tree.iteritems():
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
                        if channel not in system.delivery_tree[target][source]:
                            system.delivery_tree[target][source].append(channel)

    updated_and_failed_channel = failed_channels & updated_channel
    for pos, channel_serve in enumerate(system.access_point):
        for channel, server_probability in channel_serve.iteritems():
            if channel not in updated_and_failed_channel:
                continue
            viewer_number = system.viewers[pos][channel]
            failed_access += viewer_number
            for server, probability in server_probability.iteritems():
                topology.topo.node[server]['server'] += int(viewer_number * probability)
                topology.topo.node[server]['qoe'][pos] -= int(viewer_number * probability)

    new_viewers = [defaultdict(int) for _ in xrange(topology.topo.number_of_nodes())]
    for viewer_id in trace.schedule[round_no][2]:
        position, channel, access_point = trace.viewers[viewer_id]
        # Get new viewer whose channel can be successfully delivered
        if channel in failed_channels:
            continue
        else:
            new_viewers[position][access_point] += 1

    # Update server capacities
    for pos, ap_number in enumerate(new_viewers):
        for server, viewer_number in ap_number.iteritems():
            # TODO: set qoe and server value
            # Try to fill server capacity with user requests
            if topology.topo.node[server]['server'] - viewer_number < 0:
                failed_access += viewer_number - topology.topo.node[server]['server']
                topology.topo.node[server]['qoe'][pos] += topology.topo.node[server]['server']
                topology.topo.node[server]['server'] = 0
            else:
                topology.topo.node[server]['qoe'][pos] += viewer_number
                topology.topo.node[server]['server'] -= viewer_number

    # for u, v in topology.topo.edges_iter():
    #     print topology.topo.edge[u][v]['capacity']

    return failed_access, len(failed_channels)


if __name__ == "__main__":
    # Initialize network
    with open('topo/nsfnet.json') as sample_topo:
        data = json.load(sample_topo)
        topology = Topology(data)
        for node in topology.topo.nodes():
            print topology.topo.node[node]
        for u, v in topology.topo.edges_iter():
            print topology.topo.edge[u][v]
        print topology.routing

    # Initialize trace
    # with open('new_trace_pickle') as new_trace:
    #     trace = pickle.load(new_trace)
    #     rounds = len(trace.schedule)
    #     print "Pickle object loaded"
    trace = Trace('trace/')
    rounds = len(trace.schedule)

    # Initialize system
    system = System(topology)

    for round_no in xrange(rounds):
        # Remove leaving channels
        for leaving_channel in trace.schedule[round_no][1]:
            del trace.channels[leaving_channel]
            remove_channel(leaving_channel, topology, system)
        print "Leaving channels removed!"

        # Remove leaving users
        leaving_users = [defaultdict(int) for _ in xrange(topology.topo.number_of_nodes())]
        for leaving_user in trace.schedule[round_no][3]:
            position, channel_id, access_id = trace.viewers[leaving_user]
            del trace.viewers[leaving_user]
            leaving_users[position][access_id] += 1
            system.viewers[position][channel_id] -= 1
        remove_users(leaving_users, topology, system)
        print "Leaving user removed!"

        # Add new channels
        for channel in trace.schedule[round_no][0]:
            system.channels[channel]['src'] = topology.get_nearest_server(trace.channels[channel])
            system.channels[channel]['sites'] = []
        print "New channels prepared!"

        algo = Multicast(topology, trace, system, round_no)
        # Compute deliver tree and access points for current trace. The results should be stored in system
        channels_with_new_delivery_tree, new_delivery_tree = algo.compute()
        print "Algorithm computation complete!"
        # Update network status based on updated system
        failed_access, failed_deliver = update_network_status(topology, trace, system, round_no,
                                                              channels_with_new_delivery_tree,
                                                              new_delivery_tree)
        print failed_access, failed_deliver, len(channels_with_new_delivery_tree)

        # Remove expiring events
        trace.schedule[round_no] = [[], [], [], []]
