from resource_simulator import generator
import matplotlib.pyplot as plt
import networkx as nx
from networkx.readwrite import json_graph
from ilp import ilp
import json

# Test part
g = generator()
"""
g._assign_src(5)
g._assign_user(2, 20, 5)
g._assign_cloud_resource(5, 10)
g._assign_link_bandwidth(1000)
"""
g.start_generator('config.ini', 'topo.gpickle')
for node in g.topo.nodes():
    print g.topo.node[node]
for u, v in g.topo.edges_iter():
    print g.topo.edge[u][v]

data = json_graph.node_link_data(g.topo)
f = open("result_topo", "w+")
f.write(json.dumps(data))
f.close()

lp = ilp(g.topo, 3, [10, 8, 6, 4], 1, 0, 1, 1)
lp.solve()

# Visualization part
G = g.topo

# Calculate node color based on cloud computing power
_values = [G.node[x]['clouds'] for x in G.nodes()]
max_value = max(_values)
values = [G.node[x]['clouds']/max_value for x in G.nodes()]

# Draw nodes and edges
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_color = values)
nx.draw_networkx_edges(G, pos)

# Annotate user queries
labels = {}
for x in G.nodes():
    labels[x] = G.node[x]['user_queries'].values()
_pos = {}
for key, val in pos.iteritems():
    _pos[key] = [pos[key][0], pos[key][1]+0.05]
nx.draw_networkx_labels(G, _pos, labels=labels)
# Annotate video sources
for x in G.nodes():
    labels[x] = G.node[x]['video_src']
_pos = {}
for key, val in pos.iteritems():
    _pos[key] = [pos[key][0], pos[key][1]-0.05]
nx.draw_networkx_labels(G, _pos, labels=labels)

plt.show()