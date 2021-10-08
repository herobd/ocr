script_template="""#!/bin/bash

#SBATCH --dependency=afterok:{}
#SBATCH --time=24:00:00   # walltime
#SBATCH --ntasks=2
#SBATCH --nodes=1
#xxSBATCH --gres=gpu:1
#SBATCH -J "tar rm {}"
#SBATCH --mem-per-cpu=8048M
#SBATCH --mail-user=herobd@gmail.com   # email address
#SBATCH --mail-type=FAIL
#SBATCH --mail-type=END
#xxSBATCH --qos=standby   
#xxSBATCH --requeue
#xxSBATCH -C pascal

#130:00:00

export PBS_NODEFILE=`/fslapps/fslutils/generate_pbs_nodefile`
export PBS_JOBID=$SLURM_JOB_ID
export PBS_O_WORKDIR="$SLURM_SUBMIT_DIR"
export PBS_QUEUE=batch

export OMP_NUM_THREADS=$SLURM_CPUS_ON_NODE

cd ~/compute/out{}

tar -cf {}.tar {}
rm -r {}
cd ~/compute
rm -r images{}/{}/{}

"""
import sys,os

tar = sys.argv[1]
a,b = tar.split('.')

last_job = '{}.final.tmp'.format(tar)
with open(last_job) as f:
    job_info = f.readlines()
#Submitted batch job 43122187
dependon=[]
for line in job_info:
    line=line.strip()
    line = line.split(' ')
    dependon.append(line[-1])
dependon=':'.join(dependon)
#print('depend '+dependon)


script = script_template.format(dependon,tar,a,tar,tar,tar,a,a,b)


with open('runs/run_dotar_{}.pbs'.format(tar),'w') as f:
    f.write(script)
