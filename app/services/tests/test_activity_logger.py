import json
import pydantic
import pytest
from unittest.mock import ANY
from gundi_core.events import (
    LogLevel,
    IntegrationActionStarted,
    IntegrationActionComplete,
    IntegrationActionFailed,
    IntegrationActionCustomLog,
    IntegrationWebhookStarted,
    IntegrationWebhookComplete,
    IntegrationWebhookFailed
)
from app import settings
from app.conftest import async_return
from app.services.activity_logger import (
    publish_event, publish_events, activity_logger, webhook_activity_logger, log_activity,
    log_action_activity, log_webhook_activity, PUBSUB_MAX_MESSAGES_PER_PUBLISH, PUBSUB_MAX_BYTES_PER_PUBLISH,
)
from app.services.errors import IntegrationAuthError
from app.services.redaction import REDACTED
from app.webhooks import GenericJsonPayload, GenericJsonTransformConfig


@pytest.mark.parametrize(
    "system_event",
    [
        "action_started_event", "action_complete_event", "action_failed_event", "custom_activity_log_event",
        "webhook_started_event", "webhook_complete_event", "webhook_failed_event", "webhook_custom_activity_log_event"
    ],
    indirect=["system_event"])
@pytest.mark.asyncio
async def test_publish_event(
        mocker, mock_pubsub_client, integration_event_pubsub_message, gcp_pubsub_publish_response,
        system_event
):
    mocker.patch("app.services.activity_logger.pubsub", mock_pubsub_client)

    response = await publish_event(
        event=system_event,
        topic_name=settings.INTEGRATION_EVENTS_TOPIC
    )

    assert response == gcp_pubsub_publish_response
    assert mock_pubsub_client.PublisherClient.called
    assert mock_pubsub_client.PubsubMessage.called
    assert mock_pubsub_client.PublisherClient.called
    assert mock_pubsub_client.PublisherClient.return_value.publish.called
    mock_pubsub_client.PublisherClient.return_value.publish.assert_any_call(
        f"projects/{settings.GCP_PROJECT_ID}/topics/{settings.INTEGRATION_EVENTS_TOPIC}",
        [integration_event_pubsub_message],
    )


@pytest.mark.asyncio
async def test_activity_logger_decorator(
        mocker, mock_publish_event, integration_v2, pull_observations_config
):

    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger()
    async def action_pull_observations(integration, action_config):
        return {"observations_extracted": 10}

    await action_pull_observations(
        integration=integration_v2,
        action_config=pull_observations_config
    )

    # Two events expected: One on start and one on completion
    assert mock_publish_event.call_count == 2
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionStarted)
    assert isinstance(mock_publish_event.call_args_list[1].kwargs.get("event"), IntegrationActionComplete)


@pytest.mark.asyncio
async def test_webhook_activity_logger(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_webhook_request_payload_for_dynamic_schema, mock_generic_webhook_config
):

    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @webhook_activity_logger()
    async def webhook_handler(payload: GenericJsonPayload, integration=None, webhook_config: GenericJsonTransformConfig = None):
        return {"observations_extracted": 10}

    await webhook_handler(
        payload=GenericJsonPayload(data=mock_webhook_request_payload_for_dynamic_schema),
        integration=integration_v2_with_webhook_generic,
        webhook_config=GenericJsonTransformConfig(**mock_generic_webhook_config)
    )

    # Two events expected: One on start and one on completion
    assert mock_publish_event.call_count == 2
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationWebhookStarted)
    assert isinstance(mock_publish_event.call_args_list[1].kwargs.get("event"), IntegrationWebhookComplete)


@pytest.mark.asyncio
async def test_webhook_activity_logger_on_error(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_webhook_request_payload_for_dynamic_schema, mock_generic_webhook_config
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @webhook_activity_logger()
    async def webhook_handler(payload: GenericJsonPayload, integration=None,
                              webhook_config: GenericJsonTransformConfig = None):
        raise Exception("Something went wrong")

    with pytest.raises(Exception):
        await webhook_handler(
            payload=GenericJsonPayload(data=mock_webhook_request_payload_for_dynamic_schema),
            integration=integration_v2_with_webhook_generic,
            webhook_config=GenericJsonTransformConfig(**mock_generic_webhook_config)
        )

    # Two events expected: One on start and one on error
    assert mock_publish_event.call_count == 2
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationWebhookStarted)
    assert isinstance(mock_publish_event.call_args_list[1].kwargs.get("event"), IntegrationWebhookFailed)


