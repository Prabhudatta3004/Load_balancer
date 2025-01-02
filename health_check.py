import asyncio
import time
import aiohttp
import os


async def ping_check(server):
    """
    Performs a ping check to verify basic network connectivity.
    """
    response = os.system(f"ping -c 1 {server.host} > /dev/null 2>&1")  # Ping once, suppress output
    return response == 0


async def http_check(server, timeout=2):
    """
    Performs an HTTP health check to ensure the server responds correctly.
    """
    url = f"http://{server.host}:{server.port}/health"
    start_time = time.time()  # Record start time for measuring response latency
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()  # Parse JSON response
                    response_time = time.time() - start_time
                    cpu_utilization = data.get("cpu_utilization", 0.0)  # Get CPU utilization if provided
                    return "UP", response_time, cpu_utilization
    except Exception as e:
        print(f"[HealthCheck] HTTP check failed for {server.host}:{server.port}: {e}")
    return "DOWN", float("inf"), 0.0


async def check_server(server, timeout=2, cpu_threshold=90):
    """
    Performs a multi-layer health check (Ping, HTTP, and CPU utilization) on a server.
    """
    if not await ping_check(server):
        print(f"[HealthCheck] Ping failed for {server.host}:{server.port}")
        return "DOWN", float("inf"), server.cpu_utilization

    status, response_time, cpu_utilization = await http_check(server, timeout)
    if status == "UP" and cpu_utilization <= cpu_threshold:
        return "UP", response_time, cpu_utilization

    print(f"[HealthCheck] Server {server.host}:{server.port} is OVERLOADED or DOWN (CPU: {cpu_utilization}%)")
    return "DOWN", response_time, cpu_utilization


async def health_check(lb, stable_interval=5, unstable_interval=2, cpu_threshold=90):
    """
    Periodically performs health checks on all servers in the load balancer.
    """
    while True:
        health_check_tasks = [
            check_server(server, cpu_threshold=cpu_threshold) for server in lb.servers
        ]
        results = await asyncio.gather(*health_check_tasks)

        for i, server in enumerate(lb.servers):
            status, response_time, cpu_utilization = results[i]
            server.status = status
            server.response_time = response_time
            server.cpu_utilization = cpu_utilization
            print(
                f"[HealthCheck] Server {server.host}:{server.port} | Status: {status} | "
                f"Response Time: {response_time:.2f}s | CPU: {cpu_utilization:.2f}%"
            )

        await asyncio.sleep(stable_interval)