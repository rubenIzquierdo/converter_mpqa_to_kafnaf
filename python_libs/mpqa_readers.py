import os
import sys
import re
from operator import itemgetter

class CToken:
    def __init__(self,value,token_id=None,sentence=None,offset=None):
        self.token_id = token_id
        self.sentence = sentence
        self.offset = offset
        self.annotation_id = ''
        self.value = value
        
    def __repr__(self):
        return str(self.value)+' '+str(self.token_id)+' # '+str(self.sentence)+' # '+str(self.offset)+' # '+str(self.annotation_id)
        
        
        

class CAnnotations:
    def __init__(self):
        self.id=''
        self.annotations = {}  # annot_id --> (begin_int, end_int, type_str, features{} name --> [list of values])
        self.annot_ids_for_single_offset = {}    # Expanded list, offset range are expanded {offset_string} --> anot id
        self.annotation_id_for_link_id = {} ## Index from link id's to annotation id's

        
    def parse__str_features(self,feats_str):
        feats_map = {}
        results = re.findall(r'([^ ]+)="([^"]+)"', feats_str)
        for name, value in results:
            l_values = [val.strip() for val in value.split(',')]          
            feats_map[name] = l_values
        return feats_map
            
    def add_annotation(self,anot_id,anot_offsets,anot_type,features_str):
        fields_offset = anot_offsets.split(',')
        begin_offset = int(fields_offset[0])
        end_offset = int(fields_offset[1])
#        print 'Anot id:',anot_id
#        print 'begin offset',begin_offset
#        print 'End offset',end_offset
#        print 'Anot type',anot_type
        
        feats = {}
        if features_str is not None:
            feats = self.parse__str_features(features_str)
            
#        print 'FEATURES_STR',features_str
#        print 'FEATS MAP',feats
#        print '#'*100
        self.annotations[anot_id] = (begin_offset,end_offset,anot_type, feats)
        if 'id' in feats:
            for single_id in feats['id']:
                single_id = anot_type+'#'+single_id
                self.annotation_id_for_link_id[single_id] = anot_id
        
    def expand_annotation_offsets(self):
        for anot_id, anot_info in self.annotations.items():
            begin_offset = anot_info[0]
            end_offset = anot_info[1]
            ###if end_offset == begin_offset:   end_offset+=1
                
            for offset in range(begin_offset,end_offset+1):
                offset = str(offset)
                if offset in self.annot_ids_for_single_offset:
                    self.annot_ids_for_single_offset[offset].append(anot_id)
                else:
                    self.annot_ids_for_single_offset[offset] = [anot_id]

                
        
class CAnnotator_reader:
    def __init__(self,anot_file, sents_file):
        self.offsets_sentences = [] ## [(0,50),(52,14)....]
        self.__load_sentences(sents_file)
        self.all_annotations = CAnnotations()
        self.__load_annotations(anot_file)
        self.all_annotations.expand_annotation_offsets()

    def __load_sentences(self, sents_filename):
       
        if not os.path.exists(sents_filename):
            print>>sys.stderr,'Error. The file',sents_filename,'not found'
            sys.exit(-1)
        
        fic = open(sents_filename,'r')
        for line in fic:
            #Line is #.... or
            #id    offsets    string    GATE_sentence
            #1     290,471    string    GATE_sentence
            if line[0] != '#':
                fields = line.strip().split('\t')
                type_annot = fields[3]
                if type_annot == 'GATE_sentence':
                    offset = fields[1]
                    fields_offset = offset.split(',')
                    if len(fields_offset)==2:
                        begin_offset = int(fields_offset[0])
                        end_offset = int(fields_offset[1])
                        self.offsets_sentences.append((begin_offset,end_offset))
        fic.close()
        # The sentences are not sorted, we have to sort them
        clean_offsets = []
        for count, (this_begin, this_end) in enumerate(self.offsets_sentences):
            is_contained = False
            for count2, (cmp_begin, cmp_end) in enumerate(self.offsets_sentences):
                if count2 != count and (this_begin >= cmp_begin and this_end <= cmp_end): ## IS not the same and it's contained
                    is_contained = True
                    break
            if not is_contained:
                clean_offsets.append((this_begin,this_end))
        
        self.offsets_sentences = clean_offsets
            
        
        
        
        self.offsets_sentences.sort(key=itemgetter(0))

    def get_num_sentence(self,offset,len_word):
        current_sent = 1
        for (begin_offset, end_offset) in self.offsets_sentences:
            for this_offset in range(offset,offset+len_word):
                #print>>sys.stderr,'\n\n',current_sent,begin_offset,end_offset,this_offset
                if begin_offset <= this_offset and this_offset <=end_offset:
                    return current_sent
            current_sent += 1
        return None
    
    def get_sentences_boundaries(self):
        for begin_sent, end_sent in self.offsets_sentences:
            yield (begin_sent,end_sent)
            
    def __load_annotations(self, anot_filename):
        
        if not os.path.exists(anot_filename):
            print>>sys.stderr,'Error. The file',anot_filename,'not found'
            sys.exit(-1)
        
        fic = open(anot_filename,'r')
        for line in fic:
            if line[0] != "#":
                ## line --> 121    1515,1532    string    GATE_expressive-subjectivity     nested-source="w" intensity="high" polarity="negative"
                fields = line.strip().split('\t')
                anot_id = fields[0]
                anot_offsets = fields[1]
                anot_type = fields[3]
                if len(fields)==5: 
                    anot_feats = fields[4]
                else: anot_feats = None
                self.all_annotations.add_annotation(anot_id, anot_offsets, anot_type, anot_feats)
        fic.close()
            
    def get_anot_ids_for_single_offset(self,offset):          
        return self.all_annotations.annot_ids_for_single_offset.get(offset,None)
    
    def get_annotations_with_type(self,my_type):
        for anot_id, anot_data in self.all_annotations.annotations.items():
            ## Anots is like (begin_int, end_int, type_str, features{} name --> [list of values])
            if anot_data[2] == my_type:
                yield anot_id, anot_data
                
    def get_annotation_from_link_id(self,link_id,anot_type):
        link_id = anot_type+'#'+link_id
        if link_id in self.all_annotations.annotation_id_for_link_id:
            annot_id = self.all_annotations.annotation_id_for_link_id[link_id]
            return annot_id,self.all_annotations.annotations[annot_id]
        else:
            print>>sys.stderr,'ERROR!!! There is no annotation with link-id ',link_id
            return None,None
            


class CSentence:
    def __init__(self, text,begin_sent_offset=0):
        self.raw_sentence = text
        self.tokens = self.raw_sentence.split(' ')
        self.offsets = []
        self.annot_ids = []
        ##Calculating relatives offsets for each token
        current_offset = begin_sent_offset
        for tok in self.tokens:
            self.offsets.append(current_offset)
            current_offset = current_offset + len(tok) + 1 ## whitespace
            
    def assign_annotation_ids(self,annotator_reader):
        for num_token, token in enumerate(self.tokens):
            offset_str = str(self.offsets[num_token])
            list_anot_ids = annotator_reader.get_anot_ids_for_single_offset(offset_str)
            
            





