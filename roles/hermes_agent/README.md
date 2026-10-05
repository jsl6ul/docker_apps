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
