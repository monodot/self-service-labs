#!/bin/sh

# This script is responsible for provisioning a workshop environment.

labName=$1
labId=$2

if [ -z $labName ] || [ -z $labId ]; then
    echo "Usage: provision.sh <labName> <labId>"
    echo "Error: Lab name or lab ID not specified."
    exit 1
fi

terraform -chdir=${labName} init -reconfigure \
    -no-color \
    -backend-config="bucket=my-labs-state-bucket" \
    -backend-config="prefix=terraform/labs/${labId}"

terraform -chdir=${labName} apply \
    -no-color -auto-approve \
    -var "project_id=my-google-cloud-project" \
    -var "lab_id=${labId}"

