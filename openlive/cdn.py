import networkx as nx
import numpy as np
from collections import defaultdict

class cdn():
    def __init__(self, G=nx.Graph()):
        self.network = G
        self.servers = []
        self.V = self.network.number_of_nodes()
        for node in self.network.nodes():
            if self.network.node[node]['IO'] > 10 and self.network.node[node]['clouds'] > 1:
                self.servers.append(node)
        print "Servers at", str(self.servers)

    def solve(self):
        f = open('results/cdn', 'w+')
        server_2_user_hops = []
        cluster_per_server = defaultdict(int)
        IO_used, cloud_used = defaultdict(int), defaultdict(int)
        video_resources = defaultdict(int)
        delivery_traffic, access_traffic, overall_traffic = [[0] * self.V for _ in xrange(self.V)], \
                [[0] * self.V for _ in xrange(self.V)], \
                [[0] * self.V for _ in xrange(self.V)]
        for node in self.network.nodes():
            if self.network.node[node]['user_queries'] != {}:
                hops, choice, path = None, None, None
                for server in self.servers:
                    _path = nx.shortest_path(self.network, source=server, target=node)
                    _hops = len(_path)
                    if hops == None or _hops < hops:
                        hops, choice, path = _hops, server, _path
                    server_2_user_hops.append(hops)
                cluster_per_server[choice] += 1
                IO_used[choice] += 10 * len(self.network.node[node]['user_queries'])
                cloud_used[choice] += len(self.network.node[node]['user_queries'])
                print path
                if node != choice:
                    for i in xrange(len(path)-1):
                        access_traffic[path[i]][path[i+1]] += 10 * len(self.network.node[node]['user_queries'])
                for key in self.network.node[node]['user_queries'].iterkeys():
                    print "Query no.", key, "can be served from", choice
                    f.write("Query no. " + str(key) + " can be served from " + str(choice) + "\n")
        access_traffic_util = []
        for u, v in self.network.edges_iter():
            if access_traffic[u][v] != 0:
                access_traffic_util.append(access_traffic[u][v] * 1.0 / self.network.edge[u][v]['bandwidth'])
            if access_traffic[v][u] != 0:
                access_traffic_util.append(access_traffic[v][u] * 1.0 / self.network.edge[v][u]['bandwidth'])
        n_cluster_per_server = cluster_per_server.values()
        print "Server to user hops min/avg/max/stddev =", min(server_2_user_hops), "/", np.mean(server_2_user_hops), "/", \
                max(server_2_user_hops), "/", np.std(server_2_user_hops)
        f.write("\n")
        f.write("Server to user hops min/avg/max/stddev = " + str(min(server_2_user_hops)) + "/" +
                str(np.mean(server_2_user_hops)) + "/" + str(max(server_2_user_hops)) + "/" + str(np.std(server_2_user_hops)))
        f.write("\n")
        f.write(str(server_2_user_hops))
        print "Number of servers connected per cluster min/avg/max/stddev =", 1, "/", 1, "/", 1, "/", 0
        f.write("\n")
        f.write("Number of servers connected per cluster min/avg/max/stddev = 1/1/1/0")
        print "Number of clusters connected per server min/avg/max/stddev =", min(n_cluster_per_server), "/", \
                np.mean(n_cluster_per_server), "/", max(n_cluster_per_server), "/", np.std(n_cluster_per_server)
        f.write("\n")
        f.write("Number of clusters connected per server min/avg/max/stddev = " + str(min(n_cluster_per_server)) + "/" +
                str(np.mean(n_cluster_per_server)) + "/" + str(max(n_cluster_per_server)) + "/" + 
                str(np.std(n_cluster_per_server)))
        f.write("\n")
        f.write(str(n_cluster_per_server))
        IO_utilization = [IO_used[server]*1.0/self.network.node[server]['IO'] for server in IO_used.iterkeys()]
        cloud_utilization = [cloud_used[server]*1.0/self.network.node[server]['clouds'] for server in IO_used.iterkeys()]
        print "IO utilization of server min/avg/max/stddev/sum =", min(IO_utilization), "/", \
                np.mean(IO_utilization), "/", max(IO_utilization), "/", np.std(IO_utilization), "/", sum(IO_utilization)
        f.write("\n")
        f.write("IO utilization of server min/avg/max/stddev/sum = " + str(min(IO_utilization)) + "/" +
                str(np.mean(IO_utilization)) + "/" + str(max(IO_utilization)) + "/" +
                str(np.std(IO_utilization)) + "/" + str(sum(IO_utilization)))
        f.write("\n")
        f.write(str(IO_utilization))
        print "Cloud utilization of server min/avg/max/stddev/sum =", min(cloud_utilization), "/", \
                np.mean(cloud_utilization), "/", max(cloud_utilization), "/", np.std(cloud_utilization), "/", \
                sum(cloud_utilization)
        f.write("\n")
        f.write("Cloud utilization of server min/avg/max/stddev/sum = " + str(min(cloud_utilization)) + "/" +
                str(np.mean(cloud_utilization)) + "/" + str(max(cloud_utilization)) + "/" +
                str(np.std(cloud_utilization)) + "/" + str(sum(cloud_utilization)))
        f.write("\n")
        f.write(str(cloud_utilization))
        f.write("\n")
        f.write(str(len(cloud_utilization)) + " server used")
        print "Access traffic link utilization min/avg/max/stddev/sum =", min(access_traffic_util), "/", \
                np.mean(access_traffic_util), "/", max(access_traffic_util), "/", np.std(access_traffic_util), "/", \
                sum(access_traffic_util)
        f.write("\n")
        f.write("Access traffic link utilization min/avg/max/stddev/sum = " + str(min(access_traffic_util)) + "/" +
                str(np.mean(access_traffic_util)) + "/" + str(max(access_traffic_util)) + "/" + 
                str(np.std(access_traffic_util)) + "/" + str(sum(access_traffic_util)))
        f.write("\n")
        f.write(str(access_traffic_util))
        f.write("\n")
        f.write(str(len(access_traffic_util)) + " links used for access traffic")
        f.close()

