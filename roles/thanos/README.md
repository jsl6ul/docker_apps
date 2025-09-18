A role for [Thanos](https://thanos.io/)

Open source, highly available Prometheus setup with long term storage capabilities.

# Deployment

This role deploys a partial Thanos environment, including a Sidecar, a Compactor, a Store gateway, and a Querier.

You need an external Prometheus and an external object store.

# Prometheus

Thanos sidecar requires a Prometheus external_label. The external_label is used by Thanos to uniquely identify the Prometheus instance that the sidecar is running alongside.

```
  global:
    external_labels:
      cluster: prod-cluster-1
```

# Components

It is best to read about [Thanos](https://thanos.io/tip/thanos/quick-tutorial.md/) if you are not familiar with it.

- Prometheus scrapes targets as usual.

- Sidecar watches Prometheus’s TSDB directory and every time Prometheus finishes a block it:
  - Serves the block over the Thanos gRPC API (so the Querier can read it instantly).
  - Remote-writes the block to the configured object store.

- Compactor runs periodically, it:
  - Pulls raw blocks from the object store.
  - Merges overlapping blocks, removes duplicates, and creates down-sampled versions.
  - Writes the compacted blocks back to the same bucket, marking the originals for deletion.

- Store gateway reads historic blocks from the object store and serves them to queries.

- Querier talks to the Sidecar (for recent data) and to the Store gateway (for historic / down-sampled data). It presents a single PromQL endpoint that Grafana or any client can use.


The sidecar must be co-located with the Prometheus instance and have direct access to the TSDB directory. One sidecar per Prometheus instance.

The other components can be located on the same server as Prometheus or on remote servers.
