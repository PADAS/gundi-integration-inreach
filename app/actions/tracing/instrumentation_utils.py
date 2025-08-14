import json

from opentelemetry import propagate, context


def load_context_from_metadata(metadata=None):
    metadata = metadata or {}
    carrier = json.loads(metadata.get("tracing_context", "{}"))
    ctx = propagate.extract(carrier=carrier)
    context.attach(ctx)


def build_context_headers():
    headers = {}
    propagate.inject(headers)
    return headers
