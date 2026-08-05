from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, RedirectResponse
from langfuse.decorators import langfuse_context

from src.config import settings
from src.globals import (
    create_service_container,
    create_service_metadata,
)
from src.providers import generate_components
from src.utils import (
    init_langfuse,
    setup_custom_logger,
)
from src.web.v1 import routers

setup_custom_logger(
    "wren-ai-service", level_str=settings.logging_level, is_dev=settings.development
)


# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup events
    pipe_components = generate_components(settings.components)
    app.state.service_container = create_service_container(pipe_components, settings)
    app.state.service_metadata = create_service_metadata(pipe_components)
    init_langfuse(settings)

    try:
        import os
        from opentelemetry import metrics, trace
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        resource = Resource.create({"service.name": "wren-ai-service"})

        # Metrics Setup
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
            export_interval_millis=2000,
        )
        app.state.otel_meter_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)
        metrics.set_meter_provider(app.state.otel_meter_provider)

        # Traces Setup
        app.state.otel_tracer_provider = TracerProvider(resource=resource)
        span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        app.state.otel_tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(app.state.otel_tracer_provider)

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=app.state.otel_tracer_provider,
            meter_provider=app.state.otel_meter_provider,
        )

        meter = metrics.get_meter("wren-ai-service")
        request_counter = meter.create_counter("http_requests_total")

        @app.middleware("http")
        async def track_requests(request, call_next):
            response = await call_next(request)
            request_counter.add(1, {"path": request.url.path, "status": str(response.status_code)})
            return response
    except Exception as e:
        import logging
        logging.getLogger("wren-ai-service").warning(f"OpenTelemetry setup failed: {e}")

    yield

    # shutdown events
    langfuse_context.flush()
    if hasattr(app.state, "otel_meter_provider"):
        app.state.otel_meter_provider.shutdown()
    if hasattr(app.state, "otel_tracer_provider"):
        app.state.otel_tracer_provider.shutdown()
    

app.include_router(routers.router, prefix="/v1", tags=["v1"])
if settings.development:
    from src.web import development

    app.include_router(development.router, prefix="/dev", tags=["dev"])


@app.exception_handler(Exception)
async def exception_handler(_, exc: Exception):
    return ORJSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def request_exception_handler(_, exc: Exception):
    return ORJSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "src.__main__:app",
        host=settings.host,
        port=settings.port,
        reload=settings.development,
        reload_includes=["src/**/*.py", ".env.dev", "config.yaml"],
        reload_excludes=["tests/**/*.py", "eval/**/*.py"],
        workers=1,
        loop="uvloop",
        http="httptools",
    )


