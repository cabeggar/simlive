import json
import networkx as nx
from networkx.readwrite import json_graph
from itertools import islice


class d2resource:
    def __init__(self, topo_file):
        f = open(topo_file, "r")
        data = json.load(f)
        f.close()

        self.topo = json_graph.node_link_graph(data)
        self.V = len(self.topo.nodes)    # node no
        self.N = 3                  # path no per node pair

        self.paths = self._kshortest(self, self.N)

    def _kshortest(self, k):
        paths = [[] for _ in xrange(self.V)]

        for i, u in enumerate(self.topo.nodes()):
            for j, v in enumerate(self.topo.nodes()):
                if i == j:
                    continue

                paths[i].append(list(islice(
                    nx.shortest_simple_paths(self.topo, u, v, k),
                    weight='capacity')))

        return paths

    def serialize_path_id(self, src, dst, nid):
        if src == dst:
            return -1

        if src > dst:
            temp = src
            src = dst
            dst = temp

        path_id = ((2*self.V-src-1)*src/2 + (dst - src - 1))*self.N + nid

        return path_id

    def deserialize_path_id(self, path_id):
        nid = path_id % self.N

        phrase = (path_id - nid)/self.N

        src = 0

        for src in range(1, self.V):
            if (2*self.V-src-1)*src/2 > phrase:
                break

        src = src-1

        dst = phrase - (2*self.V-src-1)*src/2 + src + 1

        return [src, dst, nid]

    def serialize_link_id(self, src, dst):
        if src == dst:
            return -1

        if src > dst:
            temp = src
            src = dst
            dst = temp

        link_id = (2*self.V-src-1)*src/2 + (dst - src - 1)

        return link_id

    def deserialize_link_id(self, link_id):
        for src in range(1, self.V):
            if (2*self.V-src-1)*src/2 > link_id:
                break
        src = src - 1

        dst = link_id - (2*self.V-src-1)*src/2 + src + 1

        return [src, dst]

    def get_path_links_assoc(self, src, dst, nid):
        assoc_links = []
        path = self.paths[src][dst][nid]

        for i in range(1, len(path)):
            assoc_links.append(self.serialize_link_id(path[i-1], path[i]))

        return assoc_links

    def get_IO_bw(self):
        return nx.get_node_attributes(self.topo, 'IO')

    def get_compute(self):
        return nx.get_node_attributes(self.topo, 'compute')
