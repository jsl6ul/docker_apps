# ansible roles for docker apps

Pre-configured ansible roles for applications running in Docker containers.

This collection assumes that you use `jsl6ul.docker_rootless_mode` to setup the host and the account to run docker in rootless mode.

- freeipa
- gitlab
- glances
- graylog
- homepage
- monitoring (prometheus, alertmanager, grafana & blackbox)
- portainer
- privatebin
- traefik


# Traefik certificate

The default configuration of traefik required a certificate. 
You can disable TLS using `docker_apps_traefik_tls: false`, you can use a self-signed certificate, or you can use let's encrypt.

Add your certificate to `traefik_certificate`:

```
traefik_certificate:
  crt: |
    -----BEGIN CERTIFICATE-----
    MIID8TCCAtmgAwIBAgIUZgmYURoJzmqPSh4HxHQ7oUd8b84wDQYJKoZIhvcNAQEL
    qTw3z5E=
    -----END CERTIFICATE-----

  key: !vault |
    $ANSIBLE_VAULT;1.1;AES256
    65323431363436366434663935623562313234653137323530623432316464616532653264376264
    3262636163373830663966633830663661313862363264370a313930376362623664346661656265
```


or look at `docker_apps/roles/traefik/defaults/main.yml` for an example with let's encrypt and easydns.


# playbook example 

```
- name: Setup docker containers
  hosts: some_docker_host
  user: "{{ docker_rootless_user.name }}"
  become: false
  roles:
    - role: jsl6ul.docker_apps.traefik
    - role: jsl6ul.docker_apps.glances
```
