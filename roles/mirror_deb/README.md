# Ansible role for a debian mirror

This container downloads and maintains a partial local Debian/Ubuntu mirror using debmirror.

- Update `defaults/main.yml` according to your needs. (and remove `--dry-run` option when all is set)
- Distributions will be mirrored in the `mirrors` directory.
- The `extras` directory is there for your locally build packages.
  *(restart container to force update the Packages index file for the extras directory)*
- The `keys` directory is for your own package signing keys.

- https://manpages.org/debmirror
- https://salsa.debian.org/debian/debmirror

