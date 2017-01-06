class System(object):
    def __init__(self, topology):
        self.topology = topology
        self.placement = {}  # server_id -> node
        self.channel_sources = {}  # channel_id -> {'sites'->[node], 'bw'->val}

        # [channel_id -> {server_id -> probability}]
        self.access_point = [{}] * topology.topo.number_of_nodes()
        self.delivery_tree = {}  # target -> {source -> channel_id_array}
