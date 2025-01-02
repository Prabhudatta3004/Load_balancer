#!/usr/bin/env python3
"""
lb.py
A load balancer with dynamic Weighted RR + a simple circuit breaker for each server.
"""

import time
import threading
import requests
import subprocess
import random
from flask import Flask, jsonify

###############################################################################
# Configuration
###############################################################################
SERVERS = [
    {"name": "ServerA", "host": "127.0.0.1", "port": 9001},
    {"name": "ServerB", "host": "127.0.0.1", "port": 9002},
    {"name": "ServerC", "host": "127.0.0.1", "port": 9003},
]

HEALTH_CHECK_INTERVAL = 5  # seconds
FAIL_THRESHOLD = 3         # consecutive fails before circuit opens
OPEN_COOLDOWN = 10         # how long to stay open before half-open test

# Global dictionary to store server metrics + circuit breaker state
metrics_data = {
    srv["name"]: {
        "ping_ms": None,
        "http_ok": False,
        "cpu_usage": 100.0,   # placeholder
        "weight": 0.0,
        "requests_forwarded": 0,

        # Circuit Breaker fields:
        "cb_state": "CLOSED",            # or OPEN, HALF_OPEN
        "consecutive_failures": 0,
        "last_opened": 0,                # timestamp
    }
    for srv in SERVERS
}

app = Flask(__name__)

###############################################################################
# Health Checks & Circuit Breaker
###############################################################################
def ping_server(server):
    """
    We'll interpret a 'ping_fail' mode from the server by checking special endpoint /simulate?mode=ping_fail
    But let's do a naive approach:
      1. We'll fetch the server's mode from /simulate?report=true (not implemented in servers.py),
         or we can assume if 'ping_fail' => artificially set ping to None or 9999.

    For simplicity, let's just do a real ping command. If the server is truly unreachable, returns None.
    """
    try:
        cmd = ["ping", "-c", "1", "-W", "1", server["host"]]
        output = subprocess.check_output(cmd).decode()
        for line in output.split("\n"):
            if "avg" in line:
                parts = line.split("=")[1].strip().split("/")
                avg_ms = float(parts[1])
                return avg_ms
        return None
    except Exception:
        return None

def check_http_health(server):
    """
    Check /health endpoint. If 2xx => True, else => False
    """
    url = f"http://{server['host']}:{server['port']}/health"
    try:
        r = requests.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False

def mock_cpu_usage(server_name):
    """
    If the server is in "cpu_spike" mode, report high CPU usage. Otherwise random normal usage.
    We'll guess the mode by seeing if the last known mode was "cpu_spike."
    Real-world usage: query actual CPU metrics from the server or an agent.
    """
    # Check "http_ok" or we could do something else to detect mode
    # We'll just randomly generate if it's "http_ok" == True
    if metrics_data[server_name]["http_ok"]:
        # let's see if we store some usage scenario. We'll do random between 10 and 30 for normal,
        # or random between 80 and 95 for "cpu_spike"
        # Just to keep it fun, let's do a 20% chance it's spiking if the server is in "cpu_spike" mode
        # For brevity, let's skip a real check and do random logic:
        if random.random() < 0.2:  # 20% chance big spike
            return random.uniform(80, 95)
        else:
            return random.uniform(10, 30)
    else:
        # if http is not okay, let's just mark CPU as 100
        return 100.0

def compute_weight(server_name, ping_ms, http_ok, cpu_usage):
    """
    Simplistic formula:
     if circuit is OPEN => weight=0
     else => weight = (1/(ping_ms+1)) + (1 - cpu/100)
    """
    # If circuit is open, skip
    if metrics_data[server_name]["cb_state"] == "OPEN":
        return 0.0

    if not http_ok:
        # If server is down => weight=0
        return 0.0

    if ping_ms is None:
        ping_ms = 9999

    inv_ping = 1.0 / (ping_ms + 1.0)
    cpu_factor = max(0.0, 1.0 - cpu_usage / 100.0)
    w = inv_ping + cpu_factor
    return max(w, 0.0)

