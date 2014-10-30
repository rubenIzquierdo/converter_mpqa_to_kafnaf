#!/usr/bin/env python

import glob
import os
import argparse

from python_libs.mpqa_readers import *
from ext_libs.KafNafParserPy import *

KAF = 'KAF'
NAF = 'NAF'

def get_mpqa_files(path_to_mpqa):
    '''
    Given a path to MPQA it returns (yields) triples:
    (path_to_plain_text,path_to_annotated_file, path_to_meta_file)
    It reads all the documents within the subfolder path_mpqa/docs/*
    '''
    for path_to_subfolder in glob.glob(path_to_mpqa+'/docs/*'):
        subfolder = os.path.basename(path_to_subfolder)
        for path_to_plain_file in glob.glob(path_to_subfolder+'/*'):
            plain_file = os.path.basename(path_to_plain_file)
            annotated_file = path_to_mpqa+'/man_anns/'+subfolder+'/'+plain_file+'/gateman.mpqa.lre.2.0'
            sentences_file = path_to_mpqa+'/man_anns/'+subfolder+'/'+plain_file+'/gatesentences.mpqa.2.0'
            meta_file = path_to_mpqa+'/meta_anns/'+subfolder+'/'+plain_file
            out_file = subfolder+'_'+plain_file
            yield path_to_plain_file, annotated_file, sentences_file, meta_file, out_file


def extract_direct_subjective(annotator_reader):
    opinions = []
    for anot_id, anot_data in annotator_reader.get_annotations_with_type('GATE_direct-subjective'):
        ## Anot_data (begin_int, end_int, type_str, features{} name --> [list of values])
        #DIRECT SUBJ: 955 (326, 326, 'GATE_direct-subjective', {'nested-source': ['w'], 'intensity': ['medium'], 'implicit': ['true'], 'attitude-link': ['occasion']})
        begin_offset, end_offset, type, features = anot_data
        
        # Extracting the agent --> holder data
        holder_data = None
        if 'nested-source' in features:
            for agent_id in features['nested-source'][-1::-1]:  ## From the last one to the first one
                if agent_id != 'w': # This is for the writer
                    anot_agent_id, holder_data = annotator_reader.get_annotation_from_link_id(agent_id,'GATE_agent')
                    if anot_agent_id is not None: 
                        break
                    
        ## Try to obtain the expression data
        for attitude_link_id in features.get('attitude-link',[]):
            attitude_anot_id, attitude_anot_data = annotator_reader.get_annotation_from_link_id(attitude_link_id,'GATE_attitude')   # This will be the opinion expression
            if attitude_anot_id is None: 
                continue
                
            begin_offset_att, end_offset_att, type_att, feats_att = attitude_anot_data
            
            #try to get the target data
            target_data = None
            for target_link_id in feats_att.get('target-link',[]):
                target_id, target_data = annotator_reader.get_annotation_from_link_id(target_link_id,'GATE_target')
                if target_id is not None: 
                    break

            #### DEBUG INFORMATION###    
            '''        
            print>>sys.stderr,'\tDIRECT SUBJ:',anot_id,anot_data
            print>>sys.stderr,'\t\tAttitude data:',attitude_anot_data
            print>>sys.stderr,'\t\tTarget data:',target_data
            print>>sys.stderr,'\t\tHolder data:',holder_data
            '''
            
            opinions.append((anot_data,attitude_anot_data,target_data,holder_data))
            #opinions.append((opinion_expression_data,holder_data, target_data))
    print>>sys.stderr,'\tNumber of opinions: ',len(opinions)
    return opinions


def clean_token(token):
    new_token = token.strip()
    new_token = new_token.replace('\t',' ')
    new_token = new_token.replace('\n',' ')
    return new_token

def get_token_ids_for_annotation(idx,annotation):
    ids = []
    if annotation is not None: 
        begin_offset = annotation[0]
        end_offset = annotation[1]
        for offset in range(begin_offset,end_offset+1):
            offset = str(offset)
            if offset in idx:
                new_id = idx[offset]
                if new_id not in ids:
                    ids.append(new_id)  
    return ids



