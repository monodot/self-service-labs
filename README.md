# self-service-labs (prototype)

**This is a prototype of a containerised Terraform to provision labs for user learning. It's totally incomplete and is not intended to be used in production.**

**Uses:** Terraform, Google Cloud.

## Prototype 1: Deploy two separate labs using standard Terraform

This runs the provisioner locally (i.e. not in a container) and uses the `simple-workshop` lab type. 

Assumes you have Terraform installed and are already authenticated to GCP.

> Note: The `terraform init` command is required to load the state for the lab, before running `terraform apply` or `terraform destroy`. This is because the state is stored in a different location for each lab. In fact, this different location is just a different prefix in the same GCP storage bucket.

```shell
cd provisioner/simple-workshop

terraform init

# Initialise a Terraform state backend for a lab with ID 'mylab123'
terraform init -reconfigure \
    -backend-config="bucket=my-labs-state-bucket" \
    -backend-config="prefix=terraform/labs/mylab123"

# Provision the lab with ID 'mylab123' in the 'my-google-cloud-project' GCP project
terraform apply -var 'project_id=my-google-cloud-project' \
    -var 'lab_id=mylab123'

# Initialise another Terraform state backend, to deploy a second lab with ID 'mylab456'
terraform init -reconfigure \
    -backend-config="bucket=my-labs-state-bucket" \
    -backend-config="prefix=terraform/labs/mylab456"

# Provision the second lab, with ID 'mylab456'
terraform apply -var 'project_id=my-google-cloud-project' \
    -var 'lab_id=mylab456'
```

Check what's deployed:

```shell
terraform state list
```

Now destroy the second lab:

```shell
# Load the lab state from the bucket for 'mylab456'
terraform init -reconfigure \
    -backend-config="bucket=my-labs-state-bucket" \
    -backend-config="prefix=terraform/labs/mylab456"

# Destroy the lab
terraform destroy -var 'project_id=my-google-cloud-project' \
    -var 'lab_id=mylab456'
```

> **Note**
> Could we use [Terraform Workspaces][workspaces]? Perhaps. But workspaces need to acquire a **lock**, which could prevent multiple executions at the same time.

## Prototype 2: Provision labs using a shell script or Python runner

Also in this repo are another couple of prototypes, showing how the Terraform to provision a lab could be called from a shell script or Python app.

### 2a: Shell script -> Terraform

This prototype uses a simple shell script, `provision.sh`, to call Terraform. The shell script takes two arguments - the lab type, and the lab ID.

To try it out, create a key for yourself (or a Service Account user) in your GCP project, with permissions to write to your storage bucket, and then run the following commands:

```shell
podman build -t lab-provisioner -f Dockerfile.shellrunner .

podman run -v your-google-access-key.json:/root/.config/gcloud/application_default_credentials.json:z localhost/lab-provisioner simple-workshop mylab123
```

### 2b: Google PubSub -> Python app -> Terraform

This second prototype shows how to run Terraform from a Python app. 

This is a more complex example, but it shows how to use Python's `subprocess.Popen` to run Terraform. It also uses a Google PubSub subscription - allowing you to trigger the provisioning of a lab by putting a message onto a topic.

To try it out - create a PubSub topic and subscription, build the container, and then put a message onto the topic:

```shell
export TOPIC_ID=self-service-lab-requests
export SUBSCRIPTION_ID=lab-provisioner-sub

gcloud pubsub topics create $TOPIC_ID
# TODO: Increase ack time
gcloud pubsub subscriptions create $SUBSCRIPTION_ID --topic $TOPIC_ID

podman build -t lab-provisioner -f Dockerfile.pythonrunner .

# Use your own key file - in production you'd use a Service Account obviously
podman run -v $HOME/.config/gcloud/application_default_credentials.json:/root/.config/gcloud/application_default_credentials.json:z localhost/provisioner

# The provisioner will now wait for a message...

# Pop a message onto the topic
gcloud pubsub topics publish $TOPIC_ID --message='{ "action": "create", "lab_id": "tomslab12345", "project_id": "my-google-cloud-project", "lab_type": "simple-workshop" }'
```

The provisioner should receive the message and then terminate.


[workspaces]: https://www.terraform.io/docs/state/workspaces.html
