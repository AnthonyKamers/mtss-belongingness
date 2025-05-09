#!/bin/bash
# qtd benchmarks
QTD=100

# flags
ALGORITHM=rsa
#PRIV_KEY=keys/rsa_2048_priv.pem
PRIV_KEY=keys/rsa_4096_priv.pem

#ALGORITHM=Dilithium2
#PRIV_KEY=keys/dilithium_2_priv.key

#ALGORITHM=Dilithium3
#PRIV_KEY=keys/dilithium_3_priv.key

#ALGORITHM=Dilithium5
#PRIV_KEY=keys/dilithium_5_priv.key

#PUB_KEY=keys/rsa_2048_pub.pem
PUB_KEY=keys/rsa_4096_pub.pem
#PUB_KEY=keys/dilithium_2_pub.key
#PUB_KEY=keys/dilithium_3_pub.key
#PUB_KEY=keys/dilithium_5_pub.key

HASHES=(sha256 sha512 sha3-256 sha3-512 blake2b blake2s)
FILE_SIGN=msg/sign/q/125_10000.txt
FILE_VERIFY=msg/sign/q/125_10000.txt
K_SIGN=3
SIGNED_FILE=msg/sign/q/125_10000_signature.raw

MTSS_COMMAND="python3 mtss_signer.py"
RAW_COMMAND="python3 sign_verify_traditional.py"

for hash in "${HASHES[@]}"; do
  # commands
  SIGN_COMMAND="${MTSS_COMMAND} sign ${ALGORITHM} ${FILE_SIGN} ${PRIV_KEY} -k ${K_SIGN} ${hash} --time-only"
  VERIFY_COMMAND="${MTSS_COMMAND} verify ${ALGORITHM} ${FILE_VERIFY} ${PUB_KEY} ${SIGNED_FILE} ${hash} --time-only"
  CORRECT_COMMAND="${MTSS_COMMAND} verify-correct ${ALGORITHM} ${FILE_SIGN} ${PUB_KEY} ${SIGNED_FILE} ${hash} --time-only"
  SIGN_RAW="${RAW_COMMAND} sign ${ALGORITHM} ${FILE_SIGN} ${PRIV_KEY} ${hash}"
  VERIFY_RAW="${RAW_COMMAND} verify ${ALGORITHM} ${FILE_SIGN} ${PUB_KEY} ${hash} ${SIGNED_FILE}"

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

  # if we are verifying in batch, we need to sign for each hash
  if [ "$COMMAND" == "verify" ]; then
    echo "Signing using ${ALGORITHM} with hash ${hash}..."
    $SIGN_COMMAND
  fi
  if [ "$COMMAND" == "verify-raw" ]; then
    echo "Signing using ${ALGORITHM} with hash ${hash}..."
    $SIGN_RAW
  fi

  # create file to keep results
  FILE="benchmark_${ALGORITHM}_${QTD}_${hash}.txt"
  echo -n "" > "$FILE"

  # run the benchmark
  echo "Running benchmark for hash $hash..."
  for _ in $(seq 1 $QTD); do
    $COMMAND_EXECUTE >> $FILE
  done
done