# Monitoring with Prometheus and Grafana

**DEPRECATION WARNING**: This role has been deprecated. The monitoring
role has been devided into five roles. (alertmanager, blackbox,
grafana, prometheus, redfish). This role is no longer maintained and
will be removed in the future.

This role deploys the prometheus, grafana, alertmanager and
blackbox-exporter containers.

Optionally, it can deploy a
[redfish-exporter](https://github.com/mrlhansen/idrac_exporter)
container.  You need to define a `dapp_monitoring_redfish_config_yml`
to deploy it.
