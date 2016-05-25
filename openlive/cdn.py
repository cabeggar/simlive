import networkx as nx

class cdn():
    def __init__(self, G=nx.Graph()):
        self.network = G
        self.servers = []
        for node in self.network.nodes():
            if self.network.node[node]['IO'] > 10 and self.network.node[node]['clouds'] > 1:
                self.servers.append(node)
        print "Servers at", str(self.servers)

    def solve(self):
        f = open('results/cdn', 'w+')
        for node in self.network.nodes():
            if self.network.node[node]['user_queries'] != {}:
                hops, choice = None, None
                for server in self.servers:
                    _hops = len(nx.shortest_path(self.network, source=server, target=node))
                    if hops == None or _hops < hops:
                        hops, choice = _hops, server
                for key in self.network.node[node]['user_queries'].iterkeys():
                    print "Query no.", key, "can be served from", choice
                    f.write("Query no. " + str(key) + " can be served from " + str(choice) + "\n")
