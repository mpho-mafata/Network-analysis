<img src="./network-images/networks-graphical-rep.png">

# Introduction
Here we look at how to construct data sets for network analysis using SQL, Python, and R.
I always find that the data wrangling is the hardest part of any data analysis so I added this part mainly because the data wrangling part of most analysis is often omitted making it an obstacle for any given analysis.
I have used some example data from bibliometrics but the principles are widely applicable. The example data is provided in the [repository](https://github.com/mpho-mafata/Network-analysis/tree/main/network-example-data).
I have also provided the python script I used to generate and test the code [here](https://github.com/mpho-mafata/Network-analysis/blob/main/network_analysis.py).

# Table of contents
> [Introduction](https://github.com/mpho-mafata/Network-analysis/tree/main#introduction)
>
> [Table of contents](https://github.com/mpho-mafata/Network-analysis/tree/main#table-of-contents)
> 
> [Preparing the data frame](https://github.com/mpho-mafata/Network-analysis/tree/main#preparing-the-data-frame)
> 
>> [Query using postgreSQL](https://github.com/mpho-mafata/Network-analysis/tree/main#query-using-postgresql)
>>
>>> [Create an edgelist](https://github.com/mpho-mafata/Network-analysis/tree/main#Create-an-edgelist)
>>>
>>> [Remove duplicate relationships](https://github.com/mpho-mafata/Network-analysis/tree/main#remove-duplicate-relationships)
>>>
>> [Data wrangling using Python](https://github.com/mpho-mafata/Network-analysis/tree/main#data-wrangling-using-python)
>>
>> [Data wrangling using R](https://github.com/mpho-mafata/Network-analysis/tree/main#data-wrangling-using-r)
>> 
> [Visualize the network](https://github.com/mpho-mafata/Network-analysis/tree/main#visualize-the-network)
>
>> [R plots using GGally](https://github.com/mpho-mafata/Network-analysis/tree/main#r-plots-using-ggally)
>>
>> [Python plots using Networkx](https://github.com/mpho-mafata/Network-analysis/tree/main#python-plots-using-networkx)
>
> [Generating insight](https://github.com/mpho-mafata/Network-analysis/tree/main#generate-insight)
>

# Preparing the dataframe
In order to construct a network we need to create a list of nodes (central points of intersection) and edges (lines  connecting each point).
The wrangling can thus be done in different ways depending on the data source. SQL wrangling is dependednt on whether you source the data from postgreSQL, the python pandas and R tidyverse wrangling is a workable solution for local files.

## Query using postgreSQL


### Create an edgelist
```
CREATE MATERIALIZED VIEW edgelist_orgs AS
SELECT DISTINCT edgelist.ut, edgelist.from, edgelist.to
FROM
(SELECT DISTINCT ARRAYS.ut AS ut, COUNTED.organisation as
      from, unnest (ARRAYS.orgs) AS to
      FROM
          (SELECT DISTINCT ut, ARRAY_AGG (organisation) AS orgs
          FROM mpho.orgs_rankings_top
          GROUP BY ut
          ORDER BY ut
          ) AS ARRAYS

          JOIN

          (SELECT ut, COUNT (ut), organisation
          FROM mpho.orgs_rankings_top
          GROUP BY ut, organisation
          ORDER BY organisation
          ) AS COUNTED
      ON ARRAYS.ut = COUNTED.ut) AS edgelist

WHERE edgelist.from != edgelist.to
ORDER BY edgelist.ut, edgelist.from, edgelist.to
;
```
|   ut | from  | to  |
|  -------------   |  --------------------------------------    |  -------------------------   |
WOS:000084670100019|NASA Goddard Space Flight Center|National Aeronautics & Space Administration (NASA)|
WOS:000084670100019|National Aeronautics & Space Administration (NASA)|NASA Goddard Space Flight Center|
WOS:000172620600024|Harvard University|Smithsonian Institution|
WOS:000172620600024|Smithsonian Institution|Harvard University|
WOS:000172852800015|National Astronomical Observatory of Japan|National Institutes of Natural Sciences (NINS) - Japan|
WOS:000172852800015|National Institutes of Natural Sciences (NINS) - Japan|National Astronomical Observatory of Japan|
${\color{red}WOS:000173507400007}$|${\color{red} Nagoya \space University}$|${\color{red}National \space Astronomical \space Observatory \space of \space Japan}$|
WOS:000173507400007|Nagoya University|National Institutes of Natural Sciences (NINS) - Japan|
${\color{red}WOS:000173507400007}$|${\color{red}National \space Astronomical \space Observatory \space of \space Japan}$|${\color{red}Nagoya \space University}$|
WOS:000173507400007|National Astronomical Observatory of Japan|National Institutes of Natural Sciences (NINS) - Japan|

### Remove duplicate relationships
We will notice that the edgelist will contain similar pairs highlighted above. Note that these are in the same document (same ut number). 
In the case that the data has directionality, these are kept as is in the order they are observed (to and from).
In the case that there are no directional implications, these are duplicate pairs and must be removed.
We start by creating an (alphabetically) ordered list and turn it into an array of pairs.

```
CREATE MATERIALIZED VIEW alphabetical_edgelist_orgs AS
SELECT DISTINCT TABLES.links, TABLES.ut
FROM
(
SELECT ut,
    CASE WHEN
    UPPER(edgelist_orgs."from")>UPPER(edgelist_orgs."to")
    THEN edgelist_orgs."to"||'->'||edgelist_orgs."from"
    ELSE
    edgelist_orgs."from"||'->'||edgelist_orgs."to"
    END AS links
FROM mpho.edgelist_orgs
    ) as TABLES
ORDER BY tables.links, tables.ut
;
```
|ut|links|
|  -------------   |  --------------------------------------    |
WOS:000084670100019|NASA Goddard Space Flight Center->National Aeronautics & Space Administration (NASA)|
WOS:000172620600024|Harvard University->Smithsonian Institution|
WOS:000172852800015|National Astronomical Observatory of Japan->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000173507400007|National Astronomical Observatory of Japan->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000173507400007|Nagoya University->National Astronomical Observatory of Japan|
WOS:000173507400007|Nagoya University->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000178033200022|Nagoya University->National Astronomical Observatory of Japan|
WOS:000178033200022|Nagoya University->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000178033200022|National Astronomical Observatory of Japan->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000178193200015|Centre National de la Recherche Scientifique (CNRS)->Max Planck Society|
WOS:000179648100005|National Astronomical Observatory of Japan->University of Tokyo|
WOS:000179648100005|Nagoya University->National Astronomical Observatory of Japan|
WOS:000179648100005|Nagoya University->National Institutes of Natural Sciences (NINS) - Japan|
WOS:000179648100005|Nagoya University->University of Tokyo|
WOS:000179648100005|National Astronomical Observatory of Japan->National Institutes of Natural Sciences (NINS) - Japan|

### Create final edgelist of organizations for network analysis
Now that we have the pairs, we can group by them in order to remove any duplicate relationship per pair.
Now with uniques pairs per documnet, we can count the number of documents each pair shares (this will become the edge weight).
```
CREATE MATERIALIZED VIEW edgelist_orgs_network AS
SELECT nodes[1] as "from", nodes[2]  as "to", ar.weight
FROM (
    SELECT
        m.weight,
        STRING_TO_ARRAY(m.links, '->') nodes
    FROM (
        SELECT
            COUNT(DISTINCT a.ut) weight,
            a.links
        FROM alphabetical_edgelist_orgs AS a
        GROUP BY a.links
        ORDER BY COUNT(DISTINCT a.UT) DESC
    ) m
) ar
;
```
|from|to|weight|
| --|  -------------   |  --------------------------------------    |
National Astronomical Observatory of Japan|National Institutes of Natural Sciences (NINS) - Japan|135|
NASA Goddard Space Flight Center|National Aeronautics & Space Administration (NASA)|107|
National Institutes of Natural Sciences (NINS) - Japan|University of Tokyo|104|
California Institute of Technology|National Aeronautics & Space Administration (NASA)|98|
Nagoya University|National Institutes of Natural Sciences (NINS) - Japan|93|
Harvard University|Smithsonian Institution|91|
California Institute of Technology|Max Planck Society|84|
Korea Astronomy & Space Science Institute (KASI)|Max Planck Society|83|
Keele University|University of St Andrews|82|
Nagoya University|National Astronomical Observatory of Japan|81|
Korea Astronomy & Space Science Institute (KASI)|Ohio State University|78|
National Astronomical Observatory of Japan|University of Tokyo|77|
Max Planck Society|Ohio State University|76|
Max Planck Society|Smithsonian Institution|76|
Max Planck Society|National Aeronautics & Space Administration (NASA)|74|

### Optimized SQL query
The previous sections outlined important data wrangling parts to generating the dataframe needed for the network analysis. However, seperately these are not very efficient but they work. The code generates multiple MVs which is not a very efficient strategy. In optimizing the query, I used nested WITH statements, the aliases of which are the same as the MVs previously generated so the code can remain the same, for the most part.
The [example data](https://github.com/mpho-mafata/Network-analysis/tree/main/network-example-data) provided can be imported as a table to a schema referenced below. My schema name in this example is __*mpho*__.

```
DROP MATERIALIZED VIEW IF EXISTS edgelist_orgs_network;
CREATE MATERIALIZED VIEW edgelist_orgs_network AS
WITH alphabetical_edgelist_orgs AS
         (WITH edgelist_orgs AS
                   (SELECT DISTINCT edgelist.ut, edgelist.from, edgelist.to
                    FROM (SELECT DISTINCT ARRAYS.ut            AS ut,
                                          COUNTED.organisation as from,
                                          unnest(ARRAYS.orgs)  AS to
                          FROM (SELECT DISTINCT ut, ARRAY_AGG(organisation) AS orgs
                                FROM mpho.orgs_rankings_top
                                GROUP BY ut
                                ORDER BY ut) AS ARRAYS
                                   JOIN
                               (SELECT ut, COUNT(ut), organisation
                                FROM mpho.orgs_rankings_top
                                GROUP BY ut, organisation
                                ORDER BY organisation) AS COUNTED
                               ON ARRAYS.ut = COUNTED.ut) AS edgelist
                    WHERE edgelist.from != edgelist.to
                    ORDER BY edgelist.ut, edgelist.from, edgelist.to)
          SELECT DISTINCT TABLES.links, TABLES.ut
          FROM (SELECT ut,
                       CASE
                           WHEN
                               UPPER(edgelist_orgs."from") > UPPER(edgelist_orgs."to")
                               THEN edgelist_orgs."to" || '->' || edgelist_orgs."from"
                           ELSE
                               edgelist_orgs."from" || '->' || edgelist_orgs."to"
                           END AS links
                FROM edgelist_orgs) as TABLES
          ORDER BY tables.links, tables.ut)
SELECT nodes[1] as "from", nodes[2] as "to", ar.weight
FROM (SELECT m.weight,
             STRING_TO_ARRAY(m.links, '->') nodes
      FROM (SELECT COUNT(DISTINCT a.ut) weight,
                   a.links
            FROM alphabetical_edgelist_orgs AS a
            GROUP BY a.links
            ORDER BY COUNT(DISTINCT a.UT) DESC) m) ar
;
```

## Data wrangling using Python 

```
# get the original dataset
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

```

## Data wrangling using R

## Visualize the network

### R plots using GGally
```
library(RPostgres) # To interact with postgresql
library(readxl)
library(GGally) # ggnet2 is available through the GGally package

# Script settings for postgresql
my_credentials <- readxl::read_xlsx("C:/Users/folder/my_credentials.xlsx")
port = 1234
my_dbname = my_credentials$dbname[c(1)]
my_host = my_credentials$host[c(1)] 
my_user = my_credentials$user[c(1)] 
my_password = my_credentials$password[c(1)]

#first establish connection to database
drv <- RPostgres::Postgres()
print("Connecting to Database…")
connec <- dbConnect(drv, 
                    dbname = my_dbname,
                    host = my_host, 
                    port = my_port,
                    user = my_user, 
                    password = my_password)
print("Database Connected!")

# Fetch required data
table1 = 'edgelist_orgs_network'
schema1 = 'my_schema'
query1 <- dbSendQuery(connec, glue('select * from "{schema1}"."{table1}";'))
network_table <- dbFetch(query1)

table2 = 'orgs_rankings'
schema2 = 'my_other_schema'
query2 <- dbSendQuery(connec, glue('select * from "{schema2}"."{table2}";'))
nodes_table <- dbFetch(query2)
nodes_table$node_size <- as.numeric(nodes_table$pubs)

network_table$edge_size <- as.numeric((network_table$weight)/100)

network_graph <- ggnet2(network_table,
  mode = "fruchtermanreingold",
  layout.par = list(max.delta = 1),
  layout.exp = 0.3,
  label = TRUE,
  label.trim=100,
  label.color = "black",
  label.alpha = 1,
  label.size = 3.5,
  node.shape = 19,
  node.alpha = 0.7,
  node.color = "maroon",
  node.size = 5.0,
  edge.lty= 19, #'solid'
  edge.color = "navy",
  edge.alpha = 0.3,
  edge.size = "edge_size",
  vjust = 1.5,
  hjust= 0.6,
  legend.size = 9,
  legend.position = "right"
)
```

<img src="./network-images/network_graph.svg">
  <figcaption>Network graph using GGaly ggnet2.</figcaption>

### Python plots using Networkx 

When reading the file from postgreSQL and structuring from there.

```
# get my postgresql credentials
import pandas as pd
credentials = pd.read_excel("C:/Users/folder/my_credentials.xlsx")
port = 5432
my_dbname = credentials.my_dbname[0]
my_host = credentials.my_host[0]
my_user = credentials.my_user[0]
my_password = credentials.my_password[0]

# connect to postgresql
import psycopg # to connect to postgresql
connec = psycopg.connect(
    port=5432,
    host=my_host,
    dbname=my_dbname,
    user=my_user,
    password=my_password)

#Retrieve data tables
cursor = connec.cursor()
table1 = 'edgelist_orgs_network'
schema1 = 'my_schema'
cursor.execute(f'SELECT * from {schema1}.{table1}')

# Fetch required data
network_table = cursor.fetchall();

# Closing the connection
connec.close()

# structure the data
network_table = pd.DataFrame(network_table)
network_table.columns = ["from","to","weight"]

```

The data can then be plotted similarly both the SQL and python wrangling
```
# SET FREQUENCY THE LIMIT FOR THE EDGES: MINIMUM NUMBER OF SAMPLES AN ATTRIBUTE HAS TO APPEAR
# dataset = dataset.query(" weight > 70 ")

# CALCULATE THE NODE SIZES HERE AFTER FILTERING FOR THE CUT-OFF WEIGHT
node_sizes_x = dataset.groupby(["target_x"]).aggregate({'weight': 'sum'}).reset_index()
node_sizes_y = dataset.groupby(["target_y"]).aggregate({'weight': 'sum'}).reset_index()
node_sizes = pd.merge(left=node_sizes_x,left_on="target_x",
                      right=node_sizes_y,right_on="target_y",
                      how="outer").fillna(0)
node_sizes["weight"]=node_sizes["weight_x"]+node_sizes["weight_y"]
node_sizes["weight"] = node_sizes["weight"].astype("int")

# CREATE A RULE FOR THE NODE NAME
conditions = [(node_sizes["target_x"]==0),
              (node_sizes["target_x"]!=0)]
name = [node_sizes["target_y"],
        node_sizes["target_x"]]
node_sizes["labels"]=np.select(conditions,name)
node_sizes = node_sizes[["labels","weight"]]

# SCALE THE EDGE WIDTHS FOR VISUALIZATION
dataset["weight"] = dataset["weight"]/50

# INITIATE THE GRAPH
plt.figure(figsize=(10, 10))
network_graph = nx.Graph()
network_graph = nx.from_pandas_edgelist(dataset, source="target_x", target="target_y", edge_attr ='weight')

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
edge_widths = nx.get_edge_attributes(network_graph,"weight")
new_order = pd.merge(left = pd.DataFrame(network_graph.nodes(data=True)),
                     left_on=0,
                     right = node_sizes,
                     right_on="labels",
                     how="left")
node_sizes = new_order[["labels","weight"]]

# DRAW THE NETWORK GRAPH
position = nx.spring_layout(network_graph, k=4) # Adjust node distances here
network_graph = nx.draw(network_graph, with_labels=True, font_size=12, alpha=0.75,
                                node_size = node_sizes["weight"]/1, # adjust the size of nodes here
                                node_color= range(len(node_sizes)), # random node colours
                                cmap=plt.cm.Spectral, # colour map for the nodes
                                arrows=True, # even though this is an undirected network, we add this so we can make the edges curved
                                connectionstyle="arc3, rad=0.25",
                                pos=position,
                                width=list(edge_widths.values()),
                                edge_color = range(len(dataset))
                        )

# Make legend based on node sizes
for n in sorted(node_sizes["weight"].unique()):
    plt.plot([], [], 'bo', markersize=n/100, label=f"{n}")
plt.legend(labelspacing=5, loc='center left', bbox_to_anchor=(1,0), frameon=False)

# a legend for edge widths
lines = np.linspace(start= min(edge_widths.values()), stop= max(edge_widths.values()), num=5) # Get evenly distributed points over range of weights
from matplotlib.lines import Line2D # Create lines from the weights
line2ds = [Line2D([],[], linewidth=width, color='black') for width in lines]
legend2 = plt.legend(line2ds, np.round(lines, decimals=2), bbox_to_anchor=(0, 1))

# SAVE THE GRAPH
plt.savefig(fname='networkx_graph.svg', dpi=800,
            bbox_inches="tight", pad_inches=0.0,
            transparent=True, format="svg")
plt.show()

```
<img src="./network-images/networkx_graph.svg"> 
  <figcaption> Network graph using NetworkX.</figcaption>

# Generating insight
The data we have in the example above generated some insight into the relationships between network entities (nodes). 

Insights such as
 * the number of connections per entity
 * The weight of each connection

More isights can be drawn from network data if the data is available. For example, numeric or categorical data descriptors of the entities. In this example it could be geographical origin of the organization. This insights can be parsed on to the graph in different ways. 

In this section I will work on describing the different kinds of insights that can be gained from a network graph and how to incorporate them.
Examples for this are available for sensory network data [here](https://github.com/mpho-mafata/Network-analysis-of-sensory-attributes)

