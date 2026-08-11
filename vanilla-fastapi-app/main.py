import os
import time
import logging
from typing import Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

# OpenTelemetry imports
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Import our external router
from sample_routes import router as sample_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vanilla-fastapi")

SERVICE_NAME = "vanilla-fastapi-service"
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://vanilla-otel-collector:4317")

# Global OTel handles
meter = None
tracer = None
action_counter = None
button_click_counter = None
latency_histogram = None
http_server_duration = None
http_server_requests = None

resource = Resource.create({"service.name": SERVICE_NAME, "environment": "production"})

# Setup Metrics Exporter & Provider
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True),
    export_interval_millis=2000,
)
meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(SERVICE_NAME)

# 1. Custom Demo Metrics
action_counter = meter.create_counter("vanilla_api_actions_total", description="Total actions performed in Vanilla FastAPI")
button_click_counter = meter.create_counter("vanilla_button_clicks_total", description="Total UI button clicks")
latency_histogram = meter.create_histogram("vanilla_action_duration_seconds", description="Duration of Vanilla FastAPI actions")

# 2. Standard HTTP Metrics (Auto-collected for ALL routes)
http_server_duration = meter.create_histogram(
    "http.server.duration",
    description="Duration of HTTP requests",
    unit="s",
)
http_server_requests = meter.create_counter(
    "http.server.requests",
    description="Total HTTP requests",
)

