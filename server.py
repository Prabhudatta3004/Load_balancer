import argparse
from flask import Flask, jsonify, request
import time

app = Flask(__name__)

# Simulated server state
server_state = {
    "healthy": True,
    "delay": 0,
}

@app.route('/health', methods=['GET'])
def health_check():
    if server_state["healthy"]:
        return jsonify({"status": "UP"}), 200
    else:
        return jsonify({"status": "DOWN"}), 500

@app.route('/process', methods=['POST'])
def process_request():
    time.sleep(server_state["delay"])
    if not server_state["healthy"]:
        return jsonify({"error": "Server is down"}), 500
    data = request.json
    return jsonify({"status": "success", "message": f"Processed data: {data}"}), 200

@app.route('/simulate', methods=['POST'])
def simulate():
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