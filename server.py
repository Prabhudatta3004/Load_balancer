import argparse
from flask import Flask, jsonify, request
import time
import psutil  # For CPU utilization

app = Flask(__name__)

# Simulated server state
server_state = {
    "healthy": True,   # Indicates whether the server is healthy
    "delay": 0,        # Simulated processing delay in seconds
}

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to return server health status and CPU utilization.
    """
    cpu_utilization = psutil.cpu_percent(interval=0.1)  # Measure CPU utilization
    if server_state["healthy"]:
        return jsonify({
            "status": "UP",
            "cpu_utilization": cpu_utilization
        }), 200
    else:
        return jsonify({
            "status": "DOWN",
            "cpu_utilization": cpu_utilization
        }), 500

@app.route('/process', methods=['POST'])
def process_request():
    """
    Simulates processing a request with optional delay and health state.
    """
    time.sleep(server_state["delay"])  # Blocking delay
    if not server_state["healthy"]:
        return jsonify({"error": "Server is down"}), 500
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid request. JSON data is required."}), 400

    return jsonify({
        "status": "success",
        "message": f"Processed data: {data}"
    }), 200

@app.route('/simulate', methods=['POST'])
def simulate():
    """
    Allows dynamic simulation of server behavior by updating health state and delay.
    """
    data = request.json
    server_state["healthy"] = data.get("healthy", True)
    server_state["delay"] = data.get("delay", 0)
    return jsonify({"status": "Simulation updated"}), 200

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run mock server.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, default=9001, help="Port number")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port)