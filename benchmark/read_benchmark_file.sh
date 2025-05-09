FILE=$1
QTD=$(echo "$FILE" | awk -F '_' '{print $3}')

# parse the results and give the average
  SUM=0
  for line in $(cat "$FILE"); do
    line=$(echo "scale=3; $line" | bc)
    SUM=$(echo "scale=3; $SUM + $line" | bc)
  done
  AVERAGE=$(echo "scale=5; $SUM / $QTD" | bc)
  echo "Average time for $QTD executions: $AVERAGE seconds"

  standardDeviation=$(
      cat "$FILE" | awk '{sum+=$1; sumsq+=$1*$1} END {print sqrt(sumsq/NR - (sum/NR)**2)}'
  )

  echo "Standard deviation for $QTD executions: $standardDeviation seconds"