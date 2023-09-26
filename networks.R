rm(list = ls())
setwd("C:/Users/mafata/Desktop/WORK/CREST Postdoc/Astronomy Network Visualization/final_version")
library(RPostgres) # To interact with postgresql
library(glue) # Add python-style f-strings
library(tidyverse)# for data manipulations
library(plotly)#to make interactive plot
library(htmlwidgets)#to save the interactive plots as widgets
library(GGally) #ggnet2 is available through the GGally package
# The package dependencies of ggnet2 are below. 
# the ggplot2 package dependency is for plot construction, in tidyverse package already
library(sna) #for network manipulation such as node placement ('mode') in ggnet2
library(readxl)

# Script settings
credentials <- readxl::read_xlsx("C:/Users/mafata/Desktop/WORK/CREST Postdoc/my_credentials.xlsx")
crest_port = 5432
crest_dbname = credentials$crest_dbname[c(1)]
crest_host = credentials$crest_host[c(1)] 
crest_user = credentials$crest_user[c(1)] 
crest_password = credentials$crest_password[c(1)]

#first establish connection to database
drv <- RPostgres::Postgres()
print("Connecting to Database…")
connec <- dbConnect(drv, 
                    dbname = crest_dbname,
                    host = crest_host, 
                    port = crest_port,
                    user = crest_user, 
                    password = crest_password)
print("Database Connected!")

# Fetch required data
table1 = 'edgelist_orgs_network'
schema1 = 'mpho'
query1 <- dbSendQuery(connec, glue('select * from "{schema1}"."{table1}";'))
networks <- dbFetch(query1)
network_table <- networks[,c(-1)]  #networks %>% select(from,to)
network_table$edge_weight <- as.numeric(networks$weight)
network_table$edge_weight_sqrt <- as.numeric((networks$weight)/40)

table2 = 'orgs_rankings'
schema2 = 'mpho'
query2 <- dbSendQuery(connec, glue('select * from "{schema2}"."{table2}" order by pubs desc limit 18;'))
orgs_rank <- dbFetch(query2)
orgs_rank$pubs <- as.numeric(orgs_rank$pubs)

#manual quantile set
orgs_rank$publications <-
  as.factor(ifelse(
    orgs_rank$pubs <= 107,
    "[100-107]",
    ifelse(
      orgs_rank$pubs > 107 & orgs_rank$pubs <= 130,
      "(107-130]",
      ifelse(
        orgs_rank$pubs > 130 & orgs_rank$pubs <= 144,
        "(130-144]",
        ifelse(orgs_rank$pubs > 144 &
                 orgs_rank$pubs <= 198, "(144-198]", "other")
      )
    )
  ))

g <- as.network(network_table, vertices = orgs_rank)
new_graph <- ggnet2(g,
  mode = "fruchtermanreingold",
  layout.par = list(max.delta = 1),
  layout.exp = 0.3,
  label = TRUE,
  label.trim=100,
  label.color = "black",
  label.alpha = 1,
  label.size = 3.5,
  node.shape = 19,#solid circle is 19
  color = 'publications',
  palette = c("[100-107]"="#ff3d3c",
              "(107-130]"="#3b407b",
              "(130-144]"="orange",
              "(144-198]"="#89ba17",
              "other"="black"),
  node.alpha = 0.9,
  node.size =6.5,
  # size.cut = TRUE,#to make into quantiles
  edge.lty= 19, #'solid'
  edge.color = "black",
  edge.alpha = 0.2,
  edge.size = 'edge_weight_sqrt',
  vjust = -1.5,
  hjust= 0.5,
  legend.size = 9,
  legend.position = "right"
)
  # geom_label(
  # label = orgs_rank$organisation,
  # aes(colour = orgs_rank$pubs_range),
  # fill = "white",
  # position = position_dodge2(width = 1.1, padding = 0.1),
  # label.size = 0.009,
  # show.legend = FALSE
# )

