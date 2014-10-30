#!/usr/bin/env python

import sys
import os
from subprocess import Popen,PIPE
from operator import itemgetter
from lxml.etree import Element

from ext_libs.KafNafParserPy import KafNafParser
from python_libs.token_matcher import token_matcher

##############
__this_dir__ = os.path.dirname(os.path.realpath(__file__))
OPENNLP = __this_dir__ + '/ext_libs/apache-opennlp-1.5.3/bin/opennlp'
TOKENIZER_MODEL = __this_dir__ +'/ext_libs/apache-opennlp-1.5.3/models/en-token.bin'
os.environ['LC_ALL']='en_US.utf8'
#########################

def run_opennlp_tokenizer(list_tokens,offset=0):
    my_input_str = ' '.join(list_tokens)
    # Included for the problem with the constituency parser
    my_input_str = my_input_str.replace('(',' ( ')
    my_input_str = my_input_str.replace(')',' ) ')
    my_input_str = my_input_str.replace('{',' { ')
    my_input_str = my_input_str.replace('}',' } ')
    
    #print my_input_str.encode('utf-8')
    cmd = OPENNLP+' TokenizerME '+TOKENIZER_MODEL
    tokenizer = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE,shell=True)
    
    my_out,my_err = tokenizer.communicate(my_input_str.encode('utf-8'))

    print>>sys.stderr,my_err
    #print>>sys.stderr,my_out
    tokenized_tokens = my_out.strip().split(' ')
    
    ret = []
    for n, token in enumerate(tokenized_tokens):
       ret.append((token.decode('utf-8'),'w'+str(n+offset)))
    return ret
    
    
if __name__ == '__main__':
    my_kaf_parser = KafNafParser(sys.stdin)
        
    sentences = []
    current_sent = []
    previous_sent_id = None
    
    for token_obj in my_kaf_parser.get_tokens():
        sentence = token_obj.get_sent()
        token = token_obj.get_text()
        token_id = token_obj.get_id()
    
        if previous_sent_id !=None and sentence != previous_sent_id:
            sentences.append((previous_sent_id,current_sent))
            current_sent = []
        current_sent.append((token,token_id))
        previous_sent_id = sentence
        
    sentences.append((sentence,current_sent)) 
    
    offset=0
    final_map_mpqa_to_new = {}
    mpqa_id_to_new_id = {}

    new_text_element = Element('text')
    overall_offset = 0
    map_id_to_token_new = {}
    for sent_id, tokens in sentences[:]:
        # Convert to string:
        print>>sys.stderr,'Processing sentence ',sent_id
        list_token_ids = []
        list_tokens = []
        for token, token_id in tokens:
            list_tokens.append(token)
            list_token_ids.append(token_id)
            
        print>>sys.stderr,'  Running opennlp tokenizer...'
        list_new = run_opennlp_tokenizer(list_tokens,offset)
        offset += len(list_new)
        ##print list_new[:3],'...',list_new[-3:]
        
        
        for token,new_id in list_new:
            map_id_to_token_new[new_id] = token
            if my_kaf_parser.get_type() == 'NAF':
                new_token = Element('wf',attrib={'id':new_id,'sent':sent_id})
            else:
                new_token = Element('wf',attrib={'wid':new_id,'sent':sent_id, 'offset': str(overall_offset)})
            overall_offset += len(token) + 1
            new_token.text = token
            new_text_element.append(new_token)
        super_d = {}    ## This is the dictionary of mappings

        token_matcher(tokens,list_new,super_d)

        #Building a map, from the original token, to the new possible list of new tokens
        print>>sys.stderr,'  Building an index old_token_id --> [list new ids]'
        for new_id, list_mpqa_ids in super_d.items():
            for mpqa_id in list_mpqa_ids:
                if mpqa_id not in mpqa_id_to_new_id:  mpqa_id_to_new_id[mpqa_id] = [new_id]
                else: mpqa_id_to_new_id[mpqa_id].append(new_id)

       
    ## EXTRACT AND MAP THE OPINIONS
    # Remove the previous text layer and inser the new one
    print>>sys.stderr,'Regenerating the new text layer'
    path_to_text = my_kaf_parser.tree.find('text')
    my_kaf_parser.tree.getroot().remove(path_to_text)
    my_kaf_parser.tree.getroot().insert(0,new_text_element)
    
    print>>sys.stderr,'Mapping the old token ids in the opinion layer to the new ones'
    for opinion_obj in my_kaf_parser.tree.findall('opinions/opinion'):
        for opinion_child in opinion_obj:
            for my_span in opinion_child.findall('span'):
                for target in my_span.findall('target'):
                    my_span.remove(target)
                    old_id = target.get('id')
                    new_ids = sorted(mpqa_id_to_new_id[old_id])                   
                    for new_id in new_ids:
                        my_span.append(Element('target',attrib={'id':new_id}))
                
                # The first of last target are removed in case of punctuation symbols
                all_tars =  my_span.findall('target')
                for num_tar, target in enumerate(all_tars):
                    if num_tar == 0 or num_tar == len(all_tars) - 1:
                        text = map_id_to_token_new[target.get('id')]
                        if len(text) == 1:
                            my_span.remove(target)
                    
 
        
    my_kaf_parser.dump(sys.stdout)
    sys.exit(0)
    
    
