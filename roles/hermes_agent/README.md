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

To enable SSH Terminal backend:

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

2. Define terminal settings:

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

4. Apply changes using the configuration update switch:

```bash
ansible-playbook <playbook> -e hermes_config_update=true
```


## Matrix Channel

https://hermes-agent.nousresearch.com/docs/user-guide/messaging/matrix

1. Create a bot account using https://app.element.io
   Save user id, password & recovery key

2. Logout from https://app.element.io

   `All Settings -> Account -> Remove this device`

   The bot account should have exactly one active device - the one the
   Hermes gateway owns. Never leave a parallel Element web (or
   desktop/mobile) session logged in as the same bot account.

3. Generate a fresh token via the login API
   (this creates access token, device id and user id, independent of the web session)

   ```
   curl -X POST https://matrix.org/_matrix/client/v3/login \
     -H "Content-Type: application/json" \
     -d '{"type":"m.login.password","user":"@changeme:matrix.org","password":"secret"}'
   ```

4. Set Matrix environment variables, see defaults/main.yml

5. Run playbook, this will apply configuration and restart hermes gateway container.
   `ansible-playbook <playbook> -e hermes_config_update=true`


## Matrix End-to-end encryption

E2EE requires the mautrix library with encryption extras and the
libolm C library.

- Install mautrix with E2EE support: `pip install 'mautrix[encryption]'`
- Or install with hermes extras: `pip install 'hermes-agent[matrix]'`
- You also need libolm installed on your system: `apt install libolm-dev`


## Telegram Channel

https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram

1. Create a Bot via BotFather
   Every Telegram bot requires an API token issued by @BotFather,
   Telegram's official bot management tool.

   - Open Telegram and search for @BotFather
   - Send /newbot
   - Choose a display name - this can be anything
   - Choose a username - this must be unique and end in bot (e.g., my_hermes_bot)

   BotFather replies with your API token.

   Keep your bot token secret. Anyone with this token can control your
   bot. If it leaks, revoke it via /revoke in BotFather.

3. Set Telegram environment variables, see defaults/main.yml

4. Run playbook, this will apply configuration and restart hermes gateway container.
   `ansible-playbook <playbook> -e hermes_config_update=true`
