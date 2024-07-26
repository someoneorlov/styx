#!/bin/bash

# Function to generate JSON file from template
generate_json() {
  local aws_dir=$1
  local task_dir=$2
  local template_file_name=$3
  local output_file_name=$4
  local template_file="$aws_dir/$task_dir/$template_file_name"
  local output_file="$aws_dir/$task_dir/$output_file_name"
  
  /home/ec2-user/projects/styx/scripts/replace_placeholders.sh $template_file $output_file

  echo "Generated JSON file at $output_file from template $template_file"
}

# Call the function for each task directory with specific template and output file names
generate_json "/home/ec2-user/projects/styx/AWS" "ecs/raw_data_transfer_task" "raw-data-transfer-template.json" "raw-data-transfer.json"

generate_json "/home/ec2-user/projects/styx/AWS" "ecs/sentiment_result_data_transfer_task" "sentiment-result-data-transfer-template.json" "sentiment-result-data-transfer.json"

generate_json "/home/ec2-user/projects/styx/AWS" "ecs/summary_result_data_transfer_task" "summary-result-data-transfer-template.json" "summary-result-data-transfer.json"

generate_json "/home/ec2-user/projects/styx/AWS" "ecs/flyway_migration_task" "flyway-migration-template.json" "flyway-migration.json"