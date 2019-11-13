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
import itertools 
import math
import networkx as nx 
from synonames_helper import flag_similar_names, \
     create_patterns, link_pairs, find_pollution

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
    df["uri"] = df["uri"].apply(lambda x: x.split("/")[-1])
    df["names_split"] = df["name"].apply(lambda x: x.split())
    double_check = df[["uri", "names_split"]] #For later review

    #Split name strings 
    names_df = pd.DataFrame(df.names_split.to_list())
    names_df["uri"] = df["uri"].values
    names_df["lang"] = df["lang"].values
    
    #names_df.to_csv("interim/names_df.csv", index = False)

    del df 

    #Transform - from wide to long 
    names_melt = pd.melt(names_df, id_vars = ["uri", "lang"])
    names_melt.drop_duplicates(subset = ["uri", "value"], inplace = True) #Change this if you want lang frequency
    names_melt = names_melt.dropna()
    names_melt = names_melt[names_melt["value"].apply((lambda x: len(x) > 2))] #Length cut-off 

    #Transliterate
    names_melt["roman"] = names_melt["value"].apply(lambda x: normalize(latinize_text(x)))

    stopwords = ["the", "und", "de", "di", "of", "ze", "der", "and", "la", "iz",
                "al", "af", "av", "von", "van", "el", "od", "ze", "da", "wa", 
                "dello", "dari", "le", "z", "or", "oder", "ou", "the", "ton", "tes",
                 "jr", "sa", "do", "del", "του", "das", "sao", "san", "dos", "des"]

    names_melt = names_melt[~names_melt["roman"].isin(stopwords)]
    names_melt["roman"] = names_melt["roman"].apply(lambda x: None if re.search(r'\d|i', x) else x)
    names_melt = names_melt.dropna()
    #names_df.to_csv("interim/names_df2.csv", index = False)

    #Add phonetics 
    names_melt["phonetics"] = names_melt["roman"].apply(lambda x: list(phonetics.dmetaphone(x)))
    names_melt = names_melt[names_melt["phonetics"].apply(lambda x: any(x))] #Discard empty tuples
    names_melt["phonetics"] = names_melt["phonetics"].apply(lambda x: [x[0]] if x[1] == '' else x)
    #names_melt.to_csv("interim/names_melt.csv", index = False)

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

    #Flag uris/patterns that have merged names in error
    phon_group = pd.DataFrame(phon_stack.groupby(["uri", "pattern_no"])["stack_value"].apply(list)).reset_index()
    phon_group["stack_value"] = phon_group["stack_value"].apply(lambda x: list(set(x)))
    phon_group["check"] = phon_group.apply((lambda x: find_pollution(x[0], x[2], double_check)), axis = 1)
    phon_group = phon_group.rename(columns={'stack_value':'name'})

    del phon_stack

    #Save networkx output 
    nx_df = pd.DataFrame(phon_group["name"].to_list())
    nx_df["uri"] = phon_group.uri.values
    nx_df["pattern_no"] = phon_group.pattern_no.values
    nx_df["check"] = phon_group.check.values
    nx_df = pd.melt(nx_df, id_vars = ["uri", "pattern_no", "check"])
    nx_df = nx_df.dropna()
    nx_df = nx_df.rename(columns = {'value':'name'})
    nx_df[["uri", "pattern_no", "check", "name"]].to_csv("output/names_nodes_nx.csv", mode = 'a', index = False)

    #Neo4J output 
    phon_group.to_csv("output/names_nodes_neo4j.csv", mode = 'a', index = False)

    phon_group["name"] = phon_group["name"].apply(lambda x: ','.join(x))
    phon_group.to_csv("output/names_nodes_str_neo4j.csv",  mode = 'a', index = False)

    del phon_group, nx_df 

print ("FINISHED - uri synonames")
print ("STARTING - network calculations")

#Networkx - create gnetwork, merge identical name nodes
#nodes_df = nx_csv 
nodes_df = pd.read_csv("output/names_nodes_nx.csv")
print ("loaded nx data!")

name_groups = nodes_df.groupby(["uri", "pattern_no", "check"])["name"].apply(list)

#Create dictionary with weighted edges
#count - co-occurences; weight - # polluted instances 
names_dict = {}
for index_val, val in enumerate(name_groups):
    if name_groups.index[index_val][2]:
        weight = 1
    else:
        weight = 0
    if len(val) > 1: 
        val = list(set(val))
        val = sorted(val)
        for pair in list(itertools.combinations(val, 2)):
            if pair in names_dict:
                names_dict[pair]['count'] += 1 
                names_dict[pair]['weight'] += weight
            else:
                names_dict[pair] = {'count': 1, 'weight': 1 * weight}

g_data = pd.DataFrame.from_dict(names_dict,'index').reset_index()
g_data.columns = ['source', 'target', 'count', 'weight']

#decide on calculation for weighted edge 

#Import nx graph
G = nx.from_pandas_edgelist(g_data, 'source', 'target', ['count', 'weight'])
components = nx.connected_component_subgraphs(G)

#Export 
with open ('output/global_synonames.csv', 'w') as file: 
    wr = csv.writer(file)
    wr.writerows(list(components))
file.close()

nx.write_gpickle(G, "output/nx_graph_pickle")
nx.readwrite.gexf.write_gexf(G, "output/nx_graph_gexf")
