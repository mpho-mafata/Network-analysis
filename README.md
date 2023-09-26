# network analysis
Here we look at how to construct data sets for network analysis using SQL queries and graphs them using R and python.
I always find that the data structuring is the hardest part of any data analysis.
Examples are given from bibliometric data.

## SQL query
In order to construct a network we need to create a list of nodes (central points of intersection) and edges (lines  connecting each point).

### create an edgelist
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

## remove duplicate relationships
We will notice that the edgelist will contain similar pairs highlighted above. Note that these are in the same document (same ut number). 
In the case that the data has directionality, these are kept as is in the order they are observed (to and from).
In the case that there are no directional implications, these are duplicate pairs and must be removed.
We start by creating an (alphabetically)ordered list and turn it into an array of pairs.

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




## create final edgelist of organizations for network analysis
Now that we have the pairs, we can group by them in order to remove any duplicate relationship per pair.
Now with uniques pairs per documnet, we can count the number of documents each pair shares (this will become the edge weight).
```
CREATE MATERIALIZED VIEW edgelist_orgs_network AS
SELECT ar.weight, nodes[1] as "from", nodes[2]  as "to"
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
weight|from|to|
| --|  -------------   |  --------------------------------------    |
135|National Astronomical Observatory of Japan|National Institutes of Natural Sciences (NINS) - Japan|
107|NASA Goddard Space Flight Center|National Aeronautics & Space Administration (NASA)|
104|National Institutes of Natural Sciences (NINS) - Japan|University of Tokyo|
98|California Institute of Technology|National Aeronautics & Space Administration (NASA)|
93|Nagoya University|National Institutes of Natural Sciences (NINS) - Japan|
91|Harvard University|Smithsonian Institution|
84|California Institute of Technology|Max Planck Society|
83|Korea Astronomy & Space Science Institute (KASI)|Max Planck Society|
82|Keele University|University of St Andrews|
81|Nagoya University|National Astronomical Observatory of Japan|
78|Korea Astronomy & Space Science Institute (KASI)|Ohio State University|
77|National Astronomical Observatory of Japan|University of Tokyo|
76|Max Planck Society|Ohio State University|
76|Max Planck Society|Smithsonian Institution|
74|Max Planck Society|National Aeronautics & Space Administration (NASA)|


