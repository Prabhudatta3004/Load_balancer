from flask import Flask, request, jsonify
from lb_core import Server, LoadBalancer
import asyncio

app = Flask(__name__)

# Define backend servers
servers = [
    Server("127.0.0.1", 9001, weight=1),
    Server("127.0.0.1", 9002, weight=2),
    Server("127.0.0.1", 9003, weight=1),
]

# Initialize load balancer
lb = LoadBalancer(servers, fail_threshold=3, open_time=5, sticky_session=True, session_mode="ip")


@app.route("/process", methods=["POST"])
def handle_request():
    """
    Handles client requests and forwards them to a backend server.
    """
    payload = request.json
    client_ip = request.remote_addr  # Use client IP as session identifier
    chosen_server = lb._choose_server(client_id=client_ip)

    if not chosen_server:
        return jsonify({"error": "No available servers"}), 503

    # Use a synchronous wrapper for the asynchronous `_forward_request` method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response_data, status_code = loop.run_until_complete(lb._forward_request(chosen_server, payload))
    finally:
        loop.close()

    return jsonify(response_data), status_code


@app.route("/metrics", methods=["GET"])
def metrics_endpoint():
    """
    Exposes server metrics for monitoring and visualization.
    """
    return jsonify([
        {
            "host": server.host,
            "port": server.port,
            "status": server.status,
            "response_time": server.response_time,
            "dynamic_weight": server.dynamic_weight,
            "cpu_utilization": server.cpu_utilization or 0.0,
            "circuit_breaker": server.circuit_breaker,
        }
        for server in lb.servers
    ])


@app.route("/reset", methods=["POST"])
def reset_circuit_breakers():
    """
    Resets all circuit breakers for manual recovery or testing.
    """
    for server in lb.servers:
        lb._reset_circuit_breaker(server)
    return jsonify({"status": "All circuit breakers reset."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)