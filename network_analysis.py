# import the necessary libraries
import networkx as nx
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# read the data
dataset = pd.read_excel("/Users/mphomafata/Documents/GitHub/Network-analysis/network-example-data/edgelist_orgs_network.xlsx")
dataset.columns=["org1","org2","weight"]
dataset['weight'] = ((dataset['weight'])/max(dataset['weight']))*10 # attempt at scaling the edge sizes from zero to one

# this should be a function to create node sizes
node_sizes_1= dataset.groupby(['org1']).aggregate({'org1': 'count'})
node_sizes_2= dataset.groupby(['org2']).aggregate({'org2': 'count'})
node_sizes = pd.DataFrame(pd.concat([node_sizes_1, node_sizes_2]))
node_sizes['orgs'] = node_sizes.index
node_sizes = node_sizes.groupby(['orgs']).aggregate({'orgs':'sum'}).reset_index(drop=True)


print(node_sizes_1)

# plot the graph
plt.figure(figsize=(30, 15))
network_graph = nx.Graph()
network_graph = nx.from_pandas_edgelist(dataset, source="org1", target="org2", edge_attr ='weight')
widths = nx.get_edge_attributes(network_graph, name= 'weight')

network_graph = nx.draw(network_graph, with_labels=True, font_size=25, alpha=1.0,
                        node_size=800,
                        node_color=range(len(node_sizes)), # generates random node colours
                        cmap=plt.cm.viridis, # colour map for the nodes
                        arrows=True,
                        connectionstyle="arc3, rad=0.20",
                        width=list(widths.values()),
                        edge_color = 'grey'
                        )
plt.savefig(fname='networkx_graph.svg', dpi=800,
            bbox_inches="tight", pad_inches=0.0,
            transparent=True, format="svg")
plt.show()