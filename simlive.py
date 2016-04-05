import os.path
import json
from networkx.readwrite import json_graph
import networkx as nx
from itertools import islice

def k_shortest_paths(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

if __name__ == "__main__":
   
    f = open("topo.json", "r")
    data = json.load(f)
    f.close()

    G = json_graph.node_link_graph(data)

    paths = [[] for _ in xrange(len(G.nodes()))]
    for i, u in enumerate(G.nodes()):
        for j, v in enumerate(G.nodes()):
            if i == j: continue
            paths[i].append(k_shortest_paths(G, u, v, 3, weight='capacity'))
    print ([p for p in paths[0][1]])
