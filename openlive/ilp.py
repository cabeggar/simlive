import cplex
import networkx as nx

class ilp():
    def __init__(self, G=nx.Graph(), n_paths, qualities):
        self.problem = cplex.Cplex()
        self.problem.objective.set_sense(problem.objective.sense.minimize)
        self.network = G
        self.qualities = qualities

        self.V = G.number_of_nodes()    # Number of nodes
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

    def get_rho(self, i):
        if self.network.node[i]['clouds'] != 0:
            return 1
        else:
            return 0

    def get_delta(self, access_id, query_id, content_id):
        if query_id in self.network.node[access_id]['user_queries'] and
           self.network.node[access_id]['user_queries'][query_id] == content_id:
               return 1
        return 0

    def get_quality(self, quality_id):
        return self.qualities[quality_id]

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
                    rows.append(vertex_i*demand_i+demand_i)
                    cols.append(self.get_alpha_column(vertex_i,
                                                      demand_i,
                                                      quality_i))
                    vals.append(1)
                my_rhs.append(self.get_rho(vertex_i))


            """
            rows.append(vertex_i)
            cols.append(vertex_i)
            vals.append(-1)
            """
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
                        rows.append(row_offset + demand_i*video_i*vms_i + video_i*vms_i + vms_i)
                        cols.append(self.get_alpha_column(vms_i, demand_i, quality_i))
                        vals.append(val*self.get_quality(quality_i))
                    # constr. 3
                    # Intermediate variable which calculates the available highest stream quality at VMS
                    for quality_i in xrange(self.Q):
                        for src_i in xrange(self.V):
                            for path_i in xrange(self.N):
                                rows.append(row_offset + demand_i*video_i*vms_i + video_i*vms_i + vms_i)
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
