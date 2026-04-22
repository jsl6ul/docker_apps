# Ansible role for FreeIPA in rootless docker

This role has been tested in standalone mode (i.e. using self-signed
freeipa certificates, without traefik proxy), and with let's encrypt
and traefik. It should work with your own certificate files, but this
has not been tested.

Thanks to https://leo.leung.xyz/wiki/FreeIPA

*(while freeipa replica servers accept the self-signed certificate of
the master freeipa server, they will not accept a self-signed
certificate from traefik. When using traefik, you must have a
certificate from a valid authority provider.)*


## Rootless container with systemd service and cgroup v2

The freeipa container uses a systemd service, and for it to work in
rootless mode with cgroup v2, I had to do this:

- Create a systemd slice on the host.
  *(in `jsl6ul.docker_rootless_mode.roles`)*
- Keep `docker_rootless_cgroupv2: true`
- Add `--skip-mem-check` to the `dapp_freeipa_command_master`
  and `dapp_freeipa_command_replica`
- Update docker-compose.yml
  - Add `cgroup: host`
  - Add `/sys/fs/cgroup/user.slice/user-nnnn.slice/user@nnnn.service:/sys/fs/cgroup/user.slice/user-nnnn.slice/user@nnnn.service:rw` read-write
  - And keep `/sys/fs/cgroup:/sys/fs/cgroup:ro` read-only

This configuration works with Debian 11 and Debian 12.


## Server role and alias

You have to set a `dapp_freeipa_role` and `dapp_freeipa_hostname` for
each host.

```
[freeipa]
vm1  dapp_freeipa_role=master  dapp_freeipa_hostname=ipa1
vm2  dapp_freeipa_role=replica dapp_freeipa_hostname=ipa2
vm3  dapp_freeipa_role=replica dapp_freeipa_hostname=ipa3
```

In a multi-master topology, if you need to reinstall the initial
master node, don't forget to modify these variables before running the
playbook.

- change `dapp_freeipa_role` from `master` to `replica`.
- swap node names between `dapp_freeipa_server_master` and 
  `dapp_freeipa_server_replica1` or `dapp_freeipa_server_replica2`


## Another instance may already exist

You may get this error when reinstalling

```
app_1 | [error] AssertionError: Another instance named 'EXAMPLE' may already exist
app_1 | FreeIPA server configuration failed.
```

I don't know why, dns cache? old volumes/config?  Removing volume
and/or waiting 2 minutes before reinstalling seems to make the error
disappear.  Running `docker-compose up` manually seems to work every
time.


## FreeIPA Update

Normally, this should work:
`docker compose pull && docker compose down && docker compose up -d`

For various reasons, this may fail, in that case, a solution is to
remove the node from the cluster, update it, and re-enrolling it.

Something like:

```
# on host1, remove ipa2 from the cluster
host1$ docker exec -it freeipa-app-1 bash
ipa1$ kinit

ipa1$ ipa-replica-manage list
ipa1.example.com: master
ipa2.example.com: master
ipa3.example.com: master

ipa1$ ipa-replica-manage del ipa2.example.com
ipa1$ ipa-replica-manage list
ipa1.example.com: master
ipa3.example.com: master

# on host2, download new image and wipe ipa2
host2$ docker compose pull
host2$ docker compose down -v
```

You can now run your playbook to reinstall `ipa2` using the latest image.

Proceed one server at a time to update the entire cluster.

Since your cluster already exists and has two other masters, `ipa1` is
no longer the only master in terms of setup. It is now just another
member of the cluster that needs to be brought back in sync.

For that reason, make sure to set `dapp_freeipa_role` to `replica` and
swap the hostname between `dapp_freeipa_server_master` and one of the
`dapp_freeipa_server_replica` before updating `ipa1`.


## FreeIPA & traefik

You can use freeipa with traefik & let's encrypt. *(set
`dapp_freeipa_traefik: true`)*

Only the web interface will be functional, realm clients will not be
able to use this route to join the realm.  Labels for traefik define a
passthrough router for realm clients, and a second router that use
let's encrypt certificates for web ui and ldaps.

There are hard-coded redirects in freeipa that make it impossible to
use the web interface via a proxy.  This role patch `ipa-rewrite.conf`
and `rpcserver.py` to give you this option. See the task file:
`fixhttp.yml`

**WARNING** Even if it works for now, with freeipa 4.10 and 4.11, the
regexg-replace in `fixhttp.yml` will eventually be a problem, needing
to be updated to follow the freeipa code. It's just a bad solution
that works for now.  (not to mention the fact that these two changes
(removal of redirects and referer checks) reduce freeipa's security.)

*These errors are symptoms indicating that the regular expression
probably needs to be modified: 'Login failed due to an unknown
reason', 'ERROR: Rejecting request with bad Referer', 'HTTP Error 400:
Bad Request'.*


### Let's encrypt & passthrough

Make sure that the name of the host running docker is not the name
used for the freeipa container, and you should be fine.

If the host on which FreeIPA is running also hosts other containers,
then Let's Encrypt certificates generated for another container on
that host, based on the hostname, will be reused for FreeIPA, which
will likely prevent your "passthrough route" from working properly.

Using `ipahost1` for the host running docker and `ipa1` (a CNAME of
`ipahost1`) as the `dapp_freeipa_hostname`, will help avoid issues.


## More information about FreeIPA behind proxy

- https://www.adelton.com/freeipa/freeipa-behind-ssl-proxy
- https://www.adelton.com/freeipa/freeipa-behind-proxy-with-different-name
- https://pagure.io/freeipa/issue/7479
- https://github.com/painless-software/groundcontrol/blob/main/ansible/roles/identitymanagement/tasks/main.yml#L25-L31
- https://github.com/painless-software/groundcontrol/commit/729f689602da64280a77a67854e899ce3487b4a3
