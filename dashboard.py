import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import plotly.graph_objs as go

# Define the metrics endpoint
METRICS_URL = "http://127.0.0.1:8080/metrics"

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Load Balancer Metrics Dashboard"

# Define layout
app.layout = html.Div([
    html.H1("Load Balancer Metrics Dashboard", style={"textAlign": "center"}),

    dcc.Interval(
        id="update-interval",
        interval=2000,  # Update every 2 seconds
        n_intervals=0
    ),

    html.Div(id="graphs-container", style={"marginTop": "20px"}),

    html.Div(id="error-container", style={"textAlign": "center", "color": "red", "marginTop": "20px"}),
])


def fetch_metrics():
    """
    Fetch metrics from the load balancer's /metrics endpoint.
    """
    try:
        response = requests.get(METRICS_URL, timeout=5)  # Set timeout to avoid hanging
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching metrics: {e}")
    return []


@app.callback(
    [Output("graphs-container", "children"), Output("error-container", "children")],
    [Input("update-interval", "n_intervals")]
)
def update_graphs(n):
    """
    Updates graphs with the latest metrics data.
    """
    metrics = fetch_metrics()

    if not metrics:
        return [], "Error: Unable to fetch metrics from /metrics endpoint."

    # Extract metrics data
    server_names = [f"{m['host']}:{m['port']}" for m in metrics]
    dynamic_weights = [m.get("dynamic_weight", 0) for m in metrics]
    response_times = [m.get("response_time", 0) for m in metrics]
    cpu_utilizations = [m.get("cpu_utilization", 0) for m in metrics]
    statuses = [m["status"] for m in metrics]

    # Create graphs
    graphs = []

    # Traffic distribution (Dynamic Weight)
    graphs.append(dcc.Graph(
        id="traffic-distribution",
        figure=go.Figure(
            data=[go.Bar(x=server_names, y=dynamic_weights, name="Dynamic Weight", marker_color="blue")],
            layout=go.Layout(title="Traffic Distribution (Dynamic Weights)", xaxis={"title": "Servers"}, yaxis={"title": "Dynamic Weight"})
        )
    ))

    # Response time graph
    graphs.append(dcc.Graph(
        id="response-time",
        figure=go.Figure(
            data=[go.Bar(x=server_names, y=response_times, name="Response Time", marker_color="green")],
            layout=go.Layout(title="Response Times", xaxis={"title": "Servers"}, yaxis={"title": "Response Time (s)"})
        )
    ))

    # CPU Utilization graph
    graphs.append(dcc.Graph(
        id="cpu-utilization",
        figure=go.Figure(
            data=[go.Bar(x=server_names, y=cpu_utilizations, name="CPU Utilization", marker_color="orange")],
            layout=go.Layout(title="CPU Utilization", xaxis={"title": "Servers"}, yaxis={"title": "CPU Usage (%)"})
        )
    ))

    # Server status
    graphs.append(html.Div([
        html.H3("Server Status", style={"textAlign": "center", "marginTop": "20px"}),
        html.Ul([html.Li(f"{name}: {'🟢 UP' if status == 'UP' else '🔴 DOWN'}") for name, status in zip(server_names, statuses)], style={"listStyleType": "none", "textAlign": "left", "paddingLeft": "20px"})
    ]))

    return graphs, ""


if __name__ == "__main__":
    app.run_server(debug=True)