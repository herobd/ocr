script_template="""#!/bin/bash

#SBATCH --dependency=afterok:{}
#SBATCH --time=11:30:00   # walltime
#SBATCH --ntasks={}
#SBATCH --nodes=1
#xxSBATCH --gres=gpu:1
#SBATCH -J "ocr {}"
#SBATCH --mem-per-cpu=4G
#SBATCH --mail-user=herobd@gmail.com   # email address
#SBATCH --mail-type=FAIL
{}
#xxSBATCH --qos=standby   
#xxSBATCH --requeue
#xxSBATCH -C pascal

#130:00:00

export PBS_NODEFILE=`/fslapps/fslutils/generate_pbs_nodefile`
export PBS_JOBID=$SLURM_JOB_ID
export PBS_O_WORKDIR="$SLURM_SUBMIT_DIR"
export PBS_QUEUE=batch

export OMP_NUM_THREADS=$SLURM_CPUS_ON_NODE

module load libtiff/4.0
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/fslhome/brianld/local/lib
export PATH=$PATH:/fslhome/brianld/local/bin
export TESSDATA_PREFIX=/fslhome/brianld/tesseract/tessdata

module remove miniconda3
source activate /fslhome/brianld/miniconda3/envs/new

cd ~/ocr
python read.py {} {}
"""
import sys
num_threads=10
sec = sys.argv[1]
a,b,c = sec.split('.')

out_dir = '~/compute/out{}/{}.{}/{}'.format(a,a,b,sec)
last_job = '../ocr/{}.tmp'.format(sec)

with open(last_job) as f:
    job_info = f.read()
#Submitted batch job 43122187
job_info=job_info.strip()
job_info = job_info.split(' ')
last_job_id=job_info[-1]
#print('ocr depends on {}'.format(last_job_id))

if sec=='a.l.y':
    extra='#SBATCH --mail-type=END'
else:
    extra=''

script = script_template.format(last_job_id,num_threads+1,sec,extra,out_dir,num_threads)

with open('runs/run_ocr_{}.pbs'.format(sec),'w') as f:
    f.write(script)
