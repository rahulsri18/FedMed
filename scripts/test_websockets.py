import asyncio
import websockets


async def main():
    uri = "ws://127.0.0.1:8000/ws/telemetry"

    async with websockets.connect(uri) as websocket:
        for _ in range(5):
            message = await websocket.recv()
            print("\n--- TELEMETRY ---")
            print(message)


asyncio.run(main())