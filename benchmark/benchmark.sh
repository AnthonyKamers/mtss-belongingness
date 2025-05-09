#!/bin/bash

# qtd benchmarks
QTD=100

# flags
ALGORITHM=ed25519
PRIV_KEY=keys/ed25519_priv.pem
PUB_KEY=keys/ed25519_pub.pem

K_SIGN=3
HASH=sha512
FILE_SIGN=msg/sign/q/125_10000.txt
SIGNED_FILE=msg/sign/q/125_10000_signature.raw

# raw commands
MTSS_COMMAND="python3 mtss_signer.py"
RAW_COMMAND="python3 sign_verify_traditional.py"

# create file to store the benchmark results
FILE="benchmark_${ALGORITHM}_${QTD}_${HASH}.txt"
echo -n "" > $FILE

# commands
SIGN_COMMAND="${MTSS_COMMAND} sign ${ALGORITHM} ${FILE_SIGN} ${PRIV_KEY} -k ${K_SIGN} ${HASH} --time-only"
VERIFY_COMMAND="${MTSS_COMMAND} verify ${ALGORITHM} ${FILE_SIGN} ${PUB_KEY} ${SIGNED_FILE} ${HASH} --time-only"
CORRECT_COMMAND="${MTSS_COMMAND} verify-correct ${ALGORITHM} ${FILE_SIGN} ${PUB_KEY} ${SIGNED_FILE} ${HASH} --time-only"
SIGN_RAW="${RAW_COMMAND} sign ${ALGORITHM} ${FILE_SIGN} ${PRIV_KEY} ${HASH}"
VERIFY_RAW="${RAW_COMMAND} verify ${ALGORITHM} ${FILE_SIGN} ${PUB_KEY} ${HASH} ${SIGNED_FILE}"

COMMAND=$1
case "$COMMAND" in
  "sign")
    COMMAND_EXECUTE=$SIGN_COMMAND
    ;;
  "verify")
    COMMAND_EXECUTE=$VERIFY_COMMAND
    ;;
  "correct")
    COMMAND_EXECUTE=$CORRECT_COMMAND
    ;;
  "sign-raw")
    COMMAND_EXECUTE=$SIGN_RAW
    ;;
  "verify-raw")
    COMMAND_EXECUTE=$VERIFY_RAW
    ;;
  *)
    echo "Invalid command. Use 'sign', 'verify', 'correct', 'sign-raw' or 'verify-raw'."
    exit 1
    ;;
esac

if [ "$2" == "one" ]; then
  QTD=1
fi

# run the benchmark
echo "Running benchmark..."
for _ in $(seq 1 $QTD); do
  $COMMAND_EXECUTE >> $FILE
done

echo "Benchmark finished. Results saved in $FILE"