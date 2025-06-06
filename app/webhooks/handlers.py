import json
from app.services.activity_logger import webhook_activity_logger
from app.services.gundi import send_observations_to_gundi
from .configurations import InReachWebhookPayload, InReachWebhookConfig


@webhook_activity_logger()
async def webhook_handler(payload: InReachWebhookPayload, integration=None, webhook_config: InReachWebhookConfig = None):
    # Sample implementation using the JQ language to transform the incoming data
    inreach_event_payload = json.loads(payload.json())
    observations = []
    messages = []
    for inreach_event in inreach_event_payload.Events:
        # ToDo: parse observations and messages
        pass

    # ToDo: send_observations_to_gundi
    # ToDo: send_messages_to_gundi
    return {"total_observations": len(observations), "total_messages": len(messages)}
