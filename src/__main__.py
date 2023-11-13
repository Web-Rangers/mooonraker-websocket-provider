import asyncio

import websockets
from aiohttp import web

from src.abstract.models import JsonRpcRequest
from src.env import MOONRAKER_HOST, MOONRAKER_WEBSOCKET_PROVIDER_PORT
from src.json_rpc_request_message_wrapper import JsonRpcRequestMessageWrapper
from src.mapper.temperature import map_temperature_message


async def handle_hi(request: web.Request) -> web.Response[str]:
    return web.Response(body="HI")


async def main():
    app = web.Application()
    app.add_routes([
        web.get("/", handle_hi),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port=MOONRAKER_WEBSOCKET_PROVIDER_PORT)
    await site.start()

    request_ = JsonRpcRequest(
            jsonrpc="2.0",
            method="server.temperature_store",
            params={
                "include_monitors": False
            },
            id=1
        )
    async with websockets.connect(MOONRAKER_HOST) as websocket_connection:
        async with JsonRpcRequestMessageWrapper(request_, websocket_connection) as messages_manager:
            async for message in messages_manager.iterate_messages():
                temp_message = map_temperature_message(message)
                print(f"Received from server: {temp_message.extruder}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
