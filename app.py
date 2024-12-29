import asyncio
import json
from lb_core import Server, HybridLoadBalancer
from health_check import health_check


async def metrics_handler(lb, reader, writer):
    """
    Handles requests to the metrics endpoint and responds with server stats in JSON format.
    """
    try:
        print("[MetricsHandler] Received a request.")

        # Collect metrics from load balancer servers
        metrics = [
            {
                "host": s.host,
                "port": s.port,
                "status": s.status,
                "circuit": s.circuit_breaker["state"],
                "fail_count": s.circuit_breaker["fail_count"],
                "response_time": s.response_time,
                "weight": s.weight,
            }
            for s in lb.servers
        ]

        # Prepare JSON response
        response_body = json.dumps(metrics, indent=2)
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            f"Connection: close\r\n\r\n"
            + response_body
        )

        print("[MetricsHandler] Sending response.")

        # Send response
        writer.write(response.encode("utf-8"))
        await writer.drain()  # Ensure all data is flushed to the client

    except Exception as e:
        print(f"[MetricsHandler] Error occurred: {e}")
    finally:
        print("[MetricsHandler] Closing connection.")
        # Properly close the connection
        writer.close()
        await writer.wait_closed()

async def main():
    """
    Main entry point to start the load balancer and metrics endpoint.
    """
    # 1. Define backend servers
    servers = [
        Server("127.0.0.1", 9001, weight=1),
        Server("127.0.0.1", 9002, weight=2),
    ]

    # 2. Initialize the load balancer
    lb = HybridLoadBalancer(
        servers=servers,
        fail_threshold=3,
        open_time=5,
        sticky_session=False,  # No sticky sessions for this example
        adjust_weights=True,  # Enable dynamic weight adjustment
    )

    # 3. Start periodic health checks
    print("[App] Starting health checks.")
    asyncio.create_task(health_check(lb, interval=5))

    # 4. Start metrics server on port 9090
    print("[App] Starting metrics server on port 9090.")
    metrics_server = await asyncio.start_server(
        lambda r, w: metrics_handler(lb, r, w), "0.0.0.0", 9090
    )

    # 5. Start load balancer server on port 8080
    print("[App] Starting load balancer on port 8080.")
    server = await asyncio.start_server(
        lb.handle_request, "0.0.0.0", 8080
    )

    # 6. Serve both servers indefinitely
    async with metrics_server, server:
        print("[App] Both servers are running.")
        await asyncio.gather(metrics_server.serve_forever(), server.serve_forever())


if __name__ == "__main__":
    try:
        print("[App] Starting application...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[App] Shutting down gracefully.")
    except Exception as e:
        print(f"[App] Unhandled error: {e}")