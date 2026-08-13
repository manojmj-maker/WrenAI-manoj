import time
import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

# Standard Python logger - NO OpenTelemetry imports anywhere!
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zero-code-fastapi")

app = FastAPI(title="Zero-Code FastAPI Observability Demo")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zero-Code FastAPI - OpenTelemetry Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --card-bg: rgba(18, 26, 43, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --primary: #f59e0b;
            --primary-glow: rgba(245, 158, 11, 0.3);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.3);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.3);
            --cyan: #06b6d4;
            --cyan-glow: rgba(6, 182, 212, 0.3);
            --purple: #8b5cf6;
            --purple-glow: rgba(139, 92, 246, 0.3);
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
            padding: 2.5rem 1rem;
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(245, 158, 11, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 85%, rgba(6, 182, 212, 0.12) 0%, transparent 40%);
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
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fbbf24;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 0.85rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        h1 {
            font-size: 2.35rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.6rem;
        }

        p.subtitle {
            color: var(--text-dim);
            font-size: 1rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
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
        }

        .card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.18);
            box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.6);
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

        .btn-amber { background: var(--primary); color: #000; box-shadow: 0 4px 14px var(--primary-glow); }
        .btn-amber:hover { background: #fbbf24; }
        .btn-cyan { background: var(--cyan); color: #000; box-shadow: 0 4px 14px var(--cyan-glow); }
        .btn-cyan:hover { background: #22d3ee; }
        .btn-purple { background: var(--purple); color: #fff; box-shadow: 0 4px 14px var(--purple-glow); }
        .btn-purple:hover { background: #a78bfa; }
        .btn-danger { background: var(--danger); color: #fff; box-shadow: 0 4px 14px var(--danger-glow); }
        .btn-danger:hover { background: #f87171; }

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
            height: 280px;
            overflow-y: auto;
            color: #fbbf24;
        }

        .log-entry { margin-bottom: 0.4rem; border-bottom: 1px solid rgba(255, 255, 255, 0.03); padding-bottom: 0.2rem; }
        .log-time { color: #64748b; }
        .log-err { color: #f87171; }
        .log-info { color: #38bdf8; }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary);
            box-shadow: 0 0 10px var(--primary);
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge">Zero-Code Auto-Instrumentation</div>
            <h1>Zero-Code FastAPI Telemetry Demo</h1>
            <p class="subtitle">Port 8081 | 100% Pure Python without a single line of OpenTelemetry code!</p>
        </header>

        <div class="grid">
            <!-- Action 1: Get Users -->
            <div class="card">
                <div>
                    <div class="card-title">👥 GET Users</div>
                    <div class="card-desc">Simulates a database query. Latency & Spans are captured automatically by bytecode injection.</div>
                </div>
                <button class="btn btn-amber" onclick="callApi('/api/users', 'GET')">GET /api/users</button>
            </div>

            <!-- Action 2: Create Order -->
            <div class="card">
                <div>
                    <div class="card-title">📦 POST Order</div>
                    <div class="card-desc">Simulates a transactional POST request with simulated latency.</div>
                </div>
                <button class="btn btn-cyan" onclick="callApi('/api/orders', 'POST')">POST /api/orders</button>
            </div>

            <!-- Action 3: Downstream Call -->
            <div class="card">
                <div>
                    <div class="card-title">🔗 Outbound HTTP Trace</div>
                    <div class="card-desc">Calls downstream <code>vanilla-fastapi-app (8080)</code> via <code>requests</code>. Automatically traces distributed HTTP hops!</div>
                </div>
                <button class="btn btn-purple" onclick="callApi('/api/external-call', 'GET')">GET /api/external-call</button>
            </div>

            <!-- Action 4: Error Simulation -->
            <div class="card">
                <div>
                    <div class="card-title">💥 500 Server Error</div>
                    <div class="card-desc">Throws an HTTP 500 error. Exception spans and error statuses are recorded automatically.</div>
                </div>
                <button class="btn btn-danger" onclick="callApi('/api/error', 'GET')">Trigger 500 Error</button>
            </div>
        </div>

        <div class="console-card">
            <div class="console-header">
                <div><span class="status-dot"></span> Live Telemetry Terminal (Port 8081)</div>
                <div>Collector: <code>GCE Ops Agent (Port 4317)</code></div>
            </div>
            <div class="terminal" id="terminal">
                <div class="log-entry"><span class="log-time">[SYSTEM]</span> Zero-Code App initialized on <b>port 8081</b>. Service: <b>zero-code-fastapi-service</b>.</div>
            </div>
        </div>
    </div>

    <script>
        async function callApi(path, method) {
            const terminal = document.getElementById('terminal');
            const now = new Date().toLocaleTimeString();
            
            try {
                const response = await fetch(path, { method: method });
                const data = await response.json();
                
                const isError = !response.ok;
                const logClass = isError ? 'log-err' : 'log-info';
                
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="log-time">[${now}]</span> [${response.status}] <span class="${logClass}">${JSON.stringify(data)}</span> | Auto-Traced via <code>opentelemetry-instrument</code>`;
                
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
    return {"status": "ok", "app": "zero-code-fastapi-service"}

@app.get("/api/users")
async def get_users():
    logger.info("Handling /api/users request...")
    time.sleep(0.12)  # Simulate DB query delay
    return {"status": "success", "users": ["Alice", "Bob", "Charlie", "Dave"]}

@app.post("/api/orders")
async def create_order():
    logger.info("Processing /api/orders request...")
    time.sleep(0.18)  # Simulate order processing delay
    return {"status": "success", "order_id": "ORD-98214", "amount": 149.99}

@app.get("/api/external-call")
async def external_downstream_call():
    logger.info("Calling downstream vanilla-fastapi-app service...")
    try:
        # Zero-code auto-instrumentation will automatically inject trace context headers across services!
        resp = requests.get("http://vanilla-fastapi-app:8000/health", timeout=3)
        downstream_data = resp.json()
    except Exception as e:
        downstream_data = {"error": str(e)}

    return {
        "status": "success",
        "message": "Outbound HTTP request executed via requests library",
        "downstream_response": downstream_data
    }

@app.get("/api/error")
async def trigger_error():
    logger.error("Raising simulated 500 internal server error!")
    raise HTTPException(status_code=500, detail="Simulated Zero-Code Server Failure!")



