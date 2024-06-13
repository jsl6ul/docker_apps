# Ansible role for a debian mirror

This container downloads and maintains a partial local Debian/Ubuntu mirror using debmirror.

- Update `defaults/main.yml` according to your needs. (and remove `--dry-run` option when all is set)
- Distributions will be mirrored in the `mirrors` directory.
- The `extras` directory is there for your locally build packages.
  *(restart container to force update the Packages index file for the extras directory)*
- The `keys` directory is for your own package signing keys.

- https://manpages.org/debmirror
- https://salsa.debian.org/debian/debmirror


# Update / Auto update

In addition to the nginx service, there are three other commands in this container:

- `/run-debmirror.sh`, to mirror the repositories.
- `/run-extras-scanpackages.sh`, to build the `Packages.gz` for the `extras` directory.
- `/run-signing-keys.sh`, to update the mirror signing keys.

Define `dapp_mirrordeb_update_delay: 6h` to run theses commands every 6 hours,
otherwise, you have to manually run theme:

- `$ docker exec mirrordeb-app-1 /run-signing-keys.sh`
- `$ docker exec mirrordeb-app-1 /run-extras-scanpackages.sh`
- `$ docker exec mirrordeb-app-1 /run-debmirror.sh`


# gpgv: can't allocate lock for

This warning message doesn't seem to be a problem.

`gpgv: can't allocate lock for '/root/.gnupg/trustedkeys.gpg'`

Is there a way to solve it?
https://www.osso.nl/blog/2023/gpgv-can-t-allocate-lock-for/
