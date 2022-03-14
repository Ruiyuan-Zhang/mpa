#!/bin/bash

# This is a wrapper for `sbatch_run.sh` to run repeated experiments
# It will duplicate the same params file for several times and run them all

#######################################################################
# An example usage:
#     GPUS=1 CPUS_PER_TASK=8 MEM_PER_CPU=6 QOS=normal REPEAT=5 ./script/dup_run_sbatch.sh \
#       rtx6000 test-sbatch test.py ddp config.py config.yml --fp16 --cudnn
#######################################################################

# read args from command line
GPUS=${GPUS:-1}
CPUS_PER_TASK=${CPUS_PER_TASK:-5}
MEM_PER_CPU=${MEM_PER_CPU:-8}
QOS=${QOS:-normal}
REPEAT=${REPEAT:-5}

PY_ARGS=${@:6}
PARTITION=$1
JOB_NAME=$2
PY_FILE=$3
CFG=$4
YML=$5

for repeat_idx in $(seq 1 $REPEAT)
do
    yml="${YML:0:(-4)}-dup${repeat_idx}.yml"
    cp $YML $yml
    job_name="dup${repeat_idx}-${JOB_NAME}"
    echo "./script/sbatch_run.sh $PARTITION $job_name $PY_FILE --cfg_file $CFG --yml_file $yml $PY_ARGS"
    ./sbatch_run.sh $PARTITION $job_name $PY_FILE --cfg_file $CFG --yml_file $yml $PY_ARGS
done