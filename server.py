import asyncio
import sys
import random
import logging

logging.basicConfig(level=logging.INFO, format="[Server] %(message)s")
logger = logging.getLogger(__name__)

ERROR_RATE = 0.1


async def handle_client(data, reader, writer):
    message = data.decode('utf-8', errors='ignore')
    addr = writer.get_extra_info('peername')
    logger.info(f"Received request from {addr}")

    if random.random() < ERROR_RATE:
        logger.warning("Simulating error.")
        response = (
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/plain\r\n"
            "Connection: close\r\n\r\n"
            "Simulated Server Error\n"
        )
        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Connection: close\r\n\r\n"
        "Hello from the server!\n"
    )
    writer.write(response.encode('utf-8'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def health_handler(reader, writer):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Connection: close\r\n\r\n"
        "OK"
    )
    writer.write(response.encode('utf-8'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def dispatcher(reader, writer):
    data = await reader.read(1024)
    if b"health" in data.lower():
        await health_handler(reader, writer)
    else:
        await handle_client(data, reader, writer)


async def mock_backend_server(host='127.0.0.1', port=9000, error_rate=0.1):
    global ERROR_RATE
    ERROR_RATE = error_rate

    server = await asyncio.start_server(dispatcher, host, port)
    addr = server.sockets[0].getsockname()
    logger.info(f"Running on {addr} with ERROR_RATE={ERROR_RATE:.2f}")

    async with server:
        await server.serve_forever()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    error_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    asyncio.run(mock_backend_server(port=port, error_rate=error_rate))


if __name__ == "__main__":
    main()