def convert_to_kaf_naf(opinions ,output_file, type_file, token_ids_in_order, all_tokens, index_offset_to_token_id, use_attitude):
    
    knaf_obj = KafNafParser(type=type_file)
    knaf_obj.set_language('en')
    #CREATING THE TOKEN LAYER
    ids_removed = set()
    for token_id in token_ids_in_order:
        token,sentence,offset = all_tokens[token_id]   ## --> (token,sent,offset)
        my_clean_token = clean_token(token)
        
        ## If the sentence is None is because it's out of a sentence, it's whitespaces or newlines or so
        if sentence is None:             ## If the sentence is None is because it's out of a sentence, it's whitespaces or newlines or so
            ids_removed.add(token_id)
        elif len(my_clean_token) == 0:    ## After the cleaning there is nothing left
            ids_removed.add(token_id)
        else:
            #Create the wf element
            new_token = Cwf(type=type_file)
            new_token.set_id(token_id)
            new_token.set_offset(str(offset))
            new_token.set_sent(str(sentence))
            new_token.set_text(my_clean_token)
            knaf_obj.add_wf(new_token)
            
    num_opinion = 0
    for dse_data, attitude_data, target_data, holder_data in opinions:
        ## data is like --> 
        #(2681, 2877, 'GATE_attitude', {'intensity': ['high-extreme'], 'id': ['laughedAt'], 'attitude-type': ['arguing-pos'], 'target-link': ['ifThis']})
        attitude = attitude_data[3].get('attitude-type',['no-attitude'])[0]
        intensity_attitude = attitude_data[3].get('intensity',['no-intensity'])[0]
        polarity_dse = dse_data[3].get('polarity',['no-polarity'])[0]
        expresion_intensity_dse = dse_data[3].get('expression-intensity',['expression-intensity'])[0]
        intensity_dse = dse_data[3].get('intensity',['no-intensity'])[0]
        all_polarity = 'attitude=%s;polarity_dse=%s' % (attitude, polarity_dse)
        all_strength = 'intensity-attitude=%s;expression-intensity-dse=%s;intensity-dse=%s' % (intensity_attitude, expresion_intensity_dse, intensity_dse)
        
        #Build the opinion expression
        opi_exp_ids = tar_ids = hol_ids = None
        exp_identifier = tar_identifier = hol_identifier = 'None'
        if use_attitude:
            #we will use the attitude
            opi_exp_ids = [my_id for my_id in get_token_ids_for_annotation(index_offset_to_token_id,attitude_data) if my_id not in ids_removed]
            exp_identifier = attitude_data[2]+'#id:'+attitude_data[3].get('id',[''])[0]+'#'+str(attitude_data[0])+'-'+str(attitude_data[1])
        else:
            #dse used
            opi_exp_ids = [my_id for my_id in get_token_ids_for_annotation(index_offset_to_token_id,dse_data) if my_id not in ids_removed]
            exp_identifier = dse_data[2]+str(dse_data[0])+'-'+str(dse_data[1])
            
        tar_ids = [my_id for my_id in get_token_ids_for_annotation(index_offset_to_token_id,target_data) if my_id not in ids_removed]
        if target_data is not None:
            tar_identifier = target_data[2]+'#id:'+target_data[3].get('id',[''])[0]+'#'+str(target_data[0])+'-'+str(target_data[1])
        
        hol_ids = [my_id for my_id in get_token_ids_for_annotation(index_offset_to_token_id,holder_data) if my_id not in ids_removed]
        if holder_data is not None:
            hol_identifier = holder_data[2]+'#id:'+holder_data[3].get('id',[''])[0]+'#'+str(holder_data[0])+'-'+str(holder_data[1])
            
        #############
        ## Create the opinion
        #############
        my_opinion = Copinion(type=type_file)
        my_opinion.set_id('o'+str(num_opinion))
        num_opinion += 1
                          
        #############
        # opinion expression
        #############
        opi_exp = Cexpression()
        opi_exp.set_polarity(all_polarity)
        opi_exp.set_strength(all_strength)
        exp_span = Cspan()
        exp_span.create_from_ids(opi_exp_ids)
        opi_exp.set_span(exp_span)
        exp_text = ' '.join(all_tokens[token_id][0] for token_id in opi_exp_ids)
        opi_exp.set_comment(exp_identifier+'###'+exp_text)
        my_opinion.set_expression(opi_exp)
        
        #############
        # opinion target
        #############
        opi_tar = opinion_data.Ctarget()
        if len(tar_ids) != 0:
            tar_span = Cspan()
            tar_span.create_from_ids(tar_ids)
            opi_tar.set_span(tar_span)
        tar_text = ' '.join(all_tokens[token_id][0] for token_id in tar_ids)
        opi_tar.set_comment(tar_identifier+'###'+tar_text)
        my_opinion.set_target(opi_tar)
        
        #############
        # opinion holder
        #############
        opi_hol = opinion_data.Cholder()
        if len(hol_ids) != 0:
            hol_span = Cspan()
            hol_span.create_from_ids(hol_ids)
            opi_hol.set_span(hol_span)
        hol_text = ' '.join(all_tokens[token_id][0] for token_id in hol_ids)
        opi_hol.set_comment(hol_identifier+'###'+hol_text)
        my_opinion.set_holder(opi_hol)
        #############
        
        knaf_obj.add_opinion(my_opinion)
        
        
        
        
        
    knaf_obj.dump(output_file)
    print>>sys.stderr,'\t',type_file,'file created at', output_file

        
