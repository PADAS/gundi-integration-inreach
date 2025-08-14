import asyncio
import json
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from gundi_core.schemas.v2 import LogLevel

from app.actions.inreach_client import InReachAuthenticationError, InReachServiceUnreachable, InReachInternalError
from app.services.action_runner import execute_action


@pytest.mark.asyncio
async def test_execute_auth_valid_credentials(
        mocker, inreach_integration, mock_inreach_client_class, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
):
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.InReachClient", mock_inreach_client_class)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="auth",
        config_overrides={
            "username": "test_user",
            "password": "test_password"
        }
    )

    assert response.get("valid_credentials") is True


@pytest.mark.asyncio
async def test_execute_auth_bad_credentials(
        mocker, inreach_integration, mock_inreach_client_class, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
):
    mock_inreach_client_class.return_value.pingback = mock.AsyncMock(
        side_effect=InReachAuthenticationError()
    )
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.InReachClient", mock_inreach_client_class)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="auth",
        config_overrides={
            "username": "test_user",
            "password": "test_password"
        }
    )

    assert response.get("valid_credentials") is False


@pytest.mark.asyncio
async def test_execute_auth_with_inreach_error(
        mocker, inreach_integration, mock_inreach_client_class, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
):
    mock_inreach_client_class.return_value.pingback = mock.AsyncMock(
        side_effect=InReachServiceUnreachable()
    )
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.InReachClient", mock_inreach_client_class)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    integration_id = str(inreach_integration.id)

    json_response = await execute_action(
        integration_id=integration_id,
        action_id="auth",
        config_overrides={
            "username": "test_user",
            "password": "test_password"
        }
    )

    # Check that returns an 500 so that it can be retried by GCP
    assert json_response.get("valid_credentials") is False
    assert "error" in json_response
    assert "InReachServiceUnreachable" in json_response.get("error", "")



@pytest.mark.asyncio
async def test_execute_push_messages_success(
        mocker, inreach_integration, mock_inreach_client_class, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
        mock_push_messages_data, mock_push_messages_metadata
):
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.InReachClient", mock_inreach_client_class)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    mock_log_activity = AsyncMock()
    mocker.patch("app.actions.handlers.log_action_activity", mock_log_activity)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="push_messages",
        data=mock_push_messages_data,
        metadata=mock_push_messages_metadata
    )

    assert response.get("status") == "success"
    # Check that a success message is recorded in activity logs
    gundi_id = mock_push_messages_metadata.get("gundi_id")
    inreach_api_url = inreach_integration.get_action_config("auth").data.get("api_url")
    mock_log_activity.assert_awaited_once()
    mock_call = mock_log_activity.mock_calls[0]
    mock_call_kwargs = mock_call.kwargs
    assert mock_call_kwargs.get("integration_id") == integration_id
    assert mock_call_kwargs.get("action_id") == "push_messages"
    assert mock_call_kwargs.get("title") == f"Message {gundi_id} Delivered to '{inreach_api_url}'"
    assert mock_call_kwargs.get("level") == LogLevel.DEBUG
    assert "data" in mock_call_kwargs
    logged_data = mock_call_kwargs.get("data")
    assert logged_data.get("delivered_at") is not None
    for key, value in mock_push_messages_metadata.items():
        assert logged_data.get(key) == value


@pytest.mark.asyncio
async def test_execute_push_messages_with_inreach_error(
        mocker, inreach_integration, mock_inreach_client_class, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
        mock_push_messages_data, mock_push_messages_metadata
):
    mock_inreach_client_class.return_value.send_messages = mock.AsyncMock(
        side_effect=InReachInternalError()
    )
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.InReachClient", mock_inreach_client_class)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    mock_log_activity = AsyncMock()
    mocker.patch("app.actions.handlers.log_action_activity", mock_log_activity)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="push_messages",
        data=mock_push_messages_data,
        metadata=mock_push_messages_metadata
    )

    # Check that returns an 500 so that it can be retried by GCP
    assert response.status_code == 500
    # Error details should be returned for troubleshooting
    json_response = json.loads(response.body).get("detail")
    assert "error" in json_response
    assert "InReachInternalError" in json_response.get("error", "")
    # Check that an error message is recorded in activity logs
    gundi_id = mock_push_messages_metadata.get("gundi_id")
    inreach_api_url = inreach_integration.get_action_config("auth").data.get("api_url")
    mock_log_activity.assert_awaited_once()
    mock_call = mock_log_activity.mock_calls[0]
    mock_call_kwargs = mock_call.kwargs
    assert mock_call_kwargs.get("integration_id") == integration_id
    assert mock_call_kwargs.get("action_id") == "push_messages"
    assert mock_call_kwargs.get("title") == f"Error Delivering Message {gundi_id} to '{inreach_api_url}'"
    assert mock_call_kwargs.get("level") == LogLevel.ERROR
    assert "data" in mock_call_kwargs
    logged_data = mock_call_kwargs.get("data")
    assert logged_data.get("error") == "InReachInternalError: An unexpected error occurred in InReach API."
    assert logged_data.get("error_traceback")
    for key, value in mock_push_messages_metadata.items():
        assert logged_data.get(key) == value
