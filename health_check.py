import asyncio
import time
import aiohttp
import os


async def ping_check(server):
    """
    Performs a ping check to verify basic network connectivity.

    Args:
        server (Server): The server instance.
    """
    response = os.system(f"ping -c 1 {server.host} > /dev/null 2>&1")  # Ping once, suppress output
    return response == 0


async def http_check(server, timeout=2):
    """
    Performs an HTTP health check to ensure the server responds correctly.

    Args:
        server (Server): The server instance.
        timeout (int): Timeout for the health check request.

    Returns:
        tuple: (status, response_time). Status is 'UP' or 'DOWN', response_time is the measured latency.
    """
    url = f"http://{server.host}:{server.port}/health"  # Target the server's /health endpoint
    start_time = time.time()  # Record start time for measuring response latency
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    response_time = time.time() - start_time
                    return "UP", response_time
    except Exception:
        pass  # Handle connection errors or timeouts gracefully
    return "DOWN", float("inf")


async def check_server(server, timeout=2):
    """
    Performs a multi-layer health check (Ping and HTTP) on a server.

    Args:
        server (Server): The server instance.
        timeout (int): Timeout for HTTP health check.

    Returns:
        tuple: (status, response_time). Status is 'UP' or 'DOWN', response_time is the measured latency.
    """
    # Step 1: Ping Check
    if not await ping_check(server):
        print(f"[HealthCheck] Ping failed for {server.host}:{server.port}")
        return "DOWN", float("inf")

    # Step 2: HTTP Check
    status, response_time = await http_check(server, timeout)
    if status == "UP":
        return "UP", response_time

    return "DOWN", float("inf")


async def health_check(lb, stable_interval=5, unstable_interval=2):
    """
    Periodically performs health checks on all servers in the load balancer.

    Args:
        lb (HybridLoadBalancer): The load balancer instance.
        stable_interval (int): Interval for stable servers.
        unstable_interval (int): Interval for unstable servers.
    """
    while True:  # Infinite loop to continuously check server health
        for server in lb.servers:
            # Dynamic interval based on server stability
            interval = unstable_interval if server.status == "DOWN" else stable_interval
            status, response_time = await check_server(server)

            # Update server status and log results
            server.status = status
            server.response_time = response_time

            if status == "DOWN":
                print(f"[HealthCheck] Server {server.host}:{server.port} is DOWN.")
            else:
                print(f"[HealthCheck] Server {server.host}:{server.port} is UP (Response Time: {response_time:.2f}s).")
            
            await asyncio.sleep(interval)  # Wait for the interval before the next check
