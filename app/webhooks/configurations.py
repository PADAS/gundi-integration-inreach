import pydantic
from .core import WebhookPayload, GenericJsonTransformConfig
from .inreach import InreachEventPayload


class InReachWebhookPayload(InreachEventPayload, WebhookPayload):
    pass


class InReachWebhookConfig(GenericJsonTransformConfig):
    include_observations: bool = True
    include_messages: bool = True
