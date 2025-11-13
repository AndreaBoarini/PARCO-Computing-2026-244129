#!/bin/bash
set -e

trap 'echo "Error occurred at line $LINENO while executing command: $BASH_COMMAND"' ERR

DATA_DIR="./data"
mkdir -p "$DATA_DIR"
cd "$DATA_DIR" || exit

# matrices used as inputs
declare -a urls=(
  "https://suitesparse-collection-website.herokuapp.com/MM/Grund/bayer03.tar.gz"
  "https://suitesparse-collection-website.herokuapp.com/MM/Hamm/memplus.tar.gz"
  "https://suitesparse-collection-website.herokuapp.com/MM/Rajat/rajat31.tar.gz"
  "https://suitesparse-collection-website.herokuapp.com/MM/vanHeukelum/cage13.tar.gz"
  "https://suitesparse-collection-website.herokuapp.com/MM/AMD/G3_circuit.tar.gz"
)

echo "retrieving inputs from the web..."
for url in "${urls[@]}"; do
  file_name=$(basename "$url")        
  dir_name="${file_name%.tar.gz}"
  echo "Downloading $dir_name..."
  wget -q "$url" -O "$file_name"
  tar -xzf "$file_name"
  cd "$dir_name"

  if [[ -f "${dir_name}.mtx" ]]; then
    mv "${dir_name}.mtx" ../"${dir_name}.mtx"
  fi

  # remove secondary matrix if exists  
  rm -f "${dir_name}_B.mtx"
  cd ..

  # Clean up
  rm -rf "$dir_name" "$file_name"
done

echo "inputs retrieved successfully!"