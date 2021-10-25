import asyncio
import websockets


class PterodactylClient:
    websocket = None

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.establish())

    async def establish(self):
        url = "wss://can1.bennystudios.com:8080/api/servers/8ee05379-42b6-484f-9b8e-56df088648d9/ws"
        headers = {"origin": "https://panel.bennystudios.com"}

        async with websockets.connect(url, extra_headers=headers) as websocket:
            await self.consumer_handler(websocket)

    async def consumer_handler(self, websocket):
        async for message in websocket:
            print(f"=> {message}")


PterodactylClient()