# import json
import networkx as nx
# from networkx.readwrite import json_graph
from itertools import islice


class d2resource:
    def __init__(self, pickle_file):
        self.topo = None
        nx.read_gpickle(self.topo, pickle_file)

        self.V = len(self.topo.nodes)    # node no
        self.E = len(self.topo.edges)    # edge no
        self.N = 3                  # path no per node pair
        self.Q = [0.0005, 0.0015, 0.003, 0.005]

        self.paths = self._kshortest(self, self.N)
        # self.path_node_assoc
        self.link_path_assoc = [set()] * self.E
        self._cal_link_path_assoc()

    # routing
    def _kshortest(self, k):
        paths = [[] for _ in xrange(self.V)]

        for i, u in enumerate(self.topo.nodes()):
            for j, v in enumerate(self.topo.nodes()):
                if i == j:
                    paths[i].append([])
                    continue

                # get k shortest from all shortest simple paths from u to v
                # weight set to 1 to get shortest hops path
                paths[i].append(list(islice(
                    nx.shortest_simple_paths(self.topo, u, v, weight=weight),
                    k)))

        return paths

    # To get whether a link is on n-th path from s to d
    def _cal_link_path_assoc(self):
        for src in range(self.V-1):
            for dst in range(src+1, self.V):
                if src == dst: continue
                for nid in range(self.N):
                    path = self.paths[src][dst][nid]

                    for i in range(1, len(path)):
                        link_id = self.topo[path[i-1]][path[i]]['id']
                        path_id = self.serialize_path_id(src, dst, nid)
                        self.link_path_assoc[link_id].add(path_id)

    def serialize_path_id(self, src, dst, nid):
        if src == dst:
            return -1

        if src > dst:
            """
            temp = src
            src = dst
            dst = temp
            """
            src, dst = dst, src
            
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
            """
            temp = src
            src = dst
            dst = temp
            """
            src, dst = dst, src

        link_id = (2*self.V-src-1)*src/2 + (dst - src - 1)

        return link_id

    def deserialize_link_id(self, link_id):
        for src in range(1, self.V):
            if (2*self.V-src-1)*src/2 > link_id:
                break
        src = src - 1

        dst = link_id - (2*self.V-src-1)*src/2 + src + 1

        return [src, dst]

    def get_IO_bw(self):
        return nx.get_node_attributes(self.topo, 'IO')

    def get_compute(self):
        return nx.get_node_attributes(self.topo, 'clouds')
