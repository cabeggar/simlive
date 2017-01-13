import cplex
from math import log
import networkx as nx


class LiveJack(object):
    def __init__(self, topology, channels, viewers):
        self.topology = topology

        # node attr
        self.G = topology.G
        self.node_number = self.G.number_of_nodes()

        # transfer id based channel to map
        # [{'sites'->{nodes}, 'bw'->float, 'src'->node}]
        self.channels = [None] * len(channels)
        self.channel_map = [None] * len(channels)

        self.qoe_cost = None  # TODO: qoe cost
        self.cost_thres = None

        channel_cnt = 0

        for channel_id in self.channel:
            self.channel_map[channel_cnt] = channel_id
            channels[channel_cnt] = channels[channel_id]
            channel_cnt = channel_cnt + 1

        # record only the viewers that are directly connected to the server
        self.viewers = viewers

        # [channel_id -> vmf site, ... ]
        self.local_viewer_map = [{}] * self.node_number

        # cost model
        self.site_cost_scala = 1000
        self.lasthop_cost_scala = 1
        # self.trans_cost = None

    def __serial__(self, channel_id, src, dst):
        return channel_id * self.node_number * self.node_number + \
            src * self.node_number + dst

    def __deserial__(self, var_id):
        return [var_id / (self.node_number * self.node_number),
                var_id % (self.node_number * self.node_number)/self.node_number,
                var_id % (self.node_number)]

    def __serial_vmf_assign__(self, channel_id, site_id=None,
                              viewer_id=None):
        if viewer_id is None:
            return len(self.channels) * self.node_number * self.node_number + \
               channel_id * self.node_number + site_id
        else:
            return channel_id * self.node_number * self.node_number + \
               site_id * self.node_number + viewer_id

    def __deserial_vmf_assign__(self, var_id, is_assign=True):
        if is_assign:
            return [var_id / (self.node_number * self.node_number),
                    var_id % (self.node_number * self.node_number) /
                    self.node_number,
                    var_id % (self.node_number)]
        else:
            var_id = var_id - self.node_number * self.node_number *\
                len(self.channels)
            return [var_id / self.node_number,
                    var_id % self.node_number]

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

    def get_site_cost(self, channel_idx, site_idx):
        return len(nx.shortest_path(self.G,
                                    self.channels[channel_idx]['src'],
                                    self.site_idx))

    def get_trans_cost(self, src, dst):
        return len(nx.shortest_path(self.G, src, dst))

    def site_delta_constraints(self, viewer_delta):
        thres_flash_crowds = 10000

        if (viewer_delta >= thres_flash_crowds):
            return self.node_number
        else:
            return int(log(viewer_delta)/log(thres_flash_crowds) *
                       self.node_number)

    def delivery_tree(self):
        prob = cplex.Cplex()

        prob.objective.set_sense(prob.objective.sense.minimize)

        rows = []
        cols = []
        vals = []
        my_rhs = []
        row_offset = 0
        my_ub = [1] * len(self.channels) * self.node_number * self.node_number
        my_lb = [0] * len(self.channels) * self.node_number * self.node_number
        my_ctype = "I" * len(self.channels) * \
            self.node_number * self.node_number
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

        my_sense = my_sense + "E" * len(self.channels)

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
                    my_obj.append(self.channels[channel_idx]['bw'])

        my_sense = my_sense + "L" * len(self.G.number_of_edges())

        prob.linear_constraints.add(rhs=my_rhs, senses=my_sense)

        prob.variables.add(obj=my_obj, lb=my_lb,
                           ub=my_ub, types=my_ctype)

        prob.linear_constraints.set_coefficients(zip(rows, cols, vals))

        prob.solve()
        vals = prob.solution.get_values()

    def assign_sites(self):
        # based on unassigned requests, and existing sites, calculate sites
        prob = cplex.Cplex()

        prob.objective.set_sense(prob.objective.sense.minimize)

        rows = []
        cols = []
        vals = []
        my_rhs = []
        row_offset = 0

        my_ub = [1] * (len(self.channels) * len(self.node_number) * \
                       len(self.node_number),
                       len(self.channels) * len(self.node_number))
        my_lb = [0] * (len(self.channels) * len(self.node_number) * \
                       len(self.node_number),
                       len(self.channels) * len(self.node_number))
        my_ctype = "I" * (len(self.channels) * self.node_number *
                          self.node_number + len(self.channels) *
                          self.node_number)
        my_sense = ""

        # constraints on vmf modifications
        for channel_idx in range(len(self.channels)):
            rhs_channel = 0

            for site in range(self.node_number):
                rows.append(row_offset)
                cols.append(self.__serial_vmf_assign__(channel_idx,
                                                       site))

                if site in self.channels[channel_idx]['sites']:
                    vals.append(-1)
                    rhs_channel = rhs_channel - 1
                else:
                    vals.append(1)
                    rhs_channel = rhs_channel + 1

            row_offset = row_offset + 1
            my_rhs.append(rhs_channel)
            my_sense = my_sense + "L"

        # constraints on aggregate bandwidth
        for site_idx in range(self.node_number):

            for viewer_idx in range(self.node_number):
                for channel_idx in range(len(self.channels)):
                    rows.append(row_offset)
                    cols.append(self.__serial_vmf_assign__(channel_idx,
                                                           site_idx,
                                                           viewer_idx))
                    vals.append(self.channels[channel_idx]['bw'])

            row_offset = row_offset + 1
            my_rhs.append(self.G.node[site_idx]['capacity'])
            my_sense = my_sense + "L"

        # constraints on placement
        for site_idx in range(self.node_number):
            for channel_idx in range(self.channels):
                rows.append(row_offset)
                cols.append(self.__serial_vmf_assign__(channel_idx,
                                                       site_idx))
                vals.append(-1)

                for viewer_idx in range(self.channels):
                    rows.append(row_offset)
                    cols.append(self.__serial_vmf_assign__(channel_idx,
                                                           site_idx,
                                                           viewer_idx))
                    vals.append(1)

                row_offset = row_offset + 1
                my_rhs.append(0)
                my_sense = my_sense + "L"

        # total viewers
        for channel_idx in range(len(self.channels)):
            for viewer_idx in range(self.node_number):

                for site_idx in range(self.node_number):
                    rows.append(row_offset)
                    cols.append(self.__serial_vmf_assign__(channel_idx,
                                                           site_idx,
                                                           viewer_idx))
                    vals.append(1)

                row_offset = row_offset + 1
                my_rhs.append(self.viewers[channel_idx][viewer_idx])
                my_sense = my_sense + "L"

        # objective
        my_obj = []

        for channel_idx in range(len(self.channels)):

            for site_idx in range(len(self.node_number)):
                for viewer_idx in range(len(self.node_number)):
                    lasthop_cost = self.get_trans_cost(site_idx, viewer_idx)

                    my_obj.append(lasthop_cost *
                                  self.lasthop_cost_scala)

        for channel_idx in range(len(self.channels)):
            for site_idx in range(len(self.node_number)):
                site_cost = self.get_site_cost(channel_idx, site_idx)

                my_obj.append(site_cost * self.site_cost_scala)

        prob.linear_constraints.add(rhs=my_rhs, senses=my_sense)

        prob.variables.add(obj=my_obj, lb=my_lb,
                           ub=my_ub, types=my_ctype)

        prob.linear_constraints.set_coefficients(zip(rows, cols, vals))
        prob.solve()
        vals = prob.solution.get_values()

        # get assignment results
        for var_idx in range(self.node_number * len(self.channels)):
            var_id = var_idx + self.node_number *\
                self.node_number * len(self.channels)

            if vals[var_id] == 1:
                [channel_id, site_id] = self.__deserial_vmf_assign__(var_id)
                self.channels[channel_id]['new_site'].insert(site_id)

        # based on sites, calculate local decision
        for channel_idx in range(len(self.channels)):
            sites = self.channels[channel_idx]['sites']

            for loc in range(self.node_number):
                # min affinity
                min_cost = float("inf")
                min_site = -1

                for site in sites:
                    if self.qoe_cost[site][loc] < min_cost:
                        min_cost = self.qoe_cost[site][loc]
                        min_site = site

                if min_cost > self.cost_thres:  # for later VMF assignment
                    min_site = self.channels[channel_idx]['src']

                channel_id = self.channel_map[channel_idx]

                self.local_viewer_map[loc][channel_id] = min_site
