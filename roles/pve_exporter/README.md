# pve exporter

A role for [Prometheus Proxmox VE
Exporter](https://github.com/prometheus-pve/prometheus-pve-exporter)

For security reasons it is essential to add a user with read-only
access (PVEAuditor role) for the purpose of metrics collection.  Refer
to the Proxmox Documentation for the several ways of creating a
user. Once created, assign the user the / path permission.
