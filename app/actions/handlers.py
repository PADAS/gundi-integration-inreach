from gundi_core.schemas.v2 import Integration
from gundi_core.events.transformers import MessageTransformedInReach

from app.services.activity_logger import activity_logger
from app import settings
from .configurations import AuthenticateConfig, PushMessageConfig
from .inreach_client import InReachClient, InReachBadCredentials

inreach_client = InReachClient(api_url=settings.INREACH_API_URL)


async def action_auth(integration: Integration, action_config: AuthenticateConfig):
    inreach_username = action_config.username
    inreach_password = action_config.password.get_secret_value()
    try:
        await inreach_client.pingback(
            username=inreach_username,
            password=inreach_password,
        )
    except InReachBadCredentials:
        return {"valid_credentials": False, "error": "Invalid username or password."}
    except Exception as e:
        return {"valid_credentials": False, "error": f"Error in authentication test: {type(e).__name__}: {e}."}
    else:
        return {"valid_credentials": True}


# ToDo: implement auxiliary actions


@activity_logger()
async def action_push_messages(
        integration: Integration, action_config: PushMessageConfig, data: MessageTransformedInReach
):
    ipc_message = data.payload
    auth_config = integration.get_action_config("auth")
    if not auth_config:
        raise ValueError("Authentication configuration is required for sending messages.")
    parsed_auth_config = AuthenticateConfig.parse_obj(auth_config.data)
    inreach_username = parsed_auth_config.username
    inreach_password = parsed_auth_config.password.get_secret_value()
    inreach_response = await inreach_client.send_messages(
        ipc_messages=[ipc_message],
        username=inreach_username,
        password=inreach_password,
    )
    return {"status": "success", "inreach_response": inreach_response}
