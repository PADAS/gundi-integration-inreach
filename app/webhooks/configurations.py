from pydantic import Field

from .core import WebhookPayload, WebhookConfiguration
from .inreach import InreachEventPayload
from app.services.utils import UISchemaModelMixin, GlobalUISchemaOptions


class InReachWebhookPayload(InreachEventPayload, WebhookPayload):
    pass


class InReachWebhookConfig(WebhookConfiguration):
    include_observations: bool = True
    include_messages: bool = True
    append_recipients_to_message: bool = Field(
        False,
        title="Append Recipients To Message",
        description=(
            "When enabled, the addresses a device message was sent to are added to the end "
            "of the message text, e.g. 'On my way. (to: ranger@example.org, 2075550100)'."
        ),
    )

    ui_global_options: GlobalUISchemaOptions = GlobalUISchemaOptions(
        order=[
            "include_messages",
            "include_observations",
            "append_recipients_to_message",
            # react-jsonschema-form refuses to render a form whose ui:order omits a
            # property, so let inherited fields (diagnostic_destination_url, and
            # whatever the template adds next) follow the ones ordered here.
            "*",
        ],
    )
