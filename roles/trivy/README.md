# Role for a Trivy container

[Trivy](https://aquasecurity.github.io/trivy/) is a comprehensive and versatile security scanner.

- The client-server mode allows you to use a shared server, so you don't have to download vulnerability databases several times.
- This role is used to create and start a trivy server container.
- Reporting is done by the client, the one who initiates the scan.
- A [script](https://github.com/jsl6ul/server_settings/tree/main/roles/trivy/files) is available for launching analyses, either manually or via cronjobs.
