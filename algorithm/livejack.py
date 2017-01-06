import cplex
import networkx as nx


class LiveJack(object):
    def __init__(self, topology):
        self.topology = topology
        self.node_number = nx.number_of_nodes(self.topology)
        self.channel_sources = {}

        self.channel_access = {}
        self.routing = {{}}
        self.bandwidth = {{}}

    def __serial__(self, channel_id, src, dst):
        return channel_id * self.node_number * self.node_number + \
            src * self.node_number + dst

    def __deserial__(self, var_id):
        return [var_id / (self.node_number * self.node_number),
                var_id % (self.node_number * self.node_number)/self.node_number,
                var_id % (self.node_number)]

    def delivery_tree(self):
        problem = cplex.Cplex()
        self.problem.objective.set_sense(problem.objective.sense.minimize)

        rows = []
        cols = []
        vals = []
        my_rhs = []
        row_offset = 0

        # tree constraint
        for channel_id in self.channel_sources:
            for src in range(self.node_number):
                for dst in range(self.node_number):
                    if (src != dst):
                        rows.append(row_offset)
                        cols.append(self.__serial__(row_offset, src, dst))
                        vals.append(1)

                my_rhs.append(len(self.channel_access[channel_id]) - 1)

            row_offset = row_offset + 1

        # delivery site constraint
        for src in range(self.node_number):
            channel_cnt = 0
            for channel_id in self.channel_sources:
                for dst in range(self.node_number):
                    rows.append(row_offset)
                    cols.append(self.__serial__(channel_cnt, src, dst))
                    vals.append(1)

                if src in self.channel_access:
                    my_rhs.append(1)
                else:
                    my_rhs.append(0)

                row_offset = row_offset + 1
                channel_cnt = channel_cnt + 1

        for dst in range(self.node_number):
            channel_cnt = 0
            for channel_id in self.channel_sources:
                for src in range(self.node_number):
                    rows.append(row_offset)
                    cols.append(self.__serial__(channel_cnt, src, dst))
                    vals.append(1)

                if src in self.channel_access:
                    my_rhs.append(1)
                else:
                    my_rhs.append(0)

                row_offset = row_offset + 1
                channel_cnt = channel_cnt + 1

        # bandwidth constraint
        for link_src in range(self.routing):
            for link_dst in range(self.routing[link_src]):
                for src in range(self.node_number):
                    for dst in range(self.node_number):
                        if self.routing(link_src, link_dst, src, dst):
                            for channel_idx in range(len(self.channel_access)):
                                rows.append(row_offset)
                                cols.append(self.__serial__(channel_idx,
                                                            src, dst))
                                vals.append(self.bw_usage[channel_id])

                my_rhs.append(self.routing[link_src][link_dst])
                row_offset = row_offset + 1
