import asyncio
import json
from asyncio import Task
from typing import AsyncIterator, Any, Dict, Optional

from websockets import WebSocketClientProtocol

from src.abstract.models import JsonRpcRequest, JsonRpcResponse
from src.env import TEMP_UPDATE_TIME


class JsonRpcRequestMessageWrapper:
    def __init__(self, req: 'JsonRpcRequest', websocket_connection: WebSocketClientProtocol) -> None:
        self._req = req
        self._request_able_str = json.dumps(req._asdict())
        self._conn = websocket_connection
        self._task: Task

    async def __aenter__(self):
        self._task = asyncio.create_task(self._consume_websocket_request_iterator())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._task.cancel()

    async def _iterate_websocket_request(self) -> AsyncIterator[str]:
        while self._conn.open:
            yield await self._conn.send(self._request_able_str)
            await asyncio.sleep(TEMP_UPDATE_TIME)

    async def _iterate_websocket_response(self) -> AsyncIterator[str]:
        while self._conn.open:
            yield await self._conn.recv()

    async def _consume_websocket_request_iterator(self) -> None:
        async for req in self._iterate_websocket_request():
            pass

    async def iterate_messages(self) -> AsyncIterator[JsonRpcResponse]:
        message_data: Dict[str, Any]
        result: Optional[Dict[str, Any]]
        async for message in self._iterate_websocket_response():
            message_data = json.loads(message)
            if message_data.get("id", -1) == self._req.id:
                yield JsonRpcResponse(
                    jsonrpc=message_data.get("jsonrpc"),
                    method=message_data.get("method", None),
                    params=message_data.get("params", None),
                    result=message_data.get("result", None)
                )
