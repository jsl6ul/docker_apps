# Hermes Agent

Running Hermes in Docker - the agent itself runs inside a container.
[Documentation here](https://hermes-agent.nousresearch.com/docs/user-guide/docker).


## Configuration

You can run this command to generate the dashboard password hash:
`python3 -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('your-password'))"`


### 1. Manual Wizard

Run the setup container to interactively configure API keys and chat systems:

```bash
docker run -it --rm -v ~/docker/hermes_agent/data:/opt/data nousresearch/hermes-agent setup
```


### 2. Automated (Ansible)

Define your setup via `dapp_hermes_agent_config_yaml` and trigger the update using:

```bash
ansible-playbook <playbook> -e hermes_config_update=true
```


### Ssh Terminal

To enable the SSH Terminal backend:

1. Create the identity keys inside the running Hermes container.
2. Apply the terminal settings to Hermes via Ansible.
3. Create the `hermes-worker` account on the remote target host.
4. Copy Hermes public key to the worker's `authorized_keys` file.

1. Create Hermes ssh keys
```
# Enter the container
user@host:~$ docker exec -it hermes_agent-app-1 bash

# Switch to the hermes user
root@hermes:~# su - hermes

# Generate the keys (no passphrase)
hermes@hermes:~$ ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

2. Define terminal settings in Ansible variables:

```
dapp_hermes_agent_environment: |
  TERMINAL_SSH_HOST: "192.168.0.23"
  TERMINAL_SSH_USER: "hermes-worker"
```

3. Set terminal backend as ssh
```
dapp_hermes_agent_config_yaml:
  - terminal:
      backend: ssh
      container_cpu: 1
      container_disk: 51200
      container_memory: 5120
      container_persistent: true
      cwd: .
      docker_mount_cwd_to_workspace: false
      home_mode: auto
      lifetime_seconds: 300
      timeout: 180
```

4. Apply the changes using the configuration update switch:

```bash
ansible-playbook <playbook> -e hermes_config_update=true
```
