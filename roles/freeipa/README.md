# Ansible role for freeipa in rootless docker

This role has been tested in standalone mode (i.e. using self-signed freeipa certificates, without traefik proxy), 
and with let's encrypt + traefik. It should work with your own certificate files, but this has not been tested.

Thanks to https://leo.leung.xyz/wiki/FreeIPA

*(while freeipa replica servers accept the self-signed certificate of the master freeipa server, they will not accept a self-signed certificate from traefik. When using traefik, you must have a certificate from a valid authority provider.)*

## Rootless container with systemd service and cgroup v2

The freeipa container uses a systemd service, and for it to work in rootless mode with cgroup v2, I had to do this:

- Create a systemd slice on the host. *(in `jsl6ul.docker_rootless_mode.roles`)*
- Keep `docker_rootless_cgroupv2: true`
- Add `--skip-mem-check` to the `freeipa_command_master` and `freeipa_command_replica`
- Update docker-compose.yml
  - Add `cgroup: host`
  - Add `/sys/fs/cgroup/user.slice/user-nnnn.slice/user@nnnn.service:/sys/fs/cgroup/user.slice/user-nnnn.slice/user@nnnn.service:rw` read-write
  - And keep `/sys/fs/cgroup:/sys/fs/cgroup:ro` read-only

This configuration works with Debian 11 and Debian 12.

## Server role and alias

You have to set a `freeipa_role` and `freeipa_hostname` for each host.

```
[freeipa]
vm1  freeipa_role=master  freeipa_hostname=ipa1
vm2  freeipa_role=replica freeipa_hostname=ipa2
vm3  freeipa_role=replica freeipa_hostname=ipa3
```

## Another instance may already exist

You may get this error when reinstalling

```
app_1  |   [error] AssertionError: Another instance named 'EXAMPLE' may already exist
app_1  | FreeIPA server configuration failed.
```

I don't know why, dns cache? old volumes/config?
Removing volume and/or waiting 2 minutes before reinstalling seems to make the error disappear.
Running `docker-compose up` manually seems to work every time.

## Freeipa & traefik

You can use freeipa with traefik + let's encrypt. Only the web interface will be functional, realm clients will not be able to use this route to join the realm. Labels for traefik define a passthrough router for realm clients, and a second routers that use let's encrypt certificates.

There are hard-coded redirects in freeipa that make it impossible to use the web interface via a proxy.
This role patch `ipa-rewrite.conf` and `rpcserver.py` to give you this option. See the task file: `fixhttp.yml`

### Let's encrypt & passthrough
If you're using other containers on the same host, you may have trouble configuring traefik + let's encrypt + passthrough.
The tldr is: **make sure that the name of the host running docker is not the name used for the freeipa container**, and you should be fine.

*(if the host running freeipa is also running other containers, such as glances or portainer, then let's encrypt certs for glances (using the hostname) will be reused for freeipa, and this will probably prevent your 'passthrough route' from working properly.)*

So, using `ipahost1` in ansible inventory for the host running docker (ie. the dns A record) 
and `ipa1` (a cname) as the `freeipa_hostname`, this will be the hostname "inside" the freeipa container, shoudl be fine.

## More information about freeipa behind proxy

- https://www.adelton.com/freeipa/freeipa-behind-ssl-proxy
- https://www.adelton.com/freeipa/freeipa-behind-proxy-with-different-name
- https://pagure.io/freeipa/issue/7479
- https://github.com/painless-software/groundcontrol/blob/main/ansible/roles/identitymanagement/tasks/main.yml#L25-L31
- https://github.com/painless-software/groundcontrol/commit/729f689602da64280a77a67854e899ce3487b4a3
