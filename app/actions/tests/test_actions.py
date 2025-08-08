import asyncio
from unittest import mock

import pytest
from app.services.action_runner import execute_action


@pytest.mark.asyncio
async def test_execute_auth_valid_credentials(
        mocker, inreach_integration, mock_inreach_client, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
):
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.inreach_client", mock_inreach_client)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="auth",
        config_overrides={
            "username": "valid_user",
            "password": "valid_password"
        }
    )

    assert response.get("valid_credentials") is True


@pytest.mark.asyncio
async def test_execute_push_messages_success(
        mocker, inreach_integration, mock_inreach_client, mock_config_manager_inreach,
        mock_gundi_client_v2_inreach, mock_gundi_client_v2_class_inreach,
        mock_get_gundi_api_key, mock_gundi_sensors_client_class, mock_publish_event,
        mock_push_messages_data
):
    mocker.patch("app.services.action_runner._portal", mock_gundi_client_v2_inreach)
    mocker.patch("app.services.activity_logger.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.publish_event", mock_publish_event)
    mocker.patch("app.services.action_runner.config_manager", mock_config_manager_inreach)
    mocker.patch("app.actions.handlers.inreach_client", mock_inreach_client)
    mocker.patch("app.services.gundi.GundiClient", mock_gundi_client_v2_class_inreach)
    mocker.patch("app.services.gundi.GundiDataSenderClient", mock_gundi_sensors_client_class)
    mocker.patch("app.services.gundi._get_gundi_api_key", mock_get_gundi_api_key)
    integration_id = str(inreach_integration.id)

    response = await execute_action(
        integration_id=integration_id,
        action_id="push_messages",
        data=mock_push_messages_data
    )

    assert response.get("status") == "success"
