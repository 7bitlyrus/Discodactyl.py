import asyncio
import json
import logging
import typing
from urllib.parse import urlparse

import httpx
import websockets


class PterodactylClient:
    httpx_client: httpx.AsyncClient = None
    panel_url: str = None
    server_id: str = None
    websocket: websockets.WebSocketClientProtocol = None

    def __init__(self, panel_url: str, api_key: str, server_id: str):
        self.server_id = server_id

        # Normalize panel url to https://example.com
        panel_url_parsed = urlparse(panel_url)
        self.panel_url = f"{panel_url_parsed.scheme}://{panel_url_parsed.netloc}"

        self.httpx_client = httpx.AsyncClient(base_url=self.panel_url, headers={"authorization": f"Bearer {api_key}"})

    async def start(self) -> None:
        auth_token, websocket_url = await self._fetch_websocket_credentials()
        self.websocket = await websockets.connect(websocket_url, origin=self.panel_url)

        await self._authorize(auth_token)
        await self._consumer_handler(self.websocket)

    async def _authorize(self, auth_token: typing.Optional[str] = None):
        if not auth_token:
            auth_token, _ = await self._fetch_websocket_credentials()

        await self.send("auth", [auth_token])

    async def _consumer_handler(self, websocket: websockets.WebSocketClientProtocol) -> None:
        while True:
            # Prevent blocking by using timeouts and sleep.
            # "Canceling recv() is safe. There’s no risk of losing the next message. The next invocation of recv() will
            # return it."
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
            except asyncio.exceptions.TimeoutError:
                continue
            finally:
                await asyncio.sleep(0.1)

            object = json.loads(message)
            print(f'[ws] received: {object}')

            if object['event'] in ['token expiring', 'token expired']:
                await self._authorize()

    async def _fetch_websocket_credentials(self) -> typing.Tuple[str, str]:
        resp = await self.httpx_client.get(f"/api/client/servers/{self.server_id}/websocket")
        resp.raise_for_status()

        json = resp.json()
        return json["data"]["token"], json["data"]["socket"]

    async def send(self, event: str, args: list) -> None:
        object = {"event": event, "args": args}
        print(f'[ws] sent: {object}')

        await self.websocket.send(json.dumps(object))