@pytest.mark.asyncio
async def test_activity_logger_decorator_with_arguments(
        mocker, mock_publish_event, integration_v2, pull_observations_config
):

    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger(on_start=False, on_completion=True, on_error=False)
    async def action_pull_observations(integration, action_config):
        return {"observations_extracted": 10}

    await action_pull_observations(
        integration=integration_v2,
        action_config=pull_observations_config
    )

    # Only one event expected, on completion
    assert mock_publish_event.call_count == 1
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionComplete)


@pytest.mark.asyncio
async def test_activity_logger_decorator_on_error(
        mocker, mock_publish_event, integration_v2, pull_observations_config
):

    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger()
    async def action_pull_observations(integration, action_config):
        raise Exception("Something went wrong")

    with pytest.raises(Exception):
        await action_pull_observations(
            integration=integration_v2,
            action_config=pull_observations_config
        )

    # Two events expected: One on start and one on error
    assert mock_publish_event.call_count == 2
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionStarted)
    assert isinstance(mock_publish_event.call_args_list[1].kwargs.get("event"), IntegrationActionFailed)


@pytest.mark.asyncio
async def test_log_activity_with_debug_level(mocker, integration_v2, pull_observations_config, mock_publish_event):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    await log_activity(
        integration_id=integration_v2.id,
        action_id="pull_observations",
        level=LogLevel.DEBUG,
        title="Extracted 10 observations from 2 devices",
        data={"devices": ["deviceid1", "deviceid2"]},
        config_data=pull_observations_config.dict()
    )
    assert mock_publish_event.call_count == 1
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionCustomLog)


@pytest.mark.asyncio
async def test_log_activity_with_info_level(mocker, integration_v2, mock_publish_event, pull_observations_config):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    await log_activity(
        integration_id=integration_v2.id,
        action_id="pull_observations",
        level=LogLevel.INFO,
        title="Extracting observations with filter..",
        data={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        config_data=pull_observations_config.dict()
    )
    assert mock_publish_event.call_count == 1
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionCustomLog)


@pytest.mark.asyncio
async def test_log_activity_with_warning_level(mocker, integration_v2, mock_publish_event, pull_observations_config):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    await log_activity(
        integration_id=integration_v2.id,
        action_id="pull_observations",
        level=LogLevel.WARNING,
        title="Skipping end_date because it's greater than today. Please review your configuration.",
        config_data=pull_observations_config.dict()
    )
    assert mock_publish_event.call_count == 1
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionCustomLog)


@pytest.mark.asyncio
async def test_log_activity_with_error_level(mocker, integration_v2, mock_publish_event, pull_observations_config):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    await log_activity(
        integration_id=integration_v2.id,
        action_id="pull_observations",
        level=LogLevel.ERROR,
        title="Error getting data from System X",
        data={"error": "Connection error with host 'systemx.com'"},
        config_data=pull_observations_config.dict()
    )
    assert mock_publish_event.call_count == 1
    assert isinstance(mock_publish_event.call_args_list[0].kwargs.get("event"), IntegrationActionCustomLog)


