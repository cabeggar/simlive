from collections import deque
import networkx as nx


class Multicast(object):
    def __init__(self, topology, trace, system):
        self.topology = topology
        self.trace = trace
        self.system = system

    def compute(self):
        # assign access point
        for channel, request in self.trace.requests.items():
            servers = [self.system.channels[channel]['src']] + self.system.channels[channel]['sites']
            new_server = False
            for pos, number in request:
                if channel in self.system.access_point[pos]:
                    continue
                server = self.topology.get_nearest_server(pos)
                self.system.access_point[pos] = {server: 1}
                if server not in servers:
                    servers.append(server)
                    new_server = True

            # compute delivery tree
            # make overlay graph
            if new_server:
                for t in self.system.delivery_tree:
                    for s in self.system.delivery_tree[t]:
                        self.system.delivery_tree[t][s].remove(channel)

                G = nx.Graph()
                G.add_nodes_from(servers)
                for i in xrange(len(server)):
                    for j in xrange(i+1, len(server)):
                        u, v = server[i], server[j]
                        links = []
                        path = self.topology.routing[u][v]
                        for k in xrange(1, len(path)):
                            links.append(self.topology.topo[path[k-1]][path[k]]['bandwidth'])
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