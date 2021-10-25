import asyncio
import json
import typing
from urllib.parse import urlparse

import httpx
import websockets


class PterodactylClient:
    loop: asyncio.AbstractEventLoop = None
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
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._establish())

    async def _establish(self) -> None:
        _, websocket_url = await self._fetch_websocket_credentials()
        self.websocket = await websockets.connect(websocket_url, extra_headers={"origin": self.panel_url})

        await self._authorize()
        await self._consumer_handler(self.websocket)

    async def _authorize(self):
        auth_token, _ = await self._fetch_websocket_credentials()
        await self.send("auth", [auth_token])

    async def _consumer_handler(self, websocket: websockets.WebSocketClientProtocol) -> None:
        async for message in websocket:
            # Among the many todos is resending auth token
            print(f"=> {message}")

    async def _fetch_websocket_credentials(self) -> typing.Tuple[str, str]:
        resp = await self.httpx_client.get(f"/api/client/servers/{self.server_id}/websocket")
        resp.raise_for_status()

        json = resp.json()
        return json["data"]["token"], json["data"]["socket"]

    async def send(self, event: str, args: list) -> None:
        object = {"event": event, "args": args}
        await self.websocket.send(json.dumps(object))
