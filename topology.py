import networkx as nx
import json

class Topology(object):
    def __init__(self, topo_json):
        G = nx.Graph()
        # Read graph from json
        G.add_nodes_from(range(topo_json['number_of_nodes']))
        for i, (u, v, bandwidth) in enumerate(topo_json['edge_list']):
            G.add_edge(u, v, id = i, bandwidth = bandwidth, weight = 1)
        for node in topo_json['servers']:
            G.node[int(node)]['server'] = topo_json['servers'][node]
        self.topo = G

        # Compute minimum spanning tree
        number_of_nodes = G.number_of_nodes()
        self.routing = [[[] for _ in xrange(number_of_nodes)] for _ in xrange(number_of_nodes)]
        for i in xrange(number_of_nodes):
            paths = nx.single_source_shortest_path(G, i)
            for j in xrange(number_of_nodes):
                if j == i: continue
                self.routing[i][j] = paths[j]

if __name__ == "__main__":
    with open('sample_topo.json') as sample_topo:
        data = json.load(sample_topo)
        topology = Topology(data)
        for node in topology.topo.nodes():
            print topology.topo.node[node]
        for u, v in topology.topo.edges_iter():
            print topology.topo.edge[u][v]
        print topology.routing