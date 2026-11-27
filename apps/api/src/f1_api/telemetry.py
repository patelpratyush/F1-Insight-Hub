from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from f1_api.config import Settings


def setup_telemetry(app: FastAPI, settings: Settings) -> None:
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    if settings.otlp_endpoint:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "f1-api"}))
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{settings.otlp_endpoint}/v1/traces"))
        )
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)


def instrument_engine(engine: AsyncEngine, settings: Settings) -> None:
    """Trace SQLAlchemy queries when OTLP export is configured."""
    if settings.otlp_endpoint:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
