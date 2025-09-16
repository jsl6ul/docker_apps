A role for [Thanos](https://thanos.io/)

# Minimal Deployment

This role is the absolute minimum for a Thanos deployment, one Sidecar, one Compactor and one Querier.

You need an external Prometheus and an external object store.

# Components

It is best to read about [Thanos](https://thanos.io/tip/thanos/quick-tutorial.md/) if you are not familiar with it.

- Prometheus scrapes targets as usual.

- Sidecar watches Prometheus’s TSDB directory and every time Prometheus finishes a block the Sidecar:
  - Serves the block over the Thanos gRPC API (so the Querier can read it instantly).
  - Remote-writes the block to the configured object store.

- Compactor runs periodically, it:
  - Pulls raw blocks from the object store.
  - Merges overlapping blocks, removes duplicates, and creates down-sampled versions.
  - Writes the compacted blocks back to the same bucket, marking the originals for deletion.

- Querier talks to the Sidecar (for recent data) and to the Compactor (for historic / down-sampled data). It presents a single PromQL endpoint that Grafana or any client can use.
