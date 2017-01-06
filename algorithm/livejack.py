import cplex
import networkx as nx
from topology import Topology

class LiveJack(object):
    def __init__(self, topology, channels, viewers):
        self.topology = topology

        self.G = topology.G

        self.node_number = self.G.number_of_nodes()

        # transfer id based channel to map
        # [{'sites'->[nodes], 'bw'}]
        self.channels = [None] * len(channels)
        self.channel_map = [None] * len(channels)

        channel_cnt = 0

        for channel_id in self.channel:
            channel_map[channel_cnt] = channel_id
            channels[channel_cnt] = channels[channel_id]
            channel_cnt = channel_cnt + 1

        self.viewers = viewers

    def __serial__(self, channel_id, src, dst):
        return channel_id * self.node_number * self.node_number + \
            src * self.node_number + dst

    def __deserial__(self, var_id):
        return [var_id / (self.node_number * self.node_number),
                var_id % (self.node_number * self.node_number)/self.node_number,
                var_id % (self.node_number)]

    def __cal_route__(self, routing):
        for (link_src, link_dst) in self.G.edges():
            self.G[link_src][link_dst]['routes'] = set()

        for src in range(self.node_number):
            for dst in range(self.node_number):
                path = self.topology.routing[src][dst]

                for idx in range(len(path)-1):
                    link_src = path[idx]
                    link_dst = path[idx+1]
                    self.G[link_src][link_dst]['routes'].add((src, dst))

    def delivery_tree(self):
        prob = cplex.Cplex()
        prob.objective.set_sense(problem.objective.sense.minimize)

        rows = []
        cols = []
        vals = []
        my_rhs = []
        row_offset = 0
        my_ub = [1] * len(self.channels) * node_number * node_number
        my_lb = [0] * len(self.channels) * node_number * node_number
        my_ctype = "I" * len(self.channels) * node_number * node_number
        my_sense = ""

        # tree constraint
        for channel_id in self.channels:
            for src in range(self.node_number):
                for dst in range(self.node_number):
                    if (src != dst):
                        rows.append(row_offset)
                        cols.append(self.__serial__(row_offset, src, dst))
                        vals.append(1)

                my_rhs.append(len(self.channels[channel_id]['sites']) - 1)

            row_offset = row_offset + 1

        my_sense = my_sense + "E" * len(channels)

        # delivery site constraint
        for src in range(self.node_number):
            for channel_idx in range(len(self.channels)):
                for dst in range(self.node_number):
                    rows.append(row_offset)
                    cols.append(self.__serial__(channel_idx, src, dst))
                    vals.append(1)

                if src in self.channels['sites']:
                    my_rhs.append(1)
                else:
                    my_rhs.append(0)

                row_offset = row_offset + 1

        my_sense = my_sense + "E" * len(self.node_number)

        for dst in range(self.node_number):
            for channel_idx in range(len(self.channels)):
                for src in range(self.node_number):
                    rows.append(row_offset)
                    cols.append(self.__serial__(channel_idx, src, dst))
                    vals.append(1)

                if dst in self.channels['sites']:
                    my_rhs.append(1)
                else:
                    my_rhs.append(0)

                row_offset = row_offset + 1

        my_sense = my_sense + "E" * len(self.node_number)

        # bandwidth constraint
        for (link_src, link_dst) in self.topology.edges():
            routes = self.topology[link_src][link_dst]['routes']

            for src in range(self.node_number):
                for dst in range(self.node_number):
                    if (src, dst) in routes:
                        for channel_idx in range(len(self.channels)):
                            rows.append(row_offset)
                            cols.append(self.__serial__(channel_idx,
                                                        src, dst))
                            vals.append(self.channels[channel_idx]['bw'])

            my_rhs.append(self.G[link_src][link_dst])
            row_offset = row_offset + 1

        # objective
        my_obj = []

        for src in range(len(self.node_number)):
            for dst in range(len(self.node_number)):
                for channel_idx in range(len(self.node_number)):
                    my_obj.append(channels[channel_idx]['bw'])

        my_sense = my_sense + "L" * len(G.number_of_edges())

        prob.linear_constraints.add(rhs=my_rhs, senses=my_sense)

        prob.variables.add(obj=my_obj, lb=my_lb,
                           ub=my_ub, types=my_ctype)

        prob.linear_constraints.set_coefficients(zip(rows, cols, vals))

        prob.solve()
        vals = prob.solution.get_values()


    def assign_vmf(self):

        # out put sites
