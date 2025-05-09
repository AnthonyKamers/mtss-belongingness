for file in ./performance/*.py; do
  if [ "$file" != "./performance/sig_ver_all.py" ] && [ "$file" != "./performance/performance_utils.py" ]; then
    python3 "$file" run
  fi
done