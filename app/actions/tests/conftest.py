import pytest
import datetime
from gundi_core.schemas.v2.inreach import InReachIPCMessage


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
