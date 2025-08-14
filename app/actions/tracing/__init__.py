# Imports required for instrumentation
import httpx
import aiohttp
from app import settings
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)
from opentelemetry.propagate import set_global_textmap
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from . import config
from . import instrumentation_utils

# Using the X-Cloud-Trace-Context header
set_global_textmap(CloudTraceFormatPropagator())
tracer = config.configure_tracer(name="inreach-connector", version="1.0.0")

# Capture requests (sync and async)
if settings.TRACING_ENABLED:
    HTTPXClientInstrumentor().instrument()
    AioHttpClientInstrumentor().instrument()
else:
    HTTPXClientInstrumentor().uninstrument()
    AioHttpClientInstrumentor().uninstrument()
