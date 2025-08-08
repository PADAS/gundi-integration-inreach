from unittest.mock import AsyncMock

import pytest
import asyncio
import datetime
from gundi_core.schemas.v2.inreach import InReachIPCMessage
from gundi_core.schemas.v2 import Integration, IntegrationSummary


@pytest.fixture
def inreach_ipc_message():
    """Fixture to create a sample InReach IPC message."""
    return InReachIPCMessage(
        Message="Gundi test message.",
        Recipients=["0123456789"],
        Sender="admin@sitex.pamdas.org",
        ReferencePoint=None,
        Timestamp=datetime.datetime.now(datetime.timezone.utc)
    )


@pytest.fixture
def inreach_integration():
    return Integration.parse_obj(
        {
            "id": "5328877d-2a65-4654-bc18-5b5a406803f8",
            "name": "InReach API test",
            "type": {
                "id": "8b402c72-4eb3-4a47-8dc9-b13263ab886e",
                "name": "Inreach",
                "value": "inreach",
                "description": "Default type for integrations with Inreach",
                "actions": [{
                    "id": "cd6d0490-21af-4107-a9a2-15c58c0161a9",
                    "type": "auth",
                    "name": "Auth",
                    "value": "auth",
                    "description": "Inreach Auth action",
                    "action_schema": {
                        "type": "object",
                        "title": "AuthenticateConfig",
                        "properties": {
                            "password": {
                                "type": "string",
                                "title": "Password",
                                "format": "password",
                                "default": '',
                                "example": "yourpassword",
                                "writeOnly": True,
                                "description": "Password used to authenticate against inReach API"
                            },
                            "username": {
                                "type": "string",
                                "title": "Username",
                                "default": '',
                                "example": "youruser",
                                "description": "Username used to authenticate against inReach API"
                            }
                        },
                        "definitions": {},
                        "is_executable": True
                    },
                    "ui_schema": {}
                }, {
                    "id": "55a8cc58-68cc-4bfd-a1b7-402a0f484369",
                    "type": "push",
                    "name": "Push Messages",
                    "value": "push_messages",
                    "description": "Inreach Push Messages action",
                    "action_schema": {
                        "type": "object",
                        "title": "PushMessageConfig",
                        "properties": {},
                        "definitions": {},
                        "is_executable": False
                    },
                    "ui_schema": {}
                }],
                "webhook": None
            },
            "base_url": '',
            "enabled": True,
            "owner": {
                "id": "a91b400b-482a-4546-8fcb-ee42b01deeb6",
                "name": "Test Org",
                "description": ''
            },
            "configurations": [{
                "id": "92b5e7a5-94d7-4606-b253-2efbdbb780f9",
                "integration": "5328877d-2a65-4654-bc18-5b5a406803f8",
                "action": {
                    "id": "cd6d0490-21af-4107-a9a2-15c58c0161a9",
                    "type": "auth",
                    "name": "Auth",
                    "value": "auth"
                },
                "data": {
                    "password": "test",
                    "username": "test"
                }
            }, {
                "id": "f1f816d6-34a1-4eca-9420-817ee9c741d9",
                "integration": "5328877d-2a65-4654-bc18-5b5a406803f8",
                "action": {
                    "id": "55a8cc58-68cc-4bfd-a1b7-402a0f484369",
                    "type": "push",
                    "name": "Push Messages",
                    "value": "push_messages"
                },
                "data": {}
            }],
            "webhook_configuration": None,
            "default_route": None,
            "additional": {},
            "status": "healthy",
            "status_details": "No issues detected"
        }
    )


@pytest.fixture
def mock_gundi_client_v2_inreach(
        mocker,
        inreach_integration,
):
    mock_client = mocker.MagicMock()
    mock_client.get_integration_details.return_value = AsyncMock(
        return_value=inreach_integration
    )
    mock_client.__aenter__.return_value = mock_client
    return mock_client


@pytest.fixture
def mock_gundi_client_v2_class_inreach(mocker, mock_gundi_client_v2_inreach):
    mock_gundi_client_v2_class_inreach = mocker.MagicMock()
    mock_gundi_client_v2_class_inreach.return_value = mock_gundi_client_v2_inreach
    return mock_gundi_client_v2_class_inreach


@pytest.fixture
def mock_config_manager_inreach(mocker, inreach_integration):

    async def mock_get_action_configuration(integration_id, action_id):
        return inreach_integration.get_action_config(action_id)

    mock_config_manager_ir = mocker.MagicMock()
    mock_config_manager_ir.get_integration = AsyncMock(
        return_value=IntegrationSummary.from_integration(inreach_integration)
    )
    mock_config_manager_ir.get_integration_details = AsyncMock(return_value=inreach_integration)
    mock_config_manager_ir.get_action_configuration.side_effect = mock_get_action_configuration
    mock_config_manager_ir.set_integration = AsyncMock(return_value=None)
    mock_config_manager_ir.set_action_configuration = AsyncMock(return_value=None)
    mock_config_manager_ir.delete_integration = AsyncMock(return_value=None)
    mock_config_manager_ir.delete_action_configuration = AsyncMock(return_value=None)
    return mock_config_manager_ir


@pytest.fixture
def mock_inreach_client(mocker):
    mock_inreach_client = mocker.MagicMock()
    mock_inreach_client.pingback = AsyncMock(return_value={})
    mock_inreach_client.send_messages = AsyncMock(
        return_value={"status": "success", "inreach_response": {"Detail": "Message sent successfully."}}
    )
    return mock_inreach_client


@pytest.fixture
def mock_push_messages_data():
    return {
        "event_id": "5f445365-af8b-4799-971b-209afb3b292d",
        "timestamp": "2025-08-05 13:00:17.395248+00:00",
        "schema_version": "v1",
        "payload": {
            "Message": "Gundi test message.",
            "Recipients": ["2075752244"],
            "Sender": "admin@sitex.pamdas.org",
            "ReferencePoint": None,
            "Timestamp": "2025-06-04 13:35:10+03:00"
        },
        "event_type": "MessageTransformedInReach"
    }
