import json
import networkx as nx
from networkx.readwrite import json_graph
import ConfigParser


class generator:
    def __init__(self, topo_file=None, topo_type=0):
        self.topo = None

        if topo_file is None:
            if topo_type == 0:
                self.topo = self._generate_nsf_topology()

            if topo_type == 1:
                self.topo = self._generate_fattree_topology()

            if topo_type == 2:
                self.topo = self._generate_small_world_topology()
                pass

        else:
            f = open(topo_file, "r")
            self.topo = json_graph.node_link_graph(json.load(f))
            f.close()

    def _generate_nsf_topology(self):
        # TODO generate NSF topology
        # TODO assign weight to 1
        pass

    def _generate_fattree_topology(self, port_no=4):
        # TODO generate fattree topology
        # TODO assign weight to 1
        pass

    def _generate_small_world_topology(self, node=20, neigh=4, rewire=0.1):
        # TODO generate small world topology
        pass

    def _assign_src(self, src_no):
        # TODO: randomly pick different sites to attach source
        pass

    def _assign_user(self, block_no, user_no, src_no):
        # TODO: calcualte <block_no> end_points

        # TODO: assign block of users randomly to the endponts

        # TODO: attach to self.topo's attribute (userNo)

        # TODO: randomly assign one source to each user
        pass

    def _assign_cloud_resource(self, cloud_no, avg_comp_resource):
        # TODO: randomly pick cloud_no sites

        # TODO: assign randomly 1/2 avg_comp_resource to 3/2 avg_comp_resource
        pass

    def _assign_link_bandwidth(self, avg_link_bandwidth):
        # TODO: assign randomly 1/2 avg_link_bandwidth to 3/2 avg_link_band
        pass

    def start_generator(self, config_file, sav_topo):
        config = ConfigParser.ConfigParser()
        config.read(open(config_file))

        # TODO cal the above functions to assign resource and demand

        # TODO save the topology with resoruce configured
        f = open(sav_topo)
        # f.write( ... some json parsed topology file) ...
        f.close()
