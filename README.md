#Converter from MPQA to KAF/NAF#

This repository implements a converter from the original format of the [MPQA](http://mpqa.cs.pitt.edu/corpora/mpqa_corpus/) corpus to [KAF](https://github.com/opener-project/kaf/wiki/KAF-structure-overview) or
[NAF](http://www.newsreader-project.eu/files/2013/01/techreport.pdf) formats. It allows to automatically retokenize and POS-tag the resulting files.

##Introduction##

The GATE annotations of the original corpus are converted to triples (opinion_expression, target, holder), following this rules:
* GATE-direct_subjective annotations are considered to be the opinion expressions of our triples
* GATE-agent annotations linked to the GATE-direct_subjective annotations are considered to be opinion holders
* GATE-target annotations linked to the GATE-direct_subjective through the GATE_attitude annotations are considered to be our opinion holders

All the attributes of the GATE annotations are stored in the attributes `polarity` and `strength` of the extracted results. Furthermore, the MPQA
corpus is annotated at token level, and the opinions in KAF/NAF are linked to terms, so we will provide some scripts to automatically retokenise,
pos-tag and map the opinions from token-links to term-links. These are the main steps that will be applied:
1. Convert the original MPQA to KAF/NAF (opinions linked to tokens)
2. Retokenise using apache open-nlp and fix some problems with annotations including punctuation symbols
3. Apply the TreeTagger (pos-tagging) and map the opinions to be linked with terms


##Requirements and installation##

The requirementes are three:
1. The [KafNafParser](https://github.com/cltl/KafNafParserPy) library to parse and create KAF/NAF files
2. [Apache open-nlp toolkit] (https://opennlp.apache.org/) for performing the tokenisation
3. TreeTagger (http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) pos-tagger

To make it easy we provide one script that performs an **automatic and quick installation**. This script is called
`install_dependencies.sh` and will download and install all the required libraries. So basically the only needed steps
to get this software running is to clone this repository and run the installation script:
```shell
cd your_local_path
git clone XXXX
cd XXXX
bash install_dependencies.sh
```

##Usage##
There is one script called `run_all.sh` that will perform all the steps explained in the introduction. The only requeriment is that
you will have to download the MPQA corpus by yourself. Once you have it on your local machine, you will need to edit the first lines
of the script:
```shell
MPQA='./database.mpqa.2.0'
TYPE='kaf'      #you can use also naf
OUT='my_out'
USE_ATTITUDE=''         #change it to -attitude to use mpqa GATE-attitude annotations as opinion expressions
```

the `MPQA` variable must point to the place where you have downloaded the MPQA corpus (in my case just in ./database.mpqa.2.0). Then
`TYPE` could be either kaf or naf, to force to create NAF or KAF files. `OUT` is the name of the folder where you want to store the
new files, and finally `USE_ATTITUDE` can be set to `-attitude` to use the GATE_attitude annotations as opinion expressions. If it is
set to blank, the GATE_direct_subjective annotations will be used as opinion expressions. Once you have modified this script, you will
need just to run the script `run_all.sh` that will perform all the steps mentioned in the introduction.
```shell
bash run_all.sh
```

The result will be a new folder with the name you specified in the variable `OUT`, and you will find several KAF or NAF files for each MPQA file.
* $mpqa_name$.kaf: the result of the first conversion from MPQA to KAF (or NAF in case)
* $mpqa_name$.tok.kaf: the result of the tokenisation of the previous file using apache open-nlp tokeniser
* $mpqa_name$.tok.pos.kaf: the result of pos-tagging of the previous file using TreeTagger

The files *.tok.pos.kaf contain the final result, with the tokens, terms and pos-tags, and with the original MPQA opinions linked to the new terms. These are the files
that should be used.

#Contact#
* Ruben Izquierdo
* Vrije University of Amsterdam
* ruben.izquierdobevia@vu.nl  rubensanvi@gmail.com
* http://rubenizquierdobevia.com/