import numpy as np
import Levenshtein
import itertools 
import math

def flag_similar_names(phon_pairs):
    '''
    Run Levenshtein distance on every combination of strings, 
    and returns the smallest value.  
    
    Note: Does not calculate distance measures between strings in the 
    same tuple, as each tuple represents the same token.  
    ''' 
    all_phon = [value for pair in phon_pairs for value in pair]
    phon_pairs = set([tuple(pair) for pair in phon_pairs])
    comb_phon = set(itertools.combinations(all_phon, 2))
    final_values = list(comb_phon - phon_pairs)
    l_dist = math.inf  
    for val in final_values: 
        temp = Levenshtein.distance(val[0], val[1])
        if temp < l_dist: 
            l_dist = temp 
    return l_dist 

#Create Levenshtein distance matrix - clean this code 
def link_pairs(l_pairs):
    '''
    Links pairs with shared values. Returns masters lists with all linked pairs. 
    E.g. Input: [1,2] [2,3]; Output: [1,2,3]
    '''
    i = 0 
    while (len(l_pairs) > i+1): 
        iterate = False 
        l_pairs_copy = l_pairs 
        new_pattern = list(l_pairs[i])
        for pair in l_pairs[i+1:]: 
            if any(x in new_pattern for x in pair):
                new_pattern.extend(list(pair))
                iterate = True 
                l_pairs_copy.pop(i+1)
        l_pairs_copy[i] = new_pattern 
        l_pairs = l_pairs_copy 
        if iterate: #iterate from 0 if change made 
            i = 0 
        else: 
            i = i+1 
    return l_pairs

def create_patterns(all_phon):
    '''
    Runs Levenshtein distance calculations on every pair of phonetic keys for a given URI. 
    Returns lists of all related phonetic keys (per a Levenshtein distance threshold)
    for each URI. 
    E.g. threshold = 1; input keys = [AR, AK, JLZ, TLZ]; returns [[AR, AK], [JLZ, TLZ]
    '''
    input_array = np.array(all_phon)
    l_function = np.vectorize(Levenshtein.distance) #computational efficiency 
    l_results = l_function(input_array[:, np.newaxis], input_array) #results matrix 
    l_results = np.tril(l_results) #clip along diagonal
    l_pairs_input = list(np.argwhere(l_results == 1))
    
    new_pairs  = link_pairs(l_pairs_input)
    clean_patterns = [list(set(value)) for value in new_pairs]   
    
    #Match index values to phonetics patterns
    phon_patterns = []
    for value in clean_patterns: 
        phon_patterns.append(input_array[value])
    return phon_patterns 

def find_pollution(uri, name_list, double_check):
    '''
    Identifies name lists that have been 'polluted' – where
    non-synonymous names have been listed together. 
    '''
    name_list = set(name_list)
    double_subset = double_check[double_check["uri"] == uri] 
    overlap = double_subset["names_split"].apply(lambda x: len(name_list.intersection(x)))
    if max(overlap) > 1: 
        check = True 
    else: 
        check = False 
    return check 
