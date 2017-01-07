from collections import defaultdict
from collections import deque
import networkx as nx

class Multicast(object):
    def __init__(self, topology, trace, system):
        self.topology = topology
        self.trace = trace
        self.system = system
        self.access_point = [{} for _ in xrange(topology.topo.number_of_nodes())]
        self.delivery_tree = defaultdict(defaultdict(list))

    def compute(self):
        # assign access point
        for channel, request in self.trace.requests:
            servers = [self.trace.channels[channel]]
            for pos, number in request:
                server = self.topology.get_nearest_server(pos)
                self.access_point[pos] = {server: 1}
                if server not in servers: servers.append(server)

            # compute delivery tree
            # make overlay graph
            G = nx.Graph()
            G.add_nodes_from(servers)
            for i in xrange(len(server)):
                for j in xrange(i+1, len(server)):
                    u, v = server[i], server[j]
                    links = []
                    path = self.topology.routing[u][v]
                    for k in xrange(1, len(path)):
                        links.append(self.topology.topo[path[k-1]][path[k]]['capacity'])
                    G.add_edge(u, v, capacity=min(links))

            T = nx.minimum_spanning_tree(G)
            root = self.trace.channels[channel]
            visited = set()
            queue = deque([root])
            while queue:
                node = queue.popleft()
                for neighbor in T.neighbors(node):
                    self.delivery_tree[neighbor][node].append(channel)
                    if neighbor not in visited:
                        queue.append(neighbor)
                        visited.add(neighbor)
