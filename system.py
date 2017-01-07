class System(object):
    def __init__(self, topology):
        self.topology = topology
        self.placement = {}  # server_id -> node
        self.channels = {}  # channel_id -> {'sites'->[node], 'bw'->val}

        # [channel_id -> {server_id -> probability}]
        self.access_point = [{} for _ in xrange(topology.topo.number_of_nodes())]
        # [channel_id -> {server_id -> number of viewers}]
        self.viewers = [{} for _ in xrange(topology.topo.number_of_nodes)]
        self.delivery_tree = {}  # target -> {source -> channel_id_array}
