import json
import networkx as nx
from networkx.readwrite import json_graph
import ConfigParser
import random

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
        G = nx.Graph()
        G.add_nodes_from(range(13))
        G.add_edges_from([(0,1),(0,8),
                          (1,2),(1,3),
                          (2,5),
                          (3,4),(3,10),
                          (4,5),(4,6),
                          (5,7),(5,12),
                          (6,8),
                          (7,9),
                          (9,11),(9,13),
                          (10,13),
                          (11,12),
                          (12,13)],
                          weight=1)
        _id = 0
        for u, v in G.edges_iter():
            G.edge[u][v]['id'] = _id
            _id += 1
        for u in G.nodes_iter():
            G.node[u]['video_src'] = []
            G.node[u]['user_queries'] = {}
            G.node[u]['clouds'] = 0
            G.node[u]['IO'] = 0

        return G

    def _generate_fattree_topology(self, port_no=4):
        edge = port_no*port_no/2
        aggr = edge
        core = edge/2

        G = nx.Graph()
        G.add_nodes_from(range(edge+aggr+core))
        
        for i in xrange(port_no):
            core_switch = edge+aggr
            for j in xrange(port_no/2):
                for k in xrange(port_no/2):
                    # Connect edge switches with aggregation switches
                    G.add_edge(i*2+j, i*2+edge+k, {'weight': 1})
                    # Connect aggregation switches with core switches
                    G.add_edge(i*2+edge+k, core_switch, {'weight': 1})  
                    core_switch += 1
       
        _id = 0
        for u, v in G.edges_iter():
            G.edge[u][v]['id'] = _id
            _id += 1
        for u in G.nodes_iter():
            G.node[u]['video_src'] = []
            G.node[u]['user_queries'] = {}
            G.node[u]['clouds'] = 0
            G.node[u]['IO'] = 0

        return G

    def _generate_small_world_topology(self, node=20, neigh=4, rewire=0.1):
        G = nx.watts_strogatz_graph(node, neigh, rewire)

        _id = 0
        for u, v in G.edges_iter():
            G.edge[u][v]['id'] = _id
            G.edge[u][v]['weight'] = 1
            _id += 1
        for u in G.nodes_iter():
            G.node[u]['video_src'] = []
            G.node[u]['user_queries'] = {}
            G.node[u]['clouds'] = 0
            G.node[u]['IO'] = 0

        return G

    def _assign_src(self, src_no):
        for i in xrange(src_no):
            node = random.randint(0, self.topo.number_of_nodes()-1)
            print node
            print self.topo.node[node]
            self.topo.node[node]['video_src'].append(i)
            print self.topo.node[node]

    def _assign_user(self, block_no, user_no, src_no):
        # Find location of blocks
        if block_no == self.topo.number_of_nodes():
            blocks = self.topo.nodes_iter()
        elif block_no > self.topo.number_of_nodes():
            print "Block number exceeds node numbers"
        else:
            blocks = []
            node0 = random.randint(0, self.topo.number_of_nodes()-1)
            blocks.append(node0)
            _paths = nx.single_source_shortest_path(self.topo, node0)
            paths = []
            for value in _paths.itervalues():
                paths.append(value)
            paths.sort(key = lambda path: len(path))
            for i in xrange(block_no-1):
                blocks.append(paths[-i-1][-1])

        # Assign users to blocks
        users = range(user_no)
        blocks_users = [[] for _ in xrange(block_no)]
        for user in users:
            random.choice(blocks_users).append(user)

        # Assign blocks to nodes
        for i, block in enumerate(blocks):
            user_queries = {}
            for user in blocks_users[i]:
                # Randomly assign contents to users
                query_video = random.randint(0, src_no-1)
                """
                while query_video in self.topo.node[block]['video_src']:
                    query_video = random.randint(0, src_no-1)
                """
                user_queries[user] = query_video
            self.topo.node[block]["user_queries"] = user_queries

        # Add userNo attr to graph
        self.topo.graph["userNo"] = user_no


    def _assign_cloud_resource(self, cloud_no, avg_comp_resource, avg_IO_bandwidth):
        # Randomly pick some locations for clouds
        clouds = []
        if cloud_no == self.topo.number_of_nodes():
            clouds = self.topo.nodes()
        elif cloud_no > self.topo.number_of_nodes():
            print "Error! Cloud numbers exceeds node numbers!"
        else:
            node0 = random.randint(0, self.topo.number_of_nodes()-1)
            clouds.append(node0)
            _paths = nx.single_source_shortest_path(self.topo, node0)
            paths = []
            for value in _paths.itervalues():
                paths.append(value)
            paths.sort(key = lambda path: len(path))
            for i in xrange(cloud_no-1):
                clouds.append(paths[-i-1][-1])

        # Assigning random computing power
        for cloud in clouds:
            self.topo.node[cloud]['clouds'] = int(random.uniform(0.5*avg_comp_resource, 1.5*avg_comp_resource))
            self.topo.node[cloud]['IO'] = int(random.uniform(0.5*avg_IO_bandwidth, 1.5*avg_IO_bandwidth))

        # Give basic IO and clouds to video resources
        for node in self.topo.nodes():
            if node not in clouds and self.topo.node[node]['video_src'] != []:
                self.topo.node[node]['IO'] = 10
                self.topo.node[node]['clouds'] = 1

    def _assign_link_bandwidth(self, avg_link_bandwidth):
        # Assigning random link bandwidth
        for u, v in self.topo.edges_iter():
            self.topo.edge[u][v]['bandwidth'] = int(random.uniform(0.5*avg_link_bandwidth, 1.5*avg_link_bandwidth))

    def config_section_map(self, config, section):
        dict1 = {}
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1
    
    # def start_generator(self, config_file, sav_topo):
    def start_generator(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        # config.read("config.ini")

        videos = self.config_section_map(config, "Videos")
        src_no = int(videos['sourcenumbers'])

        users = self.config_section_map(config, "Users")
        block_no = int(users['blocknumbers'])
        user_no = int(users['usernumbers'])

        clouds = self.config_section_map(config, "CloudResources")
        cloud_no = int(clouds['cloudnumbers'])
        avg_comp_resource = int(clouds['averagecomputingresources'])
        avg_IO_bandwidth = int(clouds['averageiobandwidth'])

        links = self.config_section_map(config, "LinkBandwidth")
        avg_link_bandwidth = int(links['averagelinkbandwidth'])

        self._assign_src(src_no)
        self._assign_user(block_no, user_no, src_no)
        self._assign_cloud_resource(cloud_no, avg_comp_resource, avg_IO_bandwidth)
        self._assign_link_bandwidth(avg_link_bandwidth)

        # TODO save the topology with resoruce configured
        # f = open(sav_topo)
        # f.write( ... some json parsed topology file) ...
        # f.close()

        # pickle
        # nx.write_gpickle(self.topo, sav_topo)
