# TOTAL=$(wc -l < job.list)
# sbatch --array=1-${TOTAL}%1000 submit_array.sh

mkdir -p array_log
mkdir -p outputs/logs

TOTAL=$(wc -l < job.list)
CHUNK=1000

for ((OFFSET=0; OFFSET<$TOTAL; OFFSET+=CHUNK)); do
    REMAIN=$((TOTAL - OFFSET))

    if [ $REMAIN -lt $CHUNK ]; then
        SIZE=$REMAIN
    else
        SIZE=$CHUNK
    fi

    echo "Submitting OFFSET=$OFFSET SIZE=$SIZE"

    sbatch --array=1-${SIZE}%200 \
           --export=OFFSET=${OFFSET} \
           submit_relax_array.sh
done