from typing import NamedTuple, Optional, Dict, Any, List


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

