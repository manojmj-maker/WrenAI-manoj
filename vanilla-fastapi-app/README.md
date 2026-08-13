# Vanilla FastAPI OpenTelemetry Demo (GCE Ops Agent Integration)

This directory contains standalone **Vanilla FastAPI Applications** (Manual SDK + Zero-Code Auto-Instrumentation) configured to export metrics, traces, and logs directly to the **Google Cloud Ops Agent** running natively on a **Google Compute Engine (GCE) VM**.

---

## Architecture Topology

```mermaid
flowchart TD
    subgraph GKE["GKE Cluster (Kubernetes) / Host"]
        subgraph NS["Namespace: wrenai / Microservices"]
            subgraph APPS["All Services (100% Zero-Code Auto-Instrumented)"]
                WREN_AI["wren-ai-service Pod<br/>⚡ Auto-Instrumented (FastAPI / Python)"]
                WREN_UI["wren-ui Pod<br/>⚡ Auto-Instrumented (Next.js / Node.js)"]
                IBIS["ibis-server Pod<br/>⚡ Auto-Instrumented (Python / SQL)"]
                ENGINE["wren-engine Pod<br/>⚡ Auto-Instrumented (Java / Engine)"]
                QDRANT["qdrant StatefulSet<br/>⚡ Auto-Instrumented / OTLP Exporter"]
            end

            subgraph OTEL_GW["Unified OTel Collector Gateway (Deployment + Service)"]
                OTEL_SVC["otel-collector K8s Service<br/>(ClusterIP :4317 gRPC / :4318 HTTP)"]
                OTEL_POD["otel-collector Pod<br/>(Unified Metrics, Traces & Logs Pipeline)"]
                OTEL_SVC --> OTEL_POD
            end
        end
    end

    subgraph GCP["Google Cloud Platform Services"]
        MONITORING["Cloud Monitoring<br/>(Custom APM Metrics)"]
        TRACE["Cloud Trace<br/>(Distributed Spans)"]
        LOGGING["Cloud Logging<br/>(Structured & Correlated Logs)"]
    end

    WREN_AI -->|"OTLP Auto-Injected (Traces, Metrics, Logs)"| OTEL_SVC
    WREN_UI -->|"OTLP Auto-Injected (Traces & Logs)"| OTEL_SVC
    IBIS -->|"OTLP Auto-Injected (Traces, Metrics, Logs)"| OTEL_SVC
    ENGINE -->|"OTLP Auto-Injected (Traces & Metrics)"| OTEL_SVC
    QDRANT -->|"OTLP (Metrics & Logs)"| OTEL_SVC

    OTEL_POD -->|"googlecloud exporter (metrics)"| MONITORING
    OTEL_POD -->|"googlecloud exporter (traces)"| TRACE
    OTEL_POD -->|"googlecloud exporter (logs)"| LOGGING

    classDef k8s fill:#fdf4ff,stroke:#c026d3,stroke-width:2px,color:#701a75;
    classDef otel fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f;
    classDef gcp fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0369a1;
    class WREN_AI,WREN_UI,QDRANT,IBIS,ENGINE k8s;
    class OTEL_SVC,OTEL_POD otel;
    class MONITORING,TRACE,LOGGING gcp;
```

---

## 1. GCE VM Setup: Enable OTLP in Google Cloud Ops Agent

On your GCE VM, ensure the Google Cloud Ops Agent is installed and configure it to accept OTLP data:

1. **Install Ops Agent (if not already installed)**:
   ```bash
   curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
   sudo bash add-google-cloud-ops-agent-repo.sh --also-install
   ```

2. **Apply OTLP Configuration**:
   Copy the provided `ops-agent-config.yaml` to the Ops Agent configuration directory:
   ```bash
   sudo cp ops-agent-config.yaml /etc/google-cloud-ops-agent/config.yaml
   ```

3. **Restart the Ops Agent**:
   ```bash
   sudo systemctl restart google-cloud-ops-agent
   sudo systemctl status google-cloud-ops-agent
   ```
   *The Ops Agent is now listening on `0.0.0.0:4317` (gRPC) and `0.0.0.0:4318` (HTTP).*

---

## 2. Running the FastAPI Applications

### Option A: Via Docker Compose

```bash
docker compose up --build -d
```
*Port mappings:*
- Manual Instrumentation App: `http://localhost:8080`
- Zero-Code Instrumentation App: `http://localhost:8081`

### Option B: Directly on the VM (Python virtual environment)

```bash
# 1. Manual App
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Zero-Code App
cd zero-code-app
pip install -r requirements.txt
opentelemetry-bootstrap -a install
OTEL_SERVICE_NAME=zero-code-fastapi-service \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
opentelemetry-instrument uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## 3. Verifying Telemetry in GCP Console

1. **Cloud Monitoring (Metrics)**:
   - Navigate to **GCP Console $\rightarrow$ Cloud Monitoring $\rightarrow$ Metrics Explorer**.
   - Search for metric: `workload.googleapis.com/vanilla_api_actions_total` or `workload.googleapis.com/vanilla_button_clicks_total`.
   - Filter / Group by `service.name = "vanilla-fastapi-service"`.

2. **Cloud Trace (Waterfall Spans)**:
   - Navigate to **GCP Console $\rightarrow$ Cloud Trace $\rightarrow$ Trace Explorer**.
   - Filter by Service: `vanilla-fastapi-service` or `zero-code-fastapi-service`.
