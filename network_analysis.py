# import the necessary libraries
import networkx as nx
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# wrangle/ structure the original dataset
dataset = pd.read_csv("/Users/mphomafata/Documents/GitHub/Network-analysis/network-example-data/orgs_rankings_top.csv",
                       sep=";",
                       header=0)
dataset = dataset[["ut", "organisation"]]
dataset.columns = ["weight", "target"]
dataset = pd.merge(left=dataset, right= dataset, how='left', on = 'weight')
dataset = dataset.query(" target_x != target_y ").reset_index(drop=True, inplace=False)
dataset['org_array'] = dataset['target_x'] + "," + dataset['target_y']
dataset["sorted"] = dataset["org_array"].str.split(',').explode().str.split(',').apply(lambda x: [s.lstrip() for s in x]).sort_values().groupby(level=0).agg(lambda x: ' , '.join(map(str, x)))
dataset = dataset.groupby(["target_x","target_y", "sorted"]).aggregate({'weight': 'count'}).reset_index()
dataset=dataset.drop_duplicates('sorted').reset_index(drop=True)

# SET FREQUENCY THE LIMIT FOR THE EDGES: MINIMUM NUMBER OF SAMPLES AN ATTRIBUTE HAS TO APPEAR
# dataset = dataset.query(" weight > 70 ")

# CALCULATE THE NODE SIZES HERE AFTER FILTERING FOR THE CUT-OFF WEIGHT
node_sizes_x = dataset.groupby(["target_x"]).aggregate({'weight': 'sum'}).reset_index()
node_sizes_y = dataset.groupby(["target_y"]).aggregate({'weight': 'sum'}).reset_index()
node_sizes = pd.merge(left=node_sizes_x, left_on="target_x",
                      right=node_sizes_y, right_on="target_y",
                      how="outer").fillna(0)
node_sizes["weight"] = node_sizes["weight_x"] + node_sizes["weight_y"]
node_sizes["weight"] = node_sizes["weight"].astype("int")

# CREATE A RULE FOR THE NODE NAME
conditions = [(node_sizes["target_x"] == 0),
              (node_sizes["target_x"] != 0)]
name = [node_sizes["target_y"],
        node_sizes["target_x"]]
node_sizes["labels"] = np.select(conditions, name)
node_sizes = node_sizes[["labels", "weight"]]

# SCALE THE EDGE WIDTHS FOR VISUALIZATION
dataset["weight"] = dataset["weight"] / 50

# INITIATE THE GRAPH
plt.figure(figsize=(10, 10))
network_graph = nx.Graph()
network_graph = nx.from_pandas_edgelist(dataset, source="target_x", target="target_y", edge_attr='weight')

# CALCULATE SOME NETWORK METRICS
from networkx.algorithms import approximation as apxa

net_centrality = nx.degree_centrality(network_graph)
print("The network centrality is " + str(len(net_centrality)))
network_radius = nx.radius(network_graph)
print("The network radius is " + str(network_radius))
network_density = nx.density(network_graph)
print("The density is " + str(network_density))
net_clusters = apxa.k_components(network_graph)
print("The number of clusters is " + str(len(net_clusters)))

# SET NODE AND EDGE ATTRIBUTES
edge_widths = nx.get_edge_attributes(network_graph, "weight")
new_order = pd.merge(left=pd.DataFrame(network_graph.nodes(data=True)),
                     left_on=0,
                     right=node_sizes,
                     right_on="labels",
                     how="left")
node_sizes = new_order[["labels", "weight"]]

# DRAW THE NETWORK GRAPH
position = nx.spring_layout(network_graph, k=4)  # Adjust node distances here
network_graph = nx.draw(network_graph, with_labels=True, font_size=12, alpha=0.75,
                        node_size=node_sizes["weight"] / 1,  # adjust the size of nodes here
                        node_color=range(len(node_sizes)),  # random node colours
                        cmap=plt.cm.Spectral,  # colour map for the nodes
                        arrows=True,
                        # even though this is an undirected network, we add this so we can make the edges curved
                        connectionstyle="arc3, rad=0.25",
                        pos=position,
                        width=list(edge_widths.values()),
                        edge_color=range(len(dataset))
                        )

# Make legend based on node sizes
for n in sorted(node_sizes["weight"].unique()):
    plt.plot([], [], 'bo', markersize=n / 100, label=f"{n}")
plt.legend(labelspacing=5, loc='center left', bbox_to_anchor=(1, 0), frameon=False)

# a legend for edge widths
lines = np.linspace(start=min(edge_widths.values()), stop=max(edge_widths.values()),
                    num=5)  # Get evenly distributed points over range of weights
from matplotlib.lines import Line2D  # Create lines from the weights

line2ds = [Line2D([], [], linewidth=width, color='black') for width in lines]
legend2 = plt.legend(line2ds, np.round(lines, decimals=2), bbox_to_anchor=(0, 1))

# SAVE THE GRAPH
plt.savefig(fname='networkx_graph.svg', dpi=800,
            bbox_inches="tight", pad_inches=0.0,
            transparent=True, format="svg")
plt.show()
