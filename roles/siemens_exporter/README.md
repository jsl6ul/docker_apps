# Siemens exporter 

A container to run [siemens-PAC4220-exporter](https://github.com/guilbaults/siemens-PAC4220-exporter)


## Prometheus

The Prometheus scrape_configs definition for this exporter should look like this:

```yaml
    - job_name: 'siemens_exporter'
      relabel_configs:
        - source_labels: [__address__]
          target_label: __metrics_path__
          regex: "(.*)"
          replacement: "/$1"
        - source_labels: [__address__]
          target_label: instance
        - source_labels: [__address__]
          regex: "(.*)"
          replacement: 127.0.0.1:8081
          target_label: __address__
      static_configs:
        - targets:
          - energy-meter.example.com
```
