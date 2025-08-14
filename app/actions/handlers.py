import json
import logging

from gundi_core.schemas.v2 import Integration
from gundi_core.events.transformers import MessageTransformedInReach

from app.services.activity_logger import activity_logger
from app import settings
from opentelemetry.trace import SpanKind
from . import tracing
from .configurations import AuthenticateConfig, PushMessageConfig
from .inreach_client import InReachClient, InReachAuthenticationError


logger = logging.getLogger(__name__)


async def action_auth(integration: Integration, action_config: AuthenticateConfig):
    inreach_api_url = integration.base_url or action_config.api_url
    inreach_username = action_config.username
    inreach_password = action_config.password.get_secret_value()
    try:
        async with InReachClient(api_url=inreach_api_url) as inreach_client:
            await inreach_client.pingback(
                username=inreach_username,
                password=inreach_password,
            )
    except InReachAuthenticationError as e:
        return {"valid_credentials": False, "error": str(e)}
    except Exception as e:
        return {"valid_credentials": False, "error": f"Error in authentication test: {type(e).__name__}: {e}."}
    else:
        return {"valid_credentials": True}


# ToDo: implement auxiliary actions


@activity_logger()
async def action_push_messages(
        integration: Integration, action_config: PushMessageConfig, data: MessageTransformedInReach
):
    # Trace messages with Open Telemetry
    with tracing.tracer.start_as_current_span(
            "inreach_connector.action_push_messages", kind=SpanKind.CLIENT
    ) as current_span:
        current_span.add_event(
            name="inreach_connector.transformed_message_received_at_connector"
        )
        destination_id = str(integration.id)
        current_span.set_attribute("destination_id", destination_id)
        ipc_message = data.payload
        # Temporarily log content in traces for troubleshooting
        current_span.set_attribute("ipc_message", json.dumps(ipc_message.dict(), default=str))

        auth_config = integration.get_action_config("auth")
        if not auth_config:
            raise ValueError("Authentication configuration is required for sending messages.")
        parsed_auth_config = AuthenticateConfig.parse_obj(auth_config.data)
        inreach_api_url = integration.base_url or parsed_auth_config.api_url
        inreach_username = parsed_auth_config.username
        inreach_password = parsed_auth_config.password.get_secret_value()
        with tracing.tracer.start_as_current_span(
                "inreach_connector.inreach_client.send_messages", kind=SpanKind.CLIENT
        ) as sub_span:
            try:
                async with InReachClient(api_url=inreach_api_url) as inreach_client:
                    inreach_response = await inreach_client.send_messages(
                        ipc_messages=[ipc_message],
                        username=inreach_username,
                        password=inreach_password,
                    )
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                error_msg = f"Error dispatching message: {error}"
                logger.exception(error_msg)
                sub_span.set_attribute("error", error)
                raise  # Re-raise to ensure the error is captured in activity logs and retried by gcp
            else:
                sub_span.set_attribute("is_dispatched_successfully", True)
                sub_span.add_event(
                    name="inreach_connector.message_dispatched_successfully"
                )
                return {"status": "success", "inreach_response": inreach_response}