def update_circuit_breaker(server_name, http_ok, ping_ok):
    """
    Updates the circuit breaker state machine based on success/failure.
    1. If the circuit is CLOSED:
       - if fail => consecutive_failures++ 
         if consecutive_failures >= FAIL_THRESHOLD => OPEN circuit
    2. If OPEN:
       - skip checks until OPEN_COOLDOWN has passed => then move to HALF_OPEN
    3. If HALF_OPEN:
       - one test:
         if success => CLOSED, consecutive_failures=0
         if fail => OPEN again (reset last_opened)
    """
    state = metrics_data[server_name]["cb_state"]
    fails = metrics_data[server_name]["consecutive_failures"]
    now = time.time()
    success = (http_ok and ping_ok)

    if state == "CLOSED":
        if not success:
            fails += 1
            if fails >= FAIL_THRESHOLD:
                # Open the circuit
                metrics_data[server_name]["cb_state"] = "OPEN"
                metrics_data[server_name]["last_opened"] = now
            metrics_data[server_name]["consecutive_failures"] = fails
        else:
            metrics_data[server_name]["consecutive_failures"] = 0

    elif state == "OPEN":
        # Check if cooldown passed
        if now - metrics_data[server_name]["last_opened"] > OPEN_COOLDOWN:
            # move to HALF_OPEN
            metrics_data[server_name]["cb_state"] = "HALF_OPEN"
            metrics_data[server_name]["consecutive_failures"] = 0  # reset to test again

    elif state == "HALF_OPEN":
        # We do a single test
        if success:
            # close circuit
            metrics_data[server_name]["cb_state"] = "CLOSED"
            metrics_data[server_name]["consecutive_failures"] = 0
        else:
            # fail again => re-open
            metrics_data[server_name]["cb_state"] = "OPEN"
            metrics_data[server_name]["last_opened"] = now

def health_check_loop():
    """
    Periodically checks each server, updates circuit breaker and recalculates weight.
    """
    while True:
        for srv in SERVERS:
            name = srv["name"]

            # If circuit is OPEN, we might skip or we still measure ping just to see if it's up again
            avg_ping = ping_server(srv)
            ping_ok = (avg_ping is not None and avg_ping < 9999)

            http_ok = check_http_health(srv)

            # Update circuit breaker
            update_circuit_breaker(name, http_ok, ping_ok)

            # If the circuit is half-open or closed, we still measure CPU usage (mocked)
            cpu_val = mock_cpu_usage(name) if (metrics_data[name]["cb_state"] != "OPEN" or http_ok) else 100.0

            # Compute new weight
            w = compute_weight(name, avg_ping, http_ok, cpu_val)

            # Update
            metrics_data[name]["ping_ms"] = avg_ping if ping_ok else 9999
            metrics_data[name]["http_ok"] = http_ok
            metrics_data[name]["cpu_usage"] = cpu_val
            metrics_data[name]["weight"] = w

        time.sleep(HEALTH_CHECK_INTERVAL)

###############################################################################
# Weighted Round Robin
###############################################################################
def get_next_server():
    """
    Weighted random selection.
    If all weights are 0 => pick random from the entire list (fallback).
    """
    active_servers = []
    for srv in SERVERS:
        w = metrics_data[srv["name"]]["weight"]
        if w > 0:
            active_servers.append((srv, w))

    if not active_servers:
        return random.choice(SERVERS)

    total_weight = sum(w for (_, w) in active_servers)
    r = random.uniform(0, total_weight)
    upto = 0
    for srv, w in active_servers:
        if upto + w >= r:
            return srv
        upto += w
    return random.choice(SERVERS)

###############################################################################
# Flask App (LB)
###############################################################################
app = Flask(__name__)

@app.route("/")
def lb_root():
    """
    Forward GET request to Weighted RR server.
    """
    srv = get_next_server()
    metrics_data[srv["name"]]["requests_forwarded"] += 1
    url = f"http://{srv['host']}:{srv['port']}/"
    try:
        r = requests.get(url, timeout=2)
        return f"{srv['name']} => {r.text}", r.status_code
    except Exception as e:
        return f"Error contacting {srv['name']}: {e}", 503

@app.route("/health")
def lb_health():
    return "LB OK", 200

@app.route("/metrics")
def lb_metrics():
    return jsonify(metrics_data), 200

if __name__ == "__main__":
    # Start health check thread
    t = threading.Thread(target=health_check_loop, daemon=True)
    t.start()

    # Run the LB
    app.run(host="0.0.0.0", port=5100)