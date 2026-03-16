from __future__ import annotations

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_query(question: str) -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "query_documents",
                {"question": question},
            )
            _print_result(result)

async def run_list_documents() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_documents", {})
            _print_result(result)


def _print_result(result: object) -> None:
    if hasattr(result, "structuredContent") and result.structuredContent:
        print(json.dumps(result.structuredContent, indent=2))
        return

    if hasattr(result, "content") and result.content:
        for item in result.content:
            text = getattr(item, "text", None)
            if text:
                print(text)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python3 -m src.client query "Your question here"')
        print("   or: python3 -m src.client list")
        raise SystemExit(1)

    command = sys.argv[1]

    if command == "list":
        asyncio.run(run_list_documents())
        return

    if command == "query" and len(sys.argv) >= 3:
        question = " ".join(sys.argv[2:])
        asyncio.run(run_query(question))
        return

    print('Usage: python3 -m src.client query "Your question here"')
    print("   or: python3 -m src.client list")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
