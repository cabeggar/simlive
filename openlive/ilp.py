import cplex
import networkx as nx

class ilp():
    def __init__(self, G=nx.Graph(), n_paths, qualities, paths, ct, cf, wb, wc):
        self.problem = cplex.Cplex()
        self.problem.objective.set_sense(problem.objective.sense.minimize)
        self.network = G
        self.qualities = qualities
        self.paths = paths
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
        self.Q = len(qualities) # Number of available video qualities

        """
        VMS placement         [0 ~ V-1]
        delivery tree routing [V ~ V+KNQV^2-1]
        user access param     [V+KNQV^2 ~ V+KNQV^2 + VMQ-1]
        """

    def get_gamma_column(self, src, dst, kid, nid, qid):
        return src*self.V*self.K*self.N*self.Q + \
            dst*self.K*self.N*self.Q + \
            kid*self.N*self.Q + nid*self.Q + qid + \
            self.V

    def get_alpha_column(self, from_sid, mid, qid):
        return from_sid*self.M*self.Q + mid*self.Q + qid + \
            self.V + self.V*self.V*self.K*self.N*self.Q

    def get_delta(self, access_id, query_id, content_id):
        if query_id in self.network.node[access_id]['user_queries'] and
           self.network.node[access_id]['user_queries'][query_id] == content_id:
               return 1
        return 0

    def get_quality(self, quality_id):
        return self.qualities[quality_id]

    def get_beta(self, src_id, dst_id, link_id, path_id):
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

    def populate_constraints(self):
        rows = []
        cols = []
        vals = []
        my_rhs = []
        row_offset = 0
        # populate row by row

        # User access constraints: Each query links to a VMS
        # constr. 1
        for vertex_i in range(self.V):
            for demand_i in range(self.M):
                for quality_i in range(self.Q):
                    rows.append(vertex_i*self.M+demand_i)
                    cols.append(self.get_alpha_column(vertex_i,
                                                      demand_i,
                                                      quality_i))
                    vals.append(1)
                rows.appedn(vertex_i*self.M+demand_i)
                cols.append(vertex_i)
                vals.append(-1)
                my_rhs.append(0)
        row_offset += self.V * self.M

        # constr. 2
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

        row_offset += self.M

        # constr. 4
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
                    # constr. 3
                    # Intermediate variable which calculates the available highest stream quality at VMS
                    for quality_i in xrange(self.Q):
                        for src_i in xrange(self.V):
                            for path_i in xrange(self.N):
                                rows.append(row_offset + demand_i*self.K*self.V + video_i*self.V + vms_i)
                                cols.append(self.get_gamma_column(src_i, vms_i, video_i, path_i, quality_i))
                                vals.append(-self.get_quality(quality_i))
                    my_rhs.append(0)
        row_offset += self.M*self.K*self.V

        # constr. 5
        # Average quality should be no smaller than a predefined rate
        for vms_i in xrange(self.V):
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    rows.append(row_offset)
                    cols.append(self.get_alpha_column(vms_i, query_i, quality_i))
                    vals.append(self.get_quality(quality_i))
        my_rhs.append(self.qualities[-1]*self.M)
        row_offset += 1

        # constr. 6
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
                        # constr. 3
                        for quality_i in xrange(self.Q):
                            for prev_src_i in xrange(self.N):
                                for path_i in xrange(self.N):
                                    rows.append(row_offset + src_i*self.V*self.K + dst_i*self.K + content_id)
                                    cols.append(self.get_gamma_column(prev_src_i, src_i, content_id, path_i, quality_i))
                                    vals.append(-self.get_quality(quality_i))
                        my_rhs.append(0)
        row_offset += self.V*self.V*self.K

        # constr. 7
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
        row_offset += self.V*self.K

        # constr. 10
        # Link bandwidth constraint
        for link_i in xrange(self.E):

            # constr. 8
            # Link utilization contributed by the delivery tree.
            for quality_i in xrange(self.Q):
                for path_i in xrange(self.N):
                    for content_i in xrange(self.K):
                        for src_i in xrange(self.V):
                            for dst_i in xrange(self.V):
                                rows.append(row_offset + link_i)
                                cols.append(self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i))
                                vals.append(self.get_quality(quality_i)*self.get_beta(src_i, dst_i, link_i, path_i))

            # constr. 9
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
        row_offset += self.E

        # constr. 11
        # Ingress bandwidth contributed by the deliver tree
        for vms_i in xrange(self.V):
            
            for content_i in xrange(self.K):
                # constr. 3
                for quality_i in xrange(self.Q):
                    for src_i in xrange(self.V):
                        for path_i in xrange(self.N):
                            rows.append(row_offset + vms_i)
                            cols.append(self.get_gamma_column(src_i, vms_i, content_i, path_i, quality_i))
                            vals.append(self.get_quality(quality_i))
            my_rhs.append(self.get_io(vms_i))
        row_offset += self.V

        # constr. 12
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
                            vals.append(self.get_quality(quality_i))
            my_rhs.append(self.get_io(vms_i))
        row_offset += self.V

        # constr. 15
        for vms_i in xrange(self.V):

            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            rows.append(row_offset + vms_i)
                            cols.append(self.get_gamma_column(vms_i, dst_i, content_i, path_i, quality_i))
                            vals.append(0.3*self.ct+0.7*self.cf)

            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    val = 0
                    for access_i in xrange(self.V):
                        for content_i in xrange(self.K):
                            val += self.get_delta(access_i, query_i, content_i)
                    rows.append(row_offset + vms_i)
                    cols.append(self.get_alpha_column(vms_i, query_i, quality_i))
                    vals.append((0.3*self.ct + 0.7*self.cf) * val)
            my_rhs.append(self.get_cloud(vms_i))
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
                                my_obj[self.get_gamma_column(src_i, dst_i, content_i, path_i, quality_i)] +=
                                    self.get_quality(quality_i) * self.get_beta(src_i, dst_i, link_i, path_i) * self.wb
            for src_i in xrange(self.V):
                for query_i in xrange(self.M):
                    for quality_i in xrange(self.Q):
                        val = 0
                        for dst_i in xrange(self.V):
                            for content_i in xrange(self.K):
                                val += self.get_delta(dst_i, query_i, content_i)
                        my_obj[self.get_alpha_column(src_i, query_i, quality_i)] += self.get_quality(quality_i) *
                                                                                    self.get_beta(src_i, dst_i, link_i, 0) *
                                                                                    val * self.wb
        # C part
        for vms_i in xrange(self.V):
            for dst_i in xrange(self.V):
                for content_i in xrange(self.K):
                    for path_i in xrange(self.N):
                        for quality_i in xrange(self.Q):
                            my_obj[self.get_gamma_column(vms_i, dst_i, content_i, path_i, quality_i)] += self.wc * 
                                                                                                         (ct*0.3 + cf*0.7)
            for query_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    val = 0
                    for access_i in xrange(self.V):
                        for content_i in xrange(self.K):
                            val += self.get_delta(access_i, query_i, content_i)
                    my_obj[self.get_alpha_column(vms_i, query_i, quality_i)] += self.wc *
                                                                                (ct*0.3 + cf*0.7) *
                                                                                val

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
                        for quality_i in xrange(self.X):
                            if src_i == dst_i: my_ub.append(0)
                            else: my_ub.append(1)
        for vms_i in xrange(self.V):
            for content_i in xrange(self.M):
                for quality_i in xrange(self.Q):
                    if self.network.node[vms_i]['clouds'] != 0 or self.network.node[vms_i]['video_src'] != []:
                        my_ub.append(1)
                    else: my_ub.append(0)

