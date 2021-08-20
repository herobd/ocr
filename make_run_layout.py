script_template="""#!/bin/bash

#SBATCH --dependency=afterok:{}
#SBATCH --time=2:00:00   # walltime
#SBATCH --nice
#SBATCH --ntasks=3
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH -J "layout {}"
#SBATCH --mem-per-cpu=4048M
#SBATCH --mail-user=herobd@gmail.com   # email address
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#xxSBATCH --qos=standby   
#xxSBATCH --requeue
#xxSBATCH -C pascal

#130:00:00

export PBS_NODEFILE=`/fslapps/fslutils/generate_pbs_nodefile`
export PBS_JOBID=$SLURM_JOB_ID
export PBS_O_WORKDIR="$SLURM_SUBMIT_DIR"
export PBS_QUEUE=batch

export OMP_NUM_THREADS=$SLURM_CPUS_ON_NODE

module remove miniconda3
module load cuda/10.1
module load cudnn/7.6
source activate /fslhome/brianld/miniconda3/envs/new

cd ~/ocr
python do_layout.py {}
"""
import sys
sec = sys.argv[1]

out_dir = '~/compute/out/{}'.format(sec)
last_job = '../ocr/{}.tmp'.format(sec)

with open(last_job) as f:
    job_info = f.read()
#Submitted batch job 43122187
job_info=job_info.strip()
job_info = job_info.split(' ')
last_job_id=job_info[-1]
print('layout depends on {}'.format(last_job_id))


script = script_template.format(last_job_id,sec,out_dir)


with open('runs/run_layout_{}.pbs'.format(sec),'w') as f:
    f.write(script)

