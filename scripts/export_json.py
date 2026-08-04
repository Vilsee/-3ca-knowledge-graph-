import pickle, json, networkx as nx
from networkx.readwrite import json_graph

G = pickle.load(open('data/kg.gpickle', 'rb'))
data = json_graph.node_link_data(G)
json.dump(data, open('data/kg.json', 'w'))
print('Done')
