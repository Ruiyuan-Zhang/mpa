#!/bin/bash

# run training on one category of BBD everyday subset

#######################################################################
# An example usage:
#     ./script/train_one_category.sh "GPUS=1 CPUS_PER_TASK=8 MEM_PER_CPU=5 QOS=normal REPEAT=3 ./script/dup_run_sbatch.sh rtx6000 everyday_cat ./script/train.py config.py --fp16 --cudnn" config.py Bottle
#######################################################################

CMD=$1
CFG=$2
cat=$3

cfg="${CFG:0:(-3)}-$cat.py"
cp $CFG $cfg
cmd="${CMD/$CFG/$cfg}"
cmd="$cmd --category $cat"
eval $cmd
