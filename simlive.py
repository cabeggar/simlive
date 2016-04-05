"""

@author Haoqin He

Simulate a openlive network with networkx

"""

import os.path
import json
from networkx.readwrite import json_graph
import networkx as nx
from itertools import islice

class UserGroup(object):
    # Defines a group of users at the same access point
    def __init__(self, access_point):
        self.access_point = access_point
        self.queries = []

    # Query stands for an user's query for content c
    def addQuery(self, c):
        self.queries.append(c)

def k_shortest_paths(G, source, target, k, weight=None):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

if __name__ == "__main__":
   
    # Read topology
    f = open("topo.json", "r")
    data = json.load(f)
    f.close()

    G = json_graph.node_link_graph(data)

    switches, vms = [], []
    for node in G.nodes():
        switches.append(node) if isinstance(node, int) else vms.append(node) 

    # Compute k shortest path
    paths = [[] for _ in xrange(len(G.nodes()))]
    for i, u in enumerate(G.nodes()):
        for j, v in enumerate(G.nodes()):
            if i == j: continue
            # Compute k shortest path from u to v
            # Currently k hard coded as 3
            paths[i].append(k_shortest_paths(G, u, v, 3, weight='capacity'))
    # print ([p for p in paths[0][1]])

    
