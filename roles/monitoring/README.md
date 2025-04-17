# monitoring

This role deploys the prometheus, grafana, alertmanager and blackbox-exporter containers.

Optionally, it can deploy a redfish-exporter container.
You need to define a `dapp_monitoring_redfish_config_yml` to deploy it.
