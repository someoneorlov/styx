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

# Generate the Nginx Dockerfile from the template
dockerfile_template="/home/ec2-user/projects/styx/dockerfiles/Dockerfile.nginx.template"
dockerfile_path="/home/ec2-user/projects/styx/dockerfiles/Dockerfile.nginx"

sed "s/{{ENV}}/$ENVIRONMENT/g" $dockerfile_template > $dockerfile_path

echo "Generated Nginx Dockerfile at $dockerfile_path for environment $ENVIRONMENT"