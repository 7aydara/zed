"""
Zed Voice Assistant — MCP Client Stub
Clean async interface for future MCP server connection.
Replace the stub implementations with real MCP SDK calls when ready.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class MCPClient:
    """
    Minimal Model Context Protocol client.

    Exposes an async interface so it can be wired to a real MCP server
    later with minimal refactoring.  All methods currently return safe
    stub values.
    """

    def __init__(self) -> None:
        self._connected: bool = False
        self._server_url: str | None = None

    # ── properties ──────────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        """Whether the client is currently connected to an MCP server."""
        return self._connected

    @property
    def server_url(self) -> str | None:
        """The URL of the MCP server, if connected."""
        return self._server_url

    # ── lifecycle ───────────────────────────────────────────────────────────

    async def connect(self, server_url: str) -> None:
        """
        Connect to an MCP server.

        Parameters
        ----------
        server_url : str
            WebSocket or HTTP URL of the MCP server.
        """
        log.info("MCP connect requested to %s (stub — not implemented)", server_url)
        # TODO: Replace with real connection logic
        # Example:
        #   self._session = await mcp.ClientSession(server_url)
        #   await self._session.initialize()
        self._server_url = server_url
        self._connected = False  # stays False until real implementation

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        log.info("MCP disconnect requested (stub — not implemented)")
        # TODO: Replace with real disconnection logic
        self._connected = False
        self._server_url = None

    # ── tool interface ──────────────────────────────────────────────────────

    async def call_tool(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Call a tool on the connected MCP server.

        Parameters
        ----------
        name : str
            The tool name to invoke (e.g. ``"web_search"``).
        args : dict, optional
            Arguments to pass to the tool.

        Returns
        -------
        dict
            The tool's response payload.
        """
        if not self._connected:
            log.warning("call_tool('%s') called but MCP is not connected", name)
            return {
                "status": "not_connected",
                "message": "MCP server not configured. Wire up a real server in mcp_client.py.",
            }

        # TODO: Replace with real tool call
        # Example:
        #   result = await self._session.call_tool(name, arguments=args or {})
        #   return {"status": "ok", "content": result.content}
        log.info("MCP call_tool('%s', %s) — stub", name, args)
        return {"status": "stub", "tool": name, "args": args}

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List all tools available on the connected MCP server.

        Returns
        -------
        list[dict]
            Each dict contains at least ``name`` and ``description`` keys.
        """
        if not self._connected:
            log.warning("list_tools() called but MCP is not connected")
            return []

        # TODO: Replace with real listing
        # Example:
        #   response = await self._session.list_tools()
        #   return [{"name": t.name, "description": t.description} for t in response.tools]
        return []
