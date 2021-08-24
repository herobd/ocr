script_template="""#!/bin/bash

#SBATCH --dependency=afterok:{}
#SBATCH --time=1:00:00   # walltime
#SBATCH --ntasks=2
#SBATCH --nodes=1
#xxSBATCH --gres=gpu:1
#SBATCH -J "convert {}"
#SBATCH --mem-per-cpu=24048M
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


mkdir {}
cd ~/ocr
python convert_to_png.py {} {}
"""
import sys,os

sec = sys.argv[1]
a,b,c = sec.split('.')

untarred_dir = '../compute/images{}/{}/{}/{}'.format(a,a,b,c)
out_dir = '~/compute/out{}/{}.{}/{}'.format(a,a,b,sec)

last_job = '../ocr/{}.{}.tmp'.format(a,b)

with open(last_job) as f:
    job_info = f.read()
#Submitted batch job 43122187
job_info=job_info.strip()
job_info = job_info.split(' ')
last_job_id=job_info[-1]
#print('convert depends on {}'.format(last_job_id))

#if not os.path.exists(untarred_dir):
#    add = 'tar -xf tars/images.{}.tar'.format(sec)
#else:
#    add = ''
if sec=='a.f.a':
    extra='#SBATCH --mail-type=END'
else:
    extra=''

script = script_template.format(last_job_id,sec,extra,out_dir,untarred_dir,out_dir)


with open('runs/run_convert_{}.pbs'.format(sec),'w') as f:
    f.write(script)
