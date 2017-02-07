from collections import deque
from collections import defaultdict
import networkx as nx


class Multicast(object):
    def __init__(self, topology, access_point,
                 delivery_tree, channel_state):
        self.topology = topology
        self.access_point = access_point
        self.delivery_tree = delivery_tree
        self.channel_state = channel_state

        self.access_point_neighborhood = {}

        for src in self.access_point:
            src_neighbor = []

            for dst in self.access_point:
                if dst != src:
                    src_neighbor.append([dst,
                                         len(self.topology.routing[src][dst])])

            src_neighbor = sorted(src_neighbor,
                                  key=lambda x: x[1])

            src_neighbor = [x[0] for x in src_neighbor]

            self.access_point_neighborhood[src] = src_neighbor

    def Local_join(self, new_channels, new_viewers):
        # TODO compute delivery tree for new channels
        pass

        # TODO compute appended tree for new viewers
        pass
