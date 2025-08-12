from .core import WebhookPayload, WebhookConfiguration
from .inreach import InreachEventPayload
from app.services.utils import UISchemaModelMixin, GlobalUISchemaOptions


class InReachWebhookPayload(InreachEventPayload, WebhookPayload):
    pass


class InReachWebhookConfig(WebhookConfiguration):
    include_observations: bool = True
    include_messages: bool = True

    ui_global_options: GlobalUISchemaOptions = GlobalUISchemaOptions(
        order=[
            "include_messages",
            "include_observations",
        ],
    )
