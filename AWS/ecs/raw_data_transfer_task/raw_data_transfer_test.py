import os
import base64
import subprocess
import time
import requests


ssh_private_key = base64.b64decode(os.environ["SSH_PRIVATE_KEY"]).decode("utf-8")
ssh_public_key = base64.b64decode(os.environ["SSH_PUBLIC_KEY"]).decode("utf-8")
ssh_config = base64.b64decode(os.environ["SSH_CONFIG"]).decode("utf-8")

# Write the SSH private key
with open("/root/.ssh/id_aws_ecs_task", "w") as f:
    f.write(ssh_private_key)
    os.chmod("/root/.ssh/id_aws_ecs_task", 0o600)

# Write the SSH public key
with open("/root/.ssh/id_aws_ecs_task.pub", "w") as f:
    f.write(ssh_public_key)
    os.chmod("/root/.ssh/id_aws_ecs_task.pub", 0o600)

# Write the SSH public key
with open("/root/.ssh/config", "w") as f:
    f.write(ssh_config)
    os.chmod("/root/.ssh/config", 0o600)

# Create SSH tunnel using autossh
autossh_command = [
    "autossh",
    "-M",
    "0",
    "-f",
    "-N",
    "-L",
    "8004:127.0.0.1:8004",
    "ec2-user@194.242.122.57",
]
print(f"Running autossh command: {' '.join(autossh_command)}")
subprocess.Popen(autossh_command)

time.sleep(3)


# Function to test connection using requests
def test_requests():
    try:
        response = requests.get(
            "http://localhost:8004/ner-data/ner_unprocessed_news?batch_size=2"
        )
        if response.status_code == 200:
            print("Requests Output:", response.json())
        else:
            print(f"Requests failed with status code: {response.status_code}")
    except requests.ConnectionError as e:
        print(f"Requests failed to connect: {e}")


# Run the test function
if __name__ == "__main__":
    test_requests()
