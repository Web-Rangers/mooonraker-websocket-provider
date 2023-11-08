import asyncio
import json
from asyncio import Task
from typing import AsyncIterator, NamedTuple, Dict, Any, Optional

import websockets
from aiohttp import web
from websockets import WebSocketClientProtocol

from src.env import MOONRAKER_HOST, MOONRAKER_WEBSOCKET_PROVIDER_PORT, TEMP_UPDATE_TIME


class JsonRpcResponse(NamedTuple):
    jsonrpc: str
    method: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]


class JsonRpcRequestMessageWrapper:
    def __init__(self, req: 'JsonRpcRequest', websocket_connection: WebSocketClientProtocol) -> None:
        self._req = req
        self._conn = websocket_connection
        self._task: Task

    async def __aenter__(self):
        self._task = asyncio.create_task(self.consume_websocket_request_iterator(self._conn))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._task.cancel()

    async def consume_websocket_request_iterator(self, websocket_connection: WebSocketClientProtocol) -> None:
        async for req in iterate_websocket_request(websocket_connection, json.dumps(self._req._asdict())):
            print(req)

    async def iterate_messages(self) -> AsyncIterator[JsonRpcResponse]:
        message_data: Dict[str, Any]
        async for message in iterate_websocket_response(self._conn):
            message_data = json.loads(message)
            if message_data.get("id", -1) == self._req.id:
                print(message_data)
                yield JsonRpcResponse(
                    jsonrpc=message_data.get("jsonrpc"),
                    method=message_data.get("method", None),
                    params=message_data.get("params", None),
                    result=message_data.get("result", None)
                )


class JsonRpcRequest(NamedTuple):
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: int


async def iterate_websocket_request(websocket_connection: WebSocketClientProtocol, request: str) -> AsyncIterator[str]:
    while websocket_connection.open:
        yield await websocket_connection.send(request)
        await asyncio.sleep(TEMP_UPDATE_TIME)


async def iterate_websocket_response(websocket_connection: WebSocketClientProtocol) -> AsyncIterator[str]:
    while websocket_connection.open:
        yield await websocket_connection.recv()


async def handle_hi(request: web.Request) -> web.Response[str]:
    return web.Response(body="HI")


async def main():
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
                print(f"Received from server: {message}")

    app = web.Application()
    app.add_routes([
        web.get("/", handle_hi),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=MOONRAKER_WEBSOCKET_PROVIDER_PORT)
    await site.start()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
