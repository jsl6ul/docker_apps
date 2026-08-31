# Carel C.pCO controllers exporter

Prometheus exporter for Carel C.pCO controllers - Modbus TCP only.

## Prometheus

The Prometheus scrape_configs definition for this exporter should look like this:

```yaml
  - job_name: 'cdu'
    scrape_interval: 30s
    static_configs:
      - targets:
        - '192.168.0.21'
        - '192.168.0.22'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: '127.0.0.1:9340'
```
