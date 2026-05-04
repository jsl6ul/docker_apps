# enteliWEB exporter

A container to run [enteliweb-exporter](https://github.com/guilbaults/enteliweb-exporter)


## enteliWEB exporter configuration file

```
[enteliweb]
host = https://server
username = user
password = changeme
insecure = false

[exporter]
port = 8085

[devices]
//A site/10000.AO001 = MOD_VFD_PUMP, Pump modulation
```


## Prometheus

The Prometheus scrape_configs definition for this exporter should look like this:

```yaml
  - job_name: enteliweb
    scrape_interval: 30s
    scrape_timeout: 30s
    static_configs:
      - targets:
        - exporter_ip_address:8085
```
