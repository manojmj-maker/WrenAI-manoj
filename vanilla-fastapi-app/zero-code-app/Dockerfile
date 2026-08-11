FROM python:3.11-slim

WORKDIR /app

# Install dependencies and OpenTelemetry auto-instrumentors
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap -a install

# Copy application source code
COPY . .

EXPOSE 8000

# Zero-Code execution command
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
