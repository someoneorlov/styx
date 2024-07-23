#!/bin/bash

template_file=$1
output_file=$2

# Copy template file to output file
cp $template_file $output_file

# Replace placeholders in the output file
while IFS='=' read -r key value; do
  if [[ $key != \#* ]]; then
    sed -i "s|\${$key}|$value|g" $output_file
  fi
done < <(env)
