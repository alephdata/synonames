'''
WIP code to: 1) group together synonymous names per Wikipedia uri and 2) merge identical nodes in networkx 
Output: 'global_synonmes_nx.csv' -  .csv file with lists of synonames. 
Interim files - to double-check process 
'''

import sys, os 
import re
import csv 
import numpy as np 
import pandas as pd 
import pandas.io.sql as psql 
import psycopg2 as pg 
import phonetics 
import Levenshtein
from normality import latinize_text, normalize 
from synonames_helper import flag_similar_names, create_patterns, link_pairs
import itertools 
import math
import networkx as nx 

#Folder set-up
dirs = ['./interim', './output', './test_data']
for dir in dirs: 
    if not os.path.exists(dir):
            os.mkdir(dir)

#Collect data 
print ("loading")

conn = pg.connect("host = db dbname = db user = db password = db")

query = ''' SELECT DISTINCT ON (uri, lang) * FROM names WHERE lang IN %(sup_lang)s
        '''

sup_langs = ('bg', 'el', 'hy', 'ka', 'l1', 'mk', 'mn', 'ru', 'sr-ec','uk', 'sr', 'ast', 'ca', 
             'cy', 'da','de','en','es','fi','fr','hu','it','nb','nl', 'ms', 'ro', 'nn', 'sl',
             'sq','sv', 'vec', 'pl', 'pt', 'bg', 'cs', 'vi', 'gd', 'tr', 'et', 'lt', 'sl')

for df in pd.read_sql(query, con = conn, chunksize = 500000, params = {'sup_lang' :sup_langs}):
    
    print (df.head())

    df["name"] = df["name"].apply(lambda x: normalize(x))
    df["names_split"] = df["name"].apply(lambda x: x.split())
    
    #Split name strings 
    names_df = pd.DataFrame(df.names_split.to_list())
    names_df["uri"] = df["uri"].values
    names_df["uri"] = names_df["uri"].apply(lambda x: x.split("/")[-1])
    names_df["lang"] = df["lang"].values
    
    #names_df.to_csv("interim/names_df.csv", index = False)

    del df 

    #Transform - from wide to long 
    names_melt = pd.melt(names_df, id_vars = ["uri", "lang"])
    names_melt.drop_duplicates(subset = ["uri", "value"], inplace = True) #Change this if you want lang frequency
    names_melt = names_melt.dropna()
    names_melt = names_melt[names_melt["value"].apply((lambda x: len(x) > 1))] #Remove one-letter names. 

    #Transliterate
    names_melt["roman"] = names_melt["value"].apply(lambda x: normalize(latinize_text(x)))

    stopwords = ["the", "und", "de", "di", "of", "ze", "der", "and", "la", "iz",
                "al", "af", "av", "von", "van", "el", "od", "ze", "da", "wa", 
                "dello", "dari", "le", "z", "or", "oder", "ou", "the", "ton", "tes"]

    names_melt = names_melt[~names_melt["roman"].isin(stopwords)]
    names_melt["roman"] = names_melt["roman"].apply(lambda x: None if re.search(r'\d|i', x) else x)
    names_melt = names_melt.dropna()
    #names_df.to_csv("interim/names_df2.csv", index = False)

    #Add phonetics 
    names_melt["phonetics"] = names_melt["roman"].apply(lambda x: list(phonetics.dmetaphone(x)))
    names_melt = names_melt[names_melt["phonetics"].apply(lambda x: any(x))] #Discard empty tuples
    names_melt["phonetics"] = names_melt["phonetics"].apply(lambda x: [x[0]] if x[1] == '' else x)
    #names_melt.to_csv("interim/names_melt.csv", index = False)

    #Test - Identify uris with similar names that are not synonames (phonetics matching might fail) 
    sim_df = pd.DataFrame(names_melt.groupby(["uri", "lang"])["phonetics"].apply(list)).reset_index()
    sim_df["l_dist"] = sim_df["phonetics"].apply(lambda x: flag_similar_names(x))
    sim_uris = sim_df.loc[sim_df[sim_df["l_dist"]==1].groupby("uri")["l_dist"].filter(lambda x: x.count()>1).index, "uri"]

    #sim_df.to_csv("interim/sim_df.csv", index = False)
    #sim_df[sim_df["l_dist"]==1].to_csv("interim/similar_names.csv", index = False)

    del sim_df 

    #Transform from wide-to-long
    #I.e. transform from - uri, [phon1, phon2] to - uri, phon1; uri, phon2 
    temp_df = pd.DataFrame(names_melt.phonetics.to_list()) #ugly work-around for inaccurate assignment
    temp_df.columns = ["phon1", "phon2"]
    names_melt["phon1"] = temp_df["phon1"].values
    names_melt["phon2"] = temp_df["phon2"].values
    names_melt = names_melt.drop("variable", axis = 1)
    names_melt["index"] = np.arange(len(names_melt))
    #names_melt["value"] = names_melt["value"].apply(lambda x: x.replace("\"", "")) #this doesn't work 

    phon_stack = names_melt[["uri", "value", "index", "phon1", "phon2"]]\
                .set_index(["index","uri", "value"]).stack().reset_index()
    phon_stack = pd.DataFrame(phon_stack)
    phon_stack = phon_stack.drop(['level_3'], axis = 1)
    phon_stack.columns = ["stack_index", "uri", "stack_value","stack_phon"]
    phon_stack = phon_stack[phon_stack["stack_phon"] != ""]

    #names_melt.to_csv("interim/names_melt2.csv", index = False)
    #phon_stack.to_csv("interim/phon_stack.csv", index = False)

    del temp_df, names_df 

    #Groupby phonetics 
    stack_df = pd.DataFrame(phon_stack.groupby(["uri"])["stack_phon"].apply(list))
    stack_df = stack_df.reset_index()
    stack_df["stack_phon"] = stack_df["stack_phon"].apply(lambda x: list(set(x)))

    stack_df["lev_dist"] = stack_df["stack_phon"].apply(lambda x: create_patterns(x))
    stack_df.to_csv("interim/stack_df.csv", index = False)

    #Create pattern_df with uri, phonetic, pattern number (unique pattern #s per uri)
    pattern_temp = pd.DataFrame(stack_df.lev_dist.to_list())
    pattern_temp["uri"] = stack_df["uri"].values
    pattern_temp = pd.melt(pattern_temp, id_vars = "uri")
    pattern_temp["value"] = pattern_temp["value"].apply(lambda x: [] if x is None else x)

    #pattern_temp.to_csv("interim/pattern_temp.csv", index = False)
    del stack_df 

    pattern_df = pd.DataFrame(pattern_temp.value.to_list())
    pattern_df["uri"] = pattern_temp["uri"].values
    pattern_df["pattern_no"] = pattern_temp["variable"].values

    pattern_df = pd.melt(pattern_df, id_vars = ["uri", "pattern_no"])
    pattern_df = pattern_df.dropna()
    pattern_df = pattern_df.drop(["variable"], axis = 1)

    #pattern_df.to_csv("interim/pattern_df.csv", index = False)
    del pattern_temp

    #Match pattern_df with name_melt
    phon_stack = phon_stack.drop(['stack_index'], axis = 1)
    phon_stack = phon_stack.merge(pattern_df, how = 'left', left_on = ["uri", "stack_phon"], right_on = ["uri", "value"])
    phon_stack = phon_stack.dropna()

    #Networkx output 
    nx_csv = phon_stack.rename(columns={'stack_value':'name'})
    nx_csv = nx_csv[["uri", "name", "pattern_no"]].drop_duplicates()
    nx_csv.to_csv("output/names_nodes_nx.csv", mode = 'a', index = False)

    #Neo4J output 
    phon_group = pd.DataFrame(phon_stack.groupby(["uri", "pattern_no"])["stack_value"].apply(list)).reset_index()
    phon_group["stack_value"] = phon_group["stack_value"].apply(lambda x: list(set(x)))

    phon_group.to_csv("output/names_nodes_neo4j.csv", mode = 'a', index = False)
    phon_group["stack_value"] = phon_group["stack_value"].apply(lambda x: ','.join(x))
    phon_group.to_csv("output/names_nodes_str_neo4j.csv",  mode = 'a', index = False)

    phon_group["check"] = False  #flag problem uris
    phon_group.loc[phon_group["uri"].isin(sim_uris), "check"] = True 
    phon_group.to_csv("output/names_nodes_str_neo4j_flagged_uris.csv", mode = 'a', index = False)

print ("FINISHED - uri synonames")
print ("STARTING - network calculations")

#Networkx - create gnetwork, merge identical name nodes
#nodes_df = nx_csv 
nodes_df = pd.read_csv("output/names_nodes_nx.csv")
print ("loaded nx data!")
nodes_df = nodes_df.reset_index()

index_groups = nodes_df.groupby(["uri", "pattern_no"])["index"].apply(list)
names_duplicates = nodes_df.groupby(["name"])["index"].apply(list) 

nodes_df = nodes_df.set_index("index").T
nodes_dict = nodes_df.to_dict()

#Create edge list and lone nodes list 
edge_list = []
lone_nodes = []

for val in index_groups:
    if len(val) > 1: 
        edge_list.extend(list(itertools.combinations(val, 2)))
    else: 
        lone_nodes.extend(val)

#Load edges & nodes into nx 
G = nx.Graph()
G.add_edges_from(edge_list)
G.add_nodes_from(lone_nodes)

#Set node properties
nx.set_node_attributes(G, nodes_dict)

#Merge nodes - slow; can't find more optimal way 
print (len(G.nodes))
for val in names_duplicates:
    if len(val)>1: 
        for node in val[1:]:
            G = nx.contracted_nodes(G, val[0], node)
print (len(G.nodes))

nx.write_gpickle(G, "output/nx_graph_pickle")
nx.readwrite.gexf.write_gexf(G, "output/nx_graph_gexf")

#Calculate components 
components = nx.connected_component_subgraphs(G)
final_components = [list(component.nodes(data='name')) for component in components]
final_df = pd.DataFrame.from_records(final_components)
final_df = final_df.applymap(lambda x: x[1] if x != None else x) #extract names
print (final_df.head())

final_df.to_csv("output/global_synonames_nx.csv", index = False)