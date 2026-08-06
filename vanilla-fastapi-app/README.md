# Vanilla FastAPI OpenTelemetry Demo & Dedicated Collector Deployment

This directory contains a standalone **Vanilla FastAPI Application** equipped with an interactive **Telemetry UI** and a **Dedicated OpenTelemetry Collector** that exports metrics and traces to **Google Cloud Platform (Cloud Monitoring & Cloud Trace)** using the shared GCP Service Account key (`zulinginternaldev`).

---

## Architecture Topology

```
+-----------------------------------------------------------------------------------+
| Docker Network: vanilla-telemetry-net                                             |
|                                                                                   |
|  +--------------------------------+  gRPC OTLP  +------------------------------+  |
|  |  vanilla-fastapi-app (8080)    | ----------> |  vanilla-otel-collector      |  |
|  |  (FastAPI + OTel Python SDK)   |   (:4317)   |  (googlecloud exporter)      |  |
|  +--------------------------------+             +--------------+---------------+  |
+----------------------------------------------------------------|------------------+
                                                                 |
                                                                 v  googlecloud API
                                              +-------------------------------------+
                                              | Google Cloud Platform               |
                                              | - GCP Project: zulinginternaldev    |
                                              | - Cloud Monitoring (Metrics)        |
                                              | - Cloud Trace (Spans)               |
                                              +-------------------------------------+
```

---

## Quick Start Guide

### 1. Build and Start the Containers

From inside the `vanilla-fastapi-app/` directory:

```bash
docker compose up --build -d
```

### 2. Access the Interactive Dashboard UI

Open your browser to:
[http://localhost:8080](http://localhost:8080)

### 3. Emitting Telemetry Metrics & Traces

Click the action buttons on the dashboard UI:

- **🟢 Successful Action**: Emits `vanilla_api_actions_total{action="success", status="200"}` metric counter and records latency in `vanilla_action_duration_seconds` histogram.
- **🔴 Error Action**: Emits `vanilla_api_actions_total{action="error", status="500"}` metric counter and attaches an exception trace to GCP Cloud Trace.
- **⚡ Distributed Trace**: Generates nested execution spans (`db_query_simulation` $\rightarrow$ `vector_search_simulation`) for Cloud Trace waterfall analysis.
- **📊 Click Counter**: Increments custom UI click metric `vanilla_button_clicks_total`.

---

## Verifying Telemetry in GCP Console

1. **Cloud Monitoring (Metrics)**:
   - Navigate to **GCP Console $\rightarrow$ Cloud Monitoring $\rightarrow$ Metrics Explorer**.
   - Search for metric: `workload.googleapis.com/vanilla_api_actions_total` or `workload.googleapis.com/vanilla_button_clicks_total`.
   - Filter / Group by `service.name = "vanilla-fastapi-service"`.

2. **Cloud Trace (Waterfall Spans)**:
   - Navigate to **GCP Console $\rightarrow$ Cloud Trace $\rightarrow$ Trace Explorer**.
   - Filter by Service: `vanilla-fastapi-service`.
   - Click any trace to view the detailed waterfall spans (`db_query_simulation` $\rightarrow$ `vector_search_simulation`).
