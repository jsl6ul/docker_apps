# Ansible Collection - jsl6ul.docker_apps

Ansible collection for deploying Docker applications in a rootless environment.
This collection assumes that you use [jsl6ul.docker_rootless_mode](https://github.com/jsl6ul/docker_rootless_mode) to setup the host and the account to run docker in rootless mode.


You can use this collection using ansible-galaxy.

```
$ cat requirements.yml
---
collections:
  - name: git@github.com:jsl6ul/docker_apps.git
    type: git
    version: main

$ ansible-galaxy install -r requirements.yml
```
