from flask import Flask, jsonify, render_template
import requests
import threading
import time

app = Flask(__name__)
metrics_url = "http://localhost:9090/"  # Load balancer metrics endpoint
cached_metrics = []


def fetch_metrics():
    """
    Periodically fetch metrics from the load balancer's /metrics endpoint.
    """
    global cached_metrics
    while True:
        try:
            response = requests.get(metrics_url, timeout=5)
            if response.status_code == 200:
                cached_metrics = response.json()
        except Exception as e:
            print(f"[Error] Failed to fetch metrics: {e}")
        time.sleep(5)  # Fetch metrics every 5 seconds


@app.route("/api/metrics")
def api_metrics():
    """
    API endpoint to serve cached metrics to the frontend.
    """
    return jsonify(cached_metrics)


@app.route("/")
def dashboard():
    """
    Render the dashboard page.
    """
    return render_template("/dashboard.html")


if __name__ == "__main__":
    # Start the metrics fetching thread
    threading.Thread(target=fetch_metrics, daemon=True).start()

    # Run the Flask app
    app.run(host="0.0.0.0", port=5050, debug=True)