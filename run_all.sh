#!/bin/bash

MPQA='./database.mpqa.2.0'
TYPE='kaf'	#you can use also naf
OUT='my_out'
USE_ATTITUDE='' 	#change it to -attitude to use mpqa GATE-attitude annotations as opinion expressions

########################################################
## Converting to KAF/NAF, first step
########################################################
echo Converting to KAF/NAF
python convert_mpqa.py -mpqa $MPQA -type $TYPE -out $OUT $USE_ATTITUDE


########################################################
## Apply tokenizer to all
########################################################
echo 'Applying retokenisation with opennlp'
for this_file in $OUT/*.$TYPE
do
    echo "Retokenising $this_file"
    out_file=${this_file::-4}.tok.$TYPE
    cat $this_file | apply_tokenizer.py > $out_file 2> $out_file.err
    echo "Done, num lines="`wc -l $out_file | cut -d" " -f1`
    echo
done

########################################################
## Apply TREETAGGER and RE_MAP opinions-tokenids to opinion-termids
########################################################
echo 'Applying pos-tagging with treetagger and re-mapping opinion spans'
for this_file in $OUT/*.tok.$TYPE
do
  echo "Pos-tagging $this_file"
  out_file=${this_file::-8}.tok.pos.$TYPE
  err_file=$out_file.err
  tmp_term=`mktemp`
  
  sed -e 's/&gt;/0/g' $this_file | sed -e 's/&lt;/0/g' | python ./ext_libs/treetagger_kaf_naf/treetagger.py > $tmp_term 2> $err_file
  python apply_pos_tagger.py $this_file $tmp_term > $out_file 2>> $err_file 
  echo "Done, num lines="`wc -l $out_file | cut -d" " -f1`
  rm $tmp_term
done



