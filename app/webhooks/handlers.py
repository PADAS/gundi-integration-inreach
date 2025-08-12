from app.services.activity_logger import webhook_activity_logger
from app.services.gundi import send_observations_to_gundi, _get_gundi_api_key, send_messages_to_gundi
from .configurations import InReachWebhookPayload, InReachWebhookConfig
from .inreach import InreachEvent


def build_message_from_inreach_event(inreach_event: InreachEvent):
    location_data = inreach_event.point.dict()
    latitude = location_data.pop("latitude")
    longitude = location_data.pop("longitude")
    return {
        "sender": inreach_event.imei,
        "recipients": [],
        "text": inreach_event.freeText,
        "recorded_at": inreach_event.timeStamp,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "additional": {
            "message_code": inreach_event.messageCode,
            "status": inreach_event.status.dict(),
            "recipient_addresses": [
                item.address for item in inreach_event.addresses
            ],
            **location_data
        }
    }


def build_observation_from_inreach_event(inreach_event: InreachEvent):
    location_data = inreach_event.point.dict()
    latitude = location_data.pop("latitude")
    longitude = location_data.pop("longitude")
    return {
        "source": inreach_event.imei,
        "type": "gps-radio",
        "subject_type": "ranger",
        "source_name": inreach_event.imei,
        "recorded_at": inreach_event.timeStamp,
        "location": {
            "lat": latitude,
            "lon": longitude
        },
        "additional": {
            **inreach_event.status.dict(),
            **location_data
        }
    }


@webhook_activity_logger()
async def webhook_handler(payload: InReachWebhookPayload, integration=None, webhook_config: InReachWebhookConfig = None):
    observations = []
    messages = []
    # Extract observations and messages
    for inreach_event in payload.Events:
        if webhook_config.include_messages:
            messages.append(build_message_from_inreach_event(inreach_event))
        if webhook_config.include_observations:
            observations.append(build_observation_from_inreach_event(inreach_event))
    # Send the final data to gundi
    integration_id = str(integration.id)
    # Observations sent first so that subjects and sources are created
    await send_observations_to_gundi(observations=observations, integration_id=integration_id)
    await send_messages_to_gundi(messages=messages, integration_id=integration_id)
    return {"total_observations": len(observations), "total_messages": len(messages)}
