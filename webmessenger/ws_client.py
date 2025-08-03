import asyncio
import websockets


async def hello():
    uri = "ws://localhost:5000"
    async with websockets.connect(uri) as websocket:
        name = '{"username": "User", "message": "Hello, World!"}'

        await websocket.send(name)
        print(f">>> {name}")

        # greeting = await websocket.recv()
        # print(f"<<< {greeting}")
        await websocket.close()


if __name__ == "__main__":
    asyncio.run(hello())
