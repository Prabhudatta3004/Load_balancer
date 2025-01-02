#!/usr/bin/env python3
"""
servers.py
Runs three Flask servers: ServerA, ServerB, ServerC.
Each server has endpoints to simulate CPU spikes, ping fail, or HTTP fail.
"""
import threading
import time
import random
from flask import Flask, request

def create_server(name, port):
    app = Flask(name)

    # "Failure modes" we can toggle
    # - "normal": Everything works
    # - "cpu_spike": CPU usage is artificially high
    # - "ping_fail": We will simulate "network" fail by ignoring ping (we'll see how LB interprets it)
    # - "http_fail": Return HTTP 5xx from main endpoint
    server_state = {"mode": "normal"}

    @app.route("/")
    def index():
        if server_state["mode"] == "http_fail":
            return f"{name} is failing HTTP (simulated)!", 500
        else:
            return f"Hello from {name} (mode={server_state['mode']})"

    @app.route("/health")
    def health():
        """
        Standard health endpoint. If the server is in normal or cpu_spike mode,
        we return 200. If it's in http_fail, we also fail health. In real usage,
        you might want separate logic for health vs. main endpoint.
        """
        if server_state["mode"] in ("normal", "cpu_spike"):
            return "OK", 200
        return f"Health fail: {server_state['mode']}", 500

    @app.route("/simulate", methods=["POST"])
    def simulate_failure():
        """
        POST /simulate?mode=xxx
        Example: /simulate?mode=http_fail
        """
        mode = request.args.get("mode", "normal")
        server_state["mode"] = mode
        return f"{name} mode set to {mode}", 200

    def run_app():
        app.run(host="0.0.0.0", port=port, debug=False)

    return run_app

if __name__ == "__main__":
    # Create threads for each server
    serverA = threading.Thread(target=create_server("ServerA", 9001))
    serverB = threading.Thread(target=create_server("ServerB", 9002))
    serverC = threading.Thread(target=create_server("ServerC", 9003))

    serverA.start()
    serverB.start()
    serverC.start()

    # Keep main thread alive
    while True:
        time.sleep(1)