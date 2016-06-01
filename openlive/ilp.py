import cplex
from cplex.exceptions import CplexError
import networkx as nx
from itertools import islice
import cProfile, pstats, StringIO
import numpy as np
from collections import defaultdict

class ilp():
    def __init__(self, G=nx.Graph(), n_paths=3, qualities=[10,8,6,4], ct=1, cf=0, wb=1, wc=1):
        self.problem = cplex.Cplex()
        self.network = G
        self.qualities = qualities
        self.ct = ct
        self.cf = cf
        self.wb = wb
        self.wc = wc

        self.V = G.number_of_nodes()    # Number of nodes
        self.E = G.number_of_edges()
        self.K = 0
        self.M = 0
        for u in G.nodes_iter():
            self.K += len(G.node[u]['video_src'])       # Number of video resources
            self.M += len(G.node[u]['user_queries'])    # Number of queries
        self.N = n_paths        # Number of shortest paths between each pair
        self.paths = self.kshortest(self.N)
        self.Q = len(qualities) # Number of available video qualities

        """
        VMS placement         [0 ~ V-1]
        delivery tree routing [V ~ V+KNQV^2-1]
        user access param     [V+KNQV^2 ~ V+KNQV^2 + VMQ-1]
        """

    def kshortest(self, k):
        paths = [[] for _ in xrange(self.V)]

        for i, u in enumerate(self.network.nodes()):
            for j, v in enumerate(self.network.nodes()):
                if i == j:
                    paths[i].append([])
                    continue

                # get k shortest from all shortest simple paths from u to v
                # weight set to 1 to get shortest hops path
                paths[i].append(list(islice(
                    nx.shortest_simple_paths(self.network, u, v, weight='weight'),
                    k)))

        return paths

    def solve(self):
        pr = cProfile.Profile()
        pr.enable()
        try:
            my_prob = cplex.Cplex()
            handle = self.populate_constraints(my_prob)
            my_prob.solve()
        except CplexError, exc:
            print exc
            return
        pr.disable()

        numrows = my_prob.linear_constraints.get_num()
        numcols = my_prob.variables.get_num()

        my_prob.write("results/ilp.lp")

        print

        f = open('results/lp_result', 'w+')
        # solution.get_status() returns an integer code
        print "Solution status = ", my_prob.solution.get_status(), ":",
        f.write("Solution status = " + str(my_prob.solution.get_status()) + ":\n")
        # the following line prints the corresponding string
        print my_prob.solution.status[my_prob.solution.get_status()]
        f.write(str(my_prob.solution.status[my_prob.solution.get_status()]) + "\n")
        print "Solution value = ", my_prob.solution.get_objective_value()
        f.write("Solution value = " + str(my_prob.solution.get_objective_value()) + "\n")
        slack = my_prob.solution.get_linear_slacks()
        # pi = my_prob.solution.get_dual_values()
        x = my_prob.solution.get_values()
        # dj = my_prob.solution.get_reduced_costs()
        """
        for i in range(numrows):
            print "Row %d:  Slack = %10f    Pi = %10f" % (i, slack[i], pi[i])
            f.write("Row %d:  Slack = %10f    Pi = %10f" % (i, slack[i], pi[i]) + "\n")
        for j in range(numcols):
            print "Column %d:   Value = %10f    Reduced cost = %10f" % (j, x[j], dj[j])
            f.write("Column %d:   Value = %10f    Reduced cost = %10f" % (j, x[j], dj[j]) + "\n")
        """
        for i in range(numrows):
            # print "Row %d:  Slack = %10f" % (i, slack[i])
            f.write("Row %d:  Slack = %10f" % (i, slack[i]) + "\n")
        for j in range(numcols):
            # print "Column %d:   Value = %10f" % (j, x[j])
            f.write("Column %d:   Value = %10f" % (j, x[j]) + "\n")
        f.close()

        f = open('results/openlive', 'w+')
        for vms_i in xrange(self.V):
            if x[vms_i] != 0 and self.get_cloud(vms_i) != 1:
                print "VMS placed at node", vms_i, "(", x[vms_i], ")"
                f.write("VMS placed at node" + str(vms_i) + " (" + str(x[vms_i]) + ")\n")

        IO_used, cloud_used = defaultdict(int), defaultdict(int)
        delivery_tree = [[0] * self.V for _ in xrange(self.V)]
        for src_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            if x[self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i)] != 0:
                                print "Content", content_i, "can be streamed from", src_i, "to", dst_i, "via path", path_i, \
                                        "at quality", quality_i, "(", x[self.get_gamma_column(src_i, dst_i, content_i, \
                                        path_i, quality_i)], ")"
                                f.write("Content " + str(content_i) + " can be streamed from " + str(src_i) + " to " + \
                                        str(dst_i) + " via path " + str(path_i) + " at quality " + str(quality_i) + " (" + \
                                        str(x[self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i)]) + ")\n")
                                if src_i != dst_i:
                                    path = self.paths[src_i][dst_i][path_i]
                                    for i in xrange(len(path)-1):
                                        u, v = path[i], path[i+1]
                                        delivery_tree[u][v] += self.qualities[quality_i]
                                if self.network.node[src_i]['IO'] != 10*len(self.network.node[src_i]['video_src']) and \
                                        self.network.node[src_i]['clouds'] != len(self.network.node[src_i]['video_src']) and \
                                        src_i != dst_i:
                                    IO_used[src_i] += self.qualities[quality_i]
                                    cloud_used[src_i] += 1
        vms_2_user_hops = []
        vms_per_cluster, cluster_per_vms = defaultdict(list), defaultdict(list)
        access_traffic = [[0] * self.V for _ in xrange(self.V)]
        for vms_i in xrange(self.V):
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    if x[self.get_alpha_column(vms_i, query_i, quality_i)] != 0:
                        print "Query no.", query_i, "can be served from", vms_i, "at quality", quality_i, "(", \
                                x[self.get_alpha_column(vms_i, query_i, quality_i)], ")"
                        f.write("Query no. " + str(query_i) + " can be served from " + str(vms_i) + " at quality " + \
                                str(quality_i) + " (" + str(x[self.get_alpha_column(vms_i, query_i, quality_i)]) + ")\n")
                        IO_used[vms_i] += self.qualities[quality_i]
                        cloud_used[vms_i] += 1
                        for node in self.network.nodes():
                            if query_i in self.network.node[node]['user_queries']:
                                vms_2_user_hops.append(len(self.paths[vms_i][node][0]) if self.paths[vms_i][node] else 0)
                                if vms_i not in vms_per_cluster[node]: vms_per_cluster[node].append(vms_i)
                                if node not in cluster_per_vms[vms_i]: cluster_per_vms[vms_i].append(node)
                                if node != vms_i:
                                    path = self.paths[vms_i][node][0]
                                    for i in xrange(len(path)-1):
                                        access_traffic[path[i]][path[i+1]] += self.qualities[quality_i]
        overall_traffic = [[0] * self.V for _ in xrange(self.V)]
        for i in xrange(self.V):
            for j in xrange(self.V):
                overall_traffic[i][j] = delivery_tree[i][j] + access_traffic[i][j]
        delivery_tree_util, access_traffic_util, overall_traffic_util = [], [], []
        for u, v in self.network.edges_iter():
            if delivery_tree[u][v] != 0:
                delivery_tree_util.append(delivery_tree[u][v] * 1.0 / self.network.edge[u][v]['bandwidth'])
            if delivery_tree[v][u] != 0:
                delivery_tree_util.append(delivery_tree[v][u] * 1.0 / self.network.edge[v][u]['bandwidth'])
            if access_traffic[u][v] != 0:
                access_traffic_util.append(access_traffic[u][v] * 1.0 / self.network.edge[u][v]['bandwidth'])
            if access_traffic[v][u] != 0:
                access_traffic_util.append(access_traffic[v][u] * 1.0 / self.network.edge[v][u]['bandwidth'])
            if overall_traffic[u][v] != 0:
                overall_traffic_util.append(overall_traffic[u][v] * 1.0 / self.network.edge[u][v]['bandwidth'])
            if overall_traffic[v][u] != 0:
                overall_traffic_util.append(overall_traffic[v][u] * 1.0 / self.network.edge[v][u]['bandwidth'])
        n_vms_per_cluster = [len(value) for value in vms_per_cluster.itervalues()]
        n_cluster_per_vms = [len(value) for value in cluster_per_vms.itervalues()]
        IO_utilization = [IO_used[vms]*1.0/self.network.node[vms]['IO'] for vms in IO_used.iterkeys()]
        cloud_utilization = [cloud_used[vms]*1.0/self.network.node[vms]['clouds'] for vms in cloud_used.iterkeys()]
        print "VMS to user hops min/avg/max/stddev =", min(vms_2_user_hops), "/", np.mean(vms_2_user_hops), "/", \
                max(vms_2_user_hops), "/", np.std(vms_2_user_hops)
        f.write("\n")
        f.write("VMS to user hops min/avg/max/stddev = " + str(min(vms_2_user_hops)) + "/" + str(np.mean(vms_2_user_hops)) +
                "/" + str(max(vms_2_user_hops)) + "/" + str(np.std(vms_2_user_hops)))
        f.write("\n")
        f.write(str(vms_2_user_hops))
        print "Number of VMS connected per cluster min/avg/max/stddev =", min(n_vms_per_cluster), "/", \
                np.mean(n_vms_per_cluster), "/", max(n_vms_per_cluster), "/", np.std(n_vms_per_cluster)
        f.write("\n")
        f.write("Number of VMS connected per cluster min/avg/max/stddev = " + str(min(n_vms_per_cluster)) + "/" +
                str(np.mean(n_vms_per_cluster)) + "/" + str(max(n_vms_per_cluster)) + "/" + str(np.std(n_vms_per_cluster)))
        f.write("\n")
        f.write(str(n_vms_per_cluster))
        print "Number of clusters connected per VMS min/avg/max/stddev =", min(n_cluster_per_vms), "/", \
                np.mean(n_cluster_per_vms), "/", max(n_cluster_per_vms), "/", np.std(n_cluster_per_vms)
        f.write("\n")
        f.write("Number of clusters connected per VMS min/avg/max/stddev = " + str(min(n_cluster_per_vms)) + "/" +
                str(np.mean(n_cluster_per_vms)) + "/" + str(max(n_cluster_per_vms)) + "/" + str(np.std(n_cluster_per_vms)))
        f.write("\n")
        f.write(str(n_cluster_per_vms))
        print "IO utilization of VMS min/avg/max/stddev/sum =", min(IO_utilization), "/", np.mean(IO_utilization), "/", \
                max(IO_utilization), "/", np.std(IO_utilization), "/", sum(IO_utilization)
        f.write("\n")
        f.write("IO utilization of VMS min/avg/max/stddev/sum = " + str(min(IO_utilization)) + "/" +
                str(np.mean(IO_utilization)) + "/" + str(max(IO_utilization)) + "/" + str(np.std(IO_utilization)) + "/" +
                str(sum(IO_utilization)))
        f.write("\n")
        f.write(str(IO_utilization))
        print "Clouds utilization of VMS min/avg/max/stddev/sum =", min(cloud_utilization), "/", np.mean(cloud_utilization), \
                "/", max(cloud_utilization), "/", np.std(cloud_utilization), "/", sum(cloud_utilization)
        f.write("\n")
        f.write("Clouds utilization of VMS min/avg/max/stddev/sum = " + str(min(cloud_utilization)) + "/" +
                str(np.mean(cloud_utilization)) + "/" + str(max(cloud_utilization)) + "/" + str(np.std(cloud_utilization)) +
                "/" + str(sum(cloud_utilization)))
        f.write("\n")
        f.write(str(cloud_utilization))
        f.write("\n")
        f.write(str(len(cloud_utilization)) + " VMS used")
        print "Delivery tree link utilization min/avg/max/stddev/sum =", min(delivery_tree_util), "/", \
                np.mean(delivery_tree_util), "/", max(delivery_tree_util), "/", np.std(delivery_tree_util), "/", \
                sum(delivery_tree_util)
        f.write("\n")
        f.write("Delivery tree link utilization min/avg/max/stddev/sum = " + str(min(delivery_tree_util)) + "/" +
                str(np.mean(delivery_tree_util)) + "/" + str(max(delivery_tree_util)) + "/" +
                str(np.std(delivery_tree_util)) + "/" + str(sum(delivery_tree_util)))
        f.write("\n")
        f.write(str(delivery_tree_util))
        f.write("\n")
        f.write(str(len(delivery_tree_util)) + " links used for delivery tree")
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
        print "Overall traffic link utilization min/avg/max/stddev/sum =", min(overall_traffic_util), "/", \
                np.mean(overall_traffic_util), "/", max(overall_traffic_util), "/", np.std(overall_traffic_util), "/", \
                sum(overall_traffic_util)
        f.write("\n")
        f.write("Overall traffic link utilization min/avg/max/stddev/sum = " + str(min(overall_traffic_util)) + "/" +
                str(np.mean(overall_traffic_util)) + "/" + str(max(overall_traffic_util)) + "/" +
                str(np.std(overall_traffic_util)) + "/" + str(sum(overall_traffic_util)))
        f.write("\n")
        f.write(str(overall_traffic_util))
        f.write("\n")
        f.write(str(len(overall_traffic_util)) + " links used for overall traffic")
        f.close()

        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        ps.dump_stats('results/profile')
        print s.getvalue()

    def get_gamma_column(self, src, dst, kid, nid, qid):
        return src*self.V*self.K*self.N*self.Q + \
            dst*self.K*self.N*self.Q + \
            kid*self.N*self.Q + nid*self.Q + qid + \
            self.V

    def get_alpha_column(self, from_sid, mid, qid):
        return from_sid*self.M*self.Q + mid*self.Q + qid + \
            self.V + self.V*self.V*self.K*self.N*self.Q

    def get_delta(self, access_id, query_id, content_id):
        if query_id in self.network.node[access_id]['user_queries'] and \
                self.network.node[access_id]['user_queries'][query_id] == content_id:
               return 1
        return 0

    def get_quality(self, quality_id):
        return self.qualities[quality_id]

    def get_beta(self, src_id, dst_id, link_id, path_id):
        if src_id == dst_id:
            return 0
        for u, v in self.network.edges_iter():
            if self.network.edge[u][v]['id'] == link_id:
                path = self.paths[src_id][dst_id][path_id]
                for i in xrange(len(path)-1):
                    if path[i] == u and path[i+1] == v:
                        return 1
                return 0
        return 0

    def get_bandwidth(self, link_id):
        for u, v in self.network.edges_iter():
            if self.network.edge[u][v]['id'] == link_id:
                return self.network.edge[u][v]['bandwidth']

    def get_IO(self, vms_id):
        return self.network.node[vms_id]['IO']

    def get_cloud(self, vms_id):
        return self.network.node[vms_id]['clouds']

    def get_lambda(self, vms_id, content_id):
        if content_id in self.network.node[vms_id]['video_src']:
            return 1
        else:
            return 0

    def populate_constraints(self, prob):
        rows = []
        cols = []
        vals = []
        my_rhs = []
        my_sense = ""
        row_offset = 0
        # populate row by row
      
        print row_offset, "constraints populated. Starting to populate constraint 1"
        # constr. 1
        # Each query only get resource from a single VMS at a single quality
        for demand_i in range(self.M):

            for vertex_i in range(self.V):
                for quality_i in range(self.Q):
                    rows.append(row_offset + demand_i)
                    cols.append(self.get_alpha_column(vertex_i,
                                                      demand_i,
                                                      quality_i))
                    vals.append(1)
            my_rhs.append(1)
            my_sense += "E"
        row_offset += self.M

        print row_offset, "constraints populated. Starting to populate constraint 3"
        # constr. 3
        # A user can access content stream at quality no higher than that is available at the VMS
        for demand_i in xrange(self.M):
            for video_i in xrange(self.K):
                val = 0
                for access_i in xrange(self.V):
                    val += self.get_delta(access_i, demand_i, video_i)
                for vms_i in xrange(self.V):
                    for quality_i in xrange(self.Q):
                        rows.append(row_offset + demand_i*self.K*self.V + video_i*self.V + vms_i)
                        cols.append(self.get_alpha_column(vms_i, demand_i, quality_i))
                        vals.append(val*self.get_quality(quality_i))
                    # constr. 2
                    # Intermediate variable which calculates the available highest stream quality at VMS
                    for quality_i in xrange(self.Q):
                        for src_i in xrange(self.V):
                            for path_i in xrange(self.N):
                                rows.append(row_offset + demand_i*self.K*self.V + video_i*self.V + vms_i)
                                cols.append(self.get_gamma_column(src_i, vms_i, video_i, path_i, quality_i))
                                vals.append(-self.get_quality(quality_i))
                    my_rhs.append(0)
                    my_sense += "L"
        row_offset += self.M*self.K*self.V


        print row_offset, "constraints populated. Starting to populate constraint 4"
        # constr. 4
        # Average quality should be no smaller than a predefined rate
        for vms_i in xrange(self.V):
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    rows.append(row_offset)
                    cols.append(self.get_alpha_column(vms_i, query_i, quality_i))
                    vals.append(self.get_quality(quality_i))
        my_rhs.append(self.qualities[0]*self.M)
        my_sense += "G"
        row_offset += 1

        print row_offset, "constraints populated. Starting to populate constraint 5"
        # constr. 5
        focus_gamma = []
        for content_i in xrange(self.K):
            for src_i in xrange(self.V):

                for dst_i in xrange(self.V):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + content_i * self.V + src_i)
                            cols.append(self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i))
                            if self.get_lambda(src_i, content_i) == 1: focus_gamma.append(self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i))
                            vals.append(1)
                if self.get_lambda(src_i, content_i) == 1:
                    my_rhs.append(1)
                    my_sense += "E"
                else:
                    my_rhs.append(0)
                    my_sense += "G"
        row_offset += self.K * self.V

        print row_offset, "constraints populated. Starting to populate constraint 8"
        # constr. 8
        for dst_i in xrange(self.V):
            for content_i in xrange(self.K):

                for path_i in xrange(self.N):
                    for src_i in xrange(self.V):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + dst_i*self.K + content_i)
                            cols.append(self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i))
                            vals.append(1)
                rows.append(row_offset + dst_i*self.K + content_i)
                cols.append(dst_i)
                vals.append(-1)
                my_rhs.append(0)
                my_sense += "L"
        row_offset += self.V * self.K
        
        print row_offset, "constraints populated. Starting to populate constraint 9"
        # constr. 9
        # The stream can be only relayed with the same quality, or be transcoded from higher quality to lower quality
        for src_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_id in xrange(self.K):
                    
                    for path_id in xrange(self.N):
                        for quality_id in xrange(self.Q):
                            rows.append(row_offset + src_i*self.V*self.K + dst_i*self.K + content_id)
                            cols.append(self.get_gamma_column(src_i, dst_i, content_id, path_id, quality_id))
                            vals.append(self.get_quality(quality_id))
                    if self.get_lambda(src_i, content_id) == 1:
                        my_rhs.append(self.qualities[0])
                    else:
                        # constr. 2
                        for quality_i in xrange(self.Q):
                            for prev_src_i in xrange(self.N):
                                if prev_src_i == src_i: continue
                                for path_i in xrange(self.N):
                                    rows.append(row_offset + src_i*self.V*self.K + dst_i*self.K + content_id)
                                    cols.append(self.get_gamma_column(prev_src_i, src_i, content_id, path_i, quality_i))
                                    vals.append(-self.get_quality(quality_i))
                        my_rhs.append(0)
                    my_sense += "L"
        row_offset += self.V*self.V*self.K

        print row_offset, "constraints populated. Starting to populate constraint 10"
        # constr. 10
        # Live contents can be streamed to a node with VMS placed
        for vms_i in xrange(self.V):
            for content_i in xrange(self.K):
                
                for path_i in xrange(self.N):
                    for src_i in xrange(self.V):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + vms_i*self.K + content_i)
                            cols.append(self.get_gamma_column(src_i, vms_i, content_i, path_i, quality_i))
                            vals.append(1)
                rows.append(row_offset + vms_i*self.K + content_i)
                cols.append(vms_i)
                vals.append(-1)
                my_rhs.append(0)
                my_sense += "L"
        row_offset += self.V*self.K

        print row_offset, "constraints populated. Starting to populate constraint 12"
        # constr. 12
        # Link bandwidth constraint
        for link_i in xrange(self.E):

            # constr. 10
            # Link utilization contributed by the delivery tree.
            for quality_i in xrange(self.Q):
                for path_i in xrange(self.N):
                    for content_i in xrange(self.K):
                        for src_i in xrange(self.V):
                            for dst_i in xrange(self.V):
                                rows.append(row_offset + link_i)
                                cols.append(self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i))
                                vals.append(self.get_quality(quality_i)*self.get_beta(src_i, dst_i, link_i, path_i))

            # constr. 11
            # Link utilization contributed by the user access traffic
            for src_i in xrange(self.V):
                for query_i in xrange(self.M):
                    for quality_i in xrange(self.Q):
                        rows.append(row_offset + link_i)
                        cols.append(self.get_alpha_column(src_i, query_i, quality_i))
                        val = 0
                        for dst_i in xrange(self.V):
                            beta = self.get_beta(src_i, dst_i, link_i, 0)
                            for content_i in xrange(self.K):
                                val += self.get_delta(dst_i, query_i, content_i) * beta
                        vals.append(self.get_quality(quality_i)*val)
            my_rhs.append(self.get_bandwidth(link_i))
            my_sense += "L"
        row_offset += self.E

        print row_offset, "constraints populated. Starting to populate constraint 13"
        # constr. 13
        # Ingress bandwidth contributed by the deliver tree
        for vms_i in xrange(self.V):
            
            for content_i in xrange(self.K):
                # constr. 2
                for quality_i in xrange(self.Q):
                    for src_i in xrange(self.V):
                        for path_i in xrange(self.N):
                            rows.append(row_offset + vms_i)
                            cols.append(self.get_gamma_column(src_i, vms_i, content_i, path_i, quality_i))
                            vals.append(self.get_quality(quality_i))
            my_rhs.append(self.get_IO(vms_i))
            my_sense += "L"
        row_offset += self.V

        print row_offset, "constraints populated. Starting to populate constraint 14"
        # constr. 14
        # Egress bandwidth utilization contributed by bothe the delivery tree and the user access
        for vms_i in xrange(self.V):

            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    val = 0
                    for access_i in xrange(self.V):
                        for content_i in xrange(self.K):
                            val += self.get_delta(access_i, query_i, content_i)
                    rows.append(row_offset + vms_i)
                    cols.append(self.get_alpha_column(vms_i, query_i, quality_i))
                    vals.append(self.get_quality(quality_i) * val)

            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + vms_i)
                            cols.append(self.get_gamma_column(vms_i, dst_i, content_i, path_i, quality_i))
                            # vals.append(self.get_quality(quality_i) * (1-self.get_lambda(vms_i, content_i)))
                            vals.append(self.get_quality(quality_i))
            my_rhs.append(self.get_IO(vms_i))
            my_sense += "L"
        row_offset += self.V

        print row_offset, "constraints populated. Starting to populate constraint 17"
        # constr. 17
        for vms_i in xrange(self.V):

            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + vms_i)
                            cols.append(self.get_gamma_column(vms_i, dst_i, content_i, path_i, quality_i))
                            # vals.append((0.3*self.ct+0.7*self.cf) * (1-self.get_lambda(vms_i, content_i)))
                            vals.append(1)

            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    val = 0
                    for access_i in xrange(self.V):
                        for content_i in xrange(self.K):
                            val += self.get_delta(access_i, query_i, content_i)
                    rows.append(row_offset + vms_i)
                    cols.append(self.get_alpha_column(vms_i, query_i, quality_i))
                    vals.append(1)
            my_rhs.append(self.get_cloud(vms_i))
            my_sense += "L"
        row_offset += self.V

        # optimization goals
        my_obj = [0] * (self.V + self.V*self.V*self.K*self.N*self.Q + self.V*self.M*self.Q)
        # U part
        for link_i in xrange(self.E):
            for src_i in xrange(self.V):
                for dst_i in xrange(self.V):
                    for content_i in xrange(self.K):
                        for path_i in xrange(self.N):
                            for quality_i in xrange(self.Q):
                                my_obj[self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i)] += \
                                        self.get_quality(quality_i) * self.get_beta(src_i, dst_i, link_i, path_i) * self.wb
            for src_i in xrange(self.V):
                for query_i in xrange(self.M):
                    for quality_i in xrange(self.Q):
                        val = 0
                        for dst_i in xrange(self.V):
                            for content_i in xrange(self.K):
                                val += self.get_delta(dst_i, query_i, content_i)
                        my_obj[self.get_alpha_column(src_i, query_i, quality_i)] += self.get_quality(quality_i) * \
                                                                                    self.get_beta(src_i, dst_i, link_i, 0) * \
                                                                                    val * self.wb
        # C part
        for vms_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            my_obj[self.get_gamma_column(vms_i, dst_i, content_i, path_i, quality_i)] += self.wc
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    val = 0
                    for access_i in xrange(self.V):
                        for content_i in xrange(self.K):
                            val += self.get_delta(access_i, query_i, content_i)
                    my_obj[self.get_alpha_column(vms_i, query_i, quality_i)] += self.wc

        # Upper bound of values
        my_ub = []
        for vms_i in xrange(self.V):
            if self.network.node[vms_i]['clouds'] != 0 or self.network.node[vms_i]['video_src'] != []:
                my_ub.append(1)
            else:
                my_ub.append(0)
        for src_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            if src_i == dst_i and self.get_lambda(src_i, content_i) == 0:
                                my_ub.append(0)
                            else: my_ub.append(1)
        for vms_i in xrange(self.V):
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    if self.network.node[vms_i]['clouds'] != 0 or self.network.node[vms_i]['video_src'] != []:
                        my_ub.append(1)
                    else: my_ub.append(0)
        # for focus in focus_gamma: print my_ub[focus]

        # Row names
        my_rownames = []
        for i in xrange(len(my_rhs)):
            my_rownames.append("c"+str(i+1))

        # Column names
        my_colnames = []
        for vms_i in xrange(self.V):
            my_colnames.append("rho"+str(i))
        for src_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            my_colnames.append("gamma("+
                                               str(src_i)+","+
                                               str(dst_i)+","+
                                               str(content_i)+","+
                                               str(path_i)+","+
                                               str(quality_i)+")")
        for vms_i in xrange(self.V):
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    my_colnames.append("alpha("+
                                       str(vms_i)+","+
                                       str(query_i)+","+
                                       str(quality_i)+")")

        prob.objective.set_sense(prob.objective.sense.minimize)
        prob.linear_constraints.add(rhs = my_rhs,
                                    senses = my_sense,
                                    names = my_rownames)
        prob.variables.add(obj = my_obj,
                           ub = my_ub,
                           names = my_colnames,
                           types = [prob.variables.type.integer] * len(my_colnames))
        """
        prob.variables.add(obj = my_obj,
                           ub = my_ub,
                           lb = [0] * len(my_colnames),
                           names = my_colnames)
        """
        prob.linear_constraints.set_coefficients(zip(rows, cols, vals))
