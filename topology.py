import networkx as nx
import json


class Topology(object):
    def __init__(self, topo_json):
        G = nx.Graph()
        # Read graph from json
        G.add_nodes_from(range(topo_json['number_of_nodes']))

        for i, (u, v, bandwidth, cost) in enumerate(topo_json['edge_list']):
            G.add_edge(u, v, id=i, bandwidth=bandwidth, capacity=bandwidth,
                       init_cost=cost, cost=cost)

        self.servers = []
        for node in topo_json['servers']:
            G.node[int(node)]['init_server'] = topo_json['servers'][node]
            G.node[int(node)]['server'] = topo_json['servers'][node]
            self.servers.append(int(node))

        for node in topo_json['qoe']:
            G.node[int(node)]['init_qoe'] = topo_json['qoe'][node][:]
            G.node[int(node)]['qoe'] = topo_json['qoe'][node][:]

        for node in G.nodes():
            G.node[node]['io_bw'] = 100

        for node in topo_json['io_bw']:
            G.node[int(node)]['io_bw'] = topo_json['bw'][node][:]

        self.topo = G

        # Compute shortest paths
        self.number_of_nodes = G.number_of_nodes()
        self.routing = [[[] for _ in xrange(self.number_of_nodes)]
                        for _ in xrange(self.number_of_nodes)]

        for i in xrange(self.number_of_nodes):
            paths = nx.single_source_shortest_path(G, i)

            for j in xrange(self.number_of_nodes):
                if j == i:
                    continue
                self.routing[i][j] = paths[j]

    def get_nearest_server(self, pos):
        server_hop = [(node, len(self.routing[pos][node]))
                      for node in self.topo.nodes()
                      if node in self.servers]
        return min(server_hop, key=lambda x: x[1])[0]

    def get_links_on_path(self, x, y):
        links = []
        path = self.routing[x][y]
        for k in xrange(1, len(path)):
            links.append((path[k - 1], path[k]))
        return links

    def print_topo_info(self):
        print "Topology Infomation"
        print "nodes:"
        for node in topology.topo.nodes():
            print topology.topo.node[node]

        print "edges:"
        for u, v in topology.topo.edges_iter():
            print topology.topo.edge[u][v]

        print "routing:"
        print topology.routing


if __name__ == "__main__":
    with open('topo/nsfnet.json') as sample_topo:
        data = json.load(sample_topo)
        topology = Topology(data)
        for node in topology.topo.nodes():
            print topology.topo.node[node]
        for u, v in topology.topo.edges_iter():
            print topology.topo.edge[u][v]
        print topology.routing
