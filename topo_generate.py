import networkx as nx
from networkx.readwrite import json_graph
import os.path
import json

if __name__ == "__main__":
    G = nx.Graph()
    G.add_nodes_from([1,2,3,4,5,6,7])
    G.add_edges_from([(1,2),(1,3),(1,4),(2,3),(3,4),(2,5),(3,5),(4,5),(4,6),(5,6),(5,7),(6,7)], capacity=1000000000)
    G.add_edges_from([(2,1),(3,1),(4,1),(3,2),(4,3),(5,2),(5,3),(5,4),(6,4),(6,5),(7,5),(7,6)], capacity=1000000000)
    G.add_nodes_from(['v1','v2'], bandwidth=1000000000)
    G.add_edges_from([(2,'v1'),(6,'v2')], capacity=1000000000)
    G.add_edges_from([('v1',2),('v2',6)], capacity=1000000000)
    data = json_graph.node_link_data(G)
    f = open("topo.json", "w+")
    f.write(json.dumps(data))
    f.close()
