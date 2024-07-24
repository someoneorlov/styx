#!/bin/bash

# Get the current branch name
branch_name=$(git rev-parse --abbrev-ref HEAD)

# Set the ENVIRONMENT variable based on the branch name
if [ "$branch_name" == "main" ]; then
  ENVIRONMENT=prod
elif [ "$branch_name" == "test" ]; then
  ENVIRONMENT=test
else
  ENVIRONMENT=dev
fi

# Paths to the env files
common_env=".env.common"
env_file=".env.${ENVIRONMENT}"
common_env_aws="AWS/.env.common_aws"
env_file_aws="AWS/.env.${ENVIRONMENT}_aws"
target_env=".env"

# Create the target .env file by combining common and environment-specific env files
if [ -f "$common_env" ] && [ -f "$env_file" ] && [ -f "$common_env_aws" ] && [ -f "$env_file_aws" ]; then
  cat $common_env <(echo) $env_file <(echo) $common_env_aws <(echo) $env_file_aws > $target_env
else
  echo "Missing environment files for branch '$branch_name'. Skipping .env generation."
fi

# Source the generated .env file if it exists
if [ -f $target_env ]; then
  export $(cat $target_env | grep -v '^#' | xargs)
  echo "Loaded environment variables from $target_env for branch $branch_name"
else
  echo "Environment file $target_env does not exist"
fi
