script_template="""#!/bin/bash

#SBATCH --time=1:00:00   # walltime
#SBATCH --nice
#SBATCH --ntasks=2
#SBATCH --nodes=1
#xxSBATCH --gres=gpu:1
#SBATCH -J "untar {}"
#SBATCH --mem-per-cpu=8048M
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


cd ~/compute
{}

"""
import sys,os

sec = sys.argv[1]
a,b = sec.split('.')

untarred_dir = '../compute/images{}/{}/{}'.format(a,a,b)
out_dir = '~/compute/out/{}'.format(sec)

if not os.path.exists(untarred_dir):
    command = 'tar -xf tars/images.{}.tar'.format(sec)
else:
    command = ''

script = script_template.format(sec,command)


with open('runs/run_untar_{}.pbs'.format(sec),'w') as f:
    f.write(script)
