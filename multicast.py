from collections import deque
from collections import defaultdict
import networkx as nx


class Multicast(object):
    def __init__(self, topology, trace, system, round_no):
        self.topology = topology
        self.trace = trace
        self.system = system
        self.round_no = round_no

    def compute(self, incremental=True):
        channels_with_new_delivery_tree = set()
        new_delivery_tree = defaultdict(lambda: defaultdict(list))

        # assign access point
        for new_viewer_id in self.trace.events[self.round_no][2]:
            position, channel, access_point = self.trace.viewers[new_viewer_id]

            # If this position already has an access point for this channel
            if channel in self.system.access_point[position]:
                self.trace.viewers[new_viewer_id][2] = self.system.access_point[position][channel].keys()[0]
                continue

            # Assign nearest server as access_point
            server = self.topology.get_nearest_server(position)
            self.trace.viewers[new_viewer_id][2] = server
            self.system.access_point[position][channel] = {server: 1}

            # Check whether the chosen server is on delivery tree of this channel
            servers = [self.system.channels[channel]['src']] + self.system.channels[channel]['sites']
            if server not in servers:
                if incremental:
                    # Add a link from the nearest other server with channel available to the current server in delivery tree
                    min_hops, nearest_source = None, None
                    for source in servers:
                        if min_hops == None or len(self.topology.routing[server][source]) < min_hops:
                            min_hops = len(self.topology.routing[server][source])
                            nearest_source = source
                    new_delivery_tree[server][source].append(channel)
                self.system.channels[channel]['sites'].append(server)
                channels_with_new_delivery_tree.add(channel)


        if incremental:
            # If incremental, we've already appended new server to delivery tree
            return channels_with_new_delivery_tree, new_delivery_tree

        # Compute new delivery trees
        for channel in channels_with_new_delivery_tree:
            servers = [self.system.channels[channel]['src']] + self.system.channels[channel]['sites']
            # compute delivery tree
            # make overlay graph
            G = nx.Graph()
            G.add_nodes_from(servers)
            for i in xrange(len(servers)):
                for j in xrange(i+1, len(servers)):
                    u, v = servers[i], servers[j]
                    links = []
                    path = self.topology.routing[u][v]
                    for k in xrange(1, len(path)):
                        links.append(self.topology.topo[path[k-1]][path[k]]['bandwidth'])
                    G.add_edge(u, v, capacity=min(links))

            # Get delivery tree from minimum spanning tree
            T = nx.minimum_spanning_tree(G)
            root = self.system.channels[channel]['src']
            visited = set([])
            queue = deque([root])
            while queue:
                node = queue.popleft()
                for neighbor in T.neighbors(node):
                    if neighbor in visited:
                        continue
                    new_delivery_tree[neighbor][node].append(channel)
                    queue.append(neighbor)
                visited.add(node)

        return channels_with_new_delivery_tree, new_delivery_tree