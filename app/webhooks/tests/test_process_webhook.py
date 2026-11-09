"""process_webhook's answer to the sender.

Garmin's IPC Outbound service treats anything but a 200 as a failed delivery
and retries it (2, 4, 8 ... 128 s, queued for up to five days). Answering 200
to every failure, as process_webhook used to, drops the batch for good: the
sender will not resend, and unlike a pull action there is no next run.
"""
import json
import pytest
import httpx
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from gundi_client_v2.errors import GundiAPIError
from starlette.requests import Request

from app.services.webhooks import process_webhook


def _webhook_request(integration_id: str, body: dict) -> Request:
    raw = json.dumps(body).encode()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/webhooks",
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            (b"x-consumer-username", f"integration:{integration_id}".encode()),
        ],
    }

    async def receive():
        return {"type": "http.request", "body": raw, "more_body": False}

    return Request(scope, receive)


@pytest.fixture
def inreach_webhook_body(inreach_webhook_request_payload):
    return json.loads(inreach_webhook_request_payload.json())


@pytest.fixture
def webhook_environment(mocker, mock_publish_event, inreach_integration_with_webhook):
    config_manager = mocker.MagicMock()
    config_manager.get_integration_details = AsyncMock(return_value=inreach_integration_with_webhook)
    mocker.patch("app.services.webhooks.config_manager", config_manager)
    mocker.patch("app.services.webhooks.publish_event", mock_publish_event)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.webhooks.handlers.send_messages_to_gundi", AsyncMock(return_value=[]))
    return config_manager


@pytest.mark.asyncio
async def test_process_webhook_answers_503_when_forwarding_to_gundi_fails_transiently(
        mocker, webhook_environment, inreach_integration_with_webhook, inreach_webhook_body, mock_publish_event
):
    mocker.patch(
        "app.webhooks.handlers.send_observations_to_gundi",
        AsyncMock(side_effect=httpx.ReadTimeout("sensors api did not answer")),
    )

    response = await process_webhook(
        request=_webhook_request(str(inreach_integration_with_webhook.id), inreach_webhook_body)
    )

    assert response.status_code == 503
    assert "Retry-After" in response.headers
    # The failure is still reported to the activity log.
    published = [c.kwargs["event"] for c in mock_publish_event.call_args_list]
    assert any(type(e).__name__ == "IntegrationWebhookFailed" for e in published)


@pytest.mark.asyncio
async def test_process_webhook_answers_503_when_gundi_answers_5xx(
        mocker, webhook_environment, inreach_integration_with_webhook, inreach_webhook_body
):
    mocker.patch(
        "app.webhooks.handlers.send_observations_to_gundi",
        AsyncMock(side_effect=GundiAPIError(status_code=502, detail="bad gateway")),
    )

    response = await process_webhook(
        request=_webhook_request(str(inreach_integration_with_webhook.id), inreach_webhook_body)
    )

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_process_webhook_acknowledges_a_permanent_gundi_rejection(
        mocker, webhook_environment, inreach_integration_with_webhook, inreach_webhook_body
):
    """A 4xx from Gundi will not change on the next attempt. Asking the
    sender to retry would loop for five days and then pause the feed."""
    mocker.patch(
        "app.webhooks.handlers.send_observations_to_gundi",
        AsyncMock(side_effect=GundiAPIError(status_code=400, detail="invalid observation")),
    )

    response = await process_webhook(
        request=_webhook_request(str(inreach_integration_with_webhook.id), inreach_webhook_body)
    )

    assert response == {}


@pytest.mark.asyncio
async def test_process_webhook_acknowledges_an_unparseable_payload(
        webhook_environment, inreach_integration_with_webhook
):
    response = await process_webhook(
        request=_webhook_request(str(inreach_integration_with_webhook.id), {"Version": "2.0", "Events": "nope"})
    )

    assert response == {}


def test_webhooks_route_relays_503_to_the_sender_when_processing_inline(
        mocker, webhook_environment, inreach_integration_with_webhook, inreach_webhook_body
):
    """With PROCESS_WEBHOOKS_IN_BACKGROUND off the route awaits
    process_webhook and must pass its status through, so the sender's retry
    logic sees it."""
    from app.main import app
    from app.routers import webhooks as webhooks_router

    mocker.patch.object(webhooks_router.settings, "PROCESS_WEBHOOKS_IN_BACKGROUND", False)
    mocker.patch(
        "app.webhooks.handlers.send_observations_to_gundi",
        AsyncMock(side_effect=httpx.ReadTimeout("sensors api did not answer")),
    )

    client = TestClient(app)
    response = client.post(
        "/webhooks",
        json=inreach_webhook_body,
        headers={"x-consumer-username": f"integration:{inreach_integration_with_webhook.id}"},
    )

    assert response.status_code == 503