def process_document(plain_file, annotated_file, sentences_file, out_file, this_type, use_attitude_as_opinion_expression = False):
    ##############################################
    # Load the raw text
    ##############################################
    raw_text = ''
    
    fd = open(plain_file)
    raw_text = fd.read().decode('utf-8')
    fd.close()
    raw_text = raw_text.replace('\n',' ')
    raw_text = raw_text.replace('\t',' ')
    raw_text = raw_text.replace(u'\x1a',' ')
    print>>sys.stderr,'Processing',plain_file
    print>>sys.stderr,'\tAnnotations file',annotated_file
    print>>sys.stderr,'\tLen plain text',len(raw_text)
    ##############################################
    ##############################################



    ##############################################
    # Load the annotations
    ##############################################
    annotator_reader = CAnnotator_reader(annotated_file,sentences_file)
    ##############################################
    ##############################################


    ##############################################
    # Load the tokens and structures
    ##############################################
    tokens = raw_text.split(' ')    # list of tokens
    token_ids_in_order = []         # list of token identifiers
    all_tokens = {}                 # mapping from token_id --> (token, sentence, start_offset)
    index_offset_to_token_id = {}   # map from offset in text to token id (multiple offsets, for each character of the token) are mapped to the same token id)
    
    current_offset = 0
    for num_token, token in enumerate(tokens):
        sentence = annotator_reader.get_num_sentence(current_offset,len(token))
        token_id = 'w'+str(num_token+1)
        token_ids_in_order.append(token_id)
        all_tokens[token_id] = (token,sentence,current_offset)
        
        #This is to avoid tokens like (Don't, the token begins in the pos X, but the annotation refers to pos+1 as the beginning
        for this_offset in range(current_offset,current_offset+len(token)):
            index_offset_to_token_id[str(this_offset)] = token_id
        current_offset += len(token)+1
    print>>sys.stderr,'\tNum of tokens:',len(tokens)
    ##############################################
    ##############################################


    ## Opinions is a list of (DSE_data, attitude_data, holder_data, target_data
    opinions = extract_direct_subjective(annotator_reader)
    
    #We dont perform any filtering on the opinions
    convert_to_kaf_naf(opinions,out_file, this_type, token_ids_in_order, all_tokens,index_offset_to_token_id,use_attitude_as_opinion_expression)
    print>>sys.stderr
    
    

          

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts the MPQA corpus into KAF or NAF files with opinions')
    parser.add_argument('-mpqa',dest='path_to_mpqa',required=True, help ='Path to the database folder of the MPQA corpus')
    parser.add_argument('-type', dest='this_type',required=True, choices=['KAF','kaf','NAF','naf'], help='Type of the output files')
    parser.add_argument('-attitude', dest='use_attitude_as_opiexp', action='store_true',help='Use the MPQA attitude annotations as opinion expressions (by default the global direct subjective annotation will be used')
    parser.add_argument('-out', dest='out_folder',help='Output folder for the files')
    

    args = ['-mpqa','./database.mpqa.2.0','-type','kaf','-out','my_out']
    args = parser.parse_args(args)
    
    os.mkdir(args.out_folder)
    for plain_file, annotated_file, sentences_file, meta_file, out_file in get_mpqa_files(args.path_to_mpqa):
        complete_out_file = args.out_folder + '/' + out_file + '.' + args.this_type.lower()
        process_document(plain_file, annotated_file, sentences_file, complete_out_file, args.this_type.upper(), use_attitude_as_opinion_expression=args.use_attitude_as_opiexp)
    print>>sys.stderr,'#'*100
    print>>sys.stderr,'ALL DONE OK'
    print>>sys.stderr,'#'*100
    
        
