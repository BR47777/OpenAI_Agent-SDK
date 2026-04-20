"""
a2a/client.py
A2A client — sends tasks to the server and polls until completion.

Usage:
  python -m a2a.client "Review all Python files for bugs and security issues."
"""

from __future__ import annotations
import asyncio
import sys
import httpx
from a2a.types import Message


BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 2.0


async def get_agent_card(client: httpx.AsyncClient) -> dict:
    r = await client.get(f"{BASE_URL}/.well-known/agent.json")
    r.raise_for_status()
    return r.json()


async def send_task(client: httpx.AsyncClient, message: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tasks/send",
        "params": {
            "message": {"role": "user", "content": message}
        },
    }
    r = await client.post(BASE_URL, json=payload)
    r.raise_for_status()
    return r.json()["result"]


async def get_task(client: httpx.AsyncClient, task_id: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tasks/get",
        "params": {"id": task_id},
    }
    r = await client.post(BASE_URL, json=payload)
    r.raise_for_status()
    return r.json()["result"]


async def run(message: str) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        card = await get_agent_card(client)
        print(f"Connected to: {card['name']} — {card['description']}")

        task = await send_task(client, message)
        task_id = task["id"]
        print(f"Task submitted: {task_id}")

        while True:
            task = await get_task(client, task_id)
            state = task["state"]
            print(f"  State: {state}")

            if state in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(POLL_INTERVAL)

        if state == "completed":
            for msg in task["messages"]:
                if msg["role"] == "agent":
                    print("\n── Agent Response ──")
                    print(msg["content"])
        else:
            print(f"Task failed: {task.get('error')}")


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Review all Python files for bugs and security issues."
    asyncio.run(run(msg))
