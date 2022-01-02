import asyncio
import json
import logging
import typing
from urllib.parse import urlparse

import backoff
import httpx
import websockets

from .utils import CustomAdapter, fatal_http_code

logger = logging.getLogger(__name__)


class InvalidState(RuntimeError):
    pass


class TokenExpired(Exception):
    pass


class PterodactylClient:
    api_key: str = None
    closed: str = True
    events: dict = []
    httpx_client: httpx.AsyncClient = None
    panel_url: str = None
    server_id: str = None
    websocket: websockets.WebSocketClientProtocol = None

    def __init__(self, *, panel_url: str, api_key: str, server_id: str):
        self.api_key = api_key
        self.server_id = server_id

        # Normalize panel url to https://example.com
        panel_url_parsed = urlparse(panel_url)
        self.panel_url = f"{panel_url_parsed.scheme}://{panel_url_parsed.netloc}"

        self.log = CustomAdapter(logger, {'connid': self.server_id})

    async def _authorize(self, auth_token: typing.Optional[str] = None):
        if not auth_token:
            self.log.info(f'Updating authorization')
            auth_token, _ = await self._fetch_websocket_credentials()

        else:
            self.log.info(f'Sending authorization')

        await self.send("auth", auth_token)

    @backoff.on_exception(backoff.expo, httpx.HTTPError, giveup=fatal_http_code)
    @backoff.on_exception(backoff.expo, websockets.WebSocketException)
    @backoff.on_exception(backoff.expo, TokenExpired)
    async def _connect(self) -> None:
        try:
            auth_token, websocket_url = await self._fetch_websocket_credentials()
            self.websocket = await websockets.connect(websocket_url, origin=self.panel_url)
            self.log.info(f'Connected to websocket')

            await self._authorize(auth_token)
            await self._consumer_handler(self.websocket)

        # Raise exception, triggering a backoff, only if not closing
        except Exception as e:
            if self.closed:
                self.log.warning(f'Exception occured in connection handler after closure ({e})')
            else:
                raise e

    async def _consumer_handler(self, websocket: websockets.WebSocketClientProtocol) -> None:
        self.log.info(f'Ready to receive messages')

        async for message in self.websocket:
            object = json.loads(message)
            self.log.debug(f'recv: {object}')

            if object['event'] == 'auth success':
                self.log.info('Authorization successful')

            if object['event'] == 'token expiring':
                self.log.info(f'Server sent prompt for reauthorization')
                await self._authorize()

            # We could reauthorize here, but we want to backoff just in case-- this should never happen in normal use.
            if object['event'] == 'token expired':
                raise TokenExpired('Server sent notice that token expired')

            for event_name, function in self.events:
                if event_name == object['event']:

                    # Most events return addtional data, but some do not.
                    if 'args' in object:
                        data = object['args'][0]

                        # Some events may return valid json instead, such as 'stats', so we attempt to parse it.
                        try:
                            data = json.loads(data)
                        except ValueError:
                            pass

                        await function(data)

                    else:
                        await function()

    async def _fetch_websocket_credentials(self) -> typing.Tuple[str, str]:
        self.log.info(f'Fetching websocket credentials')

        resp = await self.httpx_client.get(f"/api/client/servers/{self.server_id}/websocket")
        resp.raise_for_status()

        json = resp.json()
        return json["data"]["token"], json["data"]["socket"]

    async def close(self) -> None:
        if self.closed:
            raise InvalidState('Client is already closed')

        self.log.info(f'Closing client')
        self.closed = True

        try:
            await self.websocket.close()
        except Exception as e:
            self.log.warning(f"Could not close websocket ({e})")

        await self.httpx_client.aclose()

    def on(self, event: str) -> typing.Callable:
        def decorator(func: typing.Callable) -> None:
            self.events.append((event, func))

        return decorator

    async def send(self, event: str, data: str = None) -> None:
        object = {"event": event, "args": [data]}
        self.log.debug(f'sent: {object}')

        if self.closed:
            raise InvalidState('Client is closed')

        await self.websocket.send(json.dumps(object))

    async def start(self) -> None:
        try:
            if not self.closed:
                raise InvalidState('Client is already running')

            headers = {"authorization": f"Bearer {self.api_key}"}
            self.httpx_client = httpx.AsyncClient(base_url=self.panel_url, headers=headers)

            self.closed = False
            await self._connect()

        except asyncio.CancelledError:
            await self.close()

        except Exception as e:
            raise e
