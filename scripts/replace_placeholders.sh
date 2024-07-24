#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <template_file> <output_file>"
  exit 1
fi

template_file=$1
output_file=$2

# Copy template file to output file
cp $template_file $output_file

# Read the template file and replace placeholders with environment variable values
while IFS='=' read -r key value; do
  if [[ $key != \#* ]]; then
    sed -i "s|\${$key}|$value|g" $output_file
  fi
done < <(env)