import pytest

from app.webhooks.configurations import InReachWebhookConfig
from app.webhooks.handlers import webhook_handler, build_observation_from_inreach_event, \
    build_message_from_inreach_event


# Test data transformations
def test_build_message_from_inreach_event(inreach_event):
    message = build_message_from_inreach_event(inreach_event)
    assert message.get("sender") == inreach_event.imei
    assert message.get("text") == inreach_event.freeText
    assert message.get("recorded_at") == inreach_event.timeStamp
    assert "location" in message
    assert message["location"].get("latitude") == inreach_event.point.latitude
    assert message["location"].get("longitude") == inreach_event.point.longitude
    assert "additional" in message
    assert message["additional"].get("message_code") == inreach_event.messageCode
    assert message["additional"].get("status") == inreach_event.status.dict()
    assert message["additional"].get("recipient_addresses") == [
        item.address for item in inreach_event.addresses
    ]
    for key in inreach_event.point.dict().keys():
        if key not in ["latitude", "longitude"]:
            assert key in message["additional"]
            assert message["additional"].get(key) == inreach_event.point.dict()[key]


# Test data transformations
def test_build_observation_from_inreach_event(inreach_event):
    observation = build_observation_from_inreach_event(inreach_event)
    assert observation.get("source") == inreach_event.imei
    assert observation.get("type") == "gps-radio"
    assert observation.get("subject_type") == "ranger"
    assert observation.get("source_name") == inreach_event.imei
    assert observation.get("recorded_at") == inreach_event.timeStamp
    assert "location" in observation
    assert observation["location"].get("lat") == inreach_event.point.latitude
    assert observation["location"].get("lon") == inreach_event.point.longitude
    for key, value in inreach_event.status.dict().items():
        assert key in observation["additional"]
        assert observation["additional"].get(key) == value
    for key, value in inreach_event.point.dict().items():
        if key not in ["latitude", "longitude"]:
            assert key in observation["additional"]
            assert observation["additional"].get(key) == value


# Test with different settings for extracting messages and/or observations
@pytest.mark.parametrize(
    "processing_settings",
    [
        {"include_messages": True, "include_observations": True},
        {"include_messages": False, "include_observations": True},
        {"include_messages": True, "include_observations": False},
        {"include_messages": False, "include_observations": False}
    ]
)
@pytest.mark.asyncio
async def test_webhook_handler_processes_inreach_event_success(
        mocker,
        mock_send_observations_to_gundi,
        mock_send_messages_to_gundi,
        mock_publish_event,
        inreach_integration_with_webhook,
        inreach_webhook_request_payload,
        processing_settings
):

    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.webhooks.handlers.send_observations_to_gundi", mock_send_observations_to_gundi)
    mocker.patch("app.webhooks.handlers.send_messages_to_gundi", mock_send_messages_to_gundi)

    result = await webhook_handler(
        payload=inreach_webhook_request_payload,
        integration=inreach_integration_with_webhook,
        webhook_config=InReachWebhookConfig(**processing_settings)
    )

    if processing_settings.get("include_messages"):
        expected_total_messages = len(inreach_webhook_request_payload.Events)
    else:
        expected_total_messages = 0
    if processing_settings.get("include_observations"):
        expected_total_observations = len(inreach_webhook_request_payload.Events)
    else:
        expected_total_observations = 0
    assert result == {"total_observations": expected_total_observations, "total_messages": expected_total_messages}

    if expected_total_observations > 0:
        assert mock_send_observations_to_gundi.call_count == 1
        post_observations_call = mock_send_observations_to_gundi.mock_calls[0]
        assert post_observations_call.kwargs["integration_id"] == str(inreach_integration_with_webhook.id)
        expected_observations = [build_observation_from_inreach_event(event) for event in inreach_webhook_request_payload.Events]
        assert post_observations_call.kwargs["observations"] == expected_observations

    if expected_total_messages > 0:
        assert mock_send_messages_to_gundi.call_count == 1
        send_messages_call = mock_send_messages_to_gundi.mock_calls[0]
        assert send_messages_call.kwargs["integration_id"] == str(inreach_integration_with_webhook.id)
        expected_messages = [build_message_from_inreach_event(event) for event in inreach_webhook_request_payload.Events]
        assert send_messages_call.kwargs["messages"] == expected_messages
