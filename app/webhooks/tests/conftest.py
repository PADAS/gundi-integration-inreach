import pytest

from unittest.mock import AsyncMock
from gundi_core.schemas.v2 import Integration

from ..configurations import InReachWebhookPayload
from ..inreach import InreachEvent


@pytest.fixture
def gundi_api_data_received_response():
    return [
        {
            "object_id": "efebe106-3c50-446b-9c98-0b9b503fc922",
            "created_at": "2023-11-16T19:59:55.612864Z"
        }
    ]


@pytest.fixture
def mock_send_observations_to_gundi(gundi_api_data_received_response):
    return AsyncMock(
        return_value=gundi_api_data_received_response
    )


@pytest.fixture
def mock_send_messages_to_gundi(gundi_api_data_received_response):
    return AsyncMock(
        return_value=gundi_api_data_received_response
    )


@pytest.fixture
def inreach_integration_with_webhook():
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
                        "required": ["username", "password"],
                        "properties": {
                            "password": {
                                "type": "string",
                                "title": "Password",
                                "format": "password",
                                "writeOnly": True,
                                "description": "Password for inReach account"
                            },
                            "username": {
                                "type": "string",
                                "title": "Username",
                                "description": "Username for inReach account"
                            }
                        },
                        "definitions": {},
                        "is_executable": True
                    },
                    "ui_schema": {
                        "ui:order": ["username", "password"]
                    }
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
                        "definitions": {}
                    },
                    "ui_schema": {}
                }],
                "webhook": {
                    "id": "c091520b-c8c4-4c55-b4ab-1467f0ded0f3",
                    "name": "Inreach Webhook",
                    "value": "inreach_webhook",
                    "description": "Webhook Integration with Inreach",
                    "webhook_schema": {
                        "type": "object",
                        "title": "InReachWebhookConfig",
                        "properties": {
                            "include_messages": {
                                "type": "boolean",
                                "title": "Include Messages",
                                "default": True
                            },
                            "include_observations": {
                                "type": "boolean",
                                "title": "Include Observations",
                                "default": True
                            }
                        },
                        "definitions": {}
                    },
                    "ui_schema": {
                        "ui:order": ["include_messages", "include_observations"]
                    }
                }
            },
            "base_url": "",
            "enabled": True,
            "owner": {
                "id": "a91b400b-482a-4546-8fcb-ee42b01deeb6",
                "name": "Test Org",
                "description": ""
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
            "webhook_configuration": {
                "id": "2a102791-e85c-4e61-a859-3e1585d2f79b",
                "integration": "5328877d-2a65-4654-bc18-5b5a406803f8",
                "webhook": {
                    "id": "c091520b-c8c4-4c55-b4ab-1467f0ded0f3",
                    "name": "Inreach Webhook",
                    "value": "inreach_webhook"
                },
                "data": {
                    "include_messages": True,
                    "include_observations": True
                }
            },
            "default_route": None,
            "additional": {},
            "status": "healthy",
            "status_details": "No issues detected"
        }
    )

@pytest.fixture
def inreach_event_as_dict():
    """
        Sample InReach event data based on the IPC Outbound documentation.
        https://developer.garmin.com/inReach/IPC_Outbound.pdf
    """
    return {
        "imei": "0123456789",
        "messageCode": 3,
        "freeText": "On my way.",
        "timeStamp": 1323784607376,
        "addresses": [{
            "address": "2075752244"
        },
            {
                "address": "product.support@garmin.com"
            }
        ],
        "point": {
            "latitude": 43.8078653812408,
            "longitude": -70.1636695861816,
            "altitude": 45,
            "gpsFix": 2,
            "course": 45,
            "speed": 50
        },
        "status": {
            "autonomous": 0,
            "lowBattery": 1,
            "intervalChange": 0,
            "resetDetected": 0
        }
    }


@pytest.fixture
def inreach_event(inreach_event_as_dict):
    return InreachEvent(
        **inreach_event_as_dict
    )


@pytest.fixture
def inreach_webhook_request_payload(inreach_event_as_dict):
    """
        Sample InReach webhook event payload based on the IPC Outbound documentation.
        https://developer.garmin.com/inReach/IPC_Outbound.pdf
    """
    return InReachWebhookPayload(
        Version="2.0",
        Events=[inreach_event_as_dict]
    )
