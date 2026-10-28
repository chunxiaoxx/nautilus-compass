"""Tiny user-space TCP relay: 0.0.0.0:LISTEN -> 127.0.0.1:TARGET.

Lets WSL (mirrored mode) reach the loopback-only xray proxy on the Windows host.
No admin needed (binds a high port on 0.0.0.0). Run with the Windows Python.
"""
import asyncio
import sys

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 52889
TARGET_HOST = "127.0.0.1"
TARGET_PORT = 52888


async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle(client_reader, client_writer):
    try:
        target_reader, target_writer = await asyncio.open_connection(TARGET_HOST, TARGET_PORT)
    except Exception as e:
        client_writer.close()
        return
    await asyncio.gather(
        pipe(client_reader, target_writer),
        pipe(target_reader, client_writer),
    )


async def main():
    server = await asyncio.start_server(handle, LISTEN_HOST, LISTEN_PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"relay listening on {addrs} -> {TARGET_HOST}:{TARGET_PORT}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
