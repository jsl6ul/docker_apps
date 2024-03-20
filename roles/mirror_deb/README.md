# Ansible role for a debian mirror

This container downloads and maintains a partial local Debian mirror using debmirror.

- Update `defaults/main.yml` according to your needs.
- Debian & debian-security will be mirrored in the `mirrors` directory.
- The `extras` directory is there for your locally build packages.
  *(restart container to force update the Packages index file for the extras directory)*
- The `keys` directory is for your package signing keys.

- https://manpages.org/debmirror
- https://salsa.debian.org/debian/debmirror

## Rebuild

The `Rebuild container` handler doesn't seem to work. You should run `docker compose build` manually.
