# import the necessary libraries
import networkx as nx
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# read the SQL wrangled data
dataset = pd.read_excel(
    "/Users/mphomafata/Documents/GitHub/Network-analysis/network-example-data/edgelist_orgs_network.xlsx")
dataset.columns = ["org1", "org2", "weight"]
dataset['weight'] = ((dataset['weight']) / max(
    dataset['weight'])) * 10  # attempt at scaling the edge sizes from zero to one
dataset.to_excel("old_df.xlsx")
# this creates node sizes
node_sizes_1 = dataset.groupby(['org1']).aggregate({'org1': 'count'})
node_sizes_2 = dataset.groupby(['org2']).aggregate({'org2': 'count'})
node_sizes = pd.DataFrame(pd.concat([node_sizes_1, node_sizes_2]))
node_sizes['orgs'] = node_sizes.index
node_sizes = node_sizes.groupby(['orgs']).aggregate({'orgs': 'sum'}).reset_index(drop=True)

# plot the graph
plt.figure(figsize=(30, 15))
network_graph = nx.Graph()
network_graph = nx.from_pandas_edgelist(dataset, source="org1", target="org2", edge_attr='weight')
widths = nx.get_edge_attributes(network_graph, name='weight')
network_graph = nx.draw(network_graph, with_labels=True, font_size=25, alpha=1.0,
                        node_size=800,
                        node_color=range(len(node_sizes)),  # generates random node colours
                        cmap=plt.cm.viridis,  # colour map for the nodes
                        arrows=True,
                        connectionstyle="arc3, rad=0.20",
                        width=list(widths.values()),
                        edge_color='grey'
                        )
plt.savefig(fname='networkx_graph.svg', dpi=800,
            bbox_inches="tight", pad_inches=0.0,
            transparent=True, format="svg")

# wrangle the original dataset
dataset2 = pd.read_csv("/Users/mphomafata/Documents/GitHub/Network-analysis/network-example-data/orgs_rankings_top.csv",
                       sep=";",
                       header=0)
nodes = dataset2.groupby(["organisation"]).aggregate({'pubs': 'first'}).reset_index()
edges = dataset2[["ut", "organisation"]]
# join the dataframe with itself based on the unique identifier (UT)
edges = pd.merge(left=edges, right=edges, how="left", on='ut')
# then remove the duplicates where org x is the same as org y
edges = edges.query(" organisation_x != organisation_y ").reset_index(drop=True, inplace=False)
# now remove the duplicates where org x: orgy is the same as org y: org x
# first create an array of organization_x and organization_y and add it to the dataframe
edges["org_array"] = edges["organisation_x"] + "," + edges["organisation_y"]
edges["sorted"] = edges["org_array"].str.split(',').explode().str.split(',').apply(lambda x: [s.lstrip() for s in x]) \
    .sort_values().groupby(level=0).agg(lambda x: ' , '.join(map(str, x)))
# now count the unique number of UTs
edges = edges.groupby(["organisation_x", "organisation_y", "sorted"]).aggregate({'ut': 'count'}).reset_index()
edges['ut'] = ((edges['ut']) / max(edges['ut'])) * 10  # attempt at scaling the edge sizes from zero to one

edges.to_excel("new_df.xlsx")
# plot the graph
plt.figure(figsize=(30, 15))
network_graph = nx.Graph()
network_graph = nx.from_pandas_edgelist(edges, source="organisation_x", target="organisation_y", edge_attr='ut')
widths = nx.get_edge_attributes(network_graph, name='ut')
network_graph = nx.draw(network_graph, with_labels=True, font_size=25, alpha=1.0,
                        node_size=800,
                        node_color=range(len(nodes)),  # generates random node colours
                        cmap=plt.cm.viridis,  # colour map for the nodes
                        arrows=True,
                        connectionstyle="arc3, rad=0.20",
                        width=list(widths.values()),
                        edge_color='grey'
                        )
plt.savefig(fname='networkx_graph_2.svg', dpi=800,
            bbox_inches="tight", pad_inches=0.0,
            transparent=True, format="svg")
plt.show()
