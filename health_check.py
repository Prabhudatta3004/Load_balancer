import asyncio
import time
import aiohttp


async def check_server(server, timeout=2):
    """
    Sends a health check request to a server.

    Args:
        server (Server): The server instance.
        timeout (int): Timeout for the health check request.

    Returns:
        tuple: (status, response_time). Status is 'UP' or 'DOWN', response_time is the measured latency.
    """
    url = f"http://{server.host}:{server.port}/health"
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    response_time = time.time() - start_time
                    return "UP", response_time
    except Exception:
        pass  # Connection error or timeout
    return "DOWN", float("inf")


async def health_check(lb, interval=5):
    """
    Periodically checks the health of all servers in the load balancer.

    Args:
        lb (HybridLoadBalancer): Load balancer instance.
        interval (int): Health-check interval in seconds.
    """
    while True:
        for server in lb.servers:
            status, response_time = await check_server(server)
            server.status = status
            server.response_time = response_time
            if status == "DOWN":
                print(f"[HealthCheck] Server {server.host}:{server.port} is DOWN.")
            else:
                print(f"[HealthCheck] Server {server.host}:{server.port} is UP (Response Time: {response_time:.2f}s).")
        await asyncio.sleep(interval)