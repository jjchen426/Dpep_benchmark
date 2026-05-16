#!/bin/bash
#SBATCH -J relax
#SBATCH -p cn-long
#SBATCH --ntasks-per-node=1
#SBATCH -n 1                        # 每个子任务只需要 1 个进程
#SBATCH -o array_log/out_%A_%a.std       # 标准输出日志 (%A是数组主ID，%a是子任务ID)
#SBATCH -e array_log/out_%A_%a.err       # 错误输出日志
#SBATCH --no-requeue
#SBATCH -A chuwang_g1
#SBATCH --qos=chuwangcnl

set -euo pipefail

export LD_LIBRARY_PATH=/home/chuwang_pkuhpc/lustre1/jobs/cjj/install/rosetta.source.release-425/main/source/build/src/release/linux/4.18/64/x86/gcc/11.3/mpi:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/home/chuwang_pkuhpc/lustre1/jobs/cjj/install/rosetta.source.release-425/main/source/build/external/release/linux/4.18/64/x86/gcc/11.3/mpi:$LD_LIBRARY_PATH
source /appsnew/source/openmpi-4.0.1-gcc.sh
source /appsnew/source/gcc-11.3.0.sh


OFFSET=${OFFSET:-0}
JOBLIST=${JOBLIST:-job.list}

ACTUAL_LINE=$((SLURM_ARRAY_TASK_ID + OFFSET))

COMMAND=$(sed -n "${ACTUAL_LINE}p" "$JOBLIST" | sed 's/^[ \t]*//;s/[ \t]*$//')

if [[ -z "$COMMAND" ]]; then
    echo "No command at line ${ACTUAL_LINE}, skip."
    exit 0
fi

echo "Array ID: ${SLURM_ARRAY_TASK_ID} | Offset: ${OFFSET} | Line: ${ACTUAL_LINE}"
echo "Running on $(hostname)"
echo "Start: $(date)"
echo "CMD: $COMMAND"

bash -c "$COMMAND"

echo "End: $(date)"
