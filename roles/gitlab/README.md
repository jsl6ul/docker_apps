# Gitlab initial root password

You can get the initial root password using: `docker exec -it gitlab_app_1 grep 'Password:' /etc/gitlab/initial_root_password`

https://docs.gitlab.com/ee/install/docker.html#install-gitlab-using-docker-engine

# Gitlab runner

A second container, for Gitlab Runner, will be created if you define a variable: `gitlab_runner_dockerfile`.

Then create a gitlab runner for your project: `Project settings, CI/CD, Runners, New project runner, Create runner`,
copy the token and run `register-runner.sh`.

```
$ ssh dockeruser@host

dockeruser@host:~$ export TOKEN=glrt-PrevWbdG-bgagaLsZ5sk

dockeruser@host:~$ docker/gitlab/register-runner.sh 
Runtime platform arch=amd64 os=linux pid=18 revision=782c6ecb version=16.9.1
Running in system-mode.
Verifying runner... is valid
Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded!
Configuration (with the authentication token) was saved in "/etc/gitlab-runner/config.toml" 
```


# Simple .gitlab-ci.yml test

The role bind-mount the Dockerfile inside the runner container, in `/root/Dockerfile`, 
and the build process must use `docker build - --tag cicd:latest < /root/Dockerfile`.

A simple `.gitlab-ci.yml`:

```
---
stages:
  - build
  - test

variables:
  DOCKER_DRIVER: overlay2
  PLAYBOOKS: "playbooks/*.yml"
  ANSIBLE_CONFIG: "./ansible.cfg"
  ANSIBLE_VAULT_PASSWORD_FILE: "/root/vault.pass"
  ANSIBLE_REMOTE_USER: "runner"
  ANSIBLE_FORCE_COLOR: "true"

build cicd image:
  stage: build
  tags:
    - sometag
  before_script:
    - docker info
    # - docker pull debian:12   # don't pull every time
  script:
    - docker build - --tag cicd:latest < /root/Dockerfile

test cicd image:
  image:
    name: cicd:latest
    pull_policy: never   # we never pull, we build. (available: always, if-not-present, never)
  stage: test
  tags:
    - sometag
  script:
    - ansible -i hosts.yml all -m ping
```
