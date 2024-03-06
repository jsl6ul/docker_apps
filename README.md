# Ansible Collection - jsl6ul.docker_apps

Ansible collection for deploying Docker applications in a rootless environment.

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
