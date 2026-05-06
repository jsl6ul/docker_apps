# enteliWEB exporter

A container to run [enteliweb-exporter](https://github.com/guilbaults/enteliweb-exporter)

## Prometheus

The Prometheus scrape_configs definition for this exporter should look like this:

```yaml
  - job_name: enteliweb
    scrape_interval: 60s
    scrape_timeout: 60s
    static_configs:
      - targets:
        - enteliweb_exporter_ip_address:8085
```
