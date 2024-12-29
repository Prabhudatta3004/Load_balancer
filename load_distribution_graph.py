import requests
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Server metrics endpoint
METRICS_URL = "http://127.0.0.1:9090"

# Data store
server_data = {}

def fetch_metrics():
    """
    Fetches metrics from the load balancer's metrics endpoint.
    Updates the server_data dictionary.
    """
    try:
        response = requests.get(METRICS_URL)
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            for line in lines:
                if line.startswith("Server"):
                    parts = line.split("|")
                    host_port = parts[0].split()[1]
                    status = parts[1].split("=")[1].strip()
                    weight = float(parts[4].split("=")[1].strip())
                    response_time = float(parts[3].split("=")[1].strip())

                    server_data[host_port] = {
                        "status": status,
                        "weight": weight,
                        "response_time": response_time
                    }
    except requests.RequestException as e:
        print(f"Error fetching metrics: {e}")

def update_graph(i):
    """
    Updates the graph with the latest metrics.
    """
    fetch_metrics()
    if server_data:
        servers = list(server_data.keys())
        weights = [server_data[s]["weight"] for s in servers]
        response_times = [server_data[s]["response_time"] for s in servers]

        # Clear and redraw
        ax.clear()
        ax.bar(servers, weights, label="Weights", alpha=0.7)
        ax.plot(servers, response_times, color="red", marker="o", label="Response Times")

        ax.set_title("Load Distribution")
        ax.set_xlabel("Servers")
        ax.set_ylabel("Metrics")
        ax.legend(loc="upper right")

# Initialize the plot
fig, ax = plt.subplots()
ani = FuncAnimation(fig, update_graph, interval=1000)

# Start the visualization
plt.show()