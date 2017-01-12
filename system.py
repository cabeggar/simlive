from collections import defaultdict


class System(object):
    def __init__(self, topology):
        self.topology = topology
        # channel_id -> {'site>[node], 'bw'->val, 'src'->source}
        self.channels = defaultdict(dict)
        # [channel_id -> {server_id -> probability}]
        self.access_point = [defaultdict(dict) for _ in xrange(topology.topo.number_of_nodes())]
        # [channel_id -> number of viewers]
        self.viewers = [defaultdict(int) for _ in xrange(topology.topo.number_of_nodes())]
        # target -> {source -> channel_id_array}
        self.delivery_tree = defaultdict(lambda : defaultdict(list))
        self.viewers = [{} for _ in xrange(topology.topo.number_of_nodes)]
        # target -> {source -> channel_id_array}
        self.delivery_tree = defaultdict(defaultdict(list))
