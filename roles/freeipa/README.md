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

This configuration has been tested and works with Debian 11 and Debian 12.


## Server role and hostname

Set `dapp_freeipa_role` and `dapp_freeipa_hostname` for each host.

```
[freeipa]
vm1  dapp_freeipa_role=master  dapp_freeipa_hostname=ipa1
vm2  dapp_freeipa_role=replica dapp_freeipa_hostname=ipa2
vm3  dapp_freeipa_role=replica dapp_freeipa_hostname=ipa3
```


## Upgrade

To update, pull the latest image and restart the container:

```bash
docker compose pull
docker compose down
docker compose up -d
```

### Reinstalling a Node

If the upgrade fails, you may need to remove the node from the cluster and reinstall it. 

**1. Remove the node from the cluster** (run from a healthy node, e.g., `host1`):
```bash
# Enter the container
docker exec -it freeipa-app-1 bash

# Verify the cluster members
ipa-replica-manage list

# Delete the failing node (e.g., ipa2)
ipa-replica-manage del ipa2.example.com
```

**2. Clean up the failing node** (run on `host2`):
```bash
docker compose down -v
```

**3. Reinstall**
Run the playbook to reinstall the node. Repeat this process one server at a time to update the entire cluster.

> [!IMPORTANT]
> **Reinstalling the initial master (`ipa1`)**
>
> In a multi-master topology, `ipa1` is no longer the primary setup
> master, it is now just another cluster member. Update its role
> **before** running the playbook:
>
> - `dapp_freeipa_role: replica`
> - `dapp_freeipa_server_master: ipa2`
> - `dapp_freeipa_server_replica: ipa1`


## Error: Another instance may already exist

You may get this error when reinstalling

```
app_1 | [error] AssertionError: Another instance named 'EXAMPLE' may already exist
app_1 | FreeIPA server configuration failed.
```

I don't know why, dns cache? old volumes/config?  Removing volume
and/or waiting 2 minutes before reinstalling seems to make the error
disappear.  Running `docker-compose up` manually seems to work every
time.


## Traefik

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

Make sure that the name of the host running docker is not the same as
the name used for the freeipa container, and you should be fine.

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


## Recover DNA Ranges

If you're trying to create a user and your don't have any dnarange
set, the command will fail with an error like:

`response user_add: Operations error: Allocation of a new value for
range cn=posix ids,cn=distributed numeric assignment
plugin,cn=plugins,cn=config failed! Unable to proceed.`

This can happen after an upgrade.

```
[root@ipa1]$ ipa-replica-manage dnarange-show
ipa3.example.com: No range set
ipa2.example.com: No range set
ipa1.example.com: No range set
```

In order to fix this, you must set a dnarange:

```
[root@ipa1]$ ipa-replica-manage dnarange-set ipa1.example.com 1000000-1099999
[root@ipa1]$ ipa-replica-manage dnarange-set ipa2.example.com 1100000-1199999
[root@ipa1]$ ipa-replica-manage dnarange-set ipa3.example.com 1200000-1299999
```

https://www.freeipa.org/page/V3/Recover_DNA_Ranges
