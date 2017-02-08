from collections import defaultdict


class System(object):
    def __init__(self, topology, trace):
        self.topology = topology
        self.trace = trace

        # site_id -> (channel_id -> set(viewer_id))
        self.access_point = defaultdict(defaultdict(set) for _ in
                                        xrange(self.topology.number_of_nodes))
        self.access_point_capacity = [100 for _ in
                                      xrange(self.topology.number_of_nodes)]
        # target -> {source -> [channel_id, leaf]}
        self.delivery_tree = defaultdict(lambda: defaultdict(list))

        # channel -> {viewer_id->access_point})
        self.channel_state = defaultdict(lambda: defaultdict(int))

        # FIXME deprecated
        # channel_id -> {'site>[node], 'bw'->val, 'src'->source}
        # self.channels = defaultdict(dict)

        # FIXME: deprecated
        # [channel_id -> number of viewers]
        # self.viewers = [defaultdict(int) for _ in
        #                xrange(topology.topo.number_of_nodes())]

    def run(self):
        event = self.trace.get_next_event()

        if event is None:
            return False

        joining_channels, leaving_channels, joining_viewers, leaving_viewers = \
            event

        self._remove_leaving_channels(leaving_channels)
        self._remove_leaving_viewers(leaving_viewers)

        # TODO: decision-based incremental tree appending
            # 1. new channel & new viewers -> build spanning tree
            # 2. old channel & new viewers -> increment spanning tree

        # TODO: require refines ... say 100 rounds a time...
            # reorgainize tree and viewer assignment

        return True

    def _del_sorted_from_sorted(self, orig, to_del):
        idx_orig = 0
        idx_del = 0

        del_cnt = 0

        while idx_orig < len(orig) and idx_del < len(to_del):
            if orig[idx_orig] == to_del[idx_del]:
                del orig[idx_orig]
                del_cnt += 1
                idx_del += 1
            elif orig[idx_orig] > to_del[idx_del]:
                idx_del += 1
            else:
                idx_orig += 1

        return del_cnt

    def _remove_leaving_channels(self, leaving_channels):
        leaving_channels = leaving_channels.sort()

        # Restore the link bandwidth
        for dst, src_channel_map in self.delivery_tree.iteritems():
            for src, channels in src_channel_map.iteritems():
                del_cnt = self._del_sorted_from_sorted(channels,
                                                       leaving_channels)
                links = self.topology.get_links_on_path(src, dst)

                for u, v in links:
                    self.topology.edge[u][v]['capacity'] += 100 * del_cnt
                    self.topology.edge[u][v]['cost'] -= 100 * del_cnt

        # Restore the access resouce
        for channel_id in leaving_channels:
            for ap_id in self.topology.number_of_nodes:
                if channel_id in self.access_point[ap_id]:
                    viewer_no = len(self.access_point[ap_id][channel_id])
                    self.access_point_capacity[ap_id] += viewer_no
                    del self.access_point[ap_id][channel_id]

            del self.channel_state[channel_id]

    def _remove_leaving_viewers(self, leaving_viewers):
        for viewer in leaving_viewers:
            channel_id = self.trace.viewer_info[1]
            channel_bw = self.trace.channel_info[channel_id][1]

            ap_id = self.channel_state[channel_id]

            self.access_point_capacity[ap_id] += channel_bw
            del self.access_point[ap_id][channel_id][viewer]

            # delete state
            del self.channel_state[channel_id][viewer]

            # shrink delivery tree if needed
            if len(self.access_point[ap_id][channel_id][0]) == 0:     # 0 viewer
                for src in range(len(self.topology.number_of_nodes)):
                    if self.access_point[ap_id][src][channel_id][1]:  # is leaf
                        del self.access_point[ap_id][src][channel_id]
