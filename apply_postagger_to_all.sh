#!/bin/bash

my_mpqa=$1   #'my_mpqa_in_kaf_new'
filename=$2  #'vu.doclist.attitude.ula.xbank'
input_ext=$3 # .opennlp.kaf
output_ext=$4 #.opennlp.pos.kaf

export TREE_TAGGER_PATH=/home/izquierdo/tools/treetagger/


while read file;
do
  input_file=$my_mpqa/$file$input_ext;
  output_file=$my_mpqa/$file$output_ext;
  err_file=$my_mpqa/$file$output_ext.err
  tmp_term=`mktemp`
   
  printf 'Pos tagging %s ' $file;
  while :; do
    printf ".";
    sleep 1;
  done &
  bgid=$!  


  # First --> call the pos-tagger from 
  # For the problem with the -- in the comments with the IXA parser
  # Included remove_opinion_layer.py because with the new version of the pos-tagger it fails with the opinion linked to the token layer.
  
  #For the repo of Rodrigo (opennlp)
  ###sed 's/--/-/g' $input_file | remove_opinion_layer.py | java -jar /Users/ruben/opener_repos/pos-tagger-en-es/core/target/ehu-pos-1.0.jar -l en -lem plain > $tmp_term;
  ###cat $input_file | java -jar /Users/ruben/opener_repos/pos-tagger-en-es/core/target/ehu-pos-1.0.jar -l en -lem plain > $tmp_term;
  
  #Remove html entities
  sed -e 's/&gt;/0/g' $input_file | sed -e 's/&lt;/0/g' | /home/izquierdo/code/VU-tree-tagger_kernel/core/tt_from_kaf_to_kaf.py > $tmp_term 2> $err_file;
  
  # Apply my script
  apply_pos_tagger.py $input_file $tmp_term > $output_file 2>> $err_file ;

  if [ -s $output_file ]; then
    printf ' OK!\n';
  else
    printf ' WRONG!\n'
  fi;
  kill -9 $bgid;
  rm $tmp_term;
done < $filename 2> /dev/null
 
