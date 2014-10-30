#!/bin/bash

mkdir ext_libs
cd ext_libs
touch __init__.py

########################################################
## Installing the KafNafParserPy (ext_libs/KafNafParserPy)
########################################################

echo 'Installing the KafNafParserPy library'
git clone https://github.com/cltl/KafNafParserPy.git


########################################################
## Installing the open-nlp (ex_libts/apache-opennlp-1.5.3)
########################################################
echo 'Installing apache opennlp'
wget http://ftp.tudelft.nl/apache//opennlp/opennlp-1.5.3/apache-opennlp-1.5.3-bin.tar.gz
tar xzf apache-opennlp-1.5.3-bin.tar.gz
rm apache-opennlp-1.5.3-bin.tar.gz

########################################################
## Installing the open-nlp models
########################################################
echo 'Installing open-nlp models'
cd apache-opennlp-1.5.3
mkdir models
cd models
wget http://opennlp.sourceforge.net/models-1.5/en-token.bin
cd ../..


########################################################
## Installing the treetagger_kaf_naf
########################################################

#You can skip this step if you have the treetagger_kaf_naf installed, so just create a symbolic link to it
#ln -s /home/path_to_it/treetagger_kaf_naf treetagger_kaf_naf

echo 'Installing the treetagger-kaf-naf'
git clone https://github.com/rubenIzquierdo/treetagger_kaf_naf.git
cd treetagger_kaf_naf
bash install_dependencies.sh
cd ..


