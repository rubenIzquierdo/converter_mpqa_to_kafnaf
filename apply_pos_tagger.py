#!/usr/bin/env python

import sys
from lxml import etree



#===============================================================================
# This script takes 2 parametes as inputs:
# 1) A KAF file with text and opinion layers, with the opinion layer linked with the text layer (token id
# 2) A KAF file with the text layer and the term layer (created with a pos tagger)
# 
# And performs the following steps:
# 1) Read the term layer from the 2nd file
# 2) Insert the term layer in the 1st parameter file
# 3) Obtain a mapping from the token ids to the term ids
# 4) Map the opinion layer from token ids to term ids (keeping the previous token id as a new attribute previous_token_id in the target elements)
# 
# The output is the resulting KAF file
#===============================================================================


def get_mapping_token_term(term_layer):
    token_to_term = {}
    for term in term_layer.findall('term'):
        tid = term.get('tid')
        target_ids = [target.get('id') for target in term.findall('span/target')]
        for token_id in target_ids:
            token_to_term[token_id] = tid
    return token_to_term


if __name__ == '__main__':
    file_opinions = sys.argv[1]
    file_terms = sys.argv[2]
  
    ## Read the term layer
    xml_terms = etree.parse(file_terms)
    term_layer = xml_terms.find('terms')


    ## Reading the xml with opinions
    xml_opinions = etree.parse(file_opinions)
    #Look for the position of the text child
    position_of_text = 0
    for child in xml_opinions.getroot():
        if child.tag == 'text':
            break
        position_of_text += 1
        
    ##Insert the term layer in the xml with opinions
    xml_opinions.getroot().insert(position_of_text+1,term_layer)
    
    ## Obtain the mapping from token id to the new term id
    token_to_term = get_mapping_token_term(term_layer)
    
    ## Finally we need to map the token identifiers in the opinion layer
    for opinion in xml_opinions.findall('opinions/opinion'):
        for opinion_child in opinion:
            for target in opinion_child.findall('span/target'):
                old_token_id = target.get('id')
                new_term_id = token_to_term[old_token_id]
                target.set('id',new_term_id)
                #target.set('previous_token_id',old_token_id)

    xml_opinions.write(sys.stdout)
    sys.exit(0)
  