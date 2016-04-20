import cplex


class ilp():
    def __init__(self, d2inst):
        d2inst
        self.problem = cplex.Cplex()
        self.problem.objective.set_sense(problem.objective.sense.maximize)

        self.V

        """
        VMS placement         [0 ~ V-1]
        delivery tree routing [V ~ V+KNQV^2-1]
        user access param     [V+KNQV^2 + V+KNQV^2 + VMQ-1]
        """

    def get_gamma_column(src, dst, cid, nid, qid):
        return src*self.V*self.K*self.N*self.Q + \
            dst*self.K*self.N*self.Q + \
            cid*self.N*self.Q + nid*self.Q + qid + \
            self.V

    def get_alpha_column(did, from_sid, qid):
        return did*self.V*self.Q + from_sid*self.Q + qid + \
            self.V + self.V*self.V*self.K*self.N*self.Q

    def populate_constraints():
        rows = []
        cols = []
        vals = []
        row_offset = 0
        # populate row by row

        # user access constraints
        # constr. 1
        for vertex_i in range(self.V):
            for demand_i in range(self.M):
                for quality_i in range(self.Q):
                    rows.append(vertex_i)
                    cols.append(get_alpha_column(demand_i,
                                                 vertex_i,
                                                 quality_i))
                    vals.append(1)
            rows.append(vertex_i)
            cols.append(vertex_i)
            vals.append(-1)
        row_offset += self.V

        # constr. 2
        for demand_i in range(self.M):
            for from_vertex_i in range(self.V):
                for quality_i in range(self.Q):
                    rows.append(row_offset + demand_i)
                    cols.append(get_alpha_column(demand_i,
                                                 from_vertex_i,
                                                 quality_i))
                    vals.append(1)

        row_offset += self.M

        # constr. 4
        for

