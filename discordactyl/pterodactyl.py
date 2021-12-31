import asyncio
import json
import logging
import typing
from urllib.parse import urlparse

import backoff
import httpx
import websockets


class PterodactylClient:
    api_key: str = None
    closed: str = True
    events: dict = []
    httpx_client: httpx.AsyncClient = None
    panel_url: str = None
    server_id: str = None
    websocket: websockets.WebSocketClientProtocol = None

    def __init__(self, panel_url: str, api_key: str, server_id: str):
        self.api_key = api_key
        self.server_id = server_id

        # Normalize panel url to https://example.com
        panel_url_parsed = urlparse(panel_url)
        self.panel_url = f"{panel_url_parsed.scheme}://{panel_url_parsed.netloc}"

    async def _authorize(self, auth_token: typing.Optional[str] = None):
        if not auth_token:
            auth_token, _ = await self._fetch_websocket_credentials()

        await self.send("auth", auth_token)

    @backoff.on_exception(backoff.expo, Exception)
    async def _connect(self) -> None:
        try:
            auth_token, websocket_url = await self._fetch_websocket_credentials()
            self.websocket = await websockets.connect(websocket_url, origin=self.panel_url)

            await self._authorize(auth_token)
            await self._consumer_handler(self.websocket)

        # Raise exception, triggering a backoff, only if not closing
        except Exception as e:
            if self.closed:
                logging.debug(f'Exception occured in connection handler after closure ({e})')
            else:
                raise e

    async def _consumer_handler(self, websocket: websockets.WebSocketClientProtocol) -> None:
        async for message in self.websocket:
            object = json.loads(message)
            logging.debug(f'recv: {object}')

            if object['event'] in ['token expiring', 'token expired']:
                await self._authorize()

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
        resp = await self.httpx_client.get(f"/api/client/servers/{self.server_id}/websocket")
        resp.raise_for_status()

        json = resp.json()
        logging.debug(f"Websocket credentials fetched: {json['data']}")
        return json["data"]["token"], json["data"]["socket"]

    async def close(self) -> None:
        if self.closed:
            raise RuntimeError('Client is already closed')

        self.closed = True
        await self.httpx_client.aclose()

        try:
            await self.websocket.close()
        except Exception as e:
            logging.debug(f"Could not close websocket ({e})")

    def on(self, event: str) -> typing.Callable:
        def decorator(func: typing.Callable) -> None:
            self.events.append((event, func))

        return decorator

    async def send(self, event: str, data: str = None) -> None:
        object = {"event": event, "args": [data]}
        logging.debug(f'sent: {object}')

        if self.closed:
            raise RuntimeError('Client is closed')

        await self.websocket.send(json.dumps(object))

    async def start(self) -> None:
        try:
            if not self.closed:
                raise RuntimeError('Client is already running')

            headers = {"authorization": f"Bearer {self.api_key}"}
            self.httpx_client = httpx.AsyncClient(base_url=self.panel_url, headers=headers)

            self.closed = False
            await self._connect()

        except asyncio.CancelledError:
            await self.close()
