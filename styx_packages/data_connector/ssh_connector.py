import os
import base64
import subprocess
import time


def setup_ssh():
    ssh_private_key = base64.b64decode(os.environ["SSH_PRIVATE_KEY"]).decode("utf-8")
    ssh_public_key = base64.b64decode(os.environ["SSH_PUBLIC_KEY"]).decode("utf-8")
    ssh_config = base64.b64decode(os.environ["SSH_CONFIG"]).decode("utf-8")
    ssh_port_foward = os.getenv("SSH_PORT_FORWARD")
    ssh_remote_creds = os.getenv("SSH_REMOTE_CREDS")

    # Write the SSH private key
    with open("/root/.ssh/id_aws_ecs_task", "w") as f:
        f.write(ssh_private_key)
        os.chmod("/root/.ssh/id_aws_ecs_task", 0o600)

    # Write the SSH public key
    with open("/root/.ssh/id_aws_ecs_task.pub", "w") as f:
        f.write(ssh_public_key)
        os.chmod("/root/.ssh/id_aws_ecs_task.pub", 0o600)

    # Write the SSH config
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
        ssh_port_foward,
        ssh_remote_creds,
    ]
    subprocess.Popen(autossh_command)
    time.sleep(3)
