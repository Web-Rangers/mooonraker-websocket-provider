import asyncio
import json
import time
from typing import AsyncIterator, NamedTuple, Dict, Any, Optional

import websockets
from fastapi import FastAPI, WebSocket
from starlette.responses import HTMLResponse
from websockets import WebSocketClientProtocol

MOONRAKER_HOST = 'ws://192.168.0.105/websocket'
TEMPERATURE_REQUEST = json.dumps({
            "jsonrpc": "2.0",
            "method": "server.temperature_store",
            "params": {
                "include_monitors": False
            },
            "id": 1
        });


class JsonRpcResponse(NamedTuple):
    jsonrpc: str
    method: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]


class JsonRpcRequest(NamedTuple):
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: int

    async def iterate_messages(self, websocket_connection:WebSocketClientProtocol) -> AsyncIterator[JsonRpcResponse]:
        message_data: Dict[str, Any]
        async for message in iterate_websocket_request(websocket_connection, json.dumps(self._asdict())):
            message_data = json.loads(message)
            print(message_data)
            if message_data.get("id", -1) == self.id:
                yield JsonRpcResponse(
                    jsonrpc=message_data.get("jsonrpc"),
                    method=message_data.get("method", None),
                    params=message_data.get("params", None),
                    result=message_data.get("result", None)
                )


app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.get("/")
async def api_endpoint():
    return HTMLResponse()


async def iterate_websocket_request(websocket_connection:WebSocketClientProtocol, request:str)->AsyncIterator[str]:
    while True:
        await websocket_connection.send(request)
        yield await websocket_connection.recv()
        time.sleep(1)


async def main():
    async with websockets.connect(MOONRAKER_HOST) as websocket_connection:
        async for message in JsonRpcRequest(
            jsonrpc="2.0",
            method="server.temperature_store",
            params={
                "include_monitors": False
            },
            id=1
        ).iterate_messages(websocket_connection):
            print(f"Received from server: {message}")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