# Setup Tracing Exporter & Provider
tracer_provider = TracerProvider(resource=resource)
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True))
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(SERVICE_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Vanilla FastAPI Observability Demo...")
    yield
    logger.info("Shutting down OpenTelemetry providers...")
    meter_provider.shutdown()
    tracer_provider.shutdown()

app = FastAPI(title="Vanilla FastAPI Observability Demo", lifespan=lifespan)

# Instrument FastAPI App for Automatic Traces
FastAPIInstrumentor.instrument_app(
    app,
    tracer_provider=tracer_provider,
    meter_provider=meter_provider,
)

# Global Middleware to Automatically Record Latency & Requests for EVERY Endpoint
@app.middleware("http")
async def otel_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Exclude dashboard/static polling from metric noise if desired, but capture all API calls
    attributes = {
        "http.route": request.url.path,
        "http.method": request.method,
        "http.status_code": str(response.status_code),
    }
    
    if http_server_duration:
        http_server_duration.record(duration, attributes)
    if http_server_requests:
        http_server_requests.add(1, attributes)
        
    return response

# Include the external router
app.include_router(sample_router)

# ==========================================
# DASHBOARD HTML
# ==========================================
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vanilla FastAPI - OpenTelemetry Metrics & Traces Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: rgba(22, 31, 48, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.3);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.3);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.3);
            --purple: #8b5cf6;
            --purple-glow: rgba(139, 92, 246, 0.3);
            --teal: #14b8a6;
            --teal-glow: rgba(20, 184, 166, 0.3);
            --text: #f3f4f6;
            --text-dim: #9ca3af;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }

        body {
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
            background-image: 
                radial-gradient(circle at 15% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 85% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 40%);
        }

        .container {
            max-width: 1000px;
            width: 100%;
        }

        header {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #60a5fa;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        h1 {
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff 0%, #9ca3af 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        p.subtitle {
            color: var(--text-dim);
            font-size: 1rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease-in-out;
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.5);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .card-desc {
            font-size: 0.875rem;
            color: var(--text-dim);
            margin-bottom: 1.25rem;
            line-height: 1.4;
        }

        .btn {
            width: 100%;
            padding: 0.75rem 1rem;
            border-radius: 0.6rem;
            border: none;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn-success { background: var(--success); color: #000; box-shadow: 0 4px 14px var(--success-glow); }
        .btn-success:hover { background: #34d399; }
        .btn-danger { background: var(--danger); color: #fff; box-shadow: 0 4px 14px var(--danger-glow); }
        .btn-danger:hover { background: #f87171; }
        .btn-purple { background: var(--purple); color: #fff; box-shadow: 0 4px 14px var(--purple-glow); }
        .btn-purple:hover { background: #a78bfa; }
        .btn-primary { background: var(--primary); color: #fff; box-shadow: 0 4px 14px var(--primary-glow); }
        .btn-primary:hover { background: #60a5fa; }
        .btn-teal { background: var(--teal); color: #fff; box-shadow: 0 4px 14px var(--teal-glow); }
        .btn-teal:hover { background: #2dd4bf; }

        .console-card {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.25rem;
        }

        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            font-size: 0.85rem;
            color: var(--text-dim);
            font-family: 'JetBrains Mono', monospace;
        }

        .terminal {
            background: #05070e;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            height: 300px;
            overflow-y: auto;
            color: #4ade80;
        }

        .log-entry { margin-bottom: 0.4rem; border-bottom: 1px solid rgba(255, 255, 255, 0.03); padding-bottom: 0.2rem; }
        .log-time { color: #64748b; }
        .log-err { color: #f87171; }
        .log-info { color: #38bdf8; }
        .log-trace { color: #c084fc; }
        .log-auto { color: #2dd4bf; }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge">OpenTelemetry Demo</div>
            <h1>Vanilla FastAPI Telemetry Dashboard</h1>
            <p class="subtitle">Exporting OTLP Metrics & Traces to GCP Cloud Monitoring via Dedicated Collector</p>
        </header>

        <div class="grid">
            <!-- Action 1: Success Metric -->
            <div class="card">
                <div>
                    <div class="card-title">🟢 Manual Success</div>
                    <div class="card-desc">Increments <code>vanilla_api_actions_total{action="success"}</code> counter explicitly in the route.</div>
                </div>
                <button class="btn btn-success" onclick="triggerAction('success')">Send Success Metric</button>
            </div>

            <!-- Action 2: Error Metric -->
            <div class="card">
                <div>
                    <div class="card-title">🔴 Manual Error</div>
                    <div class="card-desc">Increments <code>vanilla_api_actions_total{action="error"}</code> counter explicitly.</div>
                </div>
                <button class="btn btn-danger" onclick="triggerAction('error')">Send Error Metric</button>
            </div>

            <!-- Action 3: Heavy Trace -->
            <div class="card">
                <div>
                    <div class="card-title">⚡ Distributed Trace</div>
                    <div class="card-desc">Generates nested spans (<code>db_query</code>, <code>ai_pipeline</code>) for GCP Cloud Trace waterfall view.</div>
                </div>
                <button class="btn btn-purple" onclick="triggerAction('heavy-trace')">Send Multi-Span Trace</button>
            </div>

            <!-- Action 4: Auto Router GET -->
            <div class="card">
                <div>
                    <div class="card-title">🤖 External Router (GET)</div>
                    <div class="card-desc">Calls <code>/api/samples/users</code>. Traces, Logs, and Metrics (like <code>http.server.duration</code>) are recorded natively!</div>
                </div>
                <button class="btn btn-teal" onclick="triggerAutoRequest('/api/samples/users', 'GET')">Call Sample GET</button>
            </div>

            <!-- Action 5: Auto Router POST -->
            <div class="card">
                <div>
                    <div class="card-title">🤖 External Router (POST)</div>
                    <div class="card-desc">Calls <code>/api/samples/items</code>. Standard latency metrics and traces captured automatically.</div>
                </div>
                <button class="btn btn-teal" onclick="triggerAutoRequest('/api/samples/items', 'POST')">Call Sample POST</button>
            </div>
        </div>

        <div class="console-card">
            <div class="console-header">
                <div><span class="status-dot"></span> Live Telemetry Terminal</div>
                <div>Collector: <code>http://vanilla-otel-collector:4317</code></div>
            </div>
            <div class="terminal" id="terminal">
                <div class="log-entry"><span class="log-time">[SYSTEM]</span> Dashboard initialized. Service: <b>vanilla-fastapi-service</b>. Ready to emit telemetry events...</div>
            </div>
        </div>
    </div>

    <script>
        async function triggerAction(actionType) {
            const terminal = document.getElementById('terminal');
            const now = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch(`/api/action/${actionType}`, { method: 'POST' });
                const data = await response.json();
                
                let logClass = 'log-info';
                if (actionType === 'error') logClass = 'log-err';
                if (actionType === 'heavy-trace') logClass = 'log-trace';
                
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="log-time">[${now}]</span> <span class="${logClass}">${data.message}</span> | Metric: <code>${data.metric_emitted}</code> | Trace ID: <code>${data.trace_id || 'N/A'}</code>`;
                
                terminal.prepend(entry);
            } catch (err) {
                const entry = document.createElement('div');
                entry.className = 'log-entry log-err';
                entry.innerHTML = `<span class="log-time">[${now}]</span> Request failed: ${err}`;
                terminal.prepend(entry);
            }
        }

        async function triggerAutoRequest(path, method) {
            const terminal = document.getElementById('terminal');
            const now = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch(path, { method: method });
                const data = await response.json();
                
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="log-time">[${now}]</span> <span class="log-auto">${data.message}</span> | Metric: <code>http.server.duration</code> tracked automatically!`;
                
                terminal.prepend(entry);
            } catch (err) {
                const entry = document.createElement('div');
                entry.className = 'log-entry log-err';
                entry.innerHTML = `<span class="log-time">[${now}]</span> Request failed: ${err}`;
                terminal.prepend(entry);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return HTML_CONTENT

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": SERVICE_NAME}

# ==========================================
# OLD MANUAL METRIC ENDPOINTS
# ==========================================
@app.post("/api/action/success")
async def action_success():
    start_time = time.time()
    time.sleep(0.05)
    duration = time.time() - start_time

    if button_click_counter:
        button_click_counter.add(1, {"button_id": "success_button"})
    if action_counter:
        action_counter.add(1, {"action": "success", "status": "200"})
    if latency_histogram:
        latency_histogram.record(duration, {"action": "success"})

    current_span = trace.get_current_span()
    trace_id = hex(current_span.get_span_context().trace_id) if current_span else "N/A"

    return {
        "status": "success",
        "message": "Successfully recorded 200 OK metric & span",
        "metric_emitted": "vanilla_api_actions_total{action='success', status='200'}",
        "trace_id": trace_id,
        "latency_ms": round(duration * 1000, 2)
    }

@app.post("/api/action/error")
async def action_error():
    if button_click_counter:
        button_click_counter.add(1, {"button_id": "error_button"})
    if action_counter:
        action_counter.add(1, {"action": "error", "status": "500"})

    current_span = trace.get_current_span()
    trace_id = hex(current_span.get_span_context().trace_id) if current_span else "N/A"

    if current_span:
        current_span.set_attribute("error", True)
        current_span.set_attribute("exception.message", "Simulated internal server error in Vanilla FastAPI")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Simulated 500 Error recorded in OpenTelemetry span & metric counter",
            "metric_emitted": "vanilla_api_actions_total{action='error', status='500'}",
            "trace_id": trace_id
        }
    )

@app.post("/api/action/heavy-trace")
async def action_heavy_trace():
    if button_click_counter:
        button_click_counter.add(1, {"button_id": "heavy_trace_button"})

    current_span = trace.get_current_span()
    trace_id = hex(current_span.get_span_context().trace_id) if current_span else "N/A"

    with tracer.start_as_current_span("db_query_simulation") as span1:
        span1.set_attribute("db.system", "postgresql")
        span1.set_attribute("db.statement", "SELECT * FROM users WHERE active = true")
        time.sleep(0.08)

    with tracer.start_as_current_span("vector_search_simulation") as span2:
        span2.set_attribute("vector_db.system", "qdrant")
        span2.set_attribute("vector_db.top_k", 5)
        time.sleep(0.12)

    if action_counter:
        action_counter.add(1, {"action": "heavy_trace", "status": "200"})

    return {
        "status": "success",
        "message": "Nested spans generated (db_query_simulation -> vector_search_simulation)",
        "metric_emitted": "vanilla_api_actions_total{action='heavy_trace', status='200'}",
        "trace_id": trace_id
    }
