from typing import List, Optional

import httpx
from gundi_core.schemas.v2 import InReachIPCMessage


class InReachClientError(Exception):
    pass


class InReachBadCredentials(InReachClientError):
    pass


class InReachServiceUnreachable(InReachClientError):
    pass


class InReachInternalError(InReachClientError):
    pass


class InReachClient:
    DEFAULT_CONNECT_TIMEOUT_SECONDS = 10
    DEFAULT_DATA_TIMEOUT_SECONDS = 60

    def __init__(
            self,
            api_url: str = "https://eur-enterprise.inreach.garmin.com",
            connect_timeout: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
            data_timeout: float = DEFAULT_DATA_TIMEOUT_SECONDS,
            username: Optional[str] = None, password: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.api_url = api_url
        self.connect_timeout = connect_timeout
        self.data_timeout = data_timeout
        session_kwargs = {
            "base_url": self.api_url,
            "timeout": httpx.Timeout(
                self.data_timeout,
                connect=self.connect_timeout
            )
        }
        if username and password:
            session_kwargs["auth"] = (self.username, self.password)
        self.session = httpx.AsyncClient(**session_kwargs)

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.aclose()

    async def _call_api(self, endpoint: str, method: str = "GET", data: dict = None, **kwargs):
        """
        Make an API call to the InReach service.
        """
        url = f"{self.api_url}/{endpoint}"
        extra = {}
        if (username := kwargs.get("username")) and (password := kwargs.get("password")):
            extra["auth"] = (username, password)
        try:
            if method == "GET":
                response = await self.session.get(url, **extra)
            elif method == "POST":
                response = await self.session.post(url, json=data, **extra)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise InReachBadCredentials("Invalid username or password.")
            elif e.response.status_code in [502, 503, 504]:
                raise InReachServiceUnreachable("InReach service is currently unavailable.")
            elif e.response.status_code == 500:
                raise InReachInternalError("Internal server error from InReach service.")
            else:
                raise InReachClientError(f"Bad status: {e.response.status_code}, {e.response.text}")
        except httpx.RequestError as e:
            raise InReachServiceUnreachable(f"Failed to connect to InReach service: {type(e).__name__}: {str(e)}")
        except Exception as e:
            raise InReachClientError(f"{type(e).__name__}: {str(e)}")

    async def pingback(self, username: str = None, password: str = None):
        """
        Test the connection to the InReach API.
        """
        return await self._call_api(
            endpoint="IPCInbound/V1/Pingback.svc/PingbackRequest",
            method="POST",
            data={},
            username=username, password=password,
        )

    async def send_messages(self, ipc_messages: List[InReachIPCMessage], username: str = None, password: str = None):
        """
        Send messages to the InReach service.
        """
        return await self._call_api(
            endpoint="IPCInbound/V1/Messaging.svc/Message",
            method="POST",
            data={"Messages": ipc_messages},
            username=username, password=password
        )
