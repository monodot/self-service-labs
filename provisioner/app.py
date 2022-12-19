def synchronous_pull(project_id: str, subscription_id: str) -> None:
    """Pulling messages synchronously."""
    # [START pubsub_subscriber_sync_pull]
    from google.api_core import retry
    from google.cloud import pubsub_v1
    # from subprocess import Popen
    import json, subprocess, sys

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    bucket_name = "my-labs-state-bucket"


    NUM_MESSAGES = 1

    # Wrap the subscriber in a 'with' block to automatically call close() to
    # close the underlying gRPC channel when done.
    with subscriber:
        # The subscriber pulls a specific number of messages. The actual
        # number of messages pulled may be smaller than max_messages.
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": NUM_MESSAGES},
            retry=retry.Retry(deadline=300),
        )

        if len(response.received_messages) == 0:
            return

        ack_ids = []
        for received_message in response.received_messages:
            print("Received: {}".format(received_message.message.data))

            request = json.loads(received_message.message.data)
            print("Parsed message: {}".format(request))

            # Now call terraform!
            # First, terraform init, to set up our state backend on GCS
            
            init_cmd = ["terraform", 
                "-chdir={}".format(request["lab_type"]), 
                "init",
                "-reconfigure",
                "-no-color",
                "-backend-config", "bucket={}".format(bucket_name),
                "-backend-config", "prefix=terraform/labs/{}".format(request["lab_id"])]

            print(">> Running: {}".format(" ".join(init_cmd)))

            p = subprocess.Popen(init_cmd, stdout=subprocess.PIPE)
            while p.poll() is None:
                # l = p.stdout.readline() # This blocks until it receives a newline.
                l = p.stdout.readline().decode("utf-8") 
                sys.stdout.write(l)
                sys.stdout.flush()

            print("Program exited with status {}".format(p.returncode))

            # Now call terraform apply to create the lab!

            apply_cmd = ["terraform",
                "-chdir={}".format(request["lab_type"]),
                "apply", "-no-color", "-auto-approve",
                "-var", "project_id={}".format(project_id),
                "-var", "lab_id={}".format(request["lab_id"])]

            print(">> Running: {}".format(" ".join(apply_cmd)))

            p = subprocess.Popen(apply_cmd, stdout=subprocess.PIPE)
            while p.poll() is None:
                l = p.stdout.readline().decode("utf-8") # Fetch a line from the output
                sys.stdout.write(l)
                # We need to flush stdout immediately otherwise we don't see the output till the program terminates
                sys.stdout.flush() 

            ack_ids.append(received_message.ack_id)

        # Acknowledges the received messages so they will not be sent again.
        subscriber.acknowledge(
            request={"subscription": subscription_path, "ack_ids": ack_ids}
        )

        print(
            f"Received and acknowledged {len(response.received_messages)} messages from {subscription_path}."
        )
    # [END pubsub_subscriber_sync_pull]


synchronous_pull("my-provisioner-project", "lab-provisioner-sub")

