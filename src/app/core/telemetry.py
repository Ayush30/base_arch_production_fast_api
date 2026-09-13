from fastapi import FastAPI, Response
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings

_telemetry_configured = False


def configure_telemetry() -> None:
    global _telemetry_configured

    if _telemetry_configured:
        return

    resource = Resource(attributes={SERVICE_NAME: settings.otel_service_name})
    trace_provider = TracerProvider(resource=resource)
    metric_reader = PrometheusMetricReader()
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

    if not settings.is_local:
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(trace_provider)
    metrics.set_meter_provider(meter_provider)

    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    _telemetry_configured = True


def mount_metrics(app: FastAPI) -> None:
    if settings.metrics_enabled:
        app.add_api_route(
            settings.metrics_path,
            prometheus_metrics,
            methods=["GET"],
            include_in_schema=False,
        )


def prometheus_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def get_tracer(name: str = __name__) -> trace.Tracer:
    return trace.get_tracer(name)