@pytest.mark.asyncio
async def test_activity_logger_decorator_publishes_classified_error_text(
        mocker, mock_publish_event, integration_v2, pull_observations_config
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger()
    async def action_pull_observations(integration, action_config):
        raise IntegrationAuthError("TrackIt rejected the credentials", status_code=401)

    with pytest.raises(IntegrationAuthError):
        await action_pull_observations(
            integration=integration_v2, action_config=pull_observations_config
        )

    failed_events = [
        call.kwargs.get("event") or call.args[0]
        for call in mock_publish_event.mock_calls
        if call.kwargs.get("event") is not None or call.args
    ]
    failed_events = [e for e in failed_events if isinstance(e, IntegrationActionFailed)]
    assert len(failed_events) == 1
    assert failed_events[0].payload.error == (
        "Authentication failed — TrackIt rejected the credentials (HTTP 401)"
    )



@pytest.mark.asyncio
async def test_webhook_activity_logger_decorator_publishes_classified_error_text(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_generic_webhook_config, mock_webhook_request_payload_for_dynamic_schema
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @webhook_activity_logger()
    async def webhook_handler(payload: GenericJsonPayload, integration=None,
                              webhook_config: GenericJsonTransformConfig = None):
        raise IntegrationAuthError("Provider rejected the credentials", status_code=401)

    with pytest.raises(IntegrationAuthError):
        await webhook_handler(
            payload=GenericJsonPayload(data=mock_webhook_request_payload_for_dynamic_schema),
            integration=integration_v2_with_webhook_generic,
            webhook_config=GenericJsonTransformConfig(**mock_generic_webhook_config)
        )

    failed_events = [
        call.kwargs.get("event") or call.args[0]
        for call in mock_publish_event.mock_calls
        if call.kwargs.get("event") is not None or call.args
    ]
    failed_events = [e for e in failed_events if isinstance(e, IntegrationWebhookFailed)]
    assert len(failed_events) == 1
    assert failed_events[0].payload.error == (
        "Authentication failed — Provider rejected the credentials (HTTP 401)"
    )


@pytest.mark.asyncio
async def test_log_activity_default_level_is_a_valid_log_level(mocker, integration_v2, mock_publish_event):
    """gundi-core's LogLevel is an IntEnum, so the string default "INFO" the
    helpers used to carry never validated: a connector that called
    log_action_activity without a level got a ValidationError instead of a
    log entry. The default must be the enum member."""
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    await log_action_activity(
        integration_id=str(integration_v2.id),
        action_id="pull_observations",
        title="Something worth telling the operator",
    )
    await log_webhook_activity(
        integration_id=str(integration_v2.id),
        title="Webhook received",
    )

    levels = [call.kwargs["event"].payload.level for call in mock_publish_event.call_args_list]
    assert levels == [LogLevel.INFO, LogLevel.INFO]


@pytest.mark.asyncio
async def test_publish_events_sends_all_events_in_a_single_publish_call(
        mocker, mock_pubsub_client, action_started_event, gcp_pubsub_publish_response
):
    mocker.patch("app.services.activity_logger.pubsub", mock_pubsub_client)

    response = await publish_events([action_started_event] * 3, topic_name=settings.INTEGRATION_EVENTS_TOPIC)

    publisher = mock_pubsub_client.PublisherClient.return_value
    assert publisher.publish.call_count == 1
    topic, messages = publisher.publish.call_args.args
    assert topic == f"projects/{settings.GCP_PROJECT_ID}/topics/{settings.INTEGRATION_EVENTS_TOPIC}"
    assert len(messages) == 3
    assert response == gcp_pubsub_publish_response


@pytest.mark.asyncio
async def test_publish_events_splits_batches_at_the_pubsub_limit(
        mocker, mock_pubsub_client, action_started_event
):
    mocker.patch("app.services.activity_logger.pubsub", mock_pubsub_client)
    publisher = mock_pubsub_client.PublisherClient.return_value
    publisher.publish.side_effect = lambda topic, messages: async_return(
        {"messageIds": [str(i) for i in range(len(messages))]}
    )
    events = [action_started_event] * (PUBSUB_MAX_MESSAGES_PER_PUBLISH + 5)

    response = await publish_events(events, topic_name=settings.INTEGRATION_EVENTS_TOPIC)

    assert [len(c.args[1]) for c in publisher.publish.call_args_list] == [PUBSUB_MAX_MESSAGES_PER_PUBLISH, 5]
    assert len(response["messageIds"]) == PUBSUB_MAX_MESSAGES_PER_PUBLISH + 5


@pytest.mark.asyncio
async def test_publish_events_is_a_no_op_on_ephemeral_run(mocker, mock_pubsub_client, action_started_event):
    from app.services.activity_logger import ephemeral_run
    mocker.patch("app.services.activity_logger.pubsub", mock_pubsub_client)

    token = ephemeral_run.set(True)
    try:
        response = await publish_events([action_started_event], topic_name=settings.INTEGRATION_EVENTS_TOPIC)
    finally:
        ephemeral_run.reset(token)

    assert response is None
    assert not mock_pubsub_client.PublisherClient.return_value.publish.called


def _serialized_request_size(messages):
    # What gcloud-aio's PublisherClient.publish puts on the wire: base64 data
    # plus JSON framing. Pub/Sub's 10 MB quota applies to this body.
    return len(json.dumps({"messages": [m.to_repr() for m in messages]}))


@pytest.fixture
def mock_publisher_client_only(mocker, gcp_pubsub_publish_response):
    """Mock the publisher but keep the real PubsubMessage, so batch sizes
    reflect the events actually being sent."""
    publisher = mocker.MagicMock()
    publisher.topic_path.return_value = f"projects/{settings.GCP_PROJECT_ID}/topics/{settings.INTEGRATION_EVENTS_TOPIC}"
    publisher.publish.side_effect = lambda topic, messages: async_return(
        {"messageIds": [str(i) for i in range(len(messages))]}
    )
    mocker.patch("app.services.activity_logger.pubsub.PublisherClient", return_value=publisher)
    return publisher


@pytest.mark.asyncio
async def test_publish_events_splits_batches_at_the_byte_limit(
        mocker, mock_publisher_client_only, action_started_event
):
    # Review on #114: Pub/Sub also rejects publish requests over 10 MB, and a
    # count-only split assembled 1,000 x 12 KB commands into a 16 MB request
    # that every retry would resend. Split on serialized size as well.
    from app.services import activity_logger
    one_event = _serialized_request_size(
        [activity_logger.pubsub.PubsubMessage(json.dumps(action_started_event.dict(), default=str).encode("utf-8"))]
    )
    limit = one_event * 3 + 16  # room for three, not four
    mocker.patch.object(activity_logger, "PUBSUB_MAX_BYTES_PER_PUBLISH", limit)

    response = await publish_events([action_started_event] * 7, topic_name=settings.INTEGRATION_EVENTS_TOPIC)

    sizes = [len(c.args[1]) for c in mock_publisher_client_only.publish.call_args_list]
    assert sizes == [3, 3, 1]
    for call in mock_publisher_client_only.publish.call_args_list:
        assert _serialized_request_size(call.args[1]) <= limit
    assert len(response["messageIds"]) == 7


@pytest.mark.asyncio
async def test_publish_events_sends_an_oversized_event_alone_instead_of_dropping_it(
        mocker, mock_publisher_client_only, action_started_event
):
    # A single event larger than the limit cannot be split; it goes out on
    # its own so Pub/Sub's rejection names it, and the loop still terminates.
    from app.services import activity_logger
    mocker.patch.object(activity_logger, "PUBSUB_MAX_BYTES_PER_PUBLISH", 10)

    response = await publish_events([action_started_event] * 3, topic_name=settings.INTEGRATION_EVENTS_TOPIC)

    assert [len(c.args[1]) for c in mock_publisher_client_only.publish.call_args_list] == [1, 1, 1]
    assert len(response["messageIds"]) == 3


def test_publish_byte_limit_is_the_pubsub_quota():
    # 10 MB per publish request, per https://cloud.google.com/pubsub/quotas
    assert PUBSUB_MAX_BYTES_PER_PUBLISH <= 10 * 1000 * 1000
    assert PUBSUB_MAX_MESSAGES_PER_PUBLISH == 1000


class _PlainStringPasswordConfiguration(pydantic.BaseModel):
    # A str (not SecretStr) marked as a password only through the schema
    # hint: pydantic's own serialization would print it in clear.
    username: str
    password: str = pydantic.Field(..., format="password")


@pytest.mark.asyncio
async def test_activity_logger_decorator_redacts_secrets_in_the_published_config(
        mocker, mock_publish_event, integration_v2,
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger()
    async def action_auth(integration, action_config):
        raise RuntimeError("login rejected")

    with pytest.raises(RuntimeError):
        await action_auth(
            integration=integration_v2,
            action_config=_PlainStringPasswordConfiguration(username="me", password="hunter2"),
        )

    assert mock_publish_event.call_count == 2  # start + failure
    for call in mock_publish_event.call_args_list:
        event = call.kwargs["event"]
        assert event.payload.config_data == {"username": "me", "password": REDACTED}
        assert "hunter2" not in event.json()


@pytest.mark.asyncio
async def test_webhook_activity_logger_decorator_redacts_secrets_in_the_published_config(
        mocker, mock_publish_event, integration_v2,
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    class _HookConfig(pydantic.BaseModel):
        token: str
        topic: str

    @webhook_activity_logger()
    async def webhook_handler(payload, integration, webhook_config):
        return {"ok": True}

    await webhook_handler(
        payload={}, integration=integration_v2, webhook_config=_HookConfig(token="tok-123", topic="t"),
    )

    assert mock_publish_event.call_count == 2  # start + completion
    for call in mock_publish_event.call_args_list:
        event = call.kwargs["event"]
        assert event.payload.config_data == {"token": REDACTED, "topic": "t"}


@pytest.mark.asyncio
async def test_log_action_activity_redacts_secrets_in_the_given_config_data(
        mocker, integration_v2, mock_publish_event,
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    await log_action_activity(
        integration_id=integration_v2.id,
        action_id="pull_observations",
        title="Fetching",
        config_data={"site": "s", "api_key": "key-789"},
    )

    event = mock_publish_event.call_args.kwargs["event"]
    assert event.payload.config_data == {"site": "s", "api_key": REDACTED}


@pytest.mark.asyncio
async def test_log_webhook_activity_redacts_secrets_in_the_given_config_data(
        mocker, integration_v2, mock_publish_event,
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    await log_webhook_activity(
        integration_id=integration_v2.id,
        title="Received",
        config_data={"site": "s", "secret": "sec-000"},
    )

    event = mock_publish_event.call_args.kwargs["event"]
    assert event.payload.config_data == {"site": "s", "secret": REDACTED}


class _NestedDetails(pydantic.BaseModel):
    code: str = pydantic.Field(..., format="password")
    realm: str


class _NestingConfiguration(pydantic.BaseModel):
    details: _NestedDetails
    site: str


@pytest.mark.asyncio
async def test_activity_logger_decorator_redacts_model_declared_secrets_below_the_root(
        mocker, mock_publish_event, integration_v2,
):
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @activity_logger()
    async def action_pull(integration, action_config):
        return {}

    await action_pull(
        integration=integration_v2,
        action_config=_NestingConfiguration(details={"code": "nested-password", "realm": "r"}, site="s"),
    )

    for call in mock_publish_event.call_args_list:
        event = call.kwargs["event"]
        assert event.payload.config_data == {"details": {"code": REDACTED, "realm": "r"}, "site": "s"}


def _worst_case_waits(policy: dict) -> list:
    """The sleeps tenacity performs between attempts when every jitter draw is
    maximal: min(initial * 2**n + jitter, max) for n = 0 .. attempts-2."""
    return [
        min(policy["wait_initial"] * 2 ** n + policy["wait_jitter"], policy["wait_max"])
        for n in range(policy["attempts"] - 1)
    ]


def test_publish_event_retry_policy_reaches_every_declared_attempt():
    """stamina stops at whichever of `attempts` / `timeout` comes first, and its
    default timeout is 45 s. publish_event used to declare five attempts with
    4-9 / 8-13 / 16-21 / 32-37 s waits on top of a 20 s request timeout, so
    the 45 s default cut it off after two or three: the declared policy was
    not the one that ran in production."""
    from app.services.activity_logger import PUBLISH_EVENT_RETRY, PUBLISH_REQUEST_TIMEOUT_SECONDS

    assert PUBLISH_EVENT_RETRY["attempts"] and PUBLISH_EVENT_RETRY["timeout"], "both stops must be explicit"
    waits = _worst_case_waits(PUBLISH_EVENT_RETRY)
    # tenacity checks the stop after each failed attempt, so every declared
    # attempt is reachable only if the waits plus the requests before the last
    # attempt fit inside the timeout.
    busy_before_last_attempt = sum(waits) + (PUBLISH_EVENT_RETRY["attempts"] - 1) * PUBLISH_REQUEST_TIMEOUT_SECONDS
    assert busy_before_last_attempt <= PUBLISH_EVENT_RETRY["timeout"], (
        f"{busy_before_last_attempt}s of waiting and requests before the last attempt, more than the "
        f"{PUBLISH_EVENT_RETRY['timeout']}s budget: only part of the declared "
        f"{PUBLISH_EVENT_RETRY['attempts']} attempts can ever run"
    )
    # wait_max is a real cap on the curve, not a decorative number.
    assert waits[-1] == PUBLISH_EVENT_RETRY["wait_max"]


@pytest.mark.asyncio
async def test_webhook_activity_logger_runs_handler_when_start_event_cannot_be_published(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_webhook_request_payload_for_fixed_schema
):
    """17 of the 41 webhook failures seen in prod on 2026-11-09 were the
    'started' publish timing out: the payload was never processed and the
    sender had already been told 200. Activity logging is a side channel and
    must never decide whether the data is forwarded."""
    import asyncio
    mock_publish_event.side_effect = [asyncio.TimeoutError(), None]
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    handler_calls = []

    @webhook_activity_logger()
    async def webhook_handler(payload, integration=None, webhook_config=None):
        handler_calls.append(payload)
        return {"forwarded": 1}

    result = await webhook_handler(
        payload=mock_webhook_request_payload_for_fixed_schema,
        integration=integration_v2_with_webhook_generic,
        webhook_config=GenericJsonTransformConfig(jq_filter=".", output_type="obv"),
    )

    assert result == {"forwarded": 1}
    assert len(handler_calls) == 1
    assert mock_publish_event.call_count == 2
    assert isinstance(mock_publish_event.call_args_list[1].kwargs.get("event"), IntegrationWebhookComplete)


@pytest.mark.asyncio
async def test_webhook_activity_logger_returns_result_when_complete_event_cannot_be_published(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_webhook_request_payload_for_fixed_schema
):
    """The data is already in Gundi by the time the 'complete' event goes out.
    A failed publish there must not surface as a webhook failure (the other
    24 of the 41 prod occurrences did exactly that, flipping the integration
    to unhealthy over data that had been delivered)."""
    import asyncio
    mock_publish_event.side_effect = [None, asyncio.TimeoutError()]
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @webhook_activity_logger()
    async def webhook_handler(payload, integration=None, webhook_config=None):
        return {"forwarded": 1}

    result = await webhook_handler(
        payload=mock_webhook_request_payload_for_fixed_schema,
        integration=integration_v2_with_webhook_generic,
        webhook_config=GenericJsonTransformConfig(jq_filter=".", output_type="obv"),
    )

    assert result == {"forwarded": 1}


@pytest.mark.asyncio
async def test_webhook_activity_logger_reraises_handler_error_when_failed_event_cannot_be_published(
        mocker, mock_publish_event, integration_v2_with_webhook_generic,
        mock_webhook_request_payload_for_fixed_schema
):
    """The caller classifies the handler's exception to decide the HTTP
    status. A publish failure on the way out must not replace it."""
    import asyncio
    mock_publish_event.side_effect = [None, asyncio.TimeoutError()]
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)

    @webhook_activity_logger()
    async def webhook_handler(payload, integration=None, webhook_config=None):
        raise IntegrationAuthError("provider rejected the credentials")

    with pytest.raises(IntegrationAuthError):
        await webhook_handler(
            payload=mock_webhook_request_payload_for_fixed_schema,
            integration=integration_v2_with_webhook_generic,
            webhook_config=GenericJsonTransformConfig(jq_filter=".", output_type="obv"),
        )
