"""Tests for sendsprint/mcp/server.py (Sprint 3 issue #11)."""

from __future__ import annotations

import json
from pathlib import Path

from sendsprint.mcp import McpServer, McpTool, build_default_server


def _request(method: str, *, rpc_id: int = 1, params: dict | None = None) -> dict:
    req: dict = {"jsonrpc": "2.0", "id": rpc_id, "method": method}
    if params is not None:
        req["params"] = params
    return req


class TestHandshake:
    def test_initialize_returns_protocol_version(self) -> None:
        server = build_default_server()
        resp = server.handle(_request("initialize"))
        assert resp is not None
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert resp["result"]["serverInfo"]["name"] == "sendsprint"

    def test_initialized_notification_returns_none(self) -> None:
        server = build_default_server()
        resp = server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert resp is None


class TestToolsList:
    def test_lists_default_tools(self) -> None:
        server = build_default_server()
        resp = server.handle(_request("tools/list"))
        assert resp is not None
        names = [t["name"] for t in resp["result"]["tools"]]
        assert "sendsprint_detect_tech" in names
        assert "sendsprint_version" in names

    def test_each_tool_has_schema(self) -> None:
        server = build_default_server()
        resp = server.handle(_request("tools/list"))
        for tool in resp["result"]["tools"]:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"


class TestToolsCall:
    def test_version_call_returns_version(self) -> None:
        server = build_default_server()
        resp = server.handle(
            _request(
                "tools/call",
                params={"name": "sendsprint_version", "arguments": {}},
            )
        )
        assert resp["result"]["isError"] is False
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert "version" in payload

    def test_detect_tech_call(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18.0.0"}}')
        server = build_default_server()
        resp = server.handle(
            _request(
                "tools/call",
                params={
                    "name": "sendsprint_detect_tech",
                    "arguments": {"repo": str(tmp_path)},
                },
            )
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert "react" in payload["techs"]

    def test_detect_tech_missing_arg_is_isError(self) -> None:
        server = build_default_server()
        resp = server.handle(
            _request("tools/call", params={"name": "sendsprint_detect_tech", "arguments": {}})
        )
        # Standard JSON-RPC error path (-32603) since handler raises ValueError.
        assert "error" in resp
        assert resp["error"]["code"] == -32603

    def test_unknown_tool_returns_jsonrpc_error(self) -> None:
        server = build_default_server()
        resp = server.handle(_request("tools/call", params={"name": "nope", "arguments": {}}))
        assert resp["error"]["code"] == -32601
        assert "unknown tool" in resp["error"]["message"]


class TestUnknownMethod:
    def test_returns_method_not_found(self) -> None:
        server = build_default_server()
        resp = server.handle(_request("totally_made_up"))
        assert resp["error"]["code"] == -32601


class TestCustomTool:
    def test_register_and_call_custom_tool(self) -> None:
        server = McpServer()
        server.register(
            McpTool(
                name="echo",
                description="Echo back",
                input_schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
                handler=lambda args: {"echoed": args["text"]},
            )
        )
        resp = server.handle(
            _request(
                "tools/call",
                params={"name": "echo", "arguments": {"text": "hi"}},
            )
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert payload == {"echoed": "hi"}
