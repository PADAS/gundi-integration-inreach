import httpx
import pytest
import respx


from ..inreach_client import (
    InReachClient,
    InReachAuthenticationError,
    InReachServiceUnreachable,
    InReachInternalError,
)


@pytest.mark.asyncio
async def test_inreach_client_pingback_success():
    async with respx.mock(assert_all_called=True) as mock:
        mock.post("/IPCInbound/V1/Pingback.svc/PingbackRequest").respond(
            status_code=httpx.codes.OK,
            text=""
        )

        async with InReachClient() as client:
            response = await client.pingback(username="test_user", password="test_pass")
            assert response == {}


@pytest.mark.asyncio
async def test_inreach_client_pingback_bad_credentials():
    async with respx.mock(assert_all_called=True) as mock:
        mock.post("/IPCInbound/V1/Pingback.svc/PingbackRequest").respond(
            status_code=httpx.codes.FORBIDDEN,
            json={
                "Code": 3,
                "Description": "",
                "IMEI": None,
                "Message": "Invalid username or password",
                "URL": "https:\/\/prod-eur-inreach-web\/ipcinbound\/V1\/Pingback.svc\/PingbackRequest"
            }
        )

        async with InReachClient() as client:
            # Check that the right exception is raised
            with pytest.raises(InReachAuthenticationError) as exc:
                await client.pingback(username="wrong_user", password="wrong_pass")
            # Check that the server response is captured in the exception
            error = exc.value
            assert error.response
            assert error.response.status_code == httpx.codes.FORBIDDEN


@pytest.mark.asyncio
async def test_inreach_client_pingback_service_unreachable():
    async with respx.mock(assert_all_called=True) as mock:
        mock.post("/IPCInbound/V1/Pingback.svc/PingbackRequest").respond(
            status_code=httpx.codes.SERVICE_UNAVAILABLE,
            text="Service Unavailable"
        )

        async with InReachClient() as client:
            # Check that the right exception is raised
            with pytest.raises(InReachServiceUnreachable) as exc:
                await client.pingback(username="test_user", password="test_pass")
            # Check that the server response is captured in the exception
            error = exc.value
            assert error.response
            assert error.response.status_code == httpx.codes.SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_inreach_client_pingback_internal_error():
    async with respx.mock(assert_all_called=True) as mock:
        mock.post("/IPCInbound/V1/Pingback.svc/PingbackRequest").respond(
            status_code=httpx.codes.INTERNAL_SERVER_ERROR,
            text="Internal Server Error"
        )

        async with InReachClient() as client:
            # Check that the right exception is raised
            with pytest.raises(InReachInternalError) as exc:
                await client.pingback(username="test_user", password="test_pass")
            # Check that the server response is captured in the exception
            error = exc.value
            assert error.response
            assert error.response.status_code == httpx.codes.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_inreach_client_send_messages_success(inreach_ipc_message):
    async with respx.mock(assert_all_called=True) as mock:
        mock.post("/IPCInbound/V1/Messaging.svc/Message").respond(
            status_code=httpx.codes.OK,
            json={}  # Don't know the exact response schema
        )

        async with InReachClient() as client:
            response = await client.send_messages(
                ipc_messages=[inreach_ipc_message],
                username="test_user",
                password="test_pass"
            )
            assert response == {}